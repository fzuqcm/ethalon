from db import Device
from time import time

import numpy as np
from channel import Channel, Measurement
from multiprocessing import Pool, Queue, cpu_count
# import numpy as np

from playhouse.shortcuts import model_to_dict
# from pony import orm
# from qcm import measure
import eventlet
import socketio
import queries
# import datetime
# # import os
# from serial.tools import list_ports
# # from db import db, MeasurementModel, DeviceModel
# # , ChannelPoint, MeasurePoint
# from db2 import Device, Measurement, ChannelPoint
from pypika import Table
from utils import sleep_time
import constants as const
# from socket2 import app
from serial.tools import list_ports
# sio = socketio.Server(cors_allowed_origins='*')
sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio, static_files={
    # '': os.path.join('..', 'web', 'dist')
})
db_conn = queries.uri(
    host='localhost',
    dbname='postgres',
    user='postgres',
    password='sqljoke'
)

measurements = dict[str, Measurement]()
devices = dict[str, dict]()
channels = dict[str, Channel]()

device_db = Table('device')
measurement_db = Table('measurement')
marker_db = Table('marker')
result_queue = Queue()

DataPoint = tuple[float, float, float, int]
pool = Pool(processes=cpu_count())


def addChannel(channel: Channel):
    ch_data = dict(
        calib_freq=channel.calib_freq,
        device=channel.device_id,
        measurementId=getattr(channel.measurement, 'id', channel.measurement),
        port=channel.port
    )
    sio.emit('addChannel', ch_data)


def addDevice(device: Device):
    sio.emit('addDevice', model_to_dict(device))


def emitMeasurement(measurement: Measurement):
    m_data = {
        'id': measurement.id,
        'name': measurement.name,
        'deviceId': getattr(measurement.device, 'id', measurement.device),
        'freq': measurement.freq.tolist(),
        'diss': measurement.diss.tolist(),
        'temp': measurement.temp.tolist(),
        'time': measurement.time.tolist()
    }
    sio.emit('addMeasurement', m_data)


@sio.event
def connect(sid, environ):
    for channel in channels.values():
        addChannel(channel)

    for device in devices.values():
        addDevice(device)

    for measurement in measurements.values():
        emitMeasurement(measurement)


@sio.on('scan')
def scan(sio):
    for port in list_ports.comports():
        print(port.device)
        if port.device in channels:
            continue
        else:
            device = Device.get_or_create(
                serial_number=port.serial_number,
                defaults={'name': 'QCM ' + port.serial_number}
            )[0]
            devices[device.id] = device
            channels[port.device] = Channel(
                port.device, device.id, result_queue)
            addDevice(device)
            addChannel(channels[port.device])


@sio.on('start')
def start(sio):
    for channel in channels.values():
        channel.task_queue.put(const.QcmCommands.MEASURE)
        m = channel.start()
        measurements[m.id] = m
        emitMeasurement(channel.measurement)
        addChannel(channel)


@sio.on('stop')
def stop(sio):
    for channel in channels.values():
        channel.stop()


@sio.on('calibrate')
def calibrate(sio):
    for channel in channels.values():
        channel.calibrate()
        channel.do(const.QcmCommands.CALIBRATE)


def queue_handler():
    current_time = round(time())
    data: dict[str, DataPoint] = dict()

    pool.map()

    # from numpy.random import default_rng
    # rng = default_rng()

    # sio.emit('data', {
    #     1: rng.random(4).tolist(),
    #     2: rng.random(4).tolist()
    # })
    # return

    while result_queue.qsize() > 0:
        print('size', result_queue.qsize())
        result: tuple[const.QcmCommands,
                      str,
                      float,
                      float,
                      float
                      ] = result_queue.get_nowait()
        channel: Channel = channels[result[1]]

        if result[0] == const.QcmCommands.CALIBRATE:
            channel.calib_freq = result[2]
            channel.status = const.ChannelStatus.READY
            addChannel(channel)
            print('calibrated', result[2])
        elif result[0] == const.QcmCommands.MEASURE:
            if channel.status != const.ChannelStatus.MEASURING:
                continue

            channel.measurement.freq = np.append(
                channel.measurement.freq,
                result[2]
            )
            channel.measurement.diss = np.append(
                channel.measurement.diss,
                result[3]
            )
            channel.measurement.temp = np.append(
                channel.measurement.temp,
                result[4]
            )
            channel.measurement.time = np.append(
                channel.measurement.time,
                current_time
            )

            data[channel.measurement.id] = (
                result[2],
                result[3],
                result[4],
                current_time
            )
        else:
            print('Uknown command', result[0].value)

    print(data)
    sio.emit('data', data)

    for channel in channels.values():
        if channel.status is const.ChannelStatus.MEASURING:
            print(channel.device_id, channel.status)
            channel.task_queue.put(const.QcmCommands.MEASURE)
            print(channel.port, id(channel.task_queue), channel.task_queue.qsize())

def tick_tick():
    eventlet.sleep(sleep_time())
    while True:
        queue_handler()
        eventlet.sleep(sleep_time())


if __name__ == '__main__':
    eventlet.spawn(tick_tick)
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
