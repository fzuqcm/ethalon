import numpy as np
from constants import POLYFIT_COEFFICIENT, DISSIPATION_PERCENT


def compute_res_freq(measure_points):
    ampls = np.array(measure_points['ampl'])
    freqs = np.array(measure_points['freq'])
    max_ampl_idx = ampls.argmax()
    max_ampl = ampls[max_ampl_idx]
    min_ampl = ampls.min()

    # check for weird data input
    # if max_ampl < 5000:
    #     raise ValueError("Weird data input")

    # set boundary from which fit polynomial
    polyfit_boundary = min_ampl + ((max_ampl - min_ampl) * POLYFIT_COEFFICIENT)

    # set left index for polyfit
    li = None
    for i in range(len(ampls)):
        if ampls[i] >= polyfit_boundary:
            li = i - 1
            break
    if not li:
        raise ValueError("Left index for polyfit not set")

    # set right index for polyfit
    ri = None
    for i in reversed(range(len(ampls))):
        if ampls[i] >= polyfit_boundary:
            ri = i + 1
            break
    if not ri:
        raise ValueError("Right index for polyfit not set")

    # perform polyfit
    polyfit_ampls = ampls[li:ri+1]
    polyfit_freqs = freqs[li:ri+1]
    # print(polyfit_ampls)
    # print(polyfit_freqs)
    polyfit_coeffs = np.polyfit(polyfit_freqs, polyfit_ampls, 2)
    polyfit_func = np.poly1d(polyfit_coeffs)

    # find derivative, root and return result
    # print('res freq', float(np.roots(polyfit_func.deriv())[0]))
    return float(np.roots(polyfit_func.deriv())[0])
    # return float(np.argmax(data['measure_points']['ampl']) * data['step'] +
    # data['start'])


def compute_diss(measure_points):
    percent = DISSIPATION_PERCENT
    signal = np.array(measure_points['ampl'])
    freq = np.array(measure_points['freq'])
    f_max = np.max(signal)          # Find maximum
    i_max = np.argmax(signal, axis=0)
    # i_max = np.argmax(ampls)
    # idx_min = idx_max = ma
    # m = c = lead_min = lead_max = 0
    index_m = i_max
    # loop until the index at FWHM/others is found
    while signal[index_m] > percent*f_max:
        if index_m < 1:
            # print(TAG, 'WARNING: Left value not found')
            # self._err1 = 1
            break
        index_m = index_m-1
    # linearly interpolate between the previous values to find the value of
    # freq at the leading edge
    m = (signal[index_m+1] - signal[index_m])/(freq[index_m+1] - freq[index_m])
    c = signal[index_m] - freq[index_m]*m
    i_leading = (percent*f_max - c)/m
    # setup index for finding the trailing edge
    index_M = i_max
    # loop until the index at FWHM/others is found
    while signal[index_M] > percent*f_max:
        if index_M >= len(signal)-1:
            # print(TAG, 'WARNING: Right value not found')
            # self._err2 = 1
            break
        index_M = index_M+1
    # linearly interpolate between the previous values to find the value of
    # freq at the trailing edge
    m = (signal[index_M-1] - signal[index_M])/(freq[index_M-1] - freq[index_M])
    c = signal[index_M] - freq[index_M]*m
    i_trailing = (percent*f_max - c)/m
    # compute the FWHM/others
    bandwidth = abs(i_trailing - i_leading)
    Qfac = bandwidth/freq[i_max]

    return Qfac
