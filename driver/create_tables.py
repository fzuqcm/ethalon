from db import Device, Measurement, db

# register models
models = [Device, Measurement]

# connect to the db, drop all tables and recreate them
# ONLY RUN IN DEVELOPMENT
if True:
    db.connect()
    db.drop_tables(models)
    db.create_tables(models)
