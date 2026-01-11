# iOS Automation with WebDriverAgent + OCR

This project enables automation of **non-jailbroken iOS 18.5 devices** using WebDriverAgent and OCR-based interaction.

## 🎯 Features

- **No Jailbreak Required** - Works with stock iOS devices
- **OCR-Based Automation** - Find and tap UI elements by visible text
- **Multiple OCR Engines** - EasyOCR (recommended) and Tesseract support
- **Native WDA Integration** - Full WebDriverAgent API access
- **Windows Compatible** - Works from Windows via USB

---

## 📋 Prerequisites

### 1. Hardware/Software Requirements

| Requirement | Details |
|-------------|---------|
| iOS Device | iPhone/iPad running iOS 18.5 |
| Computer | Windows 10/11 (or Mac/Linux) |
| USB Cable | Lightning or USB-C (device-specific) |
| Apple ID | Free or paid Apple Developer account |

### 2. Windows Software

1. **iTunes or Apple Devices App**
   - Download from [Apple](https://www.apple.com/itunes/) or Microsoft Store
   - This installs required Apple Mobile Device Support drivers

2. **Python 3.10+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure "Add to PATH" is checked during installation

3. **Tesseract OCR** (Optional, for Tesseract engine)
   - Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Install to default location: `C:\Program Files\Tesseract-OCR`

---

## 🔧 WebDriverAgent Setup

> **⚠️ Critical Step**: WDA must be built and signed on a Mac, then deployed to your iOS device.

### Option A: Using a Mac (Recommended)

1. **Clone WebDriverAgent**
   ```bash
   git clone https://github.com/appium/WebDriverAgent.git
   cd WebDriverAgent
   ```

2. **Open in Xcode**
   ```bash
   open WebDriverAgent.xcodeproj
   ```

3. **Configure Signing**
   - Select `WebDriverAgentRunner` target
   - Go to "Signing & Capabilities"
   - Select your Team (Apple ID)
   - Change Bundle Identifier to something unique (e.g., `com.yourname.WebDriverAgentRunner`)

4. **Build and Install**
   - Connect your iOS device
   - Select your device as the build target
   - Press `Cmd+U` to build and run tests
   - On first run, trust the developer profile on your iPhone:
     - Go to **Settings → General → VPN & Device Management**
     - Tap your developer profile and tap "Trust"

5. **Keep WDA Running**
   - WDA needs to be running on the device for automation to work
   - You can start it via Xcode or using command line tools

### Option B: Pre-built WDA (Alternative)

If you have access to a signed WDA IPA:

```bash
# Install using tidevice
tidevice install WebDriverAgent.ipa

# Or using pymobiledevice3
python -m pymobiledevice3 apps install WebDriverAgent.ipa
```

### Option C: Cloud Mac Services

Services like [MacStadium](https://www.macstadium.com/) or [MacinCloud](https://www.macincloud.com/) provide remote Macs for WDA building.

---

## 🚀 Installation

### 1. Clone/Setup Project

```powershell
cd c:\Users\Yami\iosautomation
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Verify Installation

```powershell
python -c "from src.device import check_dependencies; print(check_dependencies())"
```

---

## 📱 Connecting Your Device

### Step 1: Trust Computer

1. Connect iPhone via USB
2. Unlock your iPhone
3. Tap "Trust" when prompted

### Step 2: Start WDA on Device

**Method A: Using tidevice (Recommended)**

```powershell
# List connected devices
tidevice list

# Start WDA proxy (forwards device port to localhost)
tidevice wdaproxy -B com.facebook.WebDriverAgentRunner.xctrunner --port 8100
```

**Method B: Using pymobiledevice3**

```powershell
# Start WDA tunnel
python -m pymobiledevice3 usbmux forward 8100 8100
```

**Method C: Start WDA from Xcode (on Mac)**

Run the WebDriverAgentRunner test target in Xcode.

### Step 3: Verify Connection

```powershell
# Check WDA is responding
curl http://localhost:8100/status
```

You should see JSON with device info.

---

## 💻 Usage Examples

### Basic Connection Test

```python
from src.wda_client import WDAClient

# Connect to WDA
wda = WDAClient("http://localhost:8100")

# Check connection
if wda.health_check():
    print("✅ Connected to device!")
    
    # Get device info
    status = wda.get_status()
    print(f"iOS Version: {status['value']['os']['version']}")
    
    # Take screenshot
    screenshot = wda.screenshot()
    screenshot.save("device_screenshot.png")
```

### OCR-Based Automation

```python
from src.automation import Automator

# Connect with OCR support
with Automator() as auto:
    # Open Settings app
    auto.launch_app("com.apple.Preferences")
    
    # Wait for Settings to load and tap "General"
    auto.tap_text("General", timeout=5)
    
    # Scroll down to find "About"
    if auto.scroll_to_text("About"):
        auto.tap_text("About")
    
    # Get all visible text
    visible_text = auto.get_all_text()
    print("Screen text:", visible_text)
```

### Find and Interact with UI Elements

```python
from src.automation import Automator

with Automator() as auto:
    # Launch Safari
    auto.launch_app("com.apple.mobilesafari")
    auto.wait(2)
    
    # Tap on URL bar (find by text)
    if auto.tap_text("Search or enter website"):
        auto.type_text("apple.com")
        # Press Enter/Go
        auto.tap_text("go")
```

### Screenshot with OCR Debug

```python
from src.automation import Automator

with Automator() as auto:
    # Take screenshot with OCR bounding boxes
    # Great for debugging what OCR sees
    auto.screenshot_with_ocr_boxes("debug_screenshot.png")
```

### Custom Automation Script

```python
from src.automation import run_automation

def my_automation(auto):
    """Your custom automation logic."""
    # Go home
    auto.press_home()
    auto.wait(1)
    
    # Check if specific app is visible
    if auto.text_exists("Instagram"):
        auto.tap_text("Instagram")
        auto.wait(3)
        
        # Like a post
        auto.tap_text("♥")  # OCR can find emoji too!

# Run with automatic connect/disconnect
run_automation(my_automation)
```

---

## 🔍 OCR Tips

### Choosing OCR Engine

| Engine | Best For | Speed | Accuracy |
|--------|----------|-------|----------|
| **EasyOCR** | Mobile UIs, multi-language | Slower | Higher |
| **Tesseract** | Clean text, documents | Faster | Variable |

```python
from src.ocr import EasyOCREngine, TesseractEngine
from src.automation import Automator

# Use Tesseract for faster (but less accurate) OCR
auto = Automator()
auto.ocr_engine = TesseractEngine()
```

### Improving OCR Accuracy

1. **Use exact text matching when possible**
   ```python
   auto.tap_text("Settings", exact=True)
   ```

2. **Handle case sensitivity**
   ```python
   # OCR matching is case-insensitive by default
   auto.tap_text("SETTINGS")  # Matches "Settings"
   ```

3. **Wait for animations**
   ```python
   auto.wait(0.5)  # Let UI settle
   auto.tap_text("Button")
   ```

---

## 📁 Project Structure

```
iosautomation/
├── src/
│   ├── __init__.py
│   ├── wda_client.py    # WebDriverAgent HTTP client
│   ├── ocr.py           # OCR engines (EasyOCR, Tesseract)
│   ├── device.py        # Device connection helpers
│   └── automation.py    # High-level automation API
├── examples/
│   └── basic_automation.py
├── screenshots/         # Saved screenshots
├── requirements.txt
└── README.md
```

---

## 🐛 Troubleshooting

### "Cannot connect to WDA"

1. Ensure WDA is running on the device
2. Check USB connection
3. Verify port forwarding: `curl http://localhost:8100/status`
4. Try restarting WDA

### "WDA session expired"

WDA sessions can expire. The client auto-creates new sessions, but you can force:

```python
wda.create_session()
```

### "OCR not finding text"

1. Save debug screenshot: `auto.screenshot_with_ocr_boxes("debug.png")`
2. Check if text is visible in the screenshot
3. Try different OCR engine
4. Adjust confidence threshold:
   ```python
   match = auto.screen.find_text("text", min_confidence=0.2)
   ```

### "Apple Mobile Device Support not found"

Install iTunes from Apple's website (not Microsoft Store version) or install Apple Devices app.

### "Device not trusted"

1. Disconnect and reconnect USB
2. On iPhone, go to Settings → General → Transfer or Reset → Reset Location & Privacy
3. Reconnect and tap "Trust" when prompted

---

## 📚 API Reference

### WDAClient

| Method | Description |
|--------|-------------|
| `screenshot()` | Capture screen as PIL Image |
| `tap(x, y)` | Tap at coordinates |
| `swipe(x1, y1, x2, y2)` | Swipe gesture |
| `type_text(text)` | Type using keyboard |
| `launch_app(bundle_id)` | Launch app by bundle ID |
| `find_element(strategy, value)` | Find UI element |

### Automator (High-level)

| Method | Description |
|--------|-------------|
| `tap_text(text)` | Find and tap text via OCR |
| `wait_for_text(text, timeout)` | Wait for text to appear |
| `scroll_to_text(text)` | Scroll until text found |
| `text_exists(text)` | Check if text visible |
| `get_all_text()` | Get all visible text |

---

## 📄 Common Bundle IDs

| App | Bundle ID |
|-----|-----------|
| Settings | `com.apple.Preferences` |
| Safari | `com.apple.mobilesafari` |
| App Store | `com.apple.AppStore` |
| Messages | `com.apple.MobileSMS` |
| Photos | `com.apple.mobileslideshow` |
| Camera | `com.apple.camera` |
| Mail | `com.apple.mobilemail` |
| Calendar | `com.apple.mobilecal` |

---

## ⚖️ Legal Notice

This tool is for **legitimate automation and testing purposes only**. Respect app terms of service and Apple's guidelines. Automating apps you don't own or have permission to automate may violate terms of service.

---

## 🤝 Contributing

Contributions welcome! Please ensure any changes maintain compatibility with non-jailbroken iOS devices.
