exports.up = function(knex) {
  knex.schema.createTable('measurement', function(table) {
    table.increments()
    table.string('example_column')
    // TODO: create table for each measurement and for the whole "experiment". It's technically measurement, but it has to be different in names. So, one word (and table) for single frequency measurement and one word (and table) for one sample measurement.
    // Documentation could be found on internet.
    // http://knexjs.org/
  })
  // Also add table for QCM device
}

exports.down = function(knex) {
  knex.schema.dropTable('measurement')
  // TODO: don't forget to add down rules for migration (eg. drop tables)
}
