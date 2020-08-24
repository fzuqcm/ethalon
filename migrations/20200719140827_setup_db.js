const createTablesSafely = knex => tables => {
  const createTables = tables.map(({ name, schema }) => {
    return knex.schema.createTable(name, schema)
  })

  return Promise.all(createTables).catch(e => {
    const dropTables = tables.map(({ name }) => {
      return knex.schema.dropTableIfExists(name)
    })

    return Promise.all(dropTables).then(() => Promise.reject(e))
  })
}

exports.up = function(knex) {
  return createTablesSafely(knex)([
    {
      name: 'session',
      schema(table) {
        table.increments()
        table.string('name')
        table.timestamps()
      },
    },
    {
      name: 'measurement',
      schema(table) {
        table.increments()
        table
          .integer('session_id')
          .unsigned()
          .notNullable()
        table
          .integer('device_id')
          .unsigned()
          .notNullable()
        table.string('name')
        table.timestamps()

        table
          .foreign('session_id')
          .references('id')
          .inTable('session')
        table
          .foreign('device_id')
          .references('id')
          .inTable('device')
      },
    },
    {
      name: 'datapoint',
      schema(table) {
        table.increments()
        table
          .integer('measurement_id')
          .unsigned()
          .notNullable()
        table.float('relative_time')
        table.float('temperature')
        table.float('frequency')
        table.float('dissipation')
        table.timestamps()

        table
          .foreign('measurement_id')
          .references('id')
          .inTable('measurement')
      },
    },
    {
      name: 'device',
      schema(table) {
        table.increments()
        table.string('serial_number').unique()
        table.string('name')
      },
    },
  ])
}

// exports.up = function(knex, Promise) {
//   // Table for all experiment (multichart = multidevice)
//   knex.schema.createTable('session', function(table) {
//     table.increments();
//     table.string('name');
//     table.timestamps();
//   })
//   // Table for one chart (one device)
//   knex.schema.createTable('measurement', function(table) {
//     table.increments();
//     table.integer('session_id').unsigned().notNullable();
//     table.integer('device_id').unsigned().notNullable();
//     table.string('name');
//     table.timestamps();

//     table.foreign('session_id').references('id').inTable('session');
//     table.foreign('device_id').references('id').inTable('device');
//   })
//   // Table for one measured point in experiment
//   knex.schema.createTable('datapoint', function(table) {
//     table.increments();
//     table.integer('measurement_id').unsigned().notNullable();
//     table.float('relative_time');
//     table.float('temperature');
//     table.float('frequency');
//     table.float('dissipation');
//     table.timestamps();

//     table.foreign('measurement_id').references('id').inTable('measurement');
//   })
//   // Table for QCM devices
//   knex.schema.createTable('device', function(table) {
//     table.increments();
//     table.string('dev_id');
//     table.string('name');
//   })
// }

// TODO: create table for each measurement and for the whole "experiment". It's technically measurement, but it has to be different in names. So, one word (and table) for single frequency measurement and one word (and table) for one sample measurement.
// Documentation could be found on internet.
// http://knexjs.org/

exports.down = function(knex) {
  return Promise.all([
    knex.schema.dropTable('session'),
    knex.schema.dropTable('measurement'),
    knex.schema.dropTable('datapoint'),
    knex.schema.dropTable('device'),
  ])
  // TODO: don't forget to add down rules for migration (eg. drop tables)
}
