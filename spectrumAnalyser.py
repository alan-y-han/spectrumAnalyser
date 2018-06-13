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


# bins
noBins = 30
maxFreq = 8000
gamma = 1.19

# scaleF = float(maxFreq - 1) / pow(noBins + 1, gamma)
scaleF = float(maxFreq) / pow(gamma, noBins - 1)

# bins = [int(scaleF * pow(x, gamma)) for x in xrange(noBins + 1)]
# bins = [int(200 + ((500.0 / (noBins + 1)) * x)) for x in xrange(noBins + 1)]
print scaleF
# bins = [int(scaleF * pow(gamma, x)) for x in xrange(noBins + 1)]
bins = [0]
for x in xrange(noBins):
    bins.append(int(scaleF * pow(gamma, x)))
print bins


# weighting

maxWeight = 32

# scaleF = float(maxWeight) / pow(noBins, gamma)
scaleF = float(maxWeight - 1) / pow(gamma, noBins - 1)

# weighting = (np.array([int(scaleF * pow(x, gamma)) + 1 for x in xrange(noBins)]))
# weighting = [3] * noBins
weighting = (np.array([scaleF * pow(gamma, x) + 1 for x in xrange(noBins)]))
print weighting


#other stuff
matrix = [0] * noBins
power = []


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
        minI = power_index(bins[i])
        maxI = power_index(bins[i + 1])
        if minI != maxI:
            matrix[i] = int(np.mean(power[power_index(bins[i]) : power_index(bins[i + 1])]))
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
#     print matrix


mdp.set_brightness(1.0)
data = wavfile.readframes(chunk)

while data != '':
    output.write(data)
    matrix = compute_fft(data, chunk, sample_rate)
    drawMatrix(matrix)
    data = wavfile.readframes(chunk)
