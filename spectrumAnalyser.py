import sys
import signal
import pyaudio
import numpy as np
import microdotphat as mdp


def power_index(val, chunkSize, sampleRate):
    return int(2 * chunkSize * val / sampleRate)


def compute_fft(data, bins, weighting):
    fourier = np.fft.rfft(data)
    fourier = np.delete(fourier, len(fourier) - 1)

    power = np.abs(fourier)

    matrix = [0] * (len(bins) - 1)

    for i in xrange(len(matrix)):
        matrix[i] = int(np.mean(power[bins[i] : bins[i + 1]]))

    matrix = np.divide(np.multiply(matrix, weighting), 1000000)
    # matrix = matrix.clip(0, 7)

    return matrix


MDP_HEIGHT = 6

def drawMatrix(matrix):

    gamma = 1.5

    mdp.clear()

    for x in range(len(matrix)):
        buf_x = x + ((x / 5) * 3)

        for y in xrange(7):            
            if matrix[x] > pow(gamma, y):
                mdp.set_pixel(buf_x, MDP_HEIGHT - y, 1)
            else:
                break


        # for y in range(int(matrix[x])):
            

    mdp.show()


def sigIntHandler(signalNo, frame):
    # clean up
    inStream.stop_stream()
    inStream.close()
    p.terminate()

    sys.exit(0)


if __name__ == '__main__':
    # setup audio input
    sampleRate = 44100
    no_channels = 1
    chunkSize = 512

    p = pyaudio.PyAudio()

    inStream = p.open(
        format=pyaudio.paInt16,
        channels=no_channels,
        rate=sampleRate,
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

    bins = [power_index(freq, chunkSize, sampleRate) for freq in freqBins]
    for i in xrange(1, len(bins)):
        if bins[i] <= bins[i - 1]:
            bins[i] = bins[i - 1] + 1

    print bins

    # weighting
    maxWeight = 32
    scaleF = float(maxWeight - 1) / pow(gamma, noBins - 1)
    weighting = (np.array([scaleF * pow(gamma, x) + 1 for x in xrange(noBins)]))
    print weighting

    mdp.set_brightness(1.0)
    signal.signal(signal.SIGINT, sigIntHandler)

    while True:

        rawsamps = inStream.read(chunkSize, False)
        # Convert raw data to NumPy array
        samps = np.fromstring(rawsamps, dtype=np.int16)

        matrix = compute_fft(samps, bins, weighting)
        drawMatrix(matrix)
