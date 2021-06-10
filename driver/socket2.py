import socketio
from app2 import channels
from serial.tools import list_ports

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio, static_files={
    # '': os.path.join('..', 'web', 'dist')
})


@sio.event
def connect(sid, environ):
    for channel in channels.values():
        sio.emit('addChannel', channel)


@sio.on('scan')
def scan(sio):
    ports = []
    # old_keys = channels.keys()
    for port in list_ports.comports():
        if port.device in channels:
            continue

        # device = Device.get(serial_number=port.serial_number)
        # if device:
        #     pass
        # else:
        #     device = Device(
        #         name='QCM {}'.format(port.serial_number),
        #         serial_number=port.serial_number,
        #     )
        #     orm.commit()

        # channels[port.device] = Channel(port.device, device)
        # devices[device.id] = device

    for _, channel in channels.items():
        ports.append(channel.port)
