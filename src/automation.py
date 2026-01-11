"""
Automation Helpers - High-level automation workflows.

Provides convenient functions for common automation tasks.
"""

import time
from typing import Optional, Callable, Any, List, Tuple, Union
from pathlib import Path

from PIL import Image
from loguru import logger

from .wda_client import WDAClient
from .ocr import ScreenOCR, EasyOCREngine, TextMatch


class Automator:
    """
    High-level automation interface combining WDA and OCR.

    Provides easy-to-use methods for common automation tasks.
    """

    def __init__(self, wda_url: str = "http://localhost:8100",
                 ocr_languages: List[str] = None):
        """
        Initialize Automator.

        Args:
            wda_url: WebDriverAgent URL
            ocr_languages: Languages for OCR (default: ['en'])
        """
        self.wda = WDAClient(wda_url)
        self.ocr_engine = EasyOCREngine(languages=ocr_languages or ['en'])
        self.screen = ScreenOCR(self.wda, self.ocr_engine)

        self._action_delay = 0.3  # Default delay between actions
        self._screenshot_dir = Path("screenshots")

    def connect(self) -> bool:
        """
        Connect to WDA and create session.

        Returns:
            True if connected successfully
        """
        if not self.wda.health_check():
            logger.error("Cannot connect to WDA")
            return False

        self.wda.create_session()
        logger.info("Connected to device")
        return True

    def disconnect(self):
        """Disconnect from WDA."""
        self.wda.delete_session()
        logger.info("Disconnected from device")

    # ==================== Basic Actions ====================

    def tap(self, x: int, y: int):
        """Tap at coordinates."""
        self.wda.tap(x, y)
        time.sleep(self._action_delay)

    def tap_text(self, text: str, timeout: float = 10.0) -> bool:
        """
        Find and tap on text.

        Args:
            text: Text to find and tap
            timeout: How long to wait for text to appear

        Returns:
            True if successful
        """
        match = self.screen.wait_for_text(text, timeout=timeout)
        if match:
            self.tap(match.center[0], match.center[1])
            return True
        return False

    def tap_if_exists(self, text: str) -> bool:
        """Tap on text if it exists (no waiting)."""
        return self.screen.tap_text(text, refresh=True)

    def double_tap(self, x: int, y: int):
        """Double tap at coordinates."""
        self.wda.double_tap(x, y)
        time.sleep(self._action_delay)

    def long_press(self, x: int, y: int, duration: float = 1.0):
        """Long press at coordinates."""
        self.wda.long_press(x, y, duration)
        time.sleep(self._action_delay)

    def swipe(self, direction: str, distance: int = 300):
        """
        Swipe in a direction.

        Args:
            direction: "up", "down", "left", or "right"
            distance: Swipe distance in points
        """
        direction = direction.lower()
        if direction == "up":
            self.wda.swipe_up(distance)
        elif direction == "down":
            self.wda.swipe_down(distance)
        elif direction == "left":
            self.wda.swipe_left(distance)
        elif direction == "right":
            self.wda.swipe_right(distance)
        else:
            raise ValueError(f"Invalid direction: {direction}")
        time.sleep(self._action_delay)

    def type_text(self, text: str, clear_first: bool = False):
        """
        Type text.

        Args:
            text: Text to type
            clear_first: Clear existing text first
        """
        if clear_first:
            # Select all and delete
            self.wda.type_text('\ue009a')  # Ctrl+A
            time.sleep(0.1)
            self.wda.type_text('\ue003')   # Backspace
            time.sleep(0.1)

        self.wda.type_text(text)
        time.sleep(self._action_delay)

    def press_home(self):
        """Press home button."""
        self.wda.home_screen()
        time.sleep(self._action_delay)

    # ==================== App Management ====================

    def launch_app(self, bundle_id: str):
        """
        Launch an app.

        Args:
            bundle_id: App bundle identifier
        """
        self.wda.launch_app(bundle_id)
        time.sleep(1)  # Give app time to launch
        logger.info(f"Launched: {bundle_id}")

    def close_app(self, bundle_id: str):
        """Close an app."""
        self.wda.terminate_app(bundle_id)
        time.sleep(self._action_delay)
        logger.info(f"Closed: {bundle_id}")

    def get_current_app(self) -> str:
        """Get bundle ID of current foreground app."""
        info = self.wda.get_active_app_info()
        return info.get("bundleId", "")

    # ==================== Screen State ====================

    def wait_for_text(self, text: str, timeout: float = 10.0) -> bool:
        """
        Wait for text to appear on screen.

        Args:
            text: Text to wait for
            timeout: Maximum wait time

        Returns:
            True if text appeared
        """
        return self.screen.wait_for_text(text, timeout) is not None

    def text_exists(self, text: str) -> bool:
        """Check if text exists on screen."""
        return self.screen.text_exists(text)

    def get_all_text(self) -> List[str]:
        """Get all visible text on screen."""
        matches = self.screen.get_all_text()
        return [m.text for m in matches]

    def find_text_location(self, text: str) -> Optional[Tuple[int, int]]:
        """
        Find location of text on screen.

        Returns:
            (x, y) center coordinates or None if not found
        """
        match = self.screen.find_text(text)
        return match.center if match else None

    # ==================== Screenshots ====================

    def screenshot(self, save_path: Optional[str] = None) -> Image.Image:
        """
        Take a screenshot.

        Args:
            save_path: Optional path to save screenshot

        Returns:
            PIL Image
        """
        img = self.wda.screenshot()
        if save_path:
            img.save(save_path)
            logger.debug(f"Screenshot saved: {save_path}")
        return img

    def screenshot_with_ocr_boxes(self, save_path: str):
        """Save screenshot with OCR bounding boxes drawn."""
        self.screen.save_screenshot_with_boxes(save_path)

    # ==================== Utility Methods ====================

    def wait(self, seconds: float):
        """Wait for specified time."""
        time.sleep(seconds)

    def retry(self, action: Callable, max_attempts: int = 3,
              delay: float = 1.0) -> Any:
        """
        Retry an action multiple times.

        Args:
            action: Function to call
            max_attempts: Maximum retry attempts
            delay: Delay between attempts

        Returns:
            Result of action if successful

        Raises:
            Exception from last attempt if all fail
        """
        last_error = None
        for attempt in range(max_attempts):
            try:
                return action()
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(delay)

        raise last_error

    def scroll_to_text(self, text: str, direction: str = "up",
                       max_scrolls: int = 5) -> bool:
        """
        Scroll until text is found.

        Args:
            text: Text to find
            direction: Scroll direction ("up" or "down")
            max_scrolls: Maximum scroll attempts

        Returns:
            True if text found
        """
        for _ in range(max_scrolls):
            if self.text_exists(text):
                return True
            self.swipe(direction)
            time.sleep(0.5)

        return self.text_exists(text)

    def tap_element_by_label(self, label: str) -> bool:
        """
        Tap element using accessibility label (native WDA).

        Faster than OCR for elements with accessibility labels.
        """
        element = self.wda.find_element("accessibility id", label)
        if element:
            elem_id = element.get("ELEMENT") or element.get(
                "element-6066-11e4-a52e-4f735466cecf")
            if elem_id:
                self.wda.element_click(elem_id)
                time.sleep(self._action_delay)
                return True
        return False

    # ==================== Context Manager ====================

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False


# ==================== Convenience Functions ====================

def quick_connect(wda_url: str = "http://localhost:8100") -> Automator:
    """
    Quickly connect to a device.

    Args:
        wda_url: WDA URL

    Returns:
        Connected Automator instance
    """
    auto = Automator(wda_url)
    if auto.connect():
        return auto
    raise ConnectionError("Failed to connect to WDA")


def run_automation(func: Callable[[Automator], Any],
                   wda_url: str = "http://localhost:8100") -> Any:
    """
    Run an automation function with automatic connect/disconnect.

    Args:
        func: Function that takes an Automator and performs actions
        wda_url: WDA URL

    Returns:
        Result of func

    Example:
        def my_automation(auto):
            auto.launch_app("com.apple.Preferences")
            auto.tap_text("General")

        run_automation(my_automation)
    """
    with Automator(wda_url) as auto:
        return func(auto)
