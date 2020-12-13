import json
import time
import datetime
import threading
import multiprocessing
import pathlib

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
CSV_SEPARATOR = ','
DATE_SEPARATOR = '_'
RAW_DATA_SEPARATOR = ';'
OUTPUT_EXT = 'output'
RAW_DATA_EXT = 'txt'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, cors_allowed_origins='*', engineio_logger=True)
socketio = SocketIO(app, cors_allowed_origins='*')
rng = np.random.default_rng()
db = TinyDB('db.json')
measurements = db.table('measurement')
devices = db.table('device')


def timestamp():
    """
    Get UNIX timestamp in milliseconds (required by JS)
    """
    return int(datetime.datetime.now().timestamp() * 1000)


def format_unix_timestamp(millis):
    """
    Format unix timestamp from milliseconds
    """
    return datetime.datetime.fromtimestamp(millis//1000) \
        .strftime('%Y-%m-%d{}%H-%M-%S'.format(DATE_SEPARATOR))


@socketio.on('getMeasurements')
def get_measurements():
    """
    Get all measurements from db
    """
    emit('getMeasurements', devices.all())


@socketio.on('start')
def start():
    """
    Start measuring on all scanned devices
    """
    if not session.get('measuring', False) and len(session.get('devices', [])) > 0:
        session['measuring'] = True
        measure()


@socketio.on('disconnect')
def disconnect():
    """
    Act upon disconnect
    """
    measurement = session.get('measurement', None)

    if measurement:
        # measurements.update(measurement, doc_ids=[measurement['id']])
        session['measurement'] = None


@socketio.on('stop')
def stop():
    """
    Stop measuring on all devices
    """
    session['measuring'] = False


@socketio.on('scan')
def scan():
    """
    Scan serial ports, retrieve devices from db by serial number and calibrate them
    """
    disconnect()
    session['measuring'] = False
    session['devices'] = list()
    ports = list_ports.comports()
    Device = Query()

    for port in ports:
        # filter devices on serial ports
        # TODO: propably not sufficient, change to more robust check
        if port.manufacturer != 'Microsoft' and port.manufacturer != 'Teensyduino':
            continue

        sn = port.serial_number

        # lookup for device in db
        device = devices.get(Device.serialNumber == sn)

        # create if not found
        if not device:
            device = {
                'name': 'QCM {}'.format(sn),
                'serialNumber': sn
            }
            device['id'] = devices.insert(device)

        # save to request-persistent memory
        session['devices'].append(dict(
            **device,
            path=port.device,
            calibFreq=INITIAL_FREQ
        ))

    # calibrate frequency
    measured_points(interval_half=INTERVAL_CALIB)

    # prepare infos about measuring devices
    # to be saved in db
    d_list = [{
        'serialNumber': d['serialNumber'],
        'initialFreq': d['calibFreq']
    } for d in session['devices']]

    # save measurement to db and session
    stamp = timestamp()
    formatted_stamp = format_unix_timestamp(stamp)
    session['measurement'] = {
        'timestamp': stamp,
        'name': formatted_stamp,
        'devices': d_list,
        'outputFile': '{}.{}'.format(formatted_stamp, OUTPUT_EXT),
        'rawDataFile': '{}.{}'.format(formatted_stamp, RAW_DATA_EXT)
    }
    measurements.insert(session['measurement'])

    # create empty export files
    with open(session['measurement']['outputFile'], 'w') as f:
        cols = ['Date', 'Time', 'Relative time']
        for d in session['devices']:
            cols.append('{} - temp'.format(d['name']))
            cols.append('{} - freq'.format(d['name']))
            cols.append('{} - diss'.format(d['name']))
        f.write(CSV_SEPARATOR.join(cols) + '\n')

    with open(session['measurement']['rawDataFile'], 'w') as f:
        cols = ['Timestamp']
        for d in session['devices']:
            cols.append('{}_freq'.format(d['serialNumber']))
            cols.append('{}_ampl'.format(d['serialNumber']))
            cols.append('{}_phas'.format(d['serialNumber']))
            cols.append('{}_temp'.format(d['serialNumber']))
        f.write(CSV_SEPARATOR.join(cols) + '\n')

    # send to client
    emit('devices', session['devices'])


def read_serial(data):
    """
    Read serial data from single device
    """
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
            freq_len = len(data['measurePoints']['freq'])
            data['measurePoints']['ampl'].append(float(values[0]))
            data['measurePoints']['phas'].append(float(values[1]))
            data['measurePoints']['freq'].append(start + freq_len * step)
        else:
            data['dataPoint']['temp'] = float(values[0])
            break

    data['dataPoint']['freq'] = compute_res_freq(data)
    data['dataPoint']['diss'] = compute_diss(data)
    data['device']['calibFreq'] = int(data['dataPoint']['freq'])

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
    """
    Measure data point and measure points on all devices
    """
    data_list = []

    for device in session['devices']:
        data = {
            'start': device['calibFreq'] - interval_half,
            'stop': device['calibFreq'] + interval_half,
            'step': INTERVAL_STEP,
            'device': device
        }
        data_list.append(read_serial(data))

    return data_list


def measure():
    """
    Continuously read one data point from all devices
    """
    while True:
        measured_data = measured_points()

        if not session.get('measuring', False):
            return

        # save output
        stamp = timestamp()
        first_stamp = session['firstStamp'] = session \
            .get('firstStamp', stamp)
        diff_stamp = stamp - first_stamp
        formatted_date = format_unix_timestamp(stamp).split('_')
        cols = [
            str(formatted_date[0]),
            str(formatted_date[1]),
            '{}.{}'.format(diff_stamp // 1000, str(diff_stamp)[-3:])
        ]

        for i in range(len(measured_data)):
            data = measured_data[i]
            cols.append(str(data['dataPoint']['temp']))
            cols.append(str(data['dataPoint']['freq']))
            cols.append(str(data['dataPoint']['diss']))

        with open(session['measurement']['outputFile'], 'a') as f:
            f.write(CSV_SEPARATOR.join(cols) + '\n')

        # save raw data
        cols = [str(stamp)]
        for data in measured_data:
            cols.append(RAW_DATA_SEPARATOR.join(
                str(x) for x in data['measurePoints']['freq'])
            )
            cols.append(RAW_DATA_SEPARATOR.join(
                str(x) for x in data['measurePoints']['ampl'])
            )
            cols.append(RAW_DATA_SEPARATOR.join(
                str(x) for x in data['measurePoints']['phas'])
            )
            cols.append(str(data['dataPoint']['temp']))

        with open(session['measurement']['rawDataFile'], 'a') as f:
            f.write(CSV_SEPARATOR.join(cols) + '\n')

        emit('measuredData', {
             'forDevices': measured_data,
             'timestamp': stamp
             })


if __name__ == '__main__':
    socketio.run(app, port=8000, debug=True)
