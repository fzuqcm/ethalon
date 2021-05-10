# from db import db, MeasurementModel, DeviceModel

# db.create_tables([DeviceModel, MeasurementModel])
from db2 import db

db.generate_mapping(create_tables=True)
