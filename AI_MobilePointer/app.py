from flask import Flask, render_template, request, jsonify
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
import socket
from concurrent.futures import ThreadPoolExecutor
import json
import os
import hashlib
import logging
from datetime import datetime
import platform
import qrcode
from io import BytesIO
import base64
from dotenv import load_dotenv

# Import project modules
from utils.device_detection import get_client_info
from services.ai_service import AIService
from services.text_extractor import TextExtractor

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize controllers
mouse = Controller()
keyboard = KeyboardController()
screen_share_active = False
frame_executor = ThreadPoolExecutor(max_workers=4)

# Initialize AI Service with vector storage
ai_service = AIService(os.getenv('OPENAI_API_KEY'), storage_path="ai_storage")

# AI Services - Load API key from .env
ai_service = AIService(os.getenv('OPENAI_API_KEY'))
text_extractor = TextExtractor()

# Configuration
config = {
    'mouse_sensitivity': 2.2,
    'scroll_sensitivity': 1.0,
    'double_click_time': 300,
    'theme': 'dark',
    'enable_visual_feedback': True,
    'video_quality': 80,
    'max_fps': 30,
    'auth_enabled': True,
    'auth_password': 'admin123',
    'pairing_code': hashlib.sha256(os.urandom(32)).hexdigest()[:6],
    'pairing_code_expiry': time.time() + 3600
}

# Track authenticated clients
authenticated_clients = set()

# Server instance management
server_instance = {
    'start_time': datetime.now(),
    'total_connections': 0,
    'current_connections': 0
}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Failed to get local IP: {e}")
        return '127.0.0.1'

