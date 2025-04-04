
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

# def eye_controlled_mouse():
#     global mouse_active
#     cam = cv2.VideoCapture(0)
#     face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
#     screen_w, screen_h = pyautogui.size()

#     # For blink detection
#     blink_count = 0
#     last_blink_time = 0
#     blink_interval = 0.4  # Time allowed between two blinks
#     RIGHT_EYE_UP = 386
#     RIGHT_EYE_DOWN = 374

#     # Iris + eye corners
#     RIGHT_IRIS_CENTER = 473
#     RIGHT_EYE_LEFT = 362
#     RIGHT_EYE_RIGHT = 263
#     RIGHT_EYE_TOP = 386
#     RIGHT_EYE_BOTTOM = 374

#     # Cursor speed
#     move_speed = 25  # pixels per step, you can adjust

#     while True:
#         if not mouse_active:
#             time.sleep(0.1)
#             continue

#         ret, frame = cam.read()
#         if not ret:
#             break

#         frame = cv2.flip(frame, 1)
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         output = face_mesh.process(rgb_frame)
#         landmark_points = output.multi_face_landmarks

#         if landmark_points:
#             landmarks = landmark_points[0].landmark

#             # Eye landmarks
#             iris_x = landmarks[RIGHT_IRIS_CENTER].x
#             iris_y = landmarks[RIGHT_IRIS_CENTER].y
#             left_x = landmarks[RIGHT_EYE_LEFT].x
#             right_x = landmarks[RIGHT_EYE_RIGHT].x
#             top_y = landmarks[RIGHT_EYE_TOP].y
#             bottom_y = landmarks[RIGHT_EYE_BOTTOM].y

#             # Normalize iris movement
#             horiz_pos = (iris_x - left_x) / (right_x - left_x)
#             vert_pos = (iris_y - top_y) / (bottom_y - top_y)

#             # Move based on direction
#             current_x, current_y = pyautogui.position()

#             if horiz_pos < 0.4:
#                 current_x -= move_speed  # Look Left
#             elif horiz_pos > 0.6:
#                 current_x += move_speed  # Look Right

#             if vert_pos < 0.4:
#                 current_y -= move_speed  # Look Up
#             elif vert_pos > 0.6:
#                 current_y += move_speed  # Look Down

#             # Clamp to screen
#             current_x = max(0, min(screen_w - 1, current_x))
#             current_y = max(0, min(screen_h - 1, current_y))

#             pyautogui.moveTo(current_x, current_y)

#             # --- Double Blink for Click ---
#             eye_dist = abs(landmarks[RIGHT_EYE_UP].y - landmarks[RIGHT_EYE_DOWN].y)
#             if eye_dist < 0.015:
#                 current_time = time.time()
#                 if current_time - last_blink_time < blink_interval:
#                     blink_count += 1
#                 else:
#                     blink_count = 1

#                 last_blink_time = current_time

#                 if blink_count == 2:
#                     pyautogui.click()
#                     blink_count = 0

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cam.release()


# def eye_controlled_mouse():
#     global mouse_active
#     cam = cv2.VideoCapture(0)
#     face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
#     screen_w, screen_h = pyautogui.size()

#     # For blink detection
#     blink_count = 0
#     last_blink_time = 0
#     blink_interval = 0.4
#     RIGHT_EYE_UP = 386
#     RIGHT_EYE_DOWN = 374

#     # Nose tip to detect head movement
#     NOSE_TIP = 1
#     neutral_x, neutral_y = None, None
#     threshold = 0.02  # Movement threshold
#     move_speed = 15  # pixels per move

#     while True:
#         if not mouse_active:
#             time.sleep(0.1)
#             continue

#         ret, frame = cam.read()
#         if not ret:
#             break

#         frame = cv2.flip(frame, 1)
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         output = face_mesh.process(rgb_frame)
#         landmark_points = output.multi_face_landmarks

#         if landmark_points:
#             landmarks = landmark_points[0].landmark
#             nose_x = landmarks[NOSE_TIP].x
#             nose_y = landmarks[NOSE_TIP].y

#             # Set neutral center once
#             if neutral_x is None or neutral_y is None:
#                 neutral_x = nose_x
#                 neutral_y = nose_y

#             dx = nose_x - neutral_x
#             dy = nose_y - neutral_y

#             current_x, current_y = pyautogui.position()

#             # Smooth movement based on head direction
#             if dx > threshold:
#                 current_x += move_speed  # Move right
#             elif dx < -threshold:
#                 current_x -= move_speed  # Move left

#             if dy > threshold:
#                 current_y += move_speed  # Move down
#             elif dy < -threshold:
#                 current_y -= move_speed  # Move up

#             # Clamp to screen
#             current_x = max(0, min(screen_w - 1, current_x))
#             current_y = max(0, min(screen_h - 1, current_y))
#             pyautogui.moveTo(current_x, current_y)

#             # --- Double Blink for Click ---
#             eye_dist = abs(landmarks[RIGHT_EYE_UP].y - landmarks[RIGHT_EYE_DOWN].y)
#             if eye_dist < 0.015:
#                 current_time = time.time()
#                 if current_time - last_blink_time < blink_interval:
#                     blink_count += 1
#                 else:
#                     blink_count = 1
#                 last_blink_time = current_time

#                 if blink_count == 2:
#                     pyautogui.click()
#                     blink_count = 0

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cam.release()

import cv2
import mediapipe as mp
import pyautogui
import time

