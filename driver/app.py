from multiprocessing import Queue, Process
import numpy as np

# from peewee import Model
from pony import orm
from qcm import measure
import eventlet
import socketio
import datetime
# import os
from serial.tools import list_ports
# from db import db, MeasurementModel, DeviceModel
# , SignalPoint, MeasurePoint
from db2 import Device, Measurement, SignalPoint

from utils import timestamp
import constants as const

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio, static_files={
    # '': os.path.join('..', 'yum', 'public')
})
measurements = dict()
devices = dict()
signals = dict()
result_queue = Queue()


def signals_to_json(all=False):
    result = dict()

    for port, signal in signals.items():
        result[port] = dict(
            calib_freq=signal.calib_freq,
            device=signal.device.id,
            measurement=getattr(signal.measurement, 'id', None),
            is_active=signal.is_active,
            port=signal.port,
            status=signal.status
        )

        # if all:
        #     result[port]['signal_points'] = signal.signal_points

    return result


def measurements_to_json():
    result = dict()

    for id, measurement in measurements.items():
        result[id] = measurement.to_dict(exclude='started_at')
        result[id]['started_at'] = timestamp(measurement.started_at)
        result[id]['freq'] = list(measurement.freq)
        result[id]['diss'] = list(measurement.diss)
        result[id]['temp'] = list(measurement.temp)
        result[id]['time'] = list(measurement.time)

    return result


def devices_to_json():
    result = dict()

    for id, device in devices.items():
        result[id] = device.to_dict()

    return result


class Signal:
    def __init__(self, port: str, device: Device):
        self.port = port
        self.device = device
        self.calib_freq = const.INITIAL_FREQ
        self.task_queue = Queue()
        self.is_active = False
        self.measurement = None
        self.status = const.STATUS_IDLE

    def __del__(self):
        if getattr(self, 'process', None):
            self.process.kill()

    def spawn_process(self):
        if self.is_active:
            raise RuntimeError('Signal is already measuring')

        self.process = Process(
            target=measure,
            args=(self, result_queue),
            daemon=True
        )
        self.is_active = True

    def start(self):
        self.measurement = Measurement(
            started_at=datetime.datetime.now(),
            name="{}_{}".format(timestamp(), self.device.name),
            device=self.device,
        )
        orm.commit()

        measurements[self.measurement.id] = self.measurement
        self.task_queue = Queue()
        self.task_queue.put('measure')
        self.spawn_process()
        self.process.start()
        self.is_calibrated = False

    def calibrate(self):
        self.spawn_process()
        self.process.start()
        self.do('calibrate')

    def do(self, action):
        self.task_queue.put(action)

    def stop(self):
        self.process.terminate()
        self.is_active = False
        self.measurement = None


@sio.event
def connect(sid, environ):
    sio.emit('measurements', measurements_to_json())
    sio.emit('signals', signals_to_json())
    sio.emit('devices', devices_to_json())


@sio.on('start')
def start(sid, ports):
    for port in ports:
        if port in signals:
            # print('signal started', port)
            signals[port].start()
            # print('signal.mesure', signals[port].measurement)

    sio.emit('measurements', measurements_to_json())
    sio.emit('signals', signals_to_json())
    sio.emit('devices', devices_to_json())


@sio.on('stop')
def stop(sid, ports):
    for port in ports:
        signals[port].stop()


@sio.on('export')
def export(sid, measurement_ids):
    for mid in measurement_ids:
        measurement = measurements.get(mid, None)

        print(measurement, mid)


@sio.on('scan')
def scan(sid):
    ports = []
    for port in list_ports.comports():
        if port.device in signals:
            continue

        device = Device.get(serial_number=port.serial_number)
        if device:
            pass
        else:
            device = Device(
                name='QCM {}'.format(port.serial_number),
                serial_number=port.serial_number,
            )
            orm.commit()

        signals[port.device] = Signal(port.device, device)
        devices[device.id] = device

    for _, signal in signals.items():
        ports.append(signal.port)

    sio.emit('measurements', measurements_to_json())
    sio.emit('signals', signals_to_json())
    sio.emit('devices', devices_to_json())


@sio.on('calibrate')
def calibrate(sid, ports):
    signal_list = list()
    signal_counter = 0

    for port in ports:
        signal = signals[port]
        signal.calibrate()
        signal_list.append(signal)
        signal_counter += 1

    while signal_counter > 0:
        (port, calib_freq) = result_queue.get(True)
        signals[port].calib_freq = calib_freq
        # print('newcalibfreq', calib_freq)
        signal_counter -= 1

    for signal in signal_list:
        # print('actualcalibfreq', signal.calib_freq)
        signal.stop()

    sio.emit('setup', signals_to_json())


# @sio.on('changeDeviceName')
# def change_device_name(sid, data):
#     print(data)
#     q = DeviceModel.update({DeviceModel.name: data['name']}).where(
#         DeviceModel.serial_number == data['serialNumber']
#     )
#     print(q.execute())

@sio.on('offset')
def offset(sid, settings):
    print(settings)
    for idx, setting in settings.items():
        print(idx, setting)
        m = measurements.get(int(idx), None)
        print('m', m)
        if m:
            m.compute_offset(setting)

    sio.emit('measurements', measurements_to_json())


@sio.on('test')
def test(sid):
    m = Measurement[2]
    m.compute_data()
    measurements[m.id] = m
    print(measurements_to_json())
    m.compute_offset({
        'freq': 10**7 + 6100
    })
    print(measurements_to_json())
    sio.emit('test')


@sio.event
def disconnect(sid):
    pass
    # print('disconnect ', sid)


def queue_handler():
    data_point = dict()
    should_emit = False
    time = datetime.datetime.now()
    time_js = timestamp(time)

    while result_queue.qsize() > 0:
        should_emit = True
        port, measure_points, signal_point = result_queue.get_nowait()
        signal_point['time'] = time_js
        # signal_point['time'] = time_js
        # signal_point['time'] = time_js
        # signal_point['time'] = time_js
        signal = signals[port]

        if not signal.measurement:
            continue

        SignalPoint(
            timestamp=time,
            temperature=signal_point['temp'],
            measurement=signal.measurement,
            freq=[int(x) for x in measure_points['freq']],
            ampl=[float(x) for x in measure_points['ampl']],
            phas=[float(x) for x in measure_points['phas']]
        )

        signal.measurement.freq = np.append(
            signal.measurement.freq,
            signal_point['freq'] - signal.measurement.offset.get('freq', 0)
        )
        signal.measurement.diss = np.append(
            signal.measurement.diss,
            signal_point['diss'] - signal.measurement.offset.get('diss', 0)
        )
        signal.measurement.temp = np.append(
            signal.measurement.temp,
            signal_point['temp'] - signal.measurement.offset.get('temp', 0)
        )
        signal.measurement.time = np.append(
            signal.measurement.time,
            signal_point['time'] - signal.measurement.offset.get('time', 0)
        )

        data_point[port] = {
            'signal_point': signal_point,
            'measure_points': measure_points
        }

    orm.commit()

    if should_emit:
        sio.emit('data', data_point)

    for port, signal in signals.items():
        if signal.measurement:
            signal.task_queue.put('measure')


def robot():
    while True:
        queue_handler()
        eventlet.sleep(0.975)


if __name__ == '__main__':
    eventlet.spawn(robot)
    with orm.db_session:
        eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
