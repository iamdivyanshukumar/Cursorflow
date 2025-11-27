import cv2
import numpy as np
import pytesseract
import logging
import threading
from PIL import Image
import os

logger = logging.getLogger(__name__)

class TextExtractor:
    def __init__(self):
        # Configure Tesseract path for Windows (adjust if needed)
        self._configure_tesseract()
        
        # Thread-local storage for MSS instances
        self._local = threading.local()
        
    def _configure_tesseract(self):
        """Configure Tesseract path for different operating systems"""
        try:
            # Windows common paths
            if os.name == 'nt':
                tesseract_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME')),
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
                ]
                
                for path in tesseract_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        logger.info(f"Tesseract configured: {path}")
                        break
                else:
                    logger.warning("Tesseract not found in common paths. Please install Tesseract-OCR")
            
            # For Linux/Mac, it should be in PATH
            else:
                # Try to find tesseract in PATH
                import shutil
                if shutil.which('tesseract'):
                    logger.info("Tesseract found in PATH")
                else:
                    logger.warning("Tesseract not found in PATH. Please install tesseract-ocr")
                    
        except Exception as e:
            logger.error(f"Tesseract configuration error: {e}")
    
    def _get_sct(self):
        """Get thread-local MSS instance"""
        if not hasattr(self._local, 'sct'):
            try:
                from mss import mss
                self._local.sct = mss()
                self._local.monitor = self._local.sct.monitors[1]
                logger.info("MSS instance created for thread")
            except Exception as e:
                logger.error(f"Failed to create MSS instance: {e}")
                return None, None
        return self._local.sct, self._local.monitor
    
    def capture_screen_area(self, x1=None, y1=None, x2=None, y2=None):
        """Capture specific screen area or full screen with error handling"""
        try:
            sct, monitor = self._get_sct()
            if sct is None or monitor is None:
                logger.error("MSS not initialized")
                return None
            
            if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
                # Capture specific region
                capture_area = {
                    'left': max(0, int(x1)),
                    'top': max(0, int(y1)),
                    'width': max(1, int(x2 - x1)),
                    'height': max(1, int(y2 - y1))
                }
            else:
                # Capture full screen
                capture_area = monitor
            
            logger.debug(f"Capturing screen area: {capture_area}")
            screenshot = sct.grab(capture_area)
            
            # Convert to numpy array
            frame = np.array(screenshot)
            
            # Convert BGRA to BGR (remove alpha channel)
            if frame.shape[2] == 4:  # BGRA
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            elif frame.shape[2] == 3:  # BGR
                pass  # Already in correct format
            
            logger.debug(f"Captured frame shape: {frame.shape}")
            return frame
            
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
            return None
    
    def preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        try:
            if image is None:
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Multiple preprocessing techniques
            processed_images = []
            
            # Method 1: Simple threshold
            _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(('threshold', thresh1))
            
            # Method 2: Adaptive threshold
            thresh2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 11, 2)
            processed_images.append(('adaptive', thresh2))
            
            # Method 3: Noise removal + threshold
            denoised = cv2.medianBlur(gray, 3)
            _, thresh3 = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(('denoised', thresh3))
            
            # Method 4: Morphological operations
            kernel = np.ones((2,2), np.uint8)
            morphed = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, kernel)
            processed_images.append(('morphed', morphed))
            
            return processed_images
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            return None
    
    def extract_text_from_image(self, image):
        """Extract text from image using multiple OCR methods"""
        try:
            if image is None:
                return None
            
            # Preprocess image with multiple methods
            processed_images = self.preprocess_image(image)
            if not processed_images:
                return None
            
            best_text = ""
            best_confidence = 0
            
            for method_name, processed_img in processed_images:
                try:
                    # Get OCR data with confidence
                    ocr_data = pytesseract.image_to_data(
                        processed_img, 
                        output_type=pytesseract.Output.DICT,
                        lang='eng'
                    )
                    
                    # Calculate average confidence for this method
                    confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    # Extract text
                    text = ' '.join([
                        ocr_data['text'][i] 
                        for i in range(len(ocr_data['text'])) 
                        if int(ocr_data['conf'][i]) > 30  # Only high confidence text
                    ]).strip()
                    
                    logger.debug(f"OCR Method: {method_name}, Confidence: {avg_confidence:.1f}, Text length: {len(text)}")
                    
                    # Keep the best result
                    if avg_confidence > best_confidence and len(text) > len(best_text):
                        best_text = text
                        best_confidence = avg_confidence
                        
                except Exception as e:
                    logger.warning(f"OCR method {method_name} failed: {e}")
                    continue
            
            # Clean up the best text
            cleaned_text = self.clean_text(best_text)
            
            if cleaned_text:
                logger.info(f"OCR successful: {len(cleaned_text)} characters, confidence: {best_confidence:.1f}")
            else:
                logger.warning("No text extracted from image")
                
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return None
    
    def clean_text(self, text):
        """Clean and format extracted text"""
        if not text:
            return ""
        
        try:
            # Remove extra whitespace and clean up
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                # Filter out very short lines, single characters, or lines with only symbols
                if (len(line) > 2 and 
                    any(c.isalnum() for c in line) and  # Must contain at least one alphanumeric character
                    not line.replace(' ', '').isnumeric()):  # Not just numbers
                    cleaned_lines.append(line)
            
            # Join with proper spacing
            cleaned_text = '\n'.join(cleaned_lines)
            
            # Remove common OCR artifacts
            artifacts = [
                '|', '[]', '{}', '()', '@@', '##', '$$', '%%', '^^', '&&', '**',
                '--==', '==--', '___', '~~~', '```'
            ]
            
            for artifact in artifacts:
                cleaned_text = cleaned_text.replace(artifact, '')
            
            # Remove multiple spaces
            cleaned_text = ' '.join(cleaned_text.split())
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Text cleaning error: {e}")
            return text
    
    def get_page_text(self, region=None, use_active_window=False):
        """Get text from current screen or specific region"""
        try:
            logger.info("Starting text extraction from screen...")
            
            # Capture screen
            if region:
                image = self.capture_screen_area(**region)
            else:
                image = self.capture_screen_area()
            
            if image is None:
                logger.error("Failed to capture screen")
                return None
            
            logger.info(f"Screen captured successfully: {image.shape}")
            
            # Extract text
            text = self.extract_text_from_image(image)
            
            if text:
                logger.info(f"Text extraction successful: {len(text)} characters")
                # Log first 100 characters for debugging
                preview = text[:100] + "..." if len(text) > 100 else text
                logger.debug(f"Text preview: {preview}")
            else:
                logger.warning("No text could be extracted from the screen")
            
            return text
            
        except Exception as e:
            logger.error(f"Page text extraction error: {e}")
            return None
    
    def get_screen_summary(self):
        """Get quick summary of visible screen content"""
        text = self.get_page_text()
        if not text:
            return "No readable text found on screen."
        
        # Return first few lines as preview
        lines = text.split('\n')[:5]
        return '\n'.join(lines)
    
    def test_ocr(self):
        """Test OCR functionality"""
        try:
            logger.info("Testing OCR functionality...")
            
            # Capture a small test area
            test_region = {
                'x1': 100, 'y1': 100, 
                'x2': 500, 'y2': 300
            }
            
            image = self.capture_screen_area(**test_region)
            if image is None:
                logger.error("Test failed: Could not capture screen")
                return False
            
            text = self.extract_text_from_image(image)
            
            if text:
                logger.info(f"OCR test successful: Extracted {len(text)} characters")
                return True
            else:
                logger.warning("OCR test: No text extracted")
                return False
                
        except Exception as e:
            logger.error(f"OCR test failed: {e}")
            return False
    
    def __del__(self):
        """Cleanup thread-local MSS instances"""
        if hasattr(self._local, 'sct'):
            try:
                self._local.sct.close()
                logger.info("MSS instance closed")
            except Exception as e:
                logger.error(f"Error closing MSS instance: {e}")