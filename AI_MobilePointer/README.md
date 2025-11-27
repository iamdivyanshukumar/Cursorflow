# WiFi Mouse Control & AI Assistant

A powerful remote control application that transforms your mobile device into a wireless mouse, keyboard, and AI-powered assistant for your computer. Control your desktop remotely with screen sharing capabilities and get AI-powered insights about your screen content.

---

## Features

### Remote Control
- Touchpad Mouse Control: Precise cursor control with customizable sensitivity
- Virtual Keyboard: Full keyboard input support
- Media Controls: Play, pause, and control media volume
- Screen Sharing: Real-time screen mirroring to your mobile device
- Multi-touch Gestures: Single/double tap, two-finger scroll support

### AI Assistant
- Screen Content Analysis: OCR-powered text extraction from screen
- Smart Summarization: AI-generated summaries of visible content
- Q&A System: Ask questions about on-screen content
- Context Awareness: Remembers conversation history and content
- Vector Database: Efficient content storage and retrieval

### Security & Connectivity
- Password Protection: Secure authentication system
- QR Code Pairing: Easy mobile connection setup
- Cross-platform: Works on Windows, macOS, and Linux
- Real-time Communication: WebSocket-based low-latency control

---

## Components Overview

### Flask Web Server (app.py)
- Handles HTTP requests and WebSocket connections
- Manages authentication and client sessions
- Coordinates between mobile clients and desktop controls

### AI Service (services/ai_service.py)
- OpenAI integration for text processing
- Vector database for content storage
- Conversation management and context retention

### Text Extraction (services/text_extractor.py)
- Screen capture using MSS
- OCR processing with Tesseract
- Image preprocessing for better text recognition

### Web Interface (templates/)
- Responsive mobile interface (index.html)
- Desktop dashboard (desktop.html)
- Real-time screen sharing display

---

## Quick Start

### Prerequisites
- Python 3.8+
- Tesseract OCR
- OpenAI API Key (for AI features)

### Installation

**Clone the repository**
```bash
git clone https://github.com/yourusername/wifi-mouse-control.git
cd wifi-mouse-control
```

**Install Python dependencies**
```bash
pip install -r requirements.txt
```

**Install Tesseract OCR**
- Windows: Download from UB-Mannheim/tesseract
- macOS: brew install tesseract
- Linux: sudo apt-get install tesseract-ocr

**Configure Environment**
```bash
cp .env.example .env
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
```

### Running the Application
**Start the server**
```bash
python app.py
```

**Access the application**
- Desktop: http://[server-ip]:5000
- Mobile: automatically redirects to the remote interface

**Connect your mobile device**
- Scan the QR code from the desktop dashboard, or
- Enter the server URL manually on your mobile browser

---

## Interface Overview

### Desktop Dashboard
<p align="center">
  <img src="assets\images\Desktop_img.png" width="50%">
</p>

### Mobile Remote Interface
<p align="center">
  <img src="assets\images\mobile_01.jpg" width="30%">
  <img src="assets\images\mobile_02.jpg" width="30%">
  <img src="assets\images\mobile_03.jpg" width="30%">
</p>
<p align="center">
  <img src="assets\images\mobile_04.jpg" width="30%">
  <img src="assets\images\mobile_05.jpg" width="30%">
  <img src="assets\images\mobile_06.jpg" width="30%">
  <img src="assets\images\mobile_07.jpg" width="30%">
</p>


---

## Configuration

### Environment Variables
Create a .env file in the project root:
```
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_optional
```

### Server Configuration
Modify config/settings.py for advanced settings:
```
MOUSE_SENSITIVITY = 2.2
SCROLL_SENSITIVITY = 1.0
VIDEO_QUALITY = 80
MAX_FPS = 30
AUTH_PASSWORD = 'admin123'
```

---

## API Endpoints

### HTTP Endpoints
GET / - Main application (auto-detects device type)
GET /mobile - Direct mobile interface access
GET /api/status - Server status information
GET /api/ai/status - AI service status

### WebSocket Events
move_mouse - Mouse movement control
click - Mouse click events
scroll - Scroll wheel control
keyboard_input - Text input
media_key - Media control commands
ai_summarize_page - AI content summarization
ai_ask_question - AI Q&A about screen content

---

## AI Assistant Usage

The AI assistant uses OCR to extract text from your screen and provides:
- Content Summarization
- Question Answering
- Content Analysis
- Caching & Performance

---

## Troubleshooting

Tesseract not found
Solution: Install Tesseract OCR and ensure it's in PATH

Screen sharing not working
Solution: Run as administrator or enable screen recording permission

AI features disabled
Solution: Add API key to .env file

Connection refused
Solution: Allow port 5000 through firewall and check server IP

---

## Performance Notes

- Latency: <100ms for mouse movements
- Screen Sharing: Adjustable quality for bandwidth optimization
- AI Processing: First OCR takes ~3s, cached for faster reuse
- Memory Usage: ~100MB base + 50MB per active session

---


## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Open a Pull Request

---

## Acknowledgments

- OpenAI – for AI capabilities
- Tesseract OCR – for text extraction
- Flask and SocketIO – for the web framework
- FAISS – for vector similarity search
