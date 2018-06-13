import sys
import wave
import alsaaudio as aa
from struct import unpack
import numpy as np
import microdotphat as mdp

wavfile = wave.open(sys.argv[1], 'r')

sample_rate = wavfile.getframerate()
no_channels = wavfile.getnchannels()
chunk = 2048

output = aa.PCM(aa.PCM_PLAYBACK, aa.PCM_NORMAL)
output.setchannels(no_channels)
output.setrate(sample_rate)
output.setformat(aa.PCM_FORMAT_S16_LE)
output.setperiodsize(chunk)

# generate fft bins
noBins = 30

step = 8000 / noBins
bins = [x * step for x in xrange(noBins + 1)]


matrix    = [0] * noBins
power     = []
weighting = [1, 1, 1, 2, 2,
             2, 4, 4, 4, 4,
             8, 8, 8, 8, 8,
             8, 8, 8, 8, 8,
             8, 8, 16, 16, 16,
             16, 16, 16, 16, 16]


def power_index(val):
    return int(2 * chunk * val / sample_rate)

def compute_fft(data, chunk, sample_rate):
    global matrix
    data = unpack("%dh" % (len(data) / 2), data)
    data = np.array(data, dtype='h')

    fourier = np.fft.rfft(data)
    fourier = np.delete(fourier, len(fourier) - 1)

    power = np.abs(fourier)

    for i in xrange(noBins):
        matrix[i] = int(np.mean(power[power_index(bins[i]) : power_index(bins[i + 1])]))

    matrix = np.divide(np.multiply(matrix, weighting), 500000)
    matrix = matrix.clip(0, 6)

    return matrix


MDP_HEIGHT = 6

def drawMatrix(matrix):
    mdp.clear()
    for x in range(len(matrix)):
        for y in range(matrix[x]):
            buf_x = x + ((x / 5) * 3)
            mdp.set_pixel(buf_x, MDP_HEIGHT - y, 1)
    mdp.show()
    print matrix


mdp.set_brightness(1.0)
data = wavfile.readframes(chunk)

while data != '':
    output.write(data)
    matrix = compute_fft(data, chunk, sample_rate)
    drawMatrix(matrix)
    data = wavfile.readframes(chunk)
