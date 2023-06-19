from scipy import signal as sg
import numpy as np
import matplotlib.pyplot as plt

def find_first_local_min_below_threshold(array, threshold):
    """
    Finds the index of the first local minima in an array below a given threshold.  

    Parameters:
    - array (ndarray): Input array to search for local minima.
    - threshold (float): Threshold value for the first local minima.  
    
    Returns:
    - index (int): Index of the first local minima below the threshold. Returns None if no such minima found.
    """
    local_minima_indices = sg.argrelmin(array)[0]
    for index in local_minima_indices:
        if array[index] < threshold:
            return index
    return None

def parabolic_interp(prev, max, next):
    """
    Performs parabolic interpolation to estimate the exact x position of the local minima.

    Parameters:
    - prev (float): Value before the local minima.
    - max (float): Value at the local minima.
    - next (float): Value after the local minima.

    Returns:
    - x_max (float): Estimated x position of the local minima.
    """
    numerator = prev - next
    denominator = prev - 2 * max + next
    
    x_max = 0.5 * numerator / denominator
    
    return x_max

def difference_vectorized(x, W, max_tau):
    """
    Calculates the difference vector for pitch detection.

    Parameters:
    - x (ndarray): Input array.
    - W (int): Window size.
    - max_tau (int): Maximum tau value.

    Returns:
    - diff (ndarray): Difference vector.
    """
    diff = [0] * (max_tau + 1)
    for tau in range(max_tau + 1):
        diff[tau] = np.sum((x[1:W-tau] - x[1+tau:W])**2)
    return diff

# Function that calculates the cumulative mean normalized difference function.
def computeCmndf(x, W, min_tau, max_tau):
    """
    Computes the Cumulative Mean Normalized Difference Function (CMNDF) for pitch detection.

    Parameters:
    - x (ndarray): Input array.
    - W (int): Window size.
    - min_tau (int): Minimum delay value.
    - max_tau (int): Maximum delay value.

    Returns:
    - cmndf (ndarray): Cumulative Mean Normalized Difference Function.
    """
    cmndf = np.empty(max_tau - min_tau)
    diff = difference_vectorized(x, W, max_tau)
    for tau in range(min_tau, max_tau):
        if tau == 0:
            cmndf[tau - min_tau] = 1.0
        else:
            sum = np.sum(diff[1:tau+1])
            cmndf[tau - min_tau] = diff[tau] / (sum / tau)
    return cmndf

def pitchDetect(audio, fs, min_f0, max_f0, W = 256, decimation_factor = 8, cmndf_threshold = 0.4):
    """
    Performs pitch detection on an audio signal.

    Parameters:
    - audio (ndarray): Input audio signal.
    - fs (int): Sampling frequency of the audio signal.
    - min_f0 (float): Minimum fundamental frequency (in Hz) to detect.
    - max_f0 (float): Maximum fundamental frequency (in Hz) to detect.
    - W (int): Window size for processing.
    - decimation_factor (int): Factor to downsample the audio signal for processing.
    - cmndf_threshold (float): Threshold for finding local minima in the Cumulative Mean Normalized Difference Function (CMNDF).

    Returns:
    - f0 (ndarray): Array of estimated pitch values corresponding to each frame in the audio signal. None values indicate no pitch detected.
    """
    f0 = []

    downsampled_audio = sg.decimate(audio, decimation_factor, zero_phase=True)
    downsampled_fs = fs // decimation_factor

    min_tau = downsampled_fs // max_f0
    max_tau = downsampled_fs // min_f0

    length = (len(downsampled_audio) // (W//2) - 1) * (W//2)

    for start in range(0, length , W//2):
      x = downsampled_audio[start:start+W]
      if (len(x) != W):
        break
      cmndf = computeCmndf(x, W, min_tau, max_tau)
      predicted_tau = find_first_local_min_below_threshold(cmndf, cmndf_threshold)
      if predicted_tau != None:
        interp_add = parabolic_interp(cmndf[predicted_tau - 1], cmndf[predicted_tau], cmndf[predicted_tau + 1])
        delay = min_tau + predicted_tau + interp_add
        res = downsampled_fs / delay
        f0.append(res)
      else:
        f0.append(None)
    return np.array(f0)

# Plot of the pitch estimation over the spectrogram
def plot_pitch_estimation(audio, fs, f0, min_f0, max_f0, decimation_factor = 8, W = 256, window_type = 'hamming'):
    downsampled_fs = fs // decimation_factor
    window = sg.get_window(window_type, W * decimation_factor)
    plt.rcParams.update({"axes.grid" : False})
    frequencies, times, spectrogram = sg.spectrogram(audio, fs, window = window)
    plt.figure(figsize=(8, 4))
    plt.pcolormesh(times, frequencies, 10 * np.log10(spectrogram))
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.colorbar(label='Power Spectral Density (dB)')
    plt.plot(np.arange(0, len(f0) * (W//2), (W//2))/downsampled_fs, f0)
    plt.ylim(min_f0, max_f0)
    plt.xlim(0, (len(f0) - 2) * (W//2) / downsampled_fs)

    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.title('Spectrogram and pitch estimation of the input audio signal')