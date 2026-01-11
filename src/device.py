"""
iOS Device Connection Helper - pymobiledevice3 wrapper for Windows.

Handles device discovery, WDA tunneling, and USB communication
without requiring a jailbroken device.
"""

import subprocess
import threading
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from loguru import logger


@dataclass
class iOSDevice:
    """Represents a connected iOS device."""
    udid: str
    name: str
    ios_version: str
    model: str
    is_usb: bool = True


class DeviceManager:
    """
    Manages iOS device connections using pymobiledevice3.

    Works on Windows/Linux/Mac without jailbreak.
    """

    def __init__(self):
        self._tunnel_process: Optional[subprocess.Popen] = None
        self._tunnel_port: int = 8100

    def list_devices(self) -> List[iOSDevice]:
        """
        List all connected iOS devices.

        Returns:
            List of iOSDevice objects
        """
        try:
            # Use pymobiledevice3 to list devices
            result = subprocess.run(
                ["python", "-m", "pymobiledevice3",
                    "usbmux", "list", "--no-color"],
                capture_output=True,
                text=True,
                timeout=10
            )

            devices = []
            # Parse output - format varies, simplified parsing
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'UDID' in line or not line.strip():
                    continue
                # Basic parsing - adjust based on actual output format
                parts = line.split()
                if len(parts) >= 1:
                    udid = parts[0]
                    devices.append(iOSDevice(
                        udid=udid,
                        name="iOS Device",
                        ios_version="Unknown",
                        model="Unknown"
                    ))

            logger.info(f"Found {len(devices)} iOS device(s)")
            return devices

        except subprocess.TimeoutExpired:
            logger.error("Timeout listing devices")
            return []
        except FileNotFoundError:
            logger.error(
                "pymobiledevice3 not installed. Run: pip install pymobiledevice3")
            return []
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return []

    def get_device_info(self, udid: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed device information.

        Args:
            udid: Device UDID (uses first device if None)
        """
        try:
            cmd = ["python", "-m", "pymobiledevice3", "lockdown", "info"]
            if udid:
                cmd.extend(["--udid", udid])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10)

            # Parse key-value output
            info = {}
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()

            return info

        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return {}

    def start_wda_tunnel(self, port: int = 8100, udid: Optional[str] = None) -> bool:
        """
        Start USB tunnel for WebDriverAgent.

        This creates a localhost proxy to WDA running on the iOS device.

        Args:
            port: Local port to expose WDA on
            udid: Device UDID (uses first device if None)

        Returns:
            True if tunnel started successfully
        """
        if self._tunnel_process:
            logger.warning("Tunnel already running")
            return True

        try:
            # Use pymobiledevice3 to start tunnel
            # WDA typically runs on port 8100 on the device
            cmd = [
                "python", "-m", "pymobiledevice3",
                "usbmux", "forward",
                str(port), "8100"
            ]
            if udid:
                cmd.extend(["--udid", udid])

            self._tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self._tunnel_port = port

            # Give it a moment to start
            time.sleep(1)

            if self._tunnel_process.poll() is None:
                logger.info(f"WDA tunnel started on localhost:{port}")
                return True
            else:
                stderr = self._tunnel_process.stderr.read().decode()
                logger.error(f"Failed to start tunnel: {stderr}")
                self._tunnel_process = None
                return False

        except Exception as e:
            logger.error(f"Error starting WDA tunnel: {e}")
            return False

    def stop_wda_tunnel(self):
        """Stop the WDA USB tunnel."""
        if self._tunnel_process:
            self._tunnel_process.terminate()
            try:
                self._tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._tunnel_process.kill()
            self._tunnel_process = None
            logger.info("WDA tunnel stopped")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_wda_tunnel()
        return False


class TideviceManager:
    """
    Alternative device manager using tidevice (Alibaba's tool).

    Often more reliable than pymobiledevice3 for WDA operations.
    """

    def __init__(self):
        self._wda_process: Optional[subprocess.Popen] = None

    def list_devices(self) -> List[str]:
        """List connected device UDIDs."""
        try:
            result = subprocess.run(
                ["tidevice", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            import json
            devices = json.loads(result.stdout)
            return [d.get('udid') for d in devices if d.get('udid')]
        except Exception as e:
            logger.error(f"tidevice list failed: {e}")
            return []

    def start_wda(self, bundle_id: str = "com.facebook.WebDriverAgentRunner.xctrunner",
                  port: int = 8100, udid: Optional[str] = None) -> bool:
        """
        Start WebDriverAgent using tidevice.

        Args:
            bundle_id: WDA bundle ID (default is standard WDA)
            port: Port to expose WDA on
            udid: Device UDID

        Returns:
            True if WDA started
        """
        try:
            cmd = ["tidevice", "wdaproxy", "-B",
                   bundle_id, "--port", str(port)]
            if udid:
                cmd.extend(["-u", udid])

            self._wda_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for WDA to be ready
            time.sleep(3)

            if self._wda_process.poll() is None:
                logger.info(f"WDA started via tidevice on port {port}")
                return True
            else:
                stderr = self._wda_process.stderr.read().decode()
                logger.error(f"tidevice wdaproxy failed: {stderr}")
                return False

        except FileNotFoundError:
            logger.error("tidevice not installed. Run: pip install tidevice")
            return False
        except Exception as e:
            logger.error(f"Error starting WDA: {e}")
            return False

    def stop_wda(self):
        """Stop WDA process."""
        if self._wda_process:
            self._wda_process.terminate()
            self._wda_process = None
            logger.info("WDA stopped")

    def install_app(self, ipa_path: str, udid: Optional[str] = None) -> bool:
        """
        Install an IPA on the device.

        Args:
            ipa_path: Path to IPA file
            udid: Device UDID
        """
        try:
            cmd = ["tidevice", "install", ipa_path]
            if udid:
                cmd.extend(["-u", udid])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                logger.info(f"Installed: {ipa_path}")
                return True
            else:
                logger.error(f"Install failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error installing app: {e}")
            return False

    def screenshot(self, output_path: str, udid: Optional[str] = None) -> bool:
        """Take a screenshot via tidevice."""
        try:
            cmd = ["tidevice", "screenshot", output_path]
            if udid:
                cmd.extend(["-u", udid])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_wda()
        return False


def check_dependencies() -> Dict[str, bool]:
    """
    Check if required tools are installed.

    Returns:
        Dict mapping tool name to availability
    """
    deps = {
        'pymobiledevice3': False,
        'tidevice': False,
        'iTunes/Apple Mobile Support': False,
    }

    # Check pymobiledevice3
    try:
        result = subprocess.run(
            ["python", "-m", "pymobiledevice3", "--version"],
            capture_output=True,
            timeout=5
        )
        deps['pymobiledevice3'] = result.returncode == 0
    except:
        pass

    # Check tidevice
    try:
        result = subprocess.run(
            ["tidevice", "version"],
            capture_output=True,
            timeout=5
        )
        deps['tidevice'] = result.returncode == 0
    except:
        pass

    # Check for Apple Mobile Device Support (Windows)
    import os
    if os.name == 'nt':
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Apple Inc.\Apple Mobile Device Support\Shared"
            )
            deps['iTunes/Apple Mobile Support'] = True
            winreg.CloseKey(key)
        except:
            # Also check common install paths
            paths = [
                r"C:\Program Files\Common Files\Apple\Mobile Device Support",
                r"C:\Program Files (x86)\Common Files\Apple\Mobile Device Support"
            ]
            for path in paths:
                if os.path.exists(path):
                    deps['iTunes/Apple Mobile Support'] = True
                    break
    else:
        deps['iTunes/Apple Mobile Support'] = True  # Not needed on Mac/Linux

    return deps