# def eye_controlled_mouse():
#     global mouse_active
#     cam = cv2.VideoCapture(0)
#     face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
#     screen_w, screen_h = pyautogui.size()

#     # Nose tip for head movement
#     NOSE_TIP = 1
#     neutral_x, neutral_y = None, None
#     threshold = 0.02  # Sensitivity
#     move_speed = 15

#     # Eye landmarks for blink detection
#     RIGHT_EYE_UP = 386
#     RIGHT_EYE_DOWN = 374

#     # Blink detection variables
#     blink_count = 0
#     last_blink_time = 0
#     blink_interval = 0.6 # Max time between blinks
#     cooldown_time = 1  # Prevents accidental double clicks

#     while True:
#         if not mouse_active:
#             time.sleep(0.1)
#             continue

#         ret, frame = cam.read()
#         if not ret:
#             break

#         frame = cv2.flip(frame, 1)
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         output = face_mesh.process(rgb_frame)
#         landmark_points = output.multi_face_landmarks

#         if landmark_points:
#             landmarks = landmark_points[0].landmark
#             nose_x = landmarks[NOSE_TIP].x
#             nose_y = landmarks[NOSE_TIP].y

#             # Set neutral position
#             if neutral_x is None or neutral_y is None:
#                 neutral_x, neutral_y = nose_x, nose_y

#             dx = nose_x - neutral_x
#             dy = nose_y - neutral_y

#             current_x, current_y = pyautogui.position()

#             # Move cursor smoothly
#             if dx > threshold:
#                 current_x += move_speed
#             elif dx < -threshold:
#                 current_x -= move_speed

#             if dy > threshold:
#                 current_y += move_speed
#             elif dy < -threshold:
#                 current_y -= move_speed

#             # Keep cursor within screen bounds
#             current_x = max(0, min(screen_w - 1, current_x))
#             current_y = max(0, min(screen_h - 1, current_y))
#             pyautogui.moveTo(current_x, current_y)

#             # --- Blink Detection ---
#             eye_dist = abs(landmarks[RIGHT_EYE_UP].y - landmarks[RIGHT_EYE_DOWN].y)

#             if eye_dist < 0.015:
#                 current_time = time.time()

#                 # If blink happens within interval
#                 if current_time - last_blink_time < blink_interval:
#                     blink_count += 1
#                 else:
#                     blink_count = 1

#                 last_blink_time = current_time

#             # Click logic
#             if blink_count == 2:  # Double blink → Left Click
#                 pyautogui.click()
#                 blink_count = 0
#                 time.sleep(cooldown_time)  # Prevent multiple clicks

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cam.release()

# def eye_controlled_mouse():
#     global mouse_active
#     cam = cv2.VideoCapture(0)
#     face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
#     screen_w, screen_h = pyautogui.size()

#     # Nose tip for head movement
#     NOSE_TIP = 1
#     neutral_x, neutral_y = None, None
#     threshold = 0.02  # Sensitivity
#     move_speed = 15

#     # Eye landmarks for blink detection
#     RIGHT_EYE_UP = 386
#     RIGHT_EYE_DOWN = 374
#     EYE_CLOSE_THRESHOLD = 0.015  # Adjust as needed

#     # Blink detection variables
#     blink_start_time = None
#     min_blink_duration = 0.5  # Click if eye closed for 0.5 sec
#     clicked = False  # Prevents repeated clicks while eye is closed
#     cooldown_time = 1  # Prevents multiple clicks

#     while True:
#         if not mouse_active:
#             time.sleep(0.1)
#             continue

#         ret, frame = cam.read()
#         if not ret:
#             break

#         frame = cv2.flip(frame, 1)
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         output = face_mesh.process(rgb_frame)
#         landmark_points = output.multi_face_landmarks

#         if landmark_points:
#             landmarks = landmark_points[0].landmark
#             nose_x = landmarks[NOSE_TIP].x
#             nose_y = landmarks[NOSE_TIP].y

#             # Set neutral position
#             if neutral_x is None or neutral_y is None:
#                 neutral_x, neutral_y = nose_x, nose_y

#             dx = nose_x - neutral_x
#             dy = nose_y - neutral_y

#             current_x, current_y = pyautogui.position()

#             # Move cursor smoothly
#             if dx > threshold:
#                 current_x += move_speed
#             elif dx < -threshold:
#                 current_x -= move_speed

#             if dy > threshold:
#                 current_y += move_speed
#             elif dy < -threshold:
#                 current_y -= move_speed

#             # Keep cursor within screen bounds
#             current_x = max(0, min(screen_w - 1, current_x))
#             current_y = max(0, min(screen_h - 1, current_y))
#             pyautogui.moveTo(current_x, current_y)

#             # --- Blink Hold Detection ---
#             eye_dist = abs(landmarks[RIGHT_EYE_UP].y - landmarks[RIGHT_EYE_DOWN].y)

#             if eye_dist < EYE_CLOSE_THRESHOLD:
#                 if blink_start_time is None:
#                     blink_start_time = time.time()  # Start timer
#                     clicked = False  # Reset click status

#                 elif time.time() - blink_start_time >= min_blink_duration and not clicked:
#                     pyautogui.click()
#                     clicked = True  # Ensures only one click per long blink
#                     time.sleep(cooldown_time)  # Prevents multiple clicks
#             else:
#                 blink_start_time = None  # Reset if eyes open
#                 clicked = False  # Reset click status

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cam.release()


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
