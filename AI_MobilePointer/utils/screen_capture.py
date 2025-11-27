import cv2
import numpy as np
from mss import mss
import time
import base64
import logging
from pynput.mouse import Controller

logger = logging.getLogger(__name__)

class ScreenCapture:
    def __init__(self, config):
        self.config = config
        self.mouse = Controller()
        self.sct = mss()
        self.monitor = self.sct.monitors[1]
        self.target_width = config.SCREEN_CAPTURE['target_width']
        self.target_height = config.SCREEN_CAPTURE['target_height']
        self.quality = config.SCREEN_CAPTURE['default_quality']
        self.max_fps = config.SCREEN_CAPTURE['max_fps']
        
    def capture_frame(self):
        """Capture a single frame with mouse cursor"""
        try:
            # Capture screen
            screenshot = self.sct.grab({
                'left': self.monitor['left'],
                'top': self.monitor['top'],
                'width': self.monitor['width'],
                'height': self.monitor['height']
            })
            
            # Convert to numpy array and resize
            frame = cv2.resize(np.array(screenshot), (self.target_width, self.target_height))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            # Get mouse position and draw cursor
            mouse_x, mouse_y = self.mouse.position
            mouse_x -= self.monitor['left']
            mouse_y -= self.monitor['top']
            
            cursor_pos = None
            if 0 <= mouse_x < self.monitor['width'] and 0 <= mouse_y < self.monitor['height']:
                scaled_x = int(mouse_x * (self.target_width / self.monitor['width']))
                scaled_y = int(mouse_y * (self.target_height / self.monitor['height']))
                
                # Draw mouse cursor
                cv2.circle(frame, (scaled_x, scaled_y), 8, (0, 0, 255), 2)
                cv2.line(frame, (scaled_x-10, scaled_y), (scaled_x+10, scaled_y), (0, 0, 255), 2)
                cv2.line(frame, (scaled_x, scaled_y-10), (scaled_x, scaled_y+10), (0, 0, 255), 2)
                
                cursor_pos = {'x': scaled_x, 'y': scaled_y}
            
            # Encode frame
            encode_params = [
                cv2.IMWRITE_JPEG_QUALITY, self.quality,
                cv2.IMWRITE_JPEG_OPTIMIZE, 1
            ]
            _, buffer = cv2.imencode('.jpg', frame, encode_params)
            
            return {
                'image': base64.b64encode(buffer).decode('utf-8'),
                'quality': self.quality,
                'timestamp': time.time(),
                'cursor': cursor_pos
            }
            
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
            return None
    
    def update_config(self, new_config):
        """Update capture configuration"""
        self.quality = new_config.get('video_quality', self.quality)
        self.max_fps = new_config.get('max_fps', self.max_fps)
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'sct'):
            self.sct.close()