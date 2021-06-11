from db import Device, Marker, Measurement, db

# register models
models = [Device, Marker, Measurement]

# connect to the db, drop all tables and recreate them
# ONLY RUN IN DEVELOPMENT
if False:
    db.connect()
    db.drop_tables(models)
    db.create_tables(models)
