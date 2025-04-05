# CursorFlow

CursorFlow is a web-based application that combines the functionalities of two innovative mouse control systems: **Dristi Mouse** and **MobiMouse**. It provides accessibility solutions for hands-free and remote mouse control, making it ideal for individuals with mobility challenges or those who want to control their computer remotely.

---

## MobiMouse

MobiMouse is a Flask-based application that allows users to control their computer's mouse using a web interface. It provides features such as mouse movement, clicks, scrolling, and screen sharing, making it a versatile tool for remote mouse control.

### Features
- **Mouse Movement**: Control the mouse pointer using a virtual touchpad on the web interface.
- **Click Actions**: Perform left and right mouse clicks remotely.
- **Scrolling**: Scroll up and down using dedicated buttons or gestures.
- **Screen Sharing**: View your computer screen in real-time on the web interface.
- **Responsive Design**: Works seamlessly on both desktop and mobile devices.

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- A device with a web browser (e.g., smartphone, tablet, or computer)
- Both the computer and the mobile device must be connected to the **same Wi-Fi network**.

### Installation Process
1. **Clone the Repository**
   ```bash
   git clone  https://github.com/iamdivyanshukumar/Cursorflow.git
   cd Cursorflow

2. **Set up a Virtual Environment**
   ```cmd
   python -m venv myenv
   myenv\Scripts\activate.bat

3. **Install Dependencies**
   ```cmd
   pip install -r requirements.txt

   
4. **For runing mouse change directory**
   ```cmd
   cd mobimouse
   

5. **Find Your Local IP Address
On Windows, open the Command Prompt and run:**
    ```cmd
   ipconfig

6. **Update the Server IP in the Code
  Open the index.html file located in the templates folder:
  index.html
  Find the line:(use ctrl+f)**
  const socket = io.connect("http://192.168.239.37:5000");

7. **Replace 192.168.239.37 with your computer's IPv4 address from the previous step.**
8. Run the Application Start the Flask application:
   ```cmd
   python app.py
9. Access the Application
Open your browser on your mobile device or computer and navigate to **http://<your-ip>:5000** (replace <your-ip> with your computer's IPv4 address).

Usage
Mouse Movement: Use the virtual touchpad on the web interface to move the mouse pointer.

Click Actions: Click the "Left Click" or "Right Click" buttons to perform respective mouse clicks.

Scrolling: Use the "▲" and "▼" buttons to scroll up and down.

Screen Sharing: Click the "Start Screen Share" button to view your computer screen on the web interface. Click "Stop Screen Share" to end the session.

Touch Gestures: On touch-enabled devices, use gestures on the touchpad for smooth mouse movement.


Dristi Mouse:-

Dristi Mouse is an innovative hands-free mouse control system that uses eye and head gestures to control the cursor. It is designed to provide accessibility solutions for individuals with mobility challenges or anyone looking for a hands-free way to interact with their computer.

Features
- Eye-Controlled Mouse Movement: Move the cursor using eye and head gestures.
Blink Detection for Clicks: Double blink to simulate a mouse click.

- Head Movement for Navigation: Control the cursor by moving your head.

- Mouth Open-Close Toggle: Pause or resume cursor control with mouth gestures.

- Customizable Sensitivity: Adjust thresholds for eye and head movements to suit your needs.

Prerequisites:-

- Python 3.8 or higher
- pip (Python package manager)
- A webcam for eye and head tracking
- Mediapipe and OpenCV libraries for facial landmark detection and image processing

Installation Process

1. For running cursorflow(Dristi mouse)
   ```bash
   cd..

3. Run the Application Start the application:
python [app.py](http://vscodecontentref/3)

4. Access the Application

Open your browser and navigate to http://localhost:5000.

4. Use the Dristi Mouse

- Go to the CursorFlow website.
- At the top, you will see a Buy option under which the Dristi Mouse is listed.
- Click on it, and you will be redirected to another page.
- On this page, you will see two options: Start Tracking and Stop Tracking.
- Click on Start Tracking to activate the Dristi Mouse and enjoy hands-free control.

Usage
- Eye-Controlled Cursor Movement: The application uses Mediapipe's face mesh to track eye and head movements. Move your head or eyes to control the cursor's position on the screen.

- Blink Detection for Clicks: Double blink to simulate a left mouse click. Long blink (hold for 0.5 seconds) to simulate a right mouse click.

- Mouth Open-Close Toggle: Open your mouth to pause cursor movement. Close your mouth to resume cursor movement.

- Head Movement for Navigation: Move your head left, right, up, or down to navigate the screen.

File Structure:-

<pre><code>Cursorflow/ ├── app.py # Main application file ├── requirements.txt # Dependencies for the project ├── mobimouse/ │ ├── app.py # Submodule for MobiMouse │ ├── requirements.txt # Dependencies for MobiMouse │ └── templates/ │ └── index.html # HTML template for MobiMouse ├── templates/ │ ├── index.html # Homepage template │ ├── mobi-mouse.html # MobiMouse page template │ ├── vanni.html # Vanni page template │ └── dristi.html # Dristi page template ├── static/ │ ├── css/ # CSS files for styling │ ├── images/ # Images used in the application │ └── js/ # JavaScript files └── README.md # Documentation file </code></pre>

Technologies Used
- Flask: Web framework for the backend.
- Flask-SocketIO: Real-time communication between the server and client.
- Mediapipe: Facial landmark detection for Dristi.
- OpenCV: Image processing for Dristi.
- PyAutoGUI: Simulate mouse movements, clicks, and scrolling.
- Pynput: Low-level control of the mouse for MobiMouse.
- MSS: Screen capturing for MobiMouse's screen sharing.

Important Notes
- Same Wi-Fi Network: Ensure that both your computer and mobile device are connected to the same Wi-Fi network for MobiMouse to work.

- Webcam Requirement: A webcam is required for Dristi's eye and head tracking features.

- Lighting Conditions: Ensure proper lighting for accurate facial landmark detection.

License
This project is licensed under the MIT License.

Contact
For any queries or support, contact us at
 - Email: udittiwarit2004@gmail.com
 - Phone Number- 6397766117
