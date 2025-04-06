from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Key
import cv2
import numpy as np
import threading
import time
import base64
from mss import mss
import zlib

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

mouse = Controller()
keyboard = KeyboardController()
screen_share_active = False
compression_enabled = True

def generate_frames():
    with mss() as sct:
        monitor = sct.monitors[1]
        prev_frame = None
        
        while screen_share_active:
            try:
                start_time = time.time()
                
                screenshot = sct.grab({
                    'left': monitor['left'] + 100,
                    'top': monitor['top'] + 100,
                    'width': monitor['width'] - 200,
                    'height': monitor['height'] - 200
                })
                
                frame = cv2.resize(np.array(screenshot), (1280, 720))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                quality = 75
                if prev_frame is not None:
                    prev_resized = cv2.resize(prev_frame, (1280, 720))
                    frame_diff = cv2.absdiff(frame, prev_resized)
                    diff_percentage = np.sum(frame_diff) / (frame.size * 255)
                    quality = max(50, min(85, 75 - int(diff_percentage * 100 * 0.2)))
                
                _, buffer = cv2.imencode('.jpg', frame, [
                    cv2.IMWRITE_JPEG_QUALITY, quality,
                    cv2.IMWRITE_JPEG_OPTIMIZE, 1
                ])
                
                if compression_enabled:
                    compressed = zlib.compress(buffer, level=1)
                    payload = {
                        'image': base64.b64encode(compressed).decode('utf-8'),
                        'compressed': True,
                        'quality': quality,
                        'timestamp': time.time()
                    }
                else:
                    payload = {
                        'image': base64.b64encode(buffer).decode('utf-8'),
                        'compressed': False,
                        'quality': quality,
                        'timestamp': time.time()
                    }
                
                socketio.emit('screen_frame', payload)
                
                prev_frame = frame
                time.sleep(max(0, 0.05 - (time.time() - start_time)))
                
            except Exception as e:
                print(f"Capture error: {e}")
                break

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('move_mouse')
def handle_move_mouse(data):
    try:
        current_x, current_y = mouse.position
        mouse.position = (current_x + data['deltaX'], current_y + data['deltaY'])
    except Exception as e:
        print(f"Mouse error: {e}")

@socketio.on('click')
def handle_click(data):
    try:
        mouse.click(Button.left if data['button'] == 'left' else Button.right)
    except Exception as e:
        print(f"Click error: {e}")

@socketio.on('scroll')
def handle_scroll(data):
    try:
        mouse.scroll(0, data['deltaY'] / 100)
    except Exception as e:
        print(f"Scroll error: {e}")

@socketio.on('keyboard_input')
def handle_keyboard_input(data):
    try:
        keyboard.type(data['text'])
    except Exception as e:
        print(f"Keyboard input error: {e}")

@socketio.on('keyboard_key')
def handle_keyboard_key(data):
    try:
        key_mapping = {
            'enter': Key.enter,
            'backspace': Key.backspace,
            'space': Key.space,
            'tab': Key.tab,
            'escape': Key.esc
        }
        
        if data['key'] in key_mapping:
            keyboard.press(key_mapping[data['key']])
            keyboard.release(key_mapping[data['key']])
    except Exception as e:
        print(f"Keyboard key error: {e}")

@socketio.on('start_screen_share')
def handle_start_share():
    global screen_share_active
    if not screen_share_active:
        screen_share_active = True
        threading.Thread(target=generate_frames, daemon=True).start()

@socketio.on('stop_screen_share')
def handle_stop_share():
    global screen_share_active
    screen_share_active = False

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    global screen_share_active
    screen_share_active = False
    print(f'Client disconnected: {request.sid}')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
