from math_utils import compute_diss, compute_res_freq
from multiprocessing import Queue
import serial
# import time
import numpy as np
from constants import INTERVAL_HALF, INTERVAL_CALIB, INTERVAL_STEP


def single_measure():
    pass


def measure(signal, result_queue: Queue):
    cmd = signal.task_queue.get(True)
    port = serial.Serial(signal.port, baudrate=115200, timeout=3)
    while cmd:
        # print('here')
        if cmd == 'calibrate':
            while port.readline() != b'':
                pass
            interval = INTERVAL_CALIB
        elif cmd == 'measure':
            interval = INTERVAL_HALF
        else:
            raise RuntimeError('Wohooo!!! Command {} not found.'.format(cmd))
        # print('calibfreqbefore', signal.calib_freq)

        # millisStart = int(round(time.time() * 1000))
        port.write(('{};{};{}\n'.format(
            signal.calib_freq-interval,
            signal.calib_freq+interval,
            INTERVAL_STEP
        ).encode()))
        # print('points', int((2 * interval) / INTERVAL_STEP + 1))
        measure_points = dict(ampl=[], phas=[], freq=list(np.linspace(
            signal.calib_freq-interval,
            signal.calib_freq+interval,
            int((2 * interval) / INTERVAL_STEP + 1)
        )))
        signal_point = dict(temp=0, freq=0, diss=0)

        data = port.readline().decode()[:-1]
        while 's' not in data:
            try:
                ampl, phas = data.split(';')
                measure_points['ampl'].append(float(ampl))
                measure_points['phas'].append(float(phas))
            except (ValueError, IndexError):
                print('-----------', signal, data)
            data = port.readline().decode()[:-1]

        temp, _ = data.split(';')
        offset = signal.measurement.offset
        signal_point['temp'] = float(temp) - offset.get('temp', 0)
        try:
            signal_point['freq'] = compute_res_freq(measure_points) \
                - offset.get('freq', 0)
            signal_point['diss'] = compute_diss(measure_points) \
                - offset.get('diss', 0)
            signal.calib_freq = round(signal_point['freq'])
            # print('here', signal.calib_freq)
        except (ValueError, IndexError):
            result_queue.put((signal.port, measure_points, signal_point))
            cmd = signal.task_queue.get(True)
            continue

        # print('qcm', signal.measurement.offset)

        if cmd == 'calibrate':
            result_queue.put((signal.port, round(signal_point['freq'])))
        elif cmd == 'measure':
            result_queue.put((signal.port, measure_points, signal_point))
        else:
            print('Wohooo!!! Command {} not found.'.format(cmd))

        # millisEnd = int(round(time.time() * 1000))
        # print('QCM', signal, millisEnd - millisStart, 'ms')

        cmd = signal.task_queue.get(True)
