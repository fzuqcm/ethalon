from utils import timestamp
from multiprocessing import Queue, Process
import constants as const
import serial
from db import Measurement


def do(portName: str, task_queue: Queue, result_queue: Queue):
    cmd: const.QcmCommands = task_queue.get(True)
    port = serial.Serial(portName, baudrate=115200, timeout=3)

    while cmd:
        # if cmd not in list(const.QcmCommands):
        #     raise RuntimeError('QCM command {} not found.'.format(cmd))

        port.write((cmd.value + '\n').encode())
        freq = port.readline()[:-1].decode()
        temp = port.readline()[:-1].decode()

        result_queue.put((
            cmd,
            portName,
            float(freq),
            float(0),
            float(temp)
        ))

        cmd = task_queue.get(True)


class Channel:
    def __init__(self, port: str, device_id: int, result_queue: Queue) -> None:
        self.port = port
        self.device_id = device_id
        self.calib_freq = const.INITIAL_FREQ
        self.task_queue = Queue()
        self.measurement = None
        self.result_queue = result_queue
        self.status = const.ChannelStatus.READY

    def __del__(self):
        if getattr(self, 'process', None):
            self.measurement.save()
            self.process.kill()
            self.status = const.ChannelStatus.READY

    def spawn_process(self):
        if self.status != const.ChannelStatus.READY:
            raise RuntimeError('Channel is busy')

        self.process = Process(
            target=do,
            args=(self.port, self.task_queue, self.result_queue),
            daemon=True
        )
        self.process.start()

    def start(self):
        self.measurement = Measurement(
            name=f"{timestamp()}_{self.device_id}",
            device=self.device_id,
        )
        self.measurement.save()
        self.spawn_process()
        self.status = const.ChannelStatus.MEASURING

        return self.measurement

    def calibrate(self):
        self.spawn_process()

    def do(self, action: const.QcmCommands.MEASURE):
        self.task_queue.put(action)

    def stop(self):
        self.measurement.save()
        self.process.terminate()
        self.status = const.ChannelStatus.READY
        self.measurement = None
