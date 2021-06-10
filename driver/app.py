from multiprocessing import Queue, Process
import numpy as np

# from peewee import Model
from pony import orm
from qcm import measure
import eventlet
import socketio
import datetime
import time
# import os
from serial.tools import list_ports
# from db import db, MeasurementModel, DeviceModel
# , ChannelPoint, MeasurePoint
from db2 import Device, Measurement, ChannelPoint

from utils import timestamp
import constants as const

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio, static_files={
    # '': os.path.join('..', 'yum', 'public')
})
measurements = dict()
devices = dict()
channels = dict()
result_queue = Queue()


# def channels_to_json(all=False):
#     result = dict()

#     for port, channel in channels.items():
#         result[port] = dict(
#             calib_freq=channel.calib_freq,
#             device=channel.device.id,
#             measurement=getattr(channel.measurement, 'id', None),
#             is_active=channel.is_active,
#             port=channel.port,
#             status=channel.status
#         )

# if all:
#     result[port]['channel_points'] = channel.channel_points

# return result


# def measurements_to_json():
#     result = dict()

#     for id, measurement in measurements.items():
#         result[id] = measurement.to_dict(exclude='started_at')
#         result[id]['started_at'] = timestamp(measurement.started_at)
#         result[id]['freq'] = list(measurement.freq)
#         result[id]['diss'] = list(measurement.diss)
#         result[id]['temp'] = list(measurement.temp)
#         result[id]['time'] = list(measurement.time)

#     return result


# def devices_to_json():
#     result = dict()

#     for id, device in devices.items():
#         result[id] = device.to_dict()

#     return result





@sio.event
def connect(sid, environ):
    pass
    # sio.emit('measurements', measurements_to_json())
    # sio.emit('channels', channels_to_json())
    # sio.emit('devices', devices_to_json())


@sio.on('start')
def start(sid, ports):
    for port in ports:
        if port in channels:
            # print('channel started', port)
            channels[port].start()
            # print('channel.mesure', channels[port].measurement)

    # sio.emit('measurements', measurements_to_json())
    # sio.emit('channels', channels_to_json())
    # sio.emit('devices', devices_to_json())


@sio.on('stop')
def stop(sid, ports):
    for port in ports:
        channels[port].stop()


@sio.on('export')
def export(sid, measurement_ids):
    for mid in measurement_ids:
        measurement = measurements.get(mid, None)

        print(measurement, mid)


@sio.on('scan')
def scan(sid):
    ports = []
    for port in list_ports.comports():
        if port.device in channels:
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

        channels[port.device] = Channel(port.device, device)
        devices[device.id] = device

    for _, channel in channels.items():
        ports.append(channel.port)

    # sio.emit('measurements', measurements_to_json())
    # sio.emit('channels', channels_to_json())
    # sio.emit('devices', devices_to_json())


@sio.on('calibrate')
def calibrate(sid, ports):
    channel_list = list()
    channel_counter = 0

    for port in ports:
        channel = channels[port]
        channel.calibrate()
        channel_list.append(channel)
        channel_counter += 1

    while channel_counter > 0:
        (port, calib_freq) = result_queue.get(True)
        channels[port].calib_freq = calib_freq
        # print('newcalibfreq', calib_freq)
        channel_counter -= 1

    for channel in channel_list:
        # print('actualcalibfreq', channel.calib_freq)
        channel.stop()

    # sio.emit('setup', channels_to_json())


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

    # sio.emit('measurements', measurements_to_json())


@sio.on('test')
def test(sid):
    m = Measurement[2]
    m.compute_data()
    measurements[m.id] = m
    # print(measurements_to_json())
    m.compute_offset({
        'freq': 10**7 + 6100
    })
    # print(measurements_to_json())
    sio.emit('test')


@sio.event
def disconnect(sid):
    pass
    # print('disconnect ', sid)


def queue_handler():
    data_point = dict()
    should_emit = False
    ttime = datetime.datetime.now()
    time_js = timestamp(time)

    while result_queue.qsize() > 0:
        should_emit = True
        port, measure_points, channel_point = result_queue.get_nowait()
        channel_point['time'] = time_js
        # channel_point['time'] = time_js
        # channel_point['time'] = time_js
        # channel_point['time'] = time_js
        channel = channels[port]

        if not channel.measurement:
            continue

        ChannelPoint(
            timestamp=ttime,
            temperature=channel_point['temp'],
            measurement=channel.measurement,
            freq=[int(x) for x in measure_points['freq']],
            ampl=[float(x) for x in measure_points['ampl']],
            phas=[float(x) for x in measure_points['phas']]
        )

        channel.measurement.freq = np.append(
            channel.measurement.freq,
            channel_point['freq'] - channel.measurement.offset.get('freq', 0)
        )
        channel.measurement.diss = np.append(
            channel.measurement.diss,
            channel_point['diss'] - channel.measurement.offset.get('diss', 0)
        )
        channel.measurement.temp = np.append(
            channel.measurement.temp,
            channel_point['temp'] - channel.measurement.offset.get('temp', 0)
        )
        channel.measurement.time = np.append(
            channel.measurement.time,
            channel_point['time'] - channel.measurement.offset.get('time', 0)
        )

        data_point[port] = {
            'channel_point': channel_point,
            'measure_points': measure_points
        }

    orm.commit()

    if should_emit:
        sio.emit('data', data_point)

    for port, channel in channels.items():
        if channel.measurement:
            channel.task_queue.put('measure')


def robot():
    while True:
        # queue_handler()
        print(round(time.time() * 1000))
        eventlet.sleep(0.975)


if __name__ == '__main__':
    eventlet.spawn(robot)
    with orm.db_session:
        eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
