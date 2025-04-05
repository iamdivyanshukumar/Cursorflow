from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from pynput.mouse import Controller, Button
import cv2
import numpy as np
import threading
import time
import base64
from mss import mss

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
mouse = Controller()
screen_share_active = False

def generate_frames():
    with mss() as sct:
        monitor = sct.monitors[1]  # Primary monitor
        while screen_share_active:
            try:
                # Capture screen using MSS
                screenshot = sct.grab(monitor)
                frame = np.array(screenshot)
                
                # Convert color from BGRA to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Resize to reduce bandwidth
                frame = cv2.resize(frame, (800, 450))
                
                # Encode as JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                frame_bytes = buffer.tobytes()
                frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
                
                # Send frame to client
                socketio.emit('screen_frame', {'image': frame_base64})
                time.sleep(0.1)  # ~10 FPS
                
            except Exception as e:
                print(f"Screen capture error: {e}")
                break

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('move_mouse')
def handle_move_mouse(data):
    try:
        delta_x = data['deltaX']
        delta_y = data['deltaY']
        current_x, current_y = mouse.position
        new_x = current_x + delta_x
        new_y = current_y + delta_y
        mouse.position = (new_x, new_y)
    except Exception as e:
        print(f"Error in move_mouse: {e}")

@socketio.on('click')
def handle_click(data):
    try:
        button = data['button']
        if button == "left":
            mouse.click(Button.left, 1)
        elif button == "right":
            mouse.click(Button.right, 1)
    except Exception as e:
        print(f"Error in click: {e}")

@socketio.on('scroll')
def handle_scroll(data):
    try:
        delta_y = data['deltaY']
        mouse.scroll(0, delta_y / 120)
    except Exception as e:
        print(f"Error in scroll: {e}")

@socketio.on('start_screen_share')
def handle_start_screen_share():
    global screen_share_active
    if not screen_share_active:
        screen_share_active = True
        threading.Thread(target=generate_frames, daemon=True).start()
        print("Screen sharing started")

@socketio.on('stop_screen_share')
def handle_stop_screen_share():
    global screen_share_active
    screen_share_active = False
    print("Screen sharing stopped")

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)