def generate_qr_code(url):
    """Generate QR code for mobile connection"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"QR code generation error: {e}")
        return None

def generate_frames():
    """Screen capture function"""
    with mss() as sct:
        monitor = sct.monitors[1]
        target_fps = config['max_fps']
        target_width = 1280
        target_height = 720
        
        while screen_share_active:
            try:
                start_time = time.time()
                
                # Capture screen
                screenshot = sct.grab({
                    'left': monitor['left'],
                    'top': monitor['top'],
                    'width': monitor['width'],
                    'height': monitor['height']
                })
                
                frame = cv2.resize(np.array(screenshot), (target_width, target_height))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Draw mouse pointer
                mouse_x, mouse_y = mouse.position
                mouse_x -= monitor['left']
                mouse_y -= monitor['top']
                
                if 0 <= mouse_x < monitor['width'] and 0 <= mouse_y < monitor['height']:
                    scaled_x = int(mouse_x * (target_width / monitor['width']))
                    scaled_y = int(mouse_y * (target_height / monitor['height']))
                    cv2.circle(frame, (scaled_x, scaled_y), 8, (0, 0, 255), 2)
                    cv2.line(frame, (scaled_x-10, scaled_y), (scaled_x+10, scaled_y), (0, 0, 255), 2)
                    cv2.line(frame, (scaled_x, scaled_y-10), (scaled_x, scaled_y+10), (0, 0, 255), 2)
                
                # Encode frame
                _, buffer = cv2.imencode('.jpg', frame, [
                    cv2.IMWRITE_JPEG_QUALITY, config['video_quality'],
                    cv2.IMWRITE_JPEG_OPTIMIZE, 1
                ])
                
                payload = {
                    'image': base64.b64encode(buffer).decode('utf-8'),
                    'quality': config['video_quality'],
                    'timestamp': time.time(),
                    'cursor': {'x': scaled_x, 'y': scaled_y}
                }
                
                socketio.emit('screen_frame', payload)
                
                # Frame rate control
                processing_time = time.time() - start_time
                sleep_time = max(0, (1.0 / target_fps) - processing_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Capture error: {e}")
                break

# Routes
@app.route('/')
def index():
    """Main route - serve desktop dashboard on desktop, mobile interface on mobile"""
    client_info = get_client_info(request)
    local_ip = get_local_ip()
    
    if client_info['device_type'] == 'mobile':
        return render_template('index.html', server_ip=local_ip)
    else:
        qr_code = generate_qr_code(f"http://{local_ip}:5000")
        return render_template('desktop.html', 
                             server_ip=local_ip, 
                             qr_code=qr_code,
                             server_url=f"http://{local_ip}:5000")

@app.route('/mobile')
def mobile_interface():
    """Direct access to mobile interface"""
    local_ip = get_local_ip()
    return render_template('index.html', server_ip=local_ip)

@app.route('/api/status')
def api_status():
    """API endpoint for server status"""
    return jsonify({
        'status': 'running',
        'start_time': server_instance['start_time'].isoformat(),
        'total_connections': server_instance['total_connections'],
        'current_connections': server_instance['current_connections'],
        'authenticated_clients': len(authenticated_clients),
        'screen_share_active': screen_share_active,
        'pairing_code': config['pairing_code'],
        'ai_configured': ai_service.is_configured()
    })

@app.route('/api/ai/status')
def ai_status():
    """Get AI service status"""
    return jsonify({
        'configured': ai_service.is_configured(),
        'has_api_key': bool(ai_service.api_key)
    })

@app.route('/api/ai/test-ocr')
def test_ocr():
    """Test OCR functionality"""
    try:
        success = text_extractor.test_ocr()
        return jsonify({
            'success': success,
            'message': 'OCR test completed' if success else 'OCR test failed'
        })
    except Exception as e:
        logger.error(f"OCR test error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/debug-capture')
def debug_capture():
    """Debug endpoint to capture and return screen info"""
    try:
        import tempfile
        import base64
        
        # Capture screen
        image = text_extractor.capture_screen_area()
        if image is None:
            return jsonify({'error': 'Failed to capture screen'}), 500
        
        # Save temporary image for debugging
        _, buffer = cv2.imencode('.jpg', image)
        img_str = base64.b64encode(buffer).decode('utf-8')
        
        # Try to extract text
        text = text_extractor.extract_text_from_image(image)
        
        return jsonify({
            'image_size': f"{image.shape[1]}x{image.shape[0]}",
            'channels': image.shape[2] if len(image.shape) > 2 else 1,
            'text_extracted': bool(text),
            'text_length': len(text) if text else 0,
            'text_preview': text[:200] + "..." if text and len(text) > 200 else text,
            'image_data': f"data:image/jpeg;base64,{img_str}" if img_str else None
        })
        
    except Exception as e:
        logger.error(f"Debug capture error: {e}")
        return jsonify({'error': str(e)}), 500

# SocketIO Handlers
@socketio.on('move_mouse')
def handle_move_mouse(data):
    if request.sid not in authenticated_clients:
        return
    try:
        sensitivity = config['mouse_sensitivity']
        current_x, current_y = mouse.position
        mouse.position = (
            current_x + data.get('deltaX', 0) * sensitivity,
            current_y + data.get('deltaY', 0) * sensitivity
        )
    except Exception as e:
        logger.error(f"Mouse movement error: {e}")

@socketio.on('click')
def handle_click(data):
    if request.sid not in authenticated_clients:
        return
    try:
        button = Button.left if data.get('button') == 'left' else Button.right
        if data.get('double', False):
            mouse.click(button, 2)
        else:
            mouse.click(button)
    except Exception as e:
        logger.error(f"Click error: {e}")

@socketio.on('scroll')
def handle_scroll(data):
    if request.sid not in authenticated_clients:
        return
    try:
        sensitivity = config['scroll_sensitivity']
        mouse.scroll(0, data.get('deltaY', 0) * sensitivity / 100)
    except Exception as e:
        logger.error(f"Scroll error: {e}")

@socketio.on('keyboard_input')
def handle_keyboard_input(data):
    if request.sid not in authenticated_clients:
        return
    try:
        keyboard.type(data.get('text', ''))
    except Exception as e:
        logger.error(f"Keyboard input error: {e}")

@socketio.on('keyboard_key')
def handle_keyboard_key(data):
    if request.sid not in authenticated_clients:
        return
    try:
        key_mapping = {
            'enter': Key.enter,
            'backspace': Key.backspace,
            'space': Key.space,
            'tab': Key.tab,
            'escape': Key.esc,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'ctrl': Key.ctrl,
            'alt': Key.alt,
            'shift': Key.shift,
            'cmd': Key.cmd
        }
        
        key = data.get('key')
        if key in key_mapping:
            keyboard.press(key_mapping[key])
            keyboard.release(key_mapping[key])
    except Exception as e:
        logger.error(f"Keyboard key error: {e}")

@socketio.on('media_key')
def handle_media_key(data):
    if request.sid not in authenticated_clients:
        return
    try:
        media_mapping = {
            'play_pause': Key.media_play_pause,
            'volume_up': Key.media_volume_up,
            'volume_down': Key.media_volume_down,
            'volume_mute': Key.media_volume_mute
        }
        
        key = data.get('key')
        if key in media_mapping:
            keyboard.press(media_mapping[key])
            keyboard.release(media_mapping[key])
    except Exception as e:
        logger.error(f"Media key error: {e}")

@socketio.on('start_screen_share')
def handle_start_share():
    if request.sid not in authenticated_clients:
        return
    global screen_share_active
    if not screen_share_active:
        screen_share_active = True
        frame_executor.submit(generate_frames)
        emit('screen_share_status', {'active': True})

@socketio.on('stop_screen_share')
def handle_stop_share():
    if request.sid not in authenticated_clients:
        return
    global screen_share_active
    screen_share_active = False
    emit('screen_share_status', {'active': False})

@socketio.on('authenticate')
def handle_authentication(data):
    current_time = time.time()
    valid = False
    
    if data.get('password') == config['auth_password']:
        valid = True
    
    if not valid and data.get('pairing_code'):
        if current_time < config['pairing_code_expiry']:
            valid = (data['pairing_code'] == config['pairing_code'])
    
    if valid:
        authenticated_clients.add(request.sid)
        emit('authentication_success')
        config['pairing_code'] = hashlib.sha256(os.urandom(32)).hexdigest()[:6]
        config['pairing_code_expiry'] = current_time + 3600
    else:
        emit('authentication_failure')
        if request.sid in authenticated_clients:
            authenticated_clients.remove(request.sid)

# AI Socket Handlers - FIXED: Added data parameter
@socketio.on('ai_summarize_page')
def handle_ai_summarize(data=None):
    """Summarize current page content"""
    if request.sid not in authenticated_clients:
        emit('ai_response', {'type': 'error', 'message': 'Authentication required'})
        return
    
    try:
        if not ai_service.is_configured():
            emit('ai_response', {'type': 'error', 'message': 'OpenAI API key not configured in .env file'})
            return
        
        # Capture text from screen
        text = text_extractor.get_page_text()
        
        if not text:
            emit('ai_response', {
                'type': 'error', 
                'message': 'No readable text found on screen. Try capturing a different area.'
            })
            return
        
        # Generate summary
        summary = ai_service.summarize_text(text)
        
        emit('ai_response', {
            'type': 'summary',
            'summary': summary,
            'original_text_length': len(text)
        })
        
    except Exception as e:
        logger.error(f"Page summarization error: {e}")
        emit('ai_response', {'type': 'error', 'message': f'Summarization failed: {str(e)}'})

@socketio.on('ai_ask_question')
def handle_ai_question(data):
    """Answer question about current page"""
    if request.sid not in authenticated_clients:
        emit('ai_response', {'type': 'error', 'message': 'Authentication required'})
        return
    
    try:
        if not ai_service.is_configured():
            emit('ai_response', {'type': 'error', 'message': 'OpenAI API key not configured in .env file'})
            return
        
        question = data.get('question')
        if not question:
            emit('ai_response', {'type': 'error', 'message': 'Question is required'})
            return
        
        # Capture text from screen
        text = text_extractor.get_page_text()
        
        if not text:
            emit('ai_response', {
                'type': 'error', 
                'message': 'No readable text found on screen. Capture content first.'
            })
            return
        
        # Get answer
        answer = ai_service.answer_question(text, question, request.sid)
        
        emit('ai_response', {
            'type': 'answer',
            'question': question,
            'answer': answer,
            'context_length': len(text)
        })
        
    except Exception as e:
        logger.error(f"Question answering error: {e}")
        emit('ai_response', {'type': 'error', 'message': f'Question answering failed: {str(e)}'})

@socketio.on('ai_analyze_page')
def handle_ai_analyze(data=None):
    """Analyze page content"""
    if request.sid not in authenticated_clients:
        emit('ai_response', {'type': 'error', 'message': 'Authentication required'})
        return
    
    try:
        if not ai_service.is_configured():
            emit('ai_response', {'type': 'error', 'message': 'OpenAI API key not configured in .env file'})
            return
        
        # Capture text from screen
        text = text_extractor.get_page_text()
        
        if not text:
            emit('ai_response', {
                'type': 'error', 
                'message': 'No readable text found on screen.'
            })
            return
        
        # Analyze content
        analysis = ai_service.analyze_page_content(text)
        
        emit('ai_response', {
            'type': 'analysis',
            'analysis': analysis,
            'text_sample': text[:500] + '...' if len(text) > 500 else text
        })
        
    except Exception as e:
        logger.error(f"Page analysis error: {e}")
        emit('ai_response', {'type': 'error', 'message': f'Analysis failed: {str(e)}'})

@socketio.on('ai_clear_history')
def handle_ai_clear_history(data=None):
    """Clear conversation history"""
    if request.sid not in authenticated_clients:
        return
    
    try:
        ai_service.clear_conversation_history(request.sid)
        emit('ai_response', {'type': 'info', 'message': 'Conversation history cleared'})
    except Exception as e:
        logger.error(f"Clear history error: {e}")

@socketio.on('connect')
def handle_connect():
    client_info = get_client_info(request)
    server_instance['total_connections'] += 1
    server_instance['current_connections'] += 1
    
    logger.info(f'Client connected: {request.sid} ({client_info["device_type"]})')
    emit('authentication_required')
    emit('pairing_code', {'code': config['pairing_code']})

@socketio.on('disconnect')
def handle_disconnect():
    global screen_share_active
    if request.sid in authenticated_clients:
        authenticated_clients.remove(request.sid)
    screen_share_active = False
    server_instance['current_connections'] -= 1
    logger.info(f'Client disconnected: {request.sid}')


# ... existing routes and socket handlers ...

@socketio.on('ai_summarize_page')
def handle_ai_summarize(data=None):
    """Summarize current page content with caching"""
    if request.sid not in authenticated_clients:
        emit('ai_response', {'type': 'error', 'message': 'Authentication required'})
        return
    
    try:
        if not ai_service.is_configured():
            emit('ai_response', {'type': 'error', 'message': 'OpenAI API key not configured in .env file'})
            return
        
        # Check if we have cached OCR for this client
        cached_text, content_hash = ai_service.get_cached_ocr(request.sid)
        
        if cached_text:
            text = cached_text
            logger.info("Using cached OCR content for summarization")
        else:
            # Capture text from screen
            text = text_extractor.get_page_text()
            if text:
                # Cache the OCR result
                ai_service.cache_ocr_result(request.sid, text)
        
        if not text:
            emit('ai_response', {
                'type': 'error', 
                'message': 'No readable text found on screen. Try capturing a different area.'
            })
            return
        
        # Generate summary
        summary = ai_service.summarize_text(text, client_id=request.sid)
        
        emit('ai_response', {
            'type': 'summary',
            'summary': summary,
            'original_text_length': len(text),
            'used_cache': bool(cached_text)
        })
        
    except Exception as e:
        logger.error(f"Page summarization error: {e}")
        emit('ai_response', {'type': 'error', 'message': f'Summarization failed: {str(e)}'})

@socketio.on('ai_ask_question')
def handle_ai_question(data):
    """Answer question about current page with context from vector store"""
    if request.sid not in authenticated_clients:
        emit('ai_response', {'type': 'error', 'message': 'Authentication required'})
        return
    
    try:
        if not ai_service.is_configured():
            emit('ai_response', {'type': 'error', 'message': 'OpenAI API key not configured in .env file'})
            return
        
        question = data.get('question')
        if not question:
            emit('ai_response', {'type': 'error', 'message': 'Question is required'})
            return
        
        # Check if we have cached OCR for this client
        cached_text, content_hash = ai_service.get_cached_ocr(request.sid)
        
        if cached_text:
            text = cached_text
            logger.info("Using cached OCR content for question answering")
        else:
            # Capture text from screen
            text = text_extractor.get_page_text()
            if text:
                # Cache the OCR result
                ai_service.cache_ocr_result(request.sid, text)
        
        if not text:
            emit('ai_response', {
                'type': 'error', 
                'message': 'No readable text found on screen. Capture content first.'
            })
            return
        
        # Get answer with context from vector store
        answer = ai_service.answer_question(text, question, request.sid)
        
        emit('ai_response', {
            'type': 'answer',
            'question': question,
            'answer': answer,
            'context_length': len(text),
            'used_cache': bool(cached_text)
        })
        
    except Exception as e:
        logger.error(f"Question answering error: {e}")
        emit('ai_response', {'type': 'error', 'message': f'Question answering failed: {str(e)}'})

@socketio.on('ai_analyze_page')
def handle_ai_analyze(data=None):
    """Analyze page content with caching"""
    if request.sid not in authenticated_clients:
        emit('ai_response', {'type': 'error', 'message': 'Authentication required'})
        return
    
    try:
        if not ai_service.is_configured():
            emit('ai_response', {'type': 'error', 'message': 'OpenAI API key not configured in .env file'})
            return
        
        # Check if we have cached OCR for this client
        cached_text, content_hash = ai_service.get_cached_ocr(request.sid)
        
        if cached_text:
            text = cached_text
            logger.info("Using cached OCR content for analysis")
        else:
            # Capture text from screen
            text = text_extractor.get_page_text()
            if text:
                # Cache the OCR result
                ai_service.cache_ocr_result(request.sid, text)
        
        if not text:
            emit('ai_response', {
                'type': 'error', 
                'message': 'No readable text found on screen.'
            })
            return
        
        # Analyze content
        analysis = ai_service.analyze_page_content(text, request.sid)
        
        emit('ai_response', {
            'type': 'analysis',
            'analysis': analysis,
            'text_sample': text[:500] + '...' if len(text) > 500 else text,
            'used_cache': bool(cached_text)
        })
        
    except Exception as e:
        logger.error(f"Page analysis error: {e}")
        emit('ai_response', {'type': 'error', 'message': f'Analysis failed: {str(e)}'})

@socketio.on('ai_get_stats')
def handle_ai_stats(data=None):
    """Get AI service statistics"""
    if request.sid not in authenticated_clients:
        return
    
    try:
        stats = ai_service.get_conversation_stats(request.sid)
        emit('ai_response', {
            'type': 'stats',
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Stats retrieval error: {e}")


if __name__ == '__main__':
    local_ip = get_local_ip()
    logger.info(f"🚀 Server running on http://{local_ip}:5000")
    logger.info(f"📱 Mobile interface: http://{local_ip}:5000 (auto-detected)")
    logger.info(f"🖥️  Desktop dashboard: http://{local_ip}:5000 (on computers)")
    logger.info(f"🔑 Pairing code: {config['pairing_code']}")
    logger.info(f"🔒 Password: {config['auth_password']}")
    logger.info(f"🤖 AI Assistant: {'✅ Configured' if ai_service.is_configured() else '❌ Not configured - add OPENAI_API_KEY to .env file'}")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)