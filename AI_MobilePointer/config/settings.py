import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    
    # Mouse settings
    MOUSE_SENSITIVITY = 2.2
    SCROLL_SENSITIVITY = 1.0
    DOUBLE_CLICK_TIME = 300
    
    # Screen capture settings
    VIDEO_QUALITY = 80
    MAX_FPS = 30
    TARGET_WIDTH = 1280
    TARGET_HEIGHT = 720
    
    # Authentication
    AUTH_ENABLED = True
    AUTH_PASSWORD = 'admin123'
    PAIRING_CODE_EXPIRY = 3600  # 1 hour

config = Config()