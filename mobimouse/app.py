from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from pynput.mouse import Controller, Button
import pyautogui

app = Flask(__name__)
socketio = SocketIO(app)
mouse = Controller()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('move_mouse')
def handle_move_mouse(data):
    try:
        delta_x = data['deltaX']
        delta_y = data['deltaY']
        
        # Get screen dimensions for boundary checking
        screen_width, screen_height = pyautogui.size()
        
        # Get current position and calculate new position
        current_x, current_y = mouse.position
        new_x = current_x + delta_x
        new_y = current_y + delta_y
        
        # Ensure we stay within screen bounds
        new_x = max(0, min(new_x, screen_width - 1))
        new_y = max(0, min(new_y, screen_height - 1))
        
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
        # Smooth scrolling with adjusted sensitivity
        mouse.scroll(0, delta_y / 120)  # Standard scroll wheel increment
    except Exception as e:
        print(f"Error in scroll: {e}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)