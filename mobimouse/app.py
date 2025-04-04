from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from pynput.mouse import Controller

app = Flask(__name__)
socketio = SocketIO(app)
mouse = Controller()  # Mouse controller instance

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('move_mouse')
def handle_move_mouse(data):
    x, y = data['x'], data['y']
    print(f"Mouse moved to: x={x}, y={y}")
    mouse.position = (x, y)  # Move the actual system mouse

@socketio.on('scroll')
def handle_scroll(data):
    print(f"Scrolling: deltaY={data['deltaY']}")

@socketio.on('click')
def handle_click(data):
    print(f"Mouse click at: x={data['x']}, y={data['y']} with button={data['button']}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)