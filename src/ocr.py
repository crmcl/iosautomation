"""
OCR Module - Screen text recognition for iOS automation.

Provides multiple OCR backends (EasyOCR, Tesseract) for recognizing
text on iOS device screenshots.
"""

import os
from typing import List, Tuple, Optional, Dict, Any, Union
from dataclasses import dataclass

import numpy as np
from PIL import Image
import cv2
from loguru import logger


@dataclass
class TextMatch:
    """Represents a detected text region on screen."""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    center: Tuple[int, int]  # center point for tapping

    @property
    def x(self) -> int:
        return self.bbox[0]

    @property
    def y(self) -> int:
        return self.bbox[1]

    @property
    def width(self) -> int:
        return self.bbox[2]

    @property
    def height(self) -> int:
        return self.bbox[3]


class OCREngine:
    """Base class for OCR engines."""

    def extract_text(self, image: Union[Image.Image, np.ndarray]) -> List[TextMatch]:
        """Extract text regions from image."""
        raise NotImplementedError

    def find_text(self, image: Union[Image.Image, np.ndarray],
                  target: str, exact: bool = False) -> Optional[TextMatch]:
        """Find specific text in image."""
        raise NotImplementedError


class EasyOCREngine(OCREngine):
    """
    EasyOCR-based text recognition.

    Best for general mobile UI text, handles multiple languages well.
    """

    def __init__(self, languages: List[str] = None, gpu: bool = False):
        """
        Initialize EasyOCR engine.

        Args:
            languages: List of language codes (default: ['en'])
            gpu: Whether to use GPU acceleration
        """
        import easyocr

        self.languages = languages or ['en']
        self.reader = easyocr.Reader(self.languages, gpu=gpu)
        logger.info(f"EasyOCR initialized with languages: {self.languages}")

    def _to_numpy(self, image: Union[Image.Image, np.ndarray]) -> np.ndarray:
        """Convert image to numpy array."""
        if isinstance(image, Image.Image):
            return np.array(image)
        return image

    def extract_text(self, image: Union[Image.Image, np.ndarray],
                     min_confidence: float = 0.3) -> List[TextMatch]:
        """
        Extract all text regions from image.

        Args:
            image: PIL Image or numpy array
            min_confidence: Minimum confidence threshold (0-1)

        Returns:
            List of TextMatch objects
        """
        img_array = self._to_numpy(image)
        results = self.reader.readtext(img_array)

        matches = []
        for (bbox, text, confidence) in results:
            if confidence < min_confidence:
                continue

            # Convert bbox to x, y, width, height format
            # EasyOCR returns [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            x1, y1 = int(bbox[0][0]), int(bbox[0][1])
            x2, y2 = int(bbox[2][0]), int(bbox[2][1])
            width = x2 - x1
            height = y2 - y1
            center = (x1 + width // 2, y1 + height // 2)

            matches.append(TextMatch(
                text=text,
                confidence=confidence,
                bbox=(x1, y1, width, height),
                center=center
            ))

        logger.debug(f"Found {len(matches)} text regions")
        return matches

    def find_text(self, image: Union[Image.Image, np.ndarray],
                  target: str, exact: bool = False,
                  min_confidence: float = 0.3) -> Optional[TextMatch]:
        """
        Find specific text in image.

        Args:
            image: PIL Image or numpy array
            target: Text to find
            exact: If True, match exact text; if False, match substring
            min_confidence: Minimum confidence threshold

        Returns:
            TextMatch if found, None otherwise
        """
        matches = self.extract_text(image, min_confidence)
        target_lower = target.lower()

        for match in matches:
            text_lower = match.text.lower()
            if exact:
                if text_lower == target_lower:
                    return match
            else:
                if target_lower in text_lower:
                    return match

        return None

    def find_all_text(self, image: Union[Image.Image, np.ndarray],
                      target: str, exact: bool = False,
                      min_confidence: float = 0.3) -> List[TextMatch]:
        """
        Find all occurrences of text in image.

        Args:
            image: PIL Image or numpy array
            target: Text to find
            exact: If True, match exact text; if False, match substring
            min_confidence: Minimum confidence threshold

        Returns:
            List of matching TextMatch objects
        """
        matches = self.extract_text(image, min_confidence)
        target_lower = target.lower()

        results = []
        for match in matches:
            text_lower = match.text.lower()
            if exact:
                if text_lower == target_lower:
                    results.append(match)
            else:
                if target_lower in text_lower:
                    results.append(match)

        return results


class TesseractEngine(OCREngine):
    """
    Tesseract-based text recognition.

    Good for clean text, requires Tesseract to be installed on system.
    """

    def __init__(self, lang: str = 'eng', tesseract_path: Optional[str] = None):
        """
        Initialize Tesseract engine.

        Args:
            lang: Tesseract language code
            tesseract_path: Path to tesseract executable (auto-detected if None)
        """
        import pytesseract

        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        elif os.name == 'nt':  # Windows
            # Common Windows installation paths
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break

        self.lang = lang
        self.pytesseract = pytesseract
        logger.info(f"Tesseract initialized with language: {lang}")

    def _to_numpy(self, image: Union[Image.Image, np.ndarray]) -> np.ndarray:
        """Convert image to numpy array."""
        if isinstance(image, Image.Image):
            return np.array(image)
        return image

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        # Convert to grayscale if color
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        # Apply threshold to get black text on white background
        _, thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh

    def extract_text(self, image: Union[Image.Image, np.ndarray],
                     min_confidence: float = 30,
                     preprocess: bool = True) -> List[TextMatch]:
        """
        Extract all text regions from image.

        Args:
            image: PIL Image or numpy array
            min_confidence: Minimum confidence threshold (0-100 for Tesseract)
            preprocess: Whether to preprocess image

        Returns:
            List of TextMatch objects
        """
        img_array = self._to_numpy(image)

        if preprocess:
            img_array = self._preprocess(img_array)

        # Get detailed OCR data
        data = self.pytesseract.image_to_data(
            img_array,
            lang=self.lang,
            output_type=self.pytesseract.Output.DICT
        )

        matches = []
        n_boxes = len(data['text'])

        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])

            if not text or conf < min_confidence:
                continue

            x, y = data['left'][i], data['top'][i]
            w, h = data['width'][i], data['height'][i]
            center = (x + w // 2, y + h // 2)

            matches.append(TextMatch(
                text=text,
                confidence=conf / 100.0,  # Normalize to 0-1
                bbox=(x, y, w, h),
                center=center
            ))

        logger.debug(f"Found {len(matches)} text regions")
        return matches

    def find_text(self, image: Union[Image.Image, np.ndarray],
                  target: str, exact: bool = False,
                  min_confidence: float = 30) -> Optional[TextMatch]:
        """
        Find specific text in image.

        Args:
            image: PIL Image or numpy array
            target: Text to find
            exact: If True, match exact text; if False, match substring
            min_confidence: Minimum confidence threshold (0-100)

        Returns:
            TextMatch if found, None otherwise
        """
        matches = self.extract_text(image, min_confidence)
        target_lower = target.lower()

        for match in matches:
            text_lower = match.text.lower()
            if exact:
                if text_lower == target_lower:
                    return match
            else:
                if target_lower in text_lower:
                    return match

        return None


class ScreenOCR:
    """
    High-level OCR interface for screen automation.

    Combines OCR with device screenshots for easy text-based automation.
    """

    def __init__(self, wda_client, ocr_engine: Optional[OCREngine] = None):
        """
        Initialize ScreenOCR.

        Args:
            wda_client: WDAClient instance for screenshots
            ocr_engine: OCR engine to use (defaults to EasyOCR)
        """
        self.wda = wda_client
        self.ocr = ocr_engine or EasyOCREngine()
        self._last_screenshot: Optional[Image.Image] = None

    def refresh(self) -> Image.Image:
        """Take a fresh screenshot."""
        self._last_screenshot = self.wda.screenshot()
        return self._last_screenshot

    @property
    def screenshot(self) -> Image.Image:
        """Get current screenshot, refreshing if needed."""
        if self._last_screenshot is None:
            self.refresh()
        return self._last_screenshot

    def find_text(self, text: str, refresh: bool = True,
                  exact: bool = False) -> Optional[TextMatch]:
        """
        Find text on screen.

        Args:
            text: Text to find
            refresh: Whether to take fresh screenshot
            exact: Match exact text only

        Returns:
            TextMatch if found
        """
        if refresh:
            self.refresh()
        return self.ocr.find_text(self.screenshot, text, exact)

    def find_all_text(self, text: str, refresh: bool = True,
                      exact: bool = False) -> List[TextMatch]:
        """Find all occurrences of text on screen."""
        if refresh:
            self.refresh()
        return self.ocr.find_all_text(self.screenshot, text, exact)

    def get_all_text(self, refresh: bool = True) -> List[TextMatch]:
        """Get all text on screen."""
        if refresh:
            self.refresh()
        return self.ocr.extract_text(self.screenshot)

    def tap_text(self, text: str, refresh: bool = True,
                 exact: bool = False) -> bool:
        """
        Find and tap on text.

        Args:
            text: Text to tap
            refresh: Whether to take fresh screenshot
            exact: Match exact text only

        Returns:
            True if text found and tapped
        """
        match = self.find_text(text, refresh, exact)
        if match:
            self.wda.tap(match.center[0], match.center[1])
            logger.info(f"Tapped on text: '{text}' at {match.center}")
            return True
        logger.warning(f"Text not found: '{text}'")
        return False

    def wait_for_text(self, text: str, timeout: float = 10.0,
                      interval: float = 0.5, exact: bool = False) -> Optional[TextMatch]:
        """
        Wait for text to appear on screen.

        Args:
            text: Text to wait for
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds
            exact: Match exact text only

        Returns:
            TextMatch if found within timeout
        """
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            match = self.find_text(text, refresh=True, exact=exact)
            if match:
                logger.info(
                    f"Text appeared: '{text}' after {time.time() - start_time:.1f}s")
                return match
            time.sleep(interval)

        logger.warning(f"Timeout waiting for text: '{text}'")
        return None

    def wait_and_tap_text(self, text: str, timeout: float = 10.0,
                          exact: bool = False) -> bool:
        """
        Wait for text to appear and tap it.

        Args:
            text: Text to wait for and tap
            timeout: Maximum wait time
            exact: Match exact text only

        Returns:
            True if text found and tapped
        """
        match = self.wait_for_text(text, timeout, exact=exact)
        if match:
            self.wda.tap(match.center[0], match.center[1])
            return True
        return False

    def text_exists(self, text: str, refresh: bool = True,
                    exact: bool = False) -> bool:
        """Check if text exists on screen."""
        return self.find_text(text, refresh, exact) is not None

    def save_screenshot_with_boxes(self, filepath: str, refresh: bool = True):
        """
        Save screenshot with OCR bounding boxes drawn.

        Useful for debugging OCR results.
        """
        if refresh:
            self.refresh()

        img_array = np.array(self.screenshot)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        matches = self.ocr.extract_text(self.screenshot)

        for match in matches:
            x, y, w, h = match.bbox
            cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img_bgr, f"{match.text[:20]} ({match.confidence:.2f})",
                        (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.imwrite(filepath, img_bgr)
        logger.info(f"Saved annotated screenshot to: {filepath}")
