import time
import datetime
from multiprocessing import Process

import numpy as np
import serial
from flask import Flask, session
from flask_socketio import SocketIO, emit
from serial.tools import list_ports
from tinydb import Query, TinyDB




"""
Prepare global variables
"""
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, cors_allowed_origins='*', engineio_logger=True)
socketio = SocketIO(app, cors_allowed_origins='*')
rng = np.random.default_rng()
db = TinyDB('db.json')
measurements = db.table('measurement')
devices = db.table('device')


def measure(qcm_no):
    name = '/dev/ttyACM{}'.format(qcm_no)
    print('\nMeasuring on port {}'.format(name))
    port = serial.Serial(name, baudrate=115200, timeout=3)
    port.flush()
    while port.readline() != b'':
        pass
    port.flush()
    # time.sleep(1)
    # port.flushInput()
    # port.flushOutput()

    while True:
        millisStart = int(round(time.time() * 1000))
        port.write(('{};{};{}\n'.format(10**7-10**5, 10**7+10**5, 40).encode()))
        port.flush()
        # time.sleep(1)
        # port.flushInput()
        # port.flushOutput()

        values = list()

        data = port.readline().decode()[:-1]
        while 's' not in data:
            # print(data)
            try:
                ampl, phas = data.split(';')
                values.append((float(ampl), float(phas)))
            except:
                print('-----------', qcm_no, data)
            data = port.readline().decode()[:-1]
            port.flush()
            # time.sleep(1)
            # port.flushInput()
            # port.flushOutput()

        millisEnd = int(round(time.time() * 1000))
        print('QCM', qcm_no, millisEnd - millisStart, 'ms')


if __name__ == '__main__':
    processes = dict()
    ports = list(list_ports.comports())
    print([port.device for port in ports])

    while True:
        qcm_no = int(input("Enter QCM: "))

        if qcm_no not in processes:
            p = Process(target=measure, args=(qcm_no,), daemon=True)
            p.start()
            processes[qcm_no] = p
        else:
            processes[qcm_no].kill()
            print('Terminate', processes[qcm_no])
            del processes[qcm_no]
            print(processes)

        # p.start()
        # p.join()

    # p0 = Process(target=hello, args=('world0',5))
    # p1 = Process(target=hello, args=('world1',10))
    # p2 = Process(target=hello, args=('world2',15))
    # p0.start()
    # p1.start()
    # p2.start()
    # p0.join()
    # p1.join()
    # p2.join()
