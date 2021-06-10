import numpy as np
from constants import Status
import uuid
from peewee import (
    IntegerField,
    PostgresqlDatabase,
    Model, ForeignKeyField,
    Field,
    TextField
)

db = PostgresqlDatabase(
    'postgres',
    user='postgres',
    host='localhost',
    password='sqljoke'
)


class RealArrayField(Field):
    field_type = 'REAL[]'

    def db_value(self, value) -> str:
        return '{' + ','.join([str(x) for x in value]) + '}'

    def python_value(self, value) -> list[float]:
        return np.array(
            [float(x) for x in value[1:-1].split(',')],
            dtype=np.float32
        )


class IntegerArrayField(Field):
    field_type = 'INT[]'

    def db_value(self, value) -> str:
        return '{' + ','.join([str(x) for x in value]) + '}'

    def python_value(self, value) -> list[int]:
        return np.array(
            [int(x) for x in value[1:-1].split(',')],
            dtype=np.int32
        )


class BaseModel(Model):
    class Meta:
        database = db


class Device(BaseModel):
    name = TextField(unique=True)
    serial_number = TextField()


class Measurement(BaseModel):
    device = ForeignKeyField(Device, backref='measurements')
    name = TextField()
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
        self.name = str(uuid.uuid4()).split('-')[-1]
        self.freq = np.array([], dtype=np.float32)
        self.diss = np.array([], dtype=np.float32)
        self.temp = np.array([], dtype=np.float32)
        self.time = np.array([], dtype=np.int32)


class Marker(BaseModel):
    name = TextField()
    timestamp = IntegerField()
    measurement = ForeignKeyField(Measurement, backref='markers')
