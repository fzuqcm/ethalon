from multiprocessing import Pool, cpu_count
from time import time

import eventlet
import numpy as np
import serial
import socketio
from serial.tools import list_ports

from constants import Command, Status
from db import Device, Measurement
from utils import sleep_time

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)
measurements = dict[str, Measurement]()


def emitMeasurement(m: Measurement):
    """
    WebSocket emit of the measurement. It also performs a serialization
    beforehand. It uses the camelCase syntax in key names.
    """
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
    """
    Perform synchronization on connect.
    """
    for m in measurements.values():
        emitMeasurement(m)


@sio.on('scan')
def scan(sio):
    """
    Scan serial ports, find or create device entry in the database and emit
    found ports.
    """
    for port in list_ports.comports():
        if port.device in measurements:
            # port already initilized
            continue
        else:
            # find or create device based on serial number
            device = Device.get_or_create(
                serial_number=port.serial_number,
                defaults={'name': 'QCM ' + port.serial_number}
            )[0]

            # create a new measurement
            measurements[port.device] = Measurement(
                port.device,
                device
            )
            emitMeasurement(measurements[port.device])


@sio.on('start')
def start(sio, ports):
    """
    Start measuring on selected ports.
    """
    for port in ports:
        m = measurements[port]
        m.status = Status.MEASURING
        emitMeasurement(m)


@sio.on('stop')
def stop(sio, ports):
    """
    Save data and stop measuring on selected ports.
    """
    for port in ports:
        m = measurements[port]

        # save previous measurement to the db
        m.save()

        # delete measurements from memory
        del measurements[m.port]

    # rescan devices
    scan(sio)


@sio.on('calibrate')
def calibrate(sio, ports):
    """
    Only run calibration on selected ports. Don't save any data.
    """
    for port in ports:
        m = measurements[port]
        m.status = Status.CALIBRATING
        emitMeasurement(measurements[m.port])


def do(args: tuple[str, str]):
    """
    This function handles measuring in in one process (on one port). It opens
    serial connection with the device and read its values.
    """
    # extract values from input tuple
    cmd = args[0]
    portName = args[1]

    try:
        # open serial port (it will be closed on the last value is read)
        with serial.Serial(portName, baudrate=115200) as port:
            # write command
            port.write((cmd + '\n').encode())
            port.flush()

            # read values
            freq = float(port.readline().decode())
            diss = float(0)
            temp = float(port.readline().decode())
    except (serial.SerialException, ValueError):
        return 'err'

    # return values in a tuple
    return (
        cmd,
        portName,
        freq,
        diss,
        temp
    )


def queue_handler():
    """
    This function should be executed once per second. It manages process pool,
    measurement and calibration. This corresponds to one measurement cycle.
    """
    # prepare
    current_time = round(time())
    data = list()

    # array of parameters for process pool
    values = []
    for m in measurements.values():
        if m.status == Status.MEASURING:
            values.append((Command.MEASURE, m.port))

    # execute everything in process pool
    results = pool.map(do, values)

    # use results
    for result in results:
        # skip on error
        if result == 'err':
            return

        # find correct measurement
        m = measurements.get(result[1], None)

        # check for existence of measurement
        if not m or m.status != Status.MEASURING:
            continue

        if result[0] == Command.MEASURE:
            # set values
            m.calib_freq = result[2]
            m.freq = np.append(m.freq, result[2])
            m.diss = np.append(m.diss, result[3])
            m.temp = np.append(m.temp, result[4])
            m.time = np.append(m.time, current_time)

            # append to data that are emitted
            data.append([*result[1:], current_time])
        elif result[0] == Command.CALIBRATE:
            # set calibration and emit
            m.calib_freq = result[2]
            emitMeasurement(m)

    # only emit when have at least one value
    if len(data) > 0:
        sio.emit('data', data)


def tick_tick():
    """
    This function should be called async and it handles 'ticking', a method
    that calls some actions exactly once per second. The milliseconds are
    always zero, as the function calls are performed every while second.
    """
    # wait for whole second
    eventlet.sleep(sleep_time())

    # run forever
    while True:
        # call handler
        queue_handler()

        # wait for whole second and print exec time
        t = sleep_time()
        print('Execution time:', int((1 - t) * 1000), 'ms')
        eventlet.sleep(t)


if __name__ == '__main__':
    # start process poll
    # MUST be initialized in this condition
    pool = Pool(processes=cpu_count() // 4)

    # async spawn of tick function
    eventlet.spawn(tick_tick)

    # start the app
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
