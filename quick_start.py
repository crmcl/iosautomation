"""
Quick Start Script - Test your setup.

Run this to verify everything is working:
    python quick_start.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    print("=" * 60)
    print("  iOS Automation Quick Start")
    print("=" * 60)

    # Step 1: Check dependencies
    print("\n📦 Step 1: Checking Python dependencies...")

    missing = []

    try:
        import requests
        print("   ✅ requests")
    except ImportError:
        print("   ❌ requests")
        missing.append("requests")

    try:
        from PIL import Image
        print("   ✅ Pillow")
    except ImportError:
        print("   ❌ Pillow")
        missing.append("Pillow")

    try:
        import cv2
        print("   ✅ opencv-python")
    except ImportError:
        print("   ❌ opencv-python")
        missing.append("opencv-python")

    try:
        import numpy
        print("   ✅ numpy")
    except ImportError:
        print("   ❌ numpy")
        missing.append("numpy")

    try:
        import easyocr
        print("   ✅ easyocr")
    except ImportError:
        print("   ⚠️ easyocr (optional, will install on first use)")

    try:
        from loguru import logger
        print("   ✅ loguru")
    except ImportError:
        print("   ❌ loguru")
        missing.append("loguru")

    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return

    # Step 2: Check system dependencies
    print("\n🔧 Step 2: Checking system tools...")

    from src.device import check_dependencies
    deps = check_dependencies()

    for name, available in deps.items():
        status = "✅" if available else "⚠️ "
        print(f"   {status} {name}")

    if not deps.get('iTunes/Apple Mobile Support'):
        print("\n⚠️  iTunes/Apple Mobile Device Support not found!")
        print("   Install iTunes from: https://www.apple.com/itunes/")

    # Step 3: Test WDA connection
    print("\n🔌 Step 3: Testing WDA connection...")

    from src.wda_client import WDAClient

    wda = WDAClient("http://localhost:8100")

    if wda.health_check():
        print("   ✅ WDA is responding!")

        try:
            status = wda.get_status()
            os_info = status.get('value', {}).get('os', {})
            print(f"   📱 Device: iOS {os_info.get('version', 'Unknown')}")
        except:
            pass

        # Step 4: Test screenshot
        print("\n📸 Step 4: Taking test screenshot...")

        try:
            screenshot = wda.screenshot()
            save_path = Path(__file__).parent / \
                "screenshots" / "quickstart_test.png"
            save_path.parent.mkdir(exist_ok=True)
            screenshot.save(save_path)
            print(f"   ✅ Screenshot saved: {save_path}")
            print(f"   📐 Resolution: {screenshot.size}")
        except Exception as e:
            print(f"   ❌ Screenshot failed: {e}")

        # Step 5: Test OCR
        print("\n🔍 Step 5: Testing OCR (this may take a moment)...")

        try:
            from src.ocr import EasyOCREngine

            ocr = EasyOCREngine(languages=['en'], gpu=False)
            matches = ocr.extract_text(screenshot, min_confidence=0.3)

            print(f"   ✅ Found {len(matches)} text regions")
            if matches:
                print("   Sample text found:")
                for match in matches[:3]:
                    print(f"      • \"{match.text}\"")
        except Exception as e:
            print(f"   ⚠️ OCR test failed: {e}")
            print("   OCR will still work, may need model download on first use.")

        print("\n" + "=" * 60)
        print("  ✅ Setup Complete! You're ready to automate.")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Check out examples/basic_automation.py")
        print("  2. Read the README.md for API documentation")
        print("  3. Start building your automation scripts!")

    else:
        print("   ❌ Cannot connect to WDA at http://localhost:8100")
        print("\n" + "=" * 60)
        print("  ⚠️  WDA Connection Required")
        print("=" * 60)
        print("""
To connect to your iOS device:

1. Make sure WebDriverAgent is installed on your iPhone
   (Requires building from Xcode on a Mac - see README.md)

2. Connect your iPhone via USB cable

3. Start the WDA tunnel with ONE of these commands:

   Using tidevice (recommended):
   > tidevice wdaproxy -B com.facebook.WebDriverAgentRunner.xctrunner --port 8100

   Using pymobiledevice3:
   > python -m pymobiledevice3 usbmux forward 8100 8100

4. Run this script again to verify connection

Need help? Check the troubleshooting section in README.md
        """)


if __name__ == "__main__":
    main()
