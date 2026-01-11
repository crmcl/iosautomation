"""
Mirror-Based iOS Automation - NO MAC REQUIRED

This module provides iOS automation by:
1. Mirroring iPhone screen to Windows
2. Using OCR on the mirrored window
3. Sending touch inputs back via the mirror tool

Supported mirroring tools:
- Scrcpy (with iOS support via USB)
- ApowerMirror
- LonelyScreen
- 5KPlayer
- Any tool that shows iPhone screen in a window

This is a workaround when you can't build WebDriverAgent.
"""

import time
from typing import Optional, Tuple, List
from dataclasses import dataclass

import pyautogui
import pygetwindow as gw
from PIL import Image
import numpy as np
from loguru import logger

from .ocr import EasyOCREngine, TextMatch


@dataclass
class MirrorWindow:
    """Represents the iOS mirror window on desktop."""
    title: str
    x: int
    y: int
    width: int
    height: int
    handle: any


class MirrorAutomator:
    """
    Automate iOS via screen mirroring.

    This works by:
    1. Finding the mirror window on your desktop
    2. Taking screenshots of that window
    3. Running OCR to find UI elements
    4. Using pyautogui to click on the window

    Requirements:
    - A screen mirroring app showing your iPhone
    - pip install pyautogui pygetwindow
    """

    # Common mirror app window titles
    KNOWN_MIRROR_APPS = [
        "ApowerMirror",
        "LonelyScreen",
        "5KPlayer",
        "AirServer",
        "Reflector",
        "X-Mirage",
        "iPhone",  # Generic
        "iPad",    # Generic
        "iOS",     # Generic
    ]

    def __init__(self, window_title: Optional[str] = None):
        """
        Initialize mirror automator.

        Args:
            window_title: Exact window title, or None to auto-detect
        """
        self.window_title = window_title
        self.window: Optional[MirrorWindow] = None
        self.ocr = EasyOCREngine(languages=['en'], gpu=False)

        # Safety settings
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1

    def find_mirror_window(self) -> Optional[MirrorWindow]:
        """
        Find the iOS mirror window on desktop.

        Returns:
            MirrorWindow if found, None otherwise
        """
        all_windows = gw.getAllTitles()

        # Try exact match first
        if self.window_title:
            matches = gw.getWindowsWithTitle(self.window_title)
            if matches:
                win = matches[0]
                self.window = MirrorWindow(
                    title=win.title,
                    x=win.left,
                    y=win.top,
                    width=win.width,
                    height=win.height,
                    handle=win
                )
                logger.info(f"Found mirror window: {self.window.title}")
                return self.window

        # Try known mirror apps
        for app_name in self.KNOWN_MIRROR_APPS:
            for title in all_windows:
                if app_name.lower() in title.lower():
                    matches = gw.getWindowsWithTitle(title)
                    if matches:
                        win = matches[0]
                        self.window = MirrorWindow(
                            title=win.title,
                            x=win.left,
                            y=win.top,
                            width=win.width,
                            height=win.height,
                            handle=win
                        )
                        logger.info(
                            f"Found mirror window: {self.window.title}")
                        return self.window

        logger.warning("No mirror window found. Available windows:")
        for title in all_windows[:10]:
            logger.warning(f"  - {title}")

        return None

    def refresh_window_position(self):
        """Update window position (in case it moved)."""
        if self.window:
            matches = gw.getWindowsWithTitle(self.window.title)
            if matches:
                win = matches[0]
                self.window.x = win.left
                self.window.y = win.top
                self.window.width = win.width
                self.window.height = win.height

    def focus_window(self):
        """Bring mirror window to front."""
        if self.window and self.window.handle:
            try:
                self.window.handle.activate()
                time.sleep(0.2)
            except Exception as e:
                logger.warning(f"Could not focus window: {e}")

    def screenshot(self) -> Optional[Image.Image]:
        """
        Take screenshot of the mirror window.

        Returns:
            PIL Image of the mirrored iOS screen
        """
        if not self.window:
            if not self.find_mirror_window():
                logger.error("No mirror window found")
                return None

        self.refresh_window_position()

        # Capture the window region
        # Add small offset to avoid window borders
        border_offset = 8
        title_bar_height = 32

        region = (
            self.window.x + border_offset,
            self.window.y + title_bar_height,
            self.window.width - (border_offset * 2),
            self.window.height - title_bar_height - border_offset
        )

        screenshot = pyautogui.screenshot(region=region)
        return screenshot

    def _window_to_screen_coords(self, x: int, y: int) -> Tuple[int, int]:
        """Convert window-relative coords to screen coords."""
        if not self.window:
            raise RuntimeError("No window connected")

        self.refresh_window_position()

        # Account for window borders
        border_offset = 8
        title_bar_height = 32

        screen_x = self.window.x + border_offset + x
        screen_y = self.window.y + title_bar_height + y

        return (screen_x, screen_y)

    def tap(self, x: int, y: int):
        """
        Tap at coordinates within the mirror window.

        Args:
            x: X coordinate relative to mirror content
            y: Y coordinate relative to mirror content
        """
        screen_x, screen_y = self._window_to_screen_coords(x, y)

        self.focus_window()
        pyautogui.click(screen_x, screen_y)
        logger.debug(
            f"Tapped at ({x}, {y}) -> screen ({screen_x}, {screen_y})")

    def double_tap(self, x: int, y: int):
        """Double tap at coordinates."""
        screen_x, screen_y = self._window_to_screen_coords(x, y)

        self.focus_window()
        pyautogui.doubleClick(screen_x, screen_y)

    def long_press(self, x: int, y: int, duration: float = 1.0):
        """Long press at coordinates."""
        screen_x, screen_y = self._window_to_screen_coords(x, y)

        self.focus_window()
        pyautogui.mouseDown(screen_x, screen_y)
        time.sleep(duration)
        pyautogui.mouseUp()

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int,
              duration: float = 0.5):
        """Swipe gesture."""
        start_screen = self._window_to_screen_coords(start_x, start_y)
        end_screen = self._window_to_screen_coords(end_x, end_y)

        self.focus_window()
        pyautogui.moveTo(start_screen[0], start_screen[1])
        pyautogui.drag(
            end_screen[0] - start_screen[0],
            end_screen[1] - start_screen[1],
            duration=duration
        )

    def swipe_up(self, distance: int = 300):
        """Swipe up from center."""
        if not self.window:
            return
        center_x = (self.window.width - 16) // 2
        center_y = (self.window.height - 40) // 2
        self.swipe(center_x, center_y + distance//2,
                   center_x, center_y - distance//2)

    def swipe_down(self, distance: int = 300):
        """Swipe down from center."""
        if not self.window:
            return
        center_x = (self.window.width - 16) // 2
        center_y = (self.window.height - 40) // 2
        self.swipe(center_x, center_y - distance//2,
                   center_x, center_y + distance//2)

    def type_text(self, text: str):
        """
        Type text (requires text field to be focused).

        Note: This types on the desktop. The mirror app must support
        keyboard passthrough to the iOS device.
        """
        self.focus_window()
        pyautogui.typewrite(text, interval=0.05)

    def find_text(self, text: str, refresh: bool = True) -> Optional[TextMatch]:
        """
        Find text on screen using OCR.

        Args:
            text: Text to find
            refresh: Take new screenshot

        Returns:
            TextMatch if found
        """
        screenshot = self.screenshot()
        if not screenshot:
            return None

        return self.ocr.find_text(screenshot, text)

    def find_all_text(self, text: str) -> List[TextMatch]:
        """Find all occurrences of text."""
        screenshot = self.screenshot()
        if not screenshot:
            return []

        return self.ocr.find_all_text(screenshot, text)

    def get_all_text(self) -> List[TextMatch]:
        """Get all visible text."""
        screenshot = self.screenshot()
        if not screenshot:
            return []

        return self.ocr.extract_text(screenshot)

    def tap_text(self, text: str, timeout: float = 10.0) -> bool:
        """
        Find and tap on text.

        Args:
            text: Text to find and tap
            timeout: How long to wait for text

        Returns:
            True if successful
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            match = self.find_text(text)
            if match:
                self.tap(match.center[0], match.center[1])
                logger.info(f"Tapped on '{text}' at {match.center}")
                return True
            time.sleep(0.5)

        logger.warning(f"Text not found: '{text}'")
        return False

    def wait_for_text(self, text: str, timeout: float = 10.0) -> bool:
        """Wait for text to appear."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.find_text(text):
                return True
            time.sleep(0.5)

        return False

    def text_exists(self, text: str) -> bool:
        """Check if text is visible."""
        return self.find_text(text) is not None

    def save_debug_screenshot(self, filepath: str):
        """Save screenshot with OCR boxes for debugging."""
        import cv2

        screenshot = self.screenshot()
        if not screenshot:
            return

        img_array = np.array(screenshot)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        matches = self.ocr.extract_text(screenshot)

        for match in matches:
            x, y, w, h = match.bbox
            cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img_bgr, match.text[:15], (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        cv2.imwrite(filepath, img_bgr)
        logger.info(f"Debug screenshot saved: {filepath}")


def list_windows():
    """List all visible windows (helper for finding mirror app)."""
    print("\nVisible Windows:")
    print("-" * 50)
    for title in gw.getAllTitles():
        if title.strip():
            print(f"  • {title}")


# Example usage
if __name__ == "__main__":
    print("Mirror-Based iOS Automation")
    print("=" * 50)
    print("\nStep 1: Make sure your iOS mirror app is running")
    print("Step 2: This script will find the window and automate it\n")

    list_windows()

    print("\nTo use:")
    print("  auto = MirrorAutomator()")
    print("  auto.find_mirror_window()")
    print("  auto.tap_text('Settings')")
