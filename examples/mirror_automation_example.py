"""
Example: Mirror-Based Automation (NO MAC REQUIRED)

This demonstrates iOS automation using screen mirroring,
which works without WebDriverAgent or Mac access.

Requirements:
1. A screen mirroring app (ApowerMirror, LonelyScreen, etc.)
2. iPhone screen mirrored to your Windows PC
3. pip install pyautogui pygetwindow
"""

from src.mirror_automation import MirrorAutomator, list_windows
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_mirror_detection():
    """Test finding the mirror window."""
    print("\n🔍 Looking for iOS mirror window...")
    print("-" * 40)

    auto = MirrorAutomator()
    window = auto.find_mirror_window()

    if window:
        print(f"✅ Found: {window.title}")
        print(f"   Position: ({window.x}, {window.y})")
        print(f"   Size: {window.width} x {window.height}")
        return auto
    else:
        print("❌ No mirror window found!")
        print("\nMake sure you have a screen mirroring app running with your iPhone connected.")
        print("\nRecommended free options:")
        print("  • ApowerMirror - https://www.apowersoft.com/phone-mirror")
        print("  • LonelyScreen - https://www.lonelyscreen.com/")
        print("  • 5KPlayer - https://www.5kplayer.com/")
        return None


def test_screenshot_and_ocr(auto: MirrorAutomator):
    """Test taking screenshot and running OCR."""
    print("\n📸 Taking screenshot of mirror window...")
    print("-" * 40)

    screenshot = auto.screenshot()
    if screenshot:
        # Save screenshot
        save_path = Path(__file__).parent.parent / \
            "screenshots" / "mirror_test.png"
        save_path.parent.mkdir(exist_ok=True)
        screenshot.save(save_path)
        print(f"✅ Screenshot saved: {save_path}")
        print(f"   Size: {screenshot.size}")

        # Run OCR
        print("\n🔍 Running OCR...")
        matches = auto.get_all_text()
        print(f"✅ Found {len(matches)} text regions")

        if matches:
            print("\nSample text found:")
            for match in matches[:5]:
                print(f"   • \"{match.text}\" at {match.center}")

        # Save debug image
        debug_path = save_path.parent / "mirror_ocr_debug.png"
        auto.save_debug_screenshot(str(debug_path))
        print(f"\n📊 Debug image saved: {debug_path}")

        return True
    else:
        print("❌ Screenshot failed")
        return False


def demo_tap_interaction(auto: MirrorAutomator):
    """Demo tapping on UI elements."""
    print("\n👆 Demo: Tap Interaction")
    print("-" * 40)

    print("Looking for tappable text on screen...")
    matches = auto.get_all_text()

    if not matches:
        print("No text found on screen")
        return

    print("\nFound text elements:")
    for i, match in enumerate(matches[:5]):
        print(f"  {i+1}. \"{match.text}\"")

    choice = input("\nEnter number to tap (or 'q' to skip): ")

    if choice.isdigit() and 1 <= int(choice) <= len(matches[:5]):
        match = matches[int(choice) - 1]
        print(f"\nTapping on '{match.text}'...")
        auto.tap(match.center[0], match.center[1])
        print("✅ Tap sent!")

        # Wait and take new screenshot
        import time
        time.sleep(1)
        test_screenshot_and_ocr(auto)


def main():
    print("=" * 60)
    print("  Mirror-Based iOS Automation (No Mac Required)")
    print("=" * 60)

    # List all windows first
    print("\n📋 Current Windows:")
    list_windows()

    # Try to find mirror window
    auto = test_mirror_detection()

    if not auto:
        print("\n" + "=" * 60)
        print("  Setup Instructions")
        print("=" * 60)
        print("""
1. Install a screen mirroring app on Windows:
   • ApowerMirror (recommended): https://www.apowersoft.com/phone-mirror
   • LonelyScreen: https://www.lonelyscreen.com/
   
2. Connect your iPhone:
   • Same WiFi network as your PC, OR
   • USB cable (more reliable)
   
3. On iPhone:
   • Open Control Center (swipe down from top-right)
   • Tap "Screen Mirroring"
   • Select your PC
   
4. Run this script again once mirroring is active
        """)
        return

    # Run tests
    if test_screenshot_and_ocr(auto):
        # Offer interactive demo
        while True:
            print("\n" + "-" * 40)
            print("Options:")
            print("  1. Take new screenshot")
            print("  2. Tap on text")
            print("  3. Swipe up")
            print("  4. Swipe down")
            print("  q. Quit")

            choice = input("\nChoice: ")

            if choice == '1':
                test_screenshot_and_ocr(auto)
            elif choice == '2':
                demo_tap_interaction(auto)
            elif choice == '3':
                print("Swiping up...")
                auto.swipe_up()
            elif choice == '4':
                print("Swiping down...")
                auto.swipe_down()
            elif choice.lower() == 'q':
                break


if __name__ == "__main__":
    main()
