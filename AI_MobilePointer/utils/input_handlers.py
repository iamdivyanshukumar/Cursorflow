import logging
from pynput.mouse import Button
from pynput.keyboard import Key

logger = logging.getLogger(__name__)

class InputHandler:
    def __init__(self, mouse, keyboard):
        self.mouse = mouse
        self.keyboard = keyboard
        
        # Key mappings
        self.key_mapping = {
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
        
        self.media_mapping = {
            'play_pause': Key.media_play_pause,
            'volume_up': Key.media_volume_up,
            'volume_down': Key.media_volume_down,
            'volume_mute': Key.media_volume_mute,
            'previous_track': Key.media_previous,
            'next_track': Key.media_next
        }
    
    def move_mouse(self, delta_x, delta_y, sensitivity=1.0):
        """Move mouse relative to current position"""
        try:
            current_x, current_y = self.mouse.position
            self.mouse.position = (
                current_x + delta_x * sensitivity,
                current_y + delta_y * sensitivity
            )
            return True
        except Exception as e:
            logger.error(f"Mouse movement error: {e}")
            return False
    
    def click(self, button='left', double_click=False):
        """Perform mouse click"""
        try:
            button_obj = Button.left if button == 'left' else Button.right
            if double_click:
                self.mouse.click(button_obj, 2)
            else:
                self.mouse.click(button_obj)
            return True
        except Exception as e:
            logger.error(f"Click error: {e}")
            return False
    
    def scroll(self, delta_y, sensitivity=1.0):
        """Perform scroll action"""
        try:
            self.mouse.scroll(0, delta_y * sensitivity / 100)
            return True
        except Exception as e:
            logger.error(f"Scroll error: {e}")
            return False
    
    def type_text(self, text):
        """Type text using keyboard"""
        try:
            self.keyboard.type(text)
            return True
        except Exception as e:
            logger.error(f"Keyboard input error: {e}")
            return False
    
    def press_key(self, key_name):
        """Press a specific key"""
        try:
            if key_name in self.key_mapping:
                self.keyboard.press(self.key_mapping[key_name])
                self.keyboard.release(self.key_mapping[key_name])
                return True
            return False
        except Exception as e:
            logger.error(f"Key press error: {e}")
            return False
    
    def press_media_key(self, media_key):
        """Press media key"""
        try:
            if media_key in self.media_mapping:
                self.keyboard.press(self.media_mapping[media_key])
                self.keyboard.release(self.media_mapping[media_key])
                return True
            return False
        except Exception as e:
            logger.error(f"Media key error: {e}")
            return False
    
    def keyboard_action(self, action):
        """Perform keyboard actions like copy, paste, etc."""
        try:
            if action == 'copy':
                self.keyboard.press(Key.ctrl)
                self.keyboard.press('c')
                self.keyboard.release('c')
                self.keyboard.release(Key.ctrl)
            elif action == 'paste':
                self.keyboard.press(Key.ctrl)
                self.keyboard.press('v')
                self.keyboard.release('v')
                self.keyboard.release(Key.ctrl)
            elif action == 'select_all':
                self.keyboard.press(Key.ctrl)
                self.keyboard.press('a')
                self.keyboard.release('a')
                self.keyboard.release(Key.ctrl)
            return True
        except Exception as e:
            logger.error(f"Keyboard action error: {e}")
            return False