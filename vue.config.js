module.exports = {
  lintOnSave: false,
  pluginOptions: {
    electronBuilder: {
      externals: ['serialport'],
      nodeIntegration: true,
    },
  },
}
