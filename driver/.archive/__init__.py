from timer import RepeatedTimer
# # from app import socketio, Flask
from utils import format_unix_timestamp, timestamp

# if __name__ == '__main__':
#     # app = Flask(__name__)
#     rt = RepeatedTimer(1, lambda: print(format_unix_timestamp(timestamp())))
#     # socketio.run(app, port=8000, debug=True)

from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

if __name__ == '__main__':
    rt = RepeatedTimer(1, lambda: print(format_unix_timestamp(timestamp())))
    socketio.run(app)