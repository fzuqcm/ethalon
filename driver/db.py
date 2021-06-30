import uuid

import numpy as np
from peewee import (Field, ForeignKeyField, Model,
                    PostgresqlDatabase, TextField)
from playhouse.postgres_ext import BinaryJSONField

from constants import Status

# initialize database connection
db = PostgresqlDatabase(
    'postgres',
    user='postgres',
    host='localhost',
    port='15432',
    password='sqljoke'
)


class RealArrayField(Field):
    """
    Native Postgres real array, that is converted to the NumPy float32 array.
    """
    field_type = 'REAL[]'

    def db_value(self, value) -> str:
        # perform fast serialization
        return '{' + ','.join([str(x) for x in value]) + '}'

    def python_value(self, value) -> 'list[float]':
        # perform converting to the NumPy array
        return np.array(
            [float(x) for x in value[1:-1].split(',')],
            dtype=np.float32
        )


class IntegerArrayField(Field):
    """
    Native Postgres int array, that is converted to the NumPy int2 array.
    """
    field_type = 'INT[]'

    def db_value(self, value) -> str:
        # perform fast serialization
        return '{' + ','.join([str(x) for x in value]) + '}'

    def python_value(self, value) -> 'list[int]':
        # perform converting to the NumPy array
        return np.array(
            [int(x) for x in value[1:-1].split(',')],
            dtype=np.int32
        )


class BaseModel(Model):
    """
    Base class for all models, that only registers database.
    """
    class Meta:
        database = db


class Device(BaseModel):
    """
    A model for storing device information.
    """
    name = TextField()
    serial_number = TextField(unique=True)


class Measurement(BaseModel):
    """
    A model for measurement. Saves all needed information.
    """
    device = ForeignKeyField(Device, backref='measurements')
    data = BinaryJSONField()
    freq = RealArrayField()
    diss = RealArrayField()
    temp = RealArrayField()
    time = IntegerArrayField()

    def __init__(self, port: str, device: Device, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calib_freq = 10**7
        self.port = port
        self.device = device
        self.status = Status.READY
        self.freq = np.array([], dtype=np.float32)
        self.diss = np.array([], dtype=np.float32)
        self.temp = np.array([], dtype=np.float32)
        self.time = np.array([], dtype=np.int32)
        self.data = {
            'name': str(uuid.uuid4()).split('-')[-1],
            'markers': list()
        }


# class Marker(BaseModel):
#     """
#     A model for saving markers in the measurement.
#     """
#     name = TextField()
#     timestamp = IntegerField()
#     measurement = ForeignKeyField(Measurement, backref='markers')
