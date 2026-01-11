# Building WebDriverAgent via GitHub Actions

Since you don't have a Mac, you can use GitHub Actions' free macOS runners to build WDA.

## 🚀 Quick Start (Easiest Method)

### Step 1: Create GitHub Repository

1. Create a new repo on GitHub (can be private)
2. Push this project to it:
   ```powershell
   cd c:\Users\Yami\iosautomation
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/iosautomation.git
   git push -u origin main
   ```

### Step 2: Run the Free Build Workflow

1. Go to your repo on GitHub
2. Click **Actions** tab
3. Select **"Build WDA (Free Apple ID - No Certificate)"**
4. Click **Run workflow**
5. Enter a unique suffix (your username, e.g., `yami2024`)
6. Wait ~5-10 minutes for build to complete
7. Download the artifact

### Step 3: Sign and Install WDA

Since the build is unsigned, use **Sideloadly** to sign and install:

1. **Download Sideloadly**: https://sideloadly.io/
2. **Install it** on Windows
3. **Connect your iPhone** via USB
4. **Download** the `WebDriverAgent-Project-*` artifact from GitHub
5. **Extract** the downloaded zip
6. In Sideloadly:
   - Drag the `WebDriverAgentRunner-Runner.app` 
   - Enter your Apple ID
   - Click "Start"
7. **Trust the app** on iPhone:
   - Settings → General → VPN & Device Management
   - Tap your Apple ID → Trust

---

## 🔐 Advanced: Full Signing in GitHub Actions

If you have a **paid Apple Developer account** ($99/year), you can fully automate signing:

### Required Secrets

Add these to your GitHub repo (Settings → Secrets → Actions):

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `APPLE_CERTIFICATE_P12_BASE64` | Base64-encoded .p12 certificate | Export from Keychain Access on any Mac |
| `APPLE_CERTIFICATE_PASSWORD` | Password for the .p12 file | You set this when exporting |
| `PROVISIONING_PROFILE_BASE64` | Base64-encoded provisioning profile | Download from Apple Developer Portal |
| `APPLE_TEAM_ID` | Your 10-character Team ID | Apple Developer Portal → Membership |
| `KEYCHAIN_PASSWORD` | Any random password | Make one up (e.g., `gh-actions-keychain-2024`) |

### Getting These Values

#### Certificate (.p12)

You need brief Mac access OR use a cloud Mac:

```bash
# On a Mac, create a certificate signing request
# Then download the certificate from Apple Developer Portal
# Export from Keychain Access as .p12

# Convert to base64:
base64 -i certificate.p12 | pbcopy
```

#### Provisioning Profile

1. Go to https://developer.apple.com/account/resources/profiles
2. Create a new "iOS App Development" profile
3. Select your certificate and device UDID
4. Download the .mobileprovision file
5. Convert to base64:
   ```bash
   base64 -i profile.mobileprovision
   ```

---

## 📱 After Installation

Once WDA is installed on your iPhone:

### 1. Start WDA Tunnel

```powershell
# In your iosautomation folder, activate venv
.\.venv\Scripts\Activate.ps1

# Start the tunnel (replace bundle ID with yours)
tidevice wdaproxy -B com.yami2024.WebDriverAgentRunner.xctrunner --port 8100
```

### 2. Verify Connection

```powershell
python quick_start.py
```

### 3. Start Automating!

```python
from src.automation import Automator

with Automator() as auto:
    auto.launch_app("com.apple.Preferences")
    auto.tap_text("General")
```

---

## ⏰ Free Account Limitations

| Account Type | App Validity | Devices | Provisioning |
|--------------|--------------|---------|--------------|
| Free Apple ID | 7 days | 3 devices | Manual re-sign weekly |
| Paid ($99/yr) | 1 year | 100 devices | Automatic |

With a **free Apple ID**, you'll need to re-sign WDA every 7 days using Sideloadly.

---

## 🛠️ Troubleshooting

### "App could not be installed"
- Make sure your device UDID is registered
- Try restarting your iPhone
- Check that you trusted the developer profile

### "WDA crashes immediately"
- Re-sign the app (might have expired)
- Check iOS version compatibility
- Try rebuilding with latest WDA source

### "Cannot connect to WDA"
- Ensure WDA is running (launch it from home screen first)
- Check USB connection
- Verify tunnel is running: `tidevice wdaproxy ...`

---

## 📚 References

- [WebDriverAgent GitHub](https://github.com/appium/WebDriverAgent)
- [Sideloadly](https://sideloadly.io/)
- [tidevice Documentation](https://github.com/alibaba/taobao-iphone-device)
- [Apple Developer Portal](https://developer.apple.com/)
