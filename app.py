
from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import cv2
import mediapipe as mp
import pyautogui
import time
import threading

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for thread control
mouse_active = False
thread = None


def eye_controlled_mouse():
    global mouse_active
    cam = cv2.VideoCapture(0)
    face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
    screen_w, screen_h = pyautogui.size()

    # Nose tip for head movement
    NOSE_TIP = 1
    neutral_x, neutral_y = None, None
    threshold = 0.02  # Sensitivity
    move_speed = 15

    # Eye landmarks for blink detection
    RIGHT_EYE_UP = 386
    RIGHT_EYE_DOWN = 374
    EYE_CLOSE_THRESHOLD = 0.015  # Adjust as needed

    # Mouth landmarks
    MOUTH_UP = 13
    MOUTH_DOWN = 14
    MOUTH_OPEN_THRESHOLD = 0.05  # Adjust as needed

    # Blink detection variables
    blink_start_time = None
    min_blink_duration = 0.5  # Click if eye closed for 0.5 sec
    clicked = False  # Prevents repeated clicks while eye is closed
    cooldown_time = 1  # Prevents multiple clicks

    # Mouth open-close detection
    mouth_was_open = False
    is_paused = False  # True when cursor is paused

    while True:
        if not mouse_active:
            time.sleep(0.1)
            continue

        ret, frame = cam.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = face_mesh.process(rgb_frame)
        landmark_points = output.multi_face_landmarks

        if landmark_points:
            landmarks = landmark_points[0].landmark
            nose_x = landmarks[NOSE_TIP].x
            nose_y = landmarks[NOSE_TIP].y

            # --- Mouth Open-Close Toggle ---
            mouth_dist = abs(landmarks[MOUTH_UP].y - landmarks[MOUTH_DOWN].y)

            if mouth_dist > MOUTH_OPEN_THRESHOLD:
                mouth_was_open = True  # Detect when mouth opens
            elif mouth_was_open:  # Detect when mouth closes
                is_paused = not is_paused  # Toggle cursor state
                mouth_was_open = False  # Reset flag
                time.sleep(0.5)  # Prevents rapid toggling

            if is_paused:
                continue  # Skip movement & click processing

            # --- Set Neutral Position ---
            if neutral_x is None or neutral_y is None:
                neutral_x, neutral_y = nose_x, nose_y

            dx = nose_x - neutral_x
            dy = nose_y - neutral_y

            current_x, current_y = pyautogui.position()

            # --- Move Cursor ---
            if dx > threshold:
                current_x += move_speed
            elif dx < -threshold:
                current_x -= move_speed

            if dy > threshold:
                current_y += move_speed
            elif dy < -threshold:
                current_y -= move_speed

            # Keep cursor within screen bounds
            current_x = max(0, min(screen_w - 1, current_x))
            current_y = max(0, min(screen_h - 1, current_y))
            pyautogui.moveTo(current_x, current_y)

            # --- Blink Hold Detection ---
            eye_dist = abs(landmarks[RIGHT_EYE_UP].y - landmarks[RIGHT_EYE_DOWN].y)

            if eye_dist < EYE_CLOSE_THRESHOLD:
                if blink_start_time is None:
                    blink_start_time = time.time()  # Start timer
                    clicked = False  # Reset click status

                elif time.time() - blink_start_time >= min_blink_duration and not clicked:
                    pyautogui.click()
                    clicked = True  # Ensures only one click per long blink
                    time.sleep(cooldown_time)  # Prevents multiple clicks
            else:
                blink_start_time = None  # Reset if eyes open
                clicked = False  # Reset click status

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mobi-mouse')
def mobimouse():
    return render_template('mobi-mouse.html')


@app.route('/vanni')
def vanni():
    return render_template('vanni.html')

@app.route('/dristi')
def dristi():
    return render_template('dristi.html')


@socketio.on('toggle_mouse')
def toggle_mouse(data):
    global mouse_active, thread
    mouse_active = data['active']
    emit('status', {'active': mouse_active})

    if mouse_active and thread is None:
        thread = threading.Thread(target=eye_controlled_mouse)
        thread.start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
