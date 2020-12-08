import json
import time
import datetime
import threading
import multiprocessing

import numpy as np
import serial
from flask import Flask, session
from flask_socketio import SocketIO, emit
from serial.tools import list_ports
from tinydb import TinyDB, Query

INITIAL_FREQ = 10**7
INTERVAL_CALIB = 10**5
INTERVAL_HALF = 10**4 // 2
INTERVAL_STEP = 40
POLYFIT_COEFFICIENT = 0.95
DISSIPATION_PERCENT = 0.707

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*', engineio_logger=True)
# socketio = SocketIO(app, cors_allowed_origins='*')
rng = np.random.default_rng()
db = TinyDB('db.json')
measurements = db.table('measurement')
devices = db.table('device')


def timestamp():
    return int(datetime.datetime.now().timestamp() * 1000)


@socketio.on('getMeasurements')
def get_measurements():
    emit('getMeasurements', devices.all())


@socketio.on('start')
def start():
    if not session.get('measuring', False) and len(session.get('devices', [])) > 0:
        session['measuring'] = True
        measure()


@socketio.on('disconnect')
def disconnect():
    measurement = session.get('measurement', None)

    if measurement:
        measurements.update(measurement, doc_ids=[measurement['id']])
        session['measurement'] = None


@socketio.on('stop')
def stop():
    session['measuring'] = False


@socketio.on('scan')
def scan():
    disconnect()
    session['measuring'] = False
    session['devices'] = list()
    session['measurement'] = {
        'serialNumbers': list(),
        'timestamps': [],
        'devicesData': []
    }
    ports = list_ports.comports()
    Device = Query()

    for port in ports:
        if port.manufacturer != 'Teensyduino':
            continue

        sn = port.serial_number
        device = devices.get(Device.serialNumber == port.serial_number)

        if not device:
            device = {
                'name': 'QCM {}'.format(sn),
                'serialNumber': sn
            }
            device['id'] = devices.insert(device)

        session['measurement']['serialNumbers'].append(sn)
        session['measurement']['devicesData'].append({
            'freq': [],
            'diss': [],
            'temp': [],
            'measure': []
        })
        session['devices'].append(dict(
            **device,
            path=port.device,
            calib_freq=INITIAL_FREQ
        ))

    session['measurement']['id'] = measurements.insert(session['measurement'])
    measured_points(interval_half=INTERVAL_CALIB)
    emit('devices', session['devices'])


def read_serial(data):
    start, stop, step = data['start'], data['stop'], data['step']
    data['measurePoints'] = {
        'ampl': [],
        'phas': [],
        'freq': []
    }
    data['dataPoint'] = {
        'freq': 0,
        'diss': 0,
        'temp': 0
    }

    buffer = ''
    with serial.Serial(data['device']['path'], baudrate=115200, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=10) as qcm:
        qcm.flush()
        qcm.write('{};{};{}\n'.format(start, stop, step).encode())
        while True:
            socketio.sleep(0)
            qcm.flush()
            buffer += qcm.readline().decode()
            if 's' in buffer:
                break

    for line in buffer.split('\r\n'):
        values = line.split(';')

        if 's' not in line:
            data['measurePoints']['ampl'].append(float(values[0]))
            data['measurePoints']['phas'].append(float(values[1]))
            data['measurePoints']['freq'].append(
                start + len(data['measurePoints']['freq']) * step)
        else:
            data['dataPoint']['temp'] = float(values[0])
            break

    data['dataPoint']['freq'] = compute_res_freq(data)
    data['dataPoint']['diss'] = compute_diss(data)
    data['device']['calib_freq'] = int(data['dataPoint']['freq'])

    return {
        'dataPoint': data['dataPoint'],
        'measurePoints': data['measurePoints']
    }


def compute_res_freq(data):
    ampls = np.array(data['measurePoints']['ampl'])
    freqs = np.array(data['measurePoints']['freq'])
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
    # print(float(np.roots(polyfit_func.deriv())[0]))
    return float(np.roots(polyfit_func.deriv())[0])
    # return float(np.argmax(data['measurePoints']['ampl']) * data['step'] + data['start'])


def compute_diss(data):
    percent = DISSIPATION_PERCENT
    signal = np.array(data['measurePoints']['ampl'])
    freq = np.array(data['measurePoints']['freq'])
    f_max = np.max(signal)          # Find maximum
    i_max = np.argmax(signal, axis=0)
    # i_max = np.argmax(ampls)
    # idx_min = idx_max = ma
    # m = c = lead_min = lead_max = 0
    index_m = i_max
    # loop until the index at FWHM/others is found
    while signal[index_m] > percent*f_max:
        if index_m < 1:
            #print(TAG, 'WARNING: Left value not found')
            # self._err1 = 1
            break
        index_m = index_m-1
    # linearly interpolate between the previous values to find the value of freq at the leading edge
    m = (signal[index_m+1] - signal[index_m])/(freq[index_m+1] - freq[index_m])
    c = signal[index_m] - freq[index_m]*m
    i_leading = (percent*f_max - c)/m
    # setup index for finding the trailing edge
    index_M = i_max
    # loop until the index at FWHM/others is found
    while signal[index_M] > percent*f_max:
        if index_M >= len(signal)-1:
            #print(TAG, 'WARNING: Right value not found')
            # self._err2 = 1
            break
        index_M = index_M+1
    # linearly interpolate between the previous values to find the value of freq at the trailing edge
    m = (signal[index_M-1] - signal[index_M])/(freq[index_M-1] - freq[index_M])
    c = signal[index_M] - freq[index_M]*m
    i_trailing = (percent*f_max - c)/m
    # compute the FWHM/others
    bandwidth = abs(i_trailing - i_leading)
    Qfac = bandwidth/freq[i_max]

    return Qfac


def measured_points(interval_half=INTERVAL_HALF, interval_step=INTERVAL_STEP):
    data_list = []

    for device in session['devices']:
        data = {
            'start': device['calib_freq'] - interval_half,
            'stop': device['calib_freq'] + interval_half,
            'step': INTERVAL_STEP,
            'device': device
        }
        data_list.append(read_serial(data))

    return data_list


def measure():
    while True:
        measured_data = measured_points()

        if not session.get('measuring', False):
            return

        measurement = session['measurement']
        measurement['timestamps'].append(timestamp())
        for i in range(len(measured_data)):
            data = measured_data[i]
            deviceData = measurement['devicesData'][i]
            deviceData['freq'].append(data['dataPoint']['freq']),
            deviceData['diss'].append(data['dataPoint']['diss']),
            deviceData['temp'].append(data['dataPoint']['temp']),
            deviceData['measure'].append(data['measurePoints'])

        # measurements.update(measurement, doc_ids=[measurement['id']])
        # print(measurements.get(doc_id=measurement['id']), measurement['id'])

        emit('measuredData', {
             'forDevices': measured_data,
             'timestamp': measurement['timestamps'][-1]
             })


if __name__ == '__main__':
    socketio.run(app, port=8000, debug=True)
