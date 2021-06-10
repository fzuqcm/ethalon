from db import db, Marker, Measurement, Device

models = [Marker, Measurement, Device]

db.connect()
db.drop_tables(models)
db.create_tables(models)
