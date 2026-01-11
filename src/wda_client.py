"""
WebDriverAgent Client - Communicate with WDA running on iOS device.

This module provides a high-level interface to WebDriverAgent for
controlling iOS devices without jailbreak.
"""

import time
from typing import Optional, Tuple, Dict, Any, List
from io import BytesIO

import requests
from PIL import Image
from loguru import logger


class WDAClient:
    """
    WebDriverAgent client for iOS device automation.

    Connects to WDA running on the iOS device and provides methods
    for screenshots, tapping, swiping, and element interaction.
    """

    def __init__(self, wda_url: str = "http://localhost:8100"):
        """
        Initialize WDA client.

        Args:
            wda_url: URL where WDA is accessible. Default is localhost:8100
                     which works when USB tunneling is set up.
        """
        self.wda_url = wda_url.rstrip('/')
        self.session_id: Optional[str] = None
        self._timeout = 30

    def health_check(self) -> bool:
        """Check if WDA is responding."""
        try:
            resp = requests.get(f"{self.wda_url}/status", timeout=5)
            return resp.status_code == 200
        except requests.RequestException as e:
            logger.error(f"WDA health check failed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get WDA status information."""
        resp = requests.get(f"{self.wda_url}/status", timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()

    def create_session(self, bundle_id: Optional[str] = None) -> str:
        """
        Create a new WDA session.

        Args:
            bundle_id: Optional app bundle ID to launch. If None, creates
                      session with current foreground app.

        Returns:
            Session ID string.
        """
        capabilities = {}
        if bundle_id:
            capabilities["bundleId"] = bundle_id

        payload = {
            "capabilities": {
                "alwaysMatch": capabilities,
                "firstMatch": [{}]
            }
        }

        resp = requests.post(
            f"{self.wda_url}/session",
            json=payload,
            timeout=self._timeout
        )
        resp.raise_for_status()
        data = resp.json()

        self.session_id = data.get("sessionId") or data.get(
            "value", {}).get("sessionId")
        logger.info(f"Created WDA session: {self.session_id}")
        return self.session_id

    def delete_session(self):
        """Delete current WDA session."""
        if self.session_id:
            try:
                requests.delete(
                    f"{self.wda_url}/session/{self.session_id}",
                    timeout=self._timeout
                )
                logger.info(f"Deleted session: {self.session_id}")
            except requests.RequestException as e:
                logger.warning(f"Failed to delete session: {e}")
            finally:
                self.session_id = None

    def screenshot(self) -> Image.Image:
        """
        Take a screenshot of the device screen.

        Returns:
            PIL Image object of the screenshot.
        """
        resp = requests.get(
            f"{self.wda_url}/screenshot",
            timeout=self._timeout
        )
        resp.raise_for_status()
        data = resp.json()

        import base64
        img_data = base64.b64decode(data["value"])
        return Image.open(BytesIO(img_data))

    def screenshot_as_bytes(self) -> bytes:
        """Take screenshot and return as PNG bytes."""
        img = self.screenshot()
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def get_window_size(self) -> Tuple[int, int]:
        """
        Get device screen size.

        Returns:
            Tuple of (width, height) in points.
        """
        if not self.session_id:
            self.create_session()

        resp = requests.get(
            f"{self.wda_url}/session/{self.session_id}/window/size",
            timeout=self._timeout
        )
        resp.raise_for_status()
        data = resp.json()["value"]
        return (data["width"], data["height"])

    def tap(self, x: int, y: int):
        """
        Tap at coordinates.

        Args:
            x: X coordinate in points
            y: Y coordinate in points
        """
        if not self.session_id:
            self.create_session()

        payload = {"x": x, "y": y}
        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/tap/0",
            json=payload,
            timeout=self._timeout
        )
        resp.raise_for_status()
        logger.debug(f"Tapped at ({x}, {y})")

    def double_tap(self, x: int, y: int):
        """Double tap at coordinates."""
        if not self.session_id:
            self.create_session()

        payload = {"x": x, "y": y}
        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/doubleTap",
            json=payload,
            timeout=self._timeout
        )
        resp.raise_for_status()
        logger.debug(f"Double tapped at ({x}, {y})")

    def long_press(self, x: int, y: int, duration: float = 1.0):
        """
        Long press at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate  
            duration: Press duration in seconds
        """
        if not self.session_id:
            self.create_session()

        payload = {"x": x, "y": y, "duration": duration}
        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/touchAndHold",
            json=payload,
            timeout=self._timeout
        )
        resp.raise_for_status()
        logger.debug(f"Long pressed at ({x}, {y}) for {duration}s")

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int,
              duration: float = 0.5):
        """
        Swipe from start to end coordinates.

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration: Swipe duration in seconds
        """
        if not self.session_id:
            self.create_session()

        payload = {
            "fromX": start_x,
            "fromY": start_y,
            "toX": end_x,
            "toY": end_y,
            "duration": duration
        }
        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/dragfromtoforduration",
            json=payload,
            timeout=self._timeout
        )
        resp.raise_for_status()
        logger.debug(
            f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})")

    def swipe_up(self, distance: int = 300, duration: float = 0.5):
        """Swipe up from center of screen."""
        width, height = self.get_window_size()
        center_x = width // 2
        center_y = height // 2
        self.swipe(center_x, center_y + distance // 2,
                   center_x, center_y - distance // 2, duration)

    def swipe_down(self, distance: int = 300, duration: float = 0.5):
        """Swipe down from center of screen."""
        width, height = self.get_window_size()
        center_x = width // 2
        center_y = height // 2
        self.swipe(center_x, center_y - distance // 2,
                   center_x, center_y + distance // 2, duration)

    def swipe_left(self, distance: int = 200, duration: float = 0.5):
        """Swipe left from center of screen."""
        width, height = self.get_window_size()
        center_x = width // 2
        center_y = height // 2
        self.swipe(center_x + distance // 2, center_y,
                   center_x - distance // 2, center_y, duration)

    def swipe_right(self, distance: int = 200, duration: float = 0.5):
        """Swipe right from center of screen."""
        width, height = self.get_window_size()
        center_x = width // 2
        center_y = height // 2
        self.swipe(center_x - distance // 2, center_y,
                   center_x + distance // 2, center_y, duration)

    def type_text(self, text: str):
        """
        Type text using the keyboard.

        Args:
            text: Text to type
        """
        if not self.session_id:
            self.create_session()

        payload = {"value": list(text)}
        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/keys",
            json=payload,
            timeout=self._timeout
        )
        resp.raise_for_status()
        logger.debug(f"Typed text: {text[:20]}...")

    def press_button(self, button: str):
        """
        Press a physical button.

        Args:
            button: Button name - "home", "volumeUp", "volumeDown"
        """
        if not self.session_id:
            self.create_session()

        payload = {"name": button}
        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/pressButton",
            json=payload,
            timeout=self._timeout
        )
        resp.raise_for_status()
        logger.debug(f"Pressed button: {button}")

    def home_screen(self):
        """Go to home screen."""
        self.press_button("home")

    def launch_app(self, bundle_id: str):
        """
        Launch an app by bundle ID.

        Args:
            bundle_id: App bundle identifier (e.g., "com.apple.mobilesafari")
        """
        if not self.session_id:
            self.create_session()

        payload = {"bundleId": bundle_id}
        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/apps/launch",
            json=payload,
            timeout=self._timeout
        )
        resp.raise_for_status()
        logger.info(f"Launched app: {bundle_id}")

    def terminate_app(self, bundle_id: str):
        """
        Terminate an app by bundle ID.

        Args:
            bundle_id: App bundle identifier
        """
        if not self.session_id:
            self.create_session()

        payload = {"bundleId": bundle_id}
        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/apps/terminate",
            json=payload,
            timeout=self._timeout
        )
        resp.raise_for_status()
        logger.info(f"Terminated app: {bundle_id}")

    def get_active_app_info(self) -> Dict[str, Any]:
        """Get info about currently active app."""
        if not self.session_id:
            self.create_session()

        resp = requests.get(
            f"{self.wda_url}/session/{self.session_id}/wda/activeAppInfo",
            timeout=self._timeout
        )
        resp.raise_for_status()
        return resp.json()["value"]

    def find_element(self, using: str, value: str) -> Optional[Dict[str, Any]]:
        """
        Find a UI element.

        Args:
            using: Strategy - "xpath", "class name", "name", "predicate string",
                   "class chain", "accessibility id"
            value: Value to search for

        Returns:
            Element dict with ELEMENT key, or None if not found
        """
        if not self.session_id:
            self.create_session()

        payload = {"using": using, "value": value}
        try:
            resp = requests.post(
                f"{self.wda_url}/session/{self.session_id}/element",
                json=payload,
                timeout=self._timeout
            )
            resp.raise_for_status()
            return resp.json()["value"]
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def find_elements(self, using: str, value: str) -> List[Dict[str, Any]]:
        """
        Find multiple UI elements.

        Args:
            using: Strategy - "xpath", "class name", "name", "predicate string"
            value: Value to search for

        Returns:
            List of element dicts
        """
        if not self.session_id:
            self.create_session()

        payload = {"using": using, "value": value}
        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/elements",
            json=payload,
            timeout=self._timeout
        )
        resp.raise_for_status()
        return resp.json()["value"]

    def element_click(self, element_id: str):
        """Click on an element."""
        if not self.session_id:
            self.create_session()

        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/element/{element_id}/click",
            timeout=self._timeout
        )
        resp.raise_for_status()

    def element_get_text(self, element_id: str) -> str:
        """Get text content of an element."""
        if not self.session_id:
            self.create_session()

        resp = requests.get(
            f"{self.wda_url}/session/{self.session_id}/element/{element_id}/text",
            timeout=self._timeout
        )
        resp.raise_for_status()
        return resp.json()["value"]

    def element_get_rect(self, element_id: str) -> Dict[str, int]:
        """
        Get element bounding rectangle.

        Returns:
            Dict with x, y, width, height
        """
        if not self.session_id:
            self.create_session()

        resp = requests.get(
            f"{self.wda_url}/session/{self.session_id}/element/{element_id}/rect",
            timeout=self._timeout
        )
        resp.raise_for_status()
        return resp.json()["value"]

    def get_page_source(self) -> str:
        """
        Get the current UI hierarchy as XML.

        Useful for debugging element locations.
        """
        if not self.session_id:
            self.create_session()

        resp = requests.get(
            f"{self.wda_url}/session/{self.session_id}/source",
            timeout=self._timeout
        )
        resp.raise_for_status()
        return resp.json()["value"]

    def set_clipboard(self, content: str, content_type: str = "plaintext"):
        """Set device clipboard content."""
        if not self.session_id:
            self.create_session()

        import base64
        payload = {
            "content": base64.b64encode(content.encode()).decode(),
            "contentType": content_type
        }
        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/setPasteboard",
            json=payload,
            timeout=self._timeout
        )
        resp.raise_for_status()

    def get_clipboard(self) -> str:
        """Get device clipboard content."""
        if not self.session_id:
            self.create_session()

        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/getPasteboard",
            json={},
            timeout=self._timeout
        )
        resp.raise_for_status()
        import base64
        return base64.b64decode(resp.json()["value"]).decode()

    def lock(self):
        """Lock the device."""
        if not self.session_id:
            self.create_session()

        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/lock",
            timeout=self._timeout
        )
        resp.raise_for_status()

    def unlock(self):
        """Unlock the device."""
        if not self.session_id:
            self.create_session()

        resp = requests.post(
            f"{self.wda_url}/session/{self.session_id}/wda/unlock",
            timeout=self._timeout
        )
        resp.raise_for_status()

    def is_locked(self) -> bool:
        """Check if device is locked."""
        if not self.session_id:
            self.create_session()

        resp = requests.get(
            f"{self.wda_url}/session/{self.session_id}/wda/locked",
            timeout=self._timeout
        )
        resp.raise_for_status()
        return resp.json()["value"]

    def __enter__(self):
        """Context manager entry."""
        self.create_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.delete_session()
        return False


# Convenience function for quick WDA connection
def connect(wda_url: str = "http://localhost:8100") -> WDAClient:
    """
    Create and connect a WDA client.

    Args:
        wda_url: WDA URL (default localhost:8100)

    Returns:
        Connected WDAClient instance
    """
    client = WDAClient(wda_url)
    if not client.health_check():
        raise ConnectionError(f"Cannot connect to WDA at {wda_url}")
    return client
