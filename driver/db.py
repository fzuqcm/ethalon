from peewee import SqliteDatabase, CharField, Model, ForeignKeyField, DateField

db = SqliteDatabase('people.db')


class DeviceModel(Model):
    name = CharField(unique=True)
    serial_number = CharField()
    is_measuring = False
    port = None
    calib_freq = 10**7

    class Meta:
        database = db


class MeasurementModel(Model):
    device = ForeignKeyField(DeviceModel, backref='measurements')
    created_at = DateField()

    class Meta:
        database = db
