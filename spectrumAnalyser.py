import sys
import pyaudio
from struct import unpack
import numpy as np
import microdotphat as mdp


sample_rate = 44100
no_channels = 1
chunk = 512


p = pyaudio.PyAudio()

inStream = p.open(
    format=pyaudio.paInt16,
    channels=no_channels,
    rate=sample_rate,
    # input_device_index=,
    input=True)


# bins
noBins = 30
maxFreq = 8000
gamma = 1.2

scaleF = float(maxFreq) / pow(gamma, noBins - 1)
freqBins = [0]
for x in xrange(noBins):
    freqBins.append(int(scaleF * pow(gamma, x)))





# weighting

maxWeight = 48
scaleF = float(maxWeight - 1) / pow(gamma, noBins - 1)
weighting = (np.array([scaleF * pow(gamma, x) + 1 for x in xrange(noBins)]))
print weighting


#other stuff
matrix = [0] * noBins


def power_index(val):
    return int(2 * chunk * val / sample_rate)


bins = [power_index(freq) for freq in freqBins]
for i in xrange(1, len(bins)):
    if bins[i] <= bins[i - 1]:
        bins[i] = bins[i - 1] + 1

print bins


def compute_fft(data, chunk, sample_rate):
    global matrix
    # data = unpack("%dh" % (len(data) / 2), data)
    # data = np.array(data, dtype='h')

    fourier = np.fft.rfft(data)
    fourier = np.delete(fourier, len(fourier) - 1)

    power = np.abs(fourier)

    for i in xrange(noBins):
        minI = bins[i]
        maxI = bins[i + 1]
        if minI != maxI:
            matrix[i] = int(np.mean(power[bins[i] : bins[i + 1]]))
        else:
            matrix[i] = 0

    matrix = np.divide(np.multiply(matrix, weighting), 1500000)
    matrix = matrix.clip(0, 7)

    return matrix


MDP_HEIGHT = 6

def drawMatrix(matrix):
    mdp.clear()
    for x in range(len(matrix)):
        for y in range(int(matrix[x])):
            buf_x = x + ((x / 5) * 3)
            mdp.set_pixel(buf_x, MDP_HEIGHT - y, 1)
    mdp.show()


mdp.set_brightness(1.0)


while True:

    rawsamps = inStream.read(chunk, False)
    # Convert raw data to NumPy array
    samps = np.fromstring(rawsamps, dtype=np.int16)

    # output.write(data)
    matrix = compute_fft(samps, chunk, sample_rate)
    drawMatrix(matrix)
    # data = wavfile.readframes(chunk)
