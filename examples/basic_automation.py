"""
Example: Basic iOS Automation with OCR

This script demonstrates:
1. Connecting to a device via WDA
2. Taking screenshots
3. Using OCR to find and tap UI elements
4. Navigating through an app

Prerequisites:
- WDA running on your iOS device
- Port forwarding set up (tidevice wdaproxy or pymobiledevice3)
- Dependencies installed (pip install -r requirements.txt)
"""

from src.device import check_dependencies
from src.automation import Automator
from src.wda_client import WDAClient
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_connection():
    """Test basic WDA connection."""
    print("\n🔌 Testing WDA Connection...")
    print("-" * 40)

    wda = WDAClient("http://localhost:8100")

    if wda.health_check():
        print("✅ WDA is responding!")

        status = wda.get_status()
        session_id = status.get('sessionId', 'N/A')

        # Get device info from status
        value = status.get('value', {})
        ios_info = value.get('os', {})

        print(f"   iOS Version: {ios_info.get('version', 'Unknown')}")
        print(f"   Device: {ios_info.get('name', 'Unknown')}")

        return True
    else:
        print("❌ Cannot connect to WDA!")
        print("   Make sure WDA is running and port forwarding is set up.")
        print("   Try: tidevice wdaproxy -B com.facebook.WebDriverAgentRunner.xctrunner --port 8100")
        return False


def test_screenshot():
    """Test taking a screenshot."""
    print("\n📸 Testing Screenshot...")
    print("-" * 40)

    wda = WDAClient("http://localhost:8100")

    try:
        # Take screenshot
        screenshot = wda.screenshot()

        # Create screenshots directory
        screenshots_dir = Path(__file__).parent.parent / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)

        # Save screenshot
        save_path = screenshots_dir / "test_screenshot.png"
        screenshot.save(save_path)

        print(f"✅ Screenshot saved to: {save_path}")
        print(f"   Size: {screenshot.size}")

        return True
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return False


def test_ocr():
    """Test OCR on current screen."""
    print("\n🔍 Testing OCR...")
    print("-" * 40)

    try:
        from src.ocr import EasyOCREngine

        wda = WDAClient("http://localhost:8100")
        screenshot = wda.screenshot()

        print("   Initializing OCR engine (first run downloads models)...")
        ocr = EasyOCREngine(languages=['en'], gpu=False)

        print("   Extracting text from screen...")
        matches = ocr.extract_text(screenshot)

        print(f"✅ Found {len(matches)} text regions:")
        for match in matches[:10]:  # Show first 10
            print(f"   • '{match.text}' (confidence: {match.confidence:.2f})")

        if len(matches) > 10:
            print(f"   ... and {len(matches) - 10} more")

        return True
    except Exception as e:
        print(f"❌ OCR failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_settings_navigation():
    """
    Demo: Navigate through Settings app using OCR.

    This opens Settings and taps on menu items by finding text.
    """
    print("\n📱 Demo: Settings Navigation")
    print("-" * 40)

    try:
        with Automator() as auto:
            # Open Settings
            print("   Opening Settings app...")
            auto.launch_app("com.apple.Preferences")
            auto.wait(2)

            # Take screenshot for debugging
            screenshots_dir = Path(__file__).parent.parent / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)
            auto.screenshot_with_ocr_boxes(
                str(screenshots_dir / "settings_ocr.png"))
            print(
                f"   Debug screenshot saved to: {screenshots_dir / 'settings_ocr.png'}")

            # Try to find and tap "General"
            print("   Looking for 'General' option...")
            if auto.tap_text("General", timeout=5):
                print("✅ Tapped on 'General'")
                auto.wait(1)

                # Look for "About"
                print("   Looking for 'About' option...")
                if auto.scroll_to_text("About"):
                    auto.tap_text("About")
                    print("✅ Navigated to About")
                else:
                    print("   'About' not found")
            else:
                print("   'General' not found - check OCR debug image")

            # Go back home
            print("   Returning to home screen...")
            auto.press_home()

        print("✅ Demo completed!")
        return True

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests and demos."""
    print("=" * 50)
    print("  iOS Automation - Basic Examples")
    print("=" * 50)

    # Check dependencies
    print("\n📋 Checking dependencies...")
    deps = check_dependencies()
    for name, available in deps.items():
        status = "✅" if available else "❌"
        print(f"   {status} {name}")

    # Run tests
    results = []

    # Test 1: Connection
    results.append(("Connection", test_connection()))

    if not results[-1][1]:
        print("\n⚠️  Cannot continue without WDA connection.")
        print("    Please ensure WDA is running on your device.")
        return

    # Test 2: Screenshot
    results.append(("Screenshot", test_screenshot()))

    # Test 3: OCR
    results.append(("OCR", test_ocr()))

    # Demo: Settings navigation
    print("\n" + "=" * 50)
    user_input = input("Run Settings navigation demo? (y/n): ")
    if user_input.lower() == 'y':
        results.append(("Settings Demo", demo_settings_navigation()))

    # Summary
    print("\n" + "=" * 50)
    print("  Results Summary")
    print("=" * 50)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {name}")


if __name__ == "__main__":
    main()
