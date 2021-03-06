from FanWheels_PIL import *
import numpy as np
from pydub import AudioSegment


class AudioAnalyzer:
    def __init__(self, file_path, ffmpeg_path, fps=30):
        AudioSegment.ffmpeg = ffmpeg_path
        sound = AudioSegment.from_file(file_path)
        self.samples = np.asarray(sound.get_array_of_samples(), dtype=np.float)
        if np.max(self.samples) != 0:
            self.samples = self.samples / np.max(self.samples)
        self.sample_rate = sound.frame_rate
        self.T = 1.0 / self.sample_rate

        self.fps = fps
        self.totalFrames = self.getTotalFrames()
        print("total frames", self.totalFrames)

    def fftAnalyzer(self, start_p, stop_p, fq_low=20, fq_up=6000, bins=80):
        freq_array = np.zeros(bins)
        if stop_p <= 0:
            return freq_array
        if start_p < 0:
            start_p = 0
        if start_p >= self.samples.shape[0] - self.sample_rate / fq_low:
            return freq_array
        if stop_p >= self.samples.shape[0]:
            stop_p = self.samples.shape[0] - 1
        y = self.samples[start_p:stop_p]
        N = y.shape[0]
        yf = np.fft.fft(y)
        yf_fq = 2.0 / N * np.abs(yf[:N // 2])
        xf = np.linspace(0.0, 1.0 / (2.0 * self.T), N // 2)
        freq_step = (fq_up - fq_low) / bins
        freq_chunck = xf[1] - xf[0]
        for i in range(bins):
            win_low = fq_low + freq_step * i
            win_up = win_low + freq_step
            win_low = round(win_low / freq_chunck / 2)
            win_up = round(win_up / freq_chunck / 2)
            if win_low >= xf.shape[0]:
                break
            if win_up >= xf.shape[0]:
                win_up = xf.shape[0] - 1
            freq_array[i] = np.sum(yf_fq[win_low:win_up])
        return freq_array

    def getSampleRate(self):
        return self.sample_rate

    def getLength(self):
        return self.samples.shape[0]

    def getTotalFrames(self):
        return int(self.fps * self.getLength() / self.getSampleRate()) + 1

    def getHistAtFrame(self, index, fq_low=20, fq_up=6000, bins=80):
        if index < 0:
            index = -5
        if index > self.totalFrames:
            index = -5
        middle = index * self.getSampleRate() / self.fps
        offset = self.sample_rate / fq_low
        left = int(round(middle)-0.5*offset)
        right = int(round(middle + 2.5*offset))
        return self.fftAnalyzer(left, right, fq_low, fq_up, bins)

def circle(draw, center, radius, fill):
    draw.ellipse((center[0] - radius + 1, center[1] - radius + 1, center[0] + radius - 1, center[1] + radius - 1),
                 fill=fill, outline=None)

def getCycleHue(start,end,bins,index,cycle=1):
    div = end - start
    fac = index/bins*cycle
    ratio = abs(round(fac)-fac)*2
    return (div*ratio + start)/360


def getColor(bins,index,color_mode="color4x"):
    sat = 0.8
    brt = 1.0
    if color_mode=="color4x":
        return hsv_to_rgb(4 * index / bins, sat, brt) + (255,)
    if color_mode == "color2x":
        return hsv_to_rgb(2 * index / bins, sat, brt) + (255,)
    if color_mode == "color1x":
        return hsv_to_rgb(1 * index / bins, sat, brt) + (255,)
    if color_mode == "white":
        return hsv_to_rgb(0, 0, brt) + (255,)
    if color_mode == "red":
        return hsv_to_rgb(0, sat, brt) + (255,)
    if color_mode == "green":
        return hsv_to_rgb(129/360, sat, brt) + (255,)
    if color_mode == "blue":
        return hsv_to_rgb(211/360, sat, brt) + (255,)
    if color_mode == "yellow":
        return hsv_to_rgb(49/360, sat, brt) + (255,)
    if color_mode == "magenta":
        return hsv_to_rgb(328/360, sat, brt) + (255,)
    if color_mode == "purple":
        return hsv_to_rgb(274/360, sat, brt) + (255,)
    if color_mode == "cyan":
        return hsv_to_rgb(184/360, sat, brt) + (255,)
    if color_mode == "lightgreen":
        return hsv_to_rgb(171/360, sat, brt) + (255,)
    if color_mode == "green-blue":
        return hsv_to_rgb(getCycleHue(122,220,bins,index,4), sat, brt) + (255,)
    if color_mode == "magenta-purple":
        return hsv_to_rgb(getCycleHue(300,370,bins,index,4), sat, brt) + (255,)
    if color_mode == "red-yellow":
        return hsv_to_rgb(getCycleHue(-20,40,bins,index,4), sat, brt) + (255,)
    if color_mode == "yellow-green":
        return hsv_to_rgb(getCycleHue(42,147,bins,index,4), sat, brt) + (255,)
    if color_mode == "blue-purple":
        return hsv_to_rgb(getCycleHue(208,313,bins,index,4), sat, brt) + (255,)
    return hsv_to_rgb(0, 0, brt) + (255,)


class AudioVisualizer:
    def __init__(self, img, rad_min, rad_max, line_thick,blur=5):
        self.background = img.copy()
        self.width, self.height = self.background.size
        self.mdpx = self.width / 2
        self.mdpy = self.height / 2
        self.rad_min = rad_min
        self.rad_max = rad_max
        self.rad_div = rad_max - rad_min
        self.line_thick = line_thick
        self.blur = blur

    def getFrame(self, hist,amplify = 5,color_mode="color4x"):
        bins = hist.shape[0]
        hist = np.clip(hist*amplify,0,1)

        ratio = 2 # antialiasing ratio
        line_thick = self.line_thick*ratio
        canvas = Image.new('RGBA', (self.width*ratio, self.height*ratio), (22,22,22,0))
        draw = ImageDraw.Draw(canvas)

        for i in range(bins):
            color = getColor(bins,i,color_mode)
            line_points = [self.getAxis(bins, i, self.rad_min,ratio),
                           self.getAxis(bins, i, self.rad_min+hist[i]*self.rad_div,ratio)]
            draw.line(line_points, width=line_thick, fill=color, joint='curve')
            circle(draw, line_points[0], line_thick / 2, color)
            circle(draw, line_points[1], line_thick / 2, color)

        canvas_blur = canvas.filter(ImageFilter.GaussianBlur(radius=self.blur*ratio))
        canvas = ImageChops.add(canvas, canvas_blur)
        canvas = canvas.resize(( self.width, self.height),Image.ANTIALIAS)

        output = self.background.copy()
        output.paste(canvas,(0,0),canvas)
        return output

    def getAxis(self, bins, index, radius,ratio):
        div = 2 * np.pi / bins
        angle = div * index - np.pi/2 - np.pi/3
        ox = (self.mdpx + radius * np.cos(angle))*ratio
        oy = (self.mdpy + radius * np.sin(angle))*ratio
        return ox, oy
