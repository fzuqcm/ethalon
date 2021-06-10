from multiprocessing import Pool, cpu_count
from time import time

import eventlet
import numpy as np
import socketio
from serial.tools import list_ports

from constants import Status, Command
from db import Device, Measurement
from utils import sleep_time

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)
measurements = dict[str, Measurement]()


def emitMeasurement(m: Measurement):
    d = m.device
    data = {
        'name': m.name,
        'status': m.status,
        'port': m.port,
        'device': {
            'id': d.id,
            'serialNumber': d.serial_number,
            'name': d.name
        },
        'freq': m.freq.tolist(),
        'diss': m.diss.tolist(),
        'temp': m.temp.tolist(),
        'time': m.time.tolist(),
        'calibFreq': m.calib_freq
    }

    sio.emit('addMeasurement', data)


@sio.event
def connect(sid, environ):
    for m in measurements.values():
        emitMeasurement(m)


@sio.on('scan')
def scan(sio):
    for port in list_ports.comports():
        print(port.device)
        if port.device in measurements:
            continue
        else:
            device = Device.get_or_create(
                serial_number=port.serial_number,
                defaults={'name': 'QCM ' + port.serial_number}
            )[0]
            measurements[port.device] = Measurement(
                port.device,
                device
            )
            emitMeasurement(measurements[port.device])


@sio.on('start')
def start(sio, ports):
    for port in ports:
        m = measurements[port]
        m.status = Status.MEASURING
        emitMeasurement(m)


@sio.on('stop')
def stop(sio, ports):
    for port in ports:
        m = measurements[port]
        m.save()
        measurements[m.port] = Measurement(
            m.port,
            m.device
        )
        emitMeasurement(measurements[m.port])


@sio.on('calibrate')
def calibrate(sio, ports):
    for port in ports:
        m = measurements[port]
        m.status = Status.CALIBRATING
        emitMeasurement(measurements[m.port])


def do(args: tuple[str, str]):
    import serial
    cmd = args[0]
    portName = args[1]

    try:
        with serial.Serial(portName, baudrate=115200) as port:
            port.write((cmd + '\n').encode())
            port.flush()
            freq = port.readline().decode()
            temp = port.readline().decode()
    except serial.SerialException:
        return 'err'

    return (
        cmd,
        portName,
        float(freq),
        float(0),
        float(temp)
    )


def queue_handler():
    current_time = round(time())
    data = list()

    values = []
    for m in measurements.values():
        if m.status == Status.MEASURING:
            values.append((Command.MEASURE, m.port))

    results = pool.map(do, values)
    for result in results:
        if result == 'err':
            return

        m = measurements.get(result[1], None)

        if not m or m.status != Status.MEASURING:
            continue

        m.calib_freq = result[2]
        m.freq = np.append(m.freq, result[2])
        m.diss = np.append(m.diss, result[3])
        m.temp = np.append(m.temp, result[4])
        m.time = np.append(m.time, current_time)
        data.append([*result[1:], current_time])

    print(data)
    sio.emit('data', data)


def tick_tick():
    eventlet.sleep(sleep_time())
    while True:
        queue_handler()
        t = sleep_time()
        print('Execution time:', int((1 - t) * 1000), 'ms')
        eventlet.sleep(t)


if __name__ == '__main__':
    pool = Pool(processes=cpu_count() // 4)

    eventlet.spawn(tick_tick)
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
