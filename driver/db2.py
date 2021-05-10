from datetime import datetime
from utils import timestamp
import numpy as np
from pony import orm
import math_utils


db = orm.Database()
db.bind(provider='sqlite', filename='database.sqlite', create_db=True)

# db.bind(provider='sqlite', filename=':memory:')


class Device(db.Entity):
    name = orm.Required(str)
    serial_number = orm.Required(str, unique=True)
    measurements = orm.Set('Measurement')


class Measurement(db.Entity):
    freq = np.array([])
    diss = np.array([])
    temp = np.array([])
    time = np.array([])
    started_at = orm.Required(datetime)
    name = orm.Required(str)
    device = orm.Required(Device)
    signal_points = orm.Set('SignalPoint')
    __settings = dict(freq=0, diss=0, temp=0, time=0)

    def compute_data(self):
        freq_list = list()
        diss_list = list()
        temp_list = list()
        time_list = list()
        for sp in self.signal_points.order_by(SignalPoint.timestamp):
            measure_points = {
                'ampl': sp.ampl,
                'freq': sp.freq,
                'phas': sp.phas
            }
            freq_list.append(math_utils.compute_res_freq(measure_points))
            diss_list.append(math_utils.compute_diss(measure_points))
            temp_list.append(sp.temperature)
            time_list.append(timestamp(sp.timestamp))

        self.freq = np.array(freq_list)
        self.diss = np.array(diss_list)
        self.temp = np.array(temp_list)
        self.time = np.array(time_list)

    def compute_offset(self, settings):
        self.freq += self.__settings.get('freq', 0) - settings.get('freq', 0)
        self.diss += self.__settings.get('diss', 0) - settings.get('diss', 0)
        self.temp += self.__settings.get('temp', 0) - settings.get('temp', 0)
        self.time += self.__settings.get('time', 0) - settings.get('time', 0)
        self.__settings = settings

    @property
    def offset(self):
        return self.__settings


class SignalPoint(db.Entity):
    measurement = orm.Required(Measurement)
    timestamp = orm.Required(datetime, precision=3)
    temperature = orm.Required(float)
    freq = orm.Required(orm.IntArray)
    ampl = orm.Required(orm.FloatArray)
    phas = orm.Required(orm.FloatArray)


db.generate_mapping(create_tables=True)
