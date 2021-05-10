import datetime
import threading
from qcm import measure
import time
from multiprocessing import Process, Queue
from utils import format_unix_timestamp, timestamp

import numpy as np
import serial
from flask import Flask, session
from flask_socketio import SocketIO, emit
from serial.tools import list_ports
from tinydb import Query, TinyDB

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, cors_allowed_origins='*', engineio_logger=True)
socketio = SocketIO(app, cors_allowed_origins='*')
rng = np.random.default_rng()
db = TinyDB('db.json')
measurements = db.table('measurement')
devices = db.table('device')
q = Queue()


@socketio.on('getMeasurements')
def get_measurements():
    """
    Get all measurements from db
    """

    emit('getMeasurements', devices.all())


@socketio.on('test')
def test():
    print('Test')


# @socketio.on('start')
# def start():
#     """
#     Start measuring on all scanned devices
#     """
#     if not session.get('measuring', False) and len(session.get('devices', [])) > 0:
#         session['measuring'] = True
#         measure()


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


@socketio.on('measureOne')
def measure_one(devices):
    processes = session.get('processes', dict())
    print(processes)
    for device in devices:
        if device not in processes:
            p = Process(target=measure, args=(device, emit), daemon=True)
            p.start()
            processes[device] = p

    session['processes'] = processes


@socketio.on('scan')
def scan():
    """
    Scan serial ports, retrieve devices from db by serial number and calibrate them
    """
    disconnect()
    session['measuring'] = False
    session['devices'] = list()
    ports = list_ports.comports()

    emit('scan', [port.device for port in ports])
