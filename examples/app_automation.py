"""
Example: App-Specific Automation

This script demonstrates how to automate interactions with specific apps
using OCR-based element detection.

Each function shows automation patterns for different app types.
"""

from src.automation import Automator, run_automation
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def automate_safari_search(auto: Automator, search_query: str):
    """
    Automate a Safari web search.

    Args:
        auto: Automator instance
        search_query: What to search for
    """
    print(f"🌐 Safari: Searching for '{search_query}'")

    # Launch Safari
    auto.launch_app("com.apple.mobilesafari")
    auto.wait(2)

    # Try multiple ways to find the search/URL bar
    search_bar_texts = [
        "Search or enter website",
        "Search",
        ".com",
        "Address"
    ]

    tapped = False
    for text in search_bar_texts:
        if auto.tap_if_exists(text):
            tapped = True
            break

    if not tapped:
        # Tap near top center where URL bar typically is
        width, height = auto.wda.get_window_size()
        auto.tap(width // 2, 60)

    auto.wait(0.5)

    # Type search query
    auto.type_text(search_query, clear_first=True)
    auto.wait(0.3)

    # Press Go/Search
    if not auto.tap_if_exists("go"):
        # Try tapping the keyboard's search button area
        auto.tap_if_exists("Search")

    auto.wait(3)  # Wait for results to load
    print("✅ Search complete")


def automate_notes_creation(auto: Automator, note_text: str):
    """
    Create a note in the Notes app.

    Args:
        auto: Automator instance
        note_text: Text to put in the note
    """
    print(f"📝 Notes: Creating note")

    # Launch Notes
    auto.launch_app("com.apple.mobilenotes")
    auto.wait(2)

    # Look for new note button (usually a compose icon)
    # OCR might find it as a square with pencil
    if not auto.tap_if_exists("New Note"):
        # Try tapping bottom right where compose button usually is
        width, height = auto.wda.get_window_size()
        auto.tap(width - 50, height - 100)

    auto.wait(1)

    # Type the note content
    auto.type_text(note_text)

    print("✅ Note created")


def automate_app_store_search(auto: Automator, app_name: str):
    """
    Search for an app in the App Store.

    Args:
        auto: Automator instance
        app_name: App to search for
    """
    print(f"🏪 App Store: Searching for '{app_name}'")

    # Launch App Store
    auto.launch_app("com.apple.AppStore")
    auto.wait(2)

    # Tap Search tab
    if auto.tap_text("Search", timeout=5):
        auto.wait(1)

        # Tap search field
        search_texts = ["Games, Apps, Stories and More", "Search"]
        for text in search_texts:
            if auto.tap_if_exists(text):
                break

        auto.wait(0.5)
        auto.type_text(app_name)

        # Submit search
        auto.tap_if_exists("search")
        auto.wait(2)

        print("✅ Search complete")
    else:
        print("❌ Could not find Search tab")


def automate_photos_browsing(auto: Automator):
    """
    Browse through the Photos app.

    Args:
        auto: Automator instance
    """
    print("📷 Photos: Browsing photos")

    # Launch Photos
    auto.launch_app("com.apple.mobileslideshow")
    auto.wait(2)

    # Go to Library tab
    if auto.tap_if_exists("Library"):
        auto.wait(1)

        # Swipe through some photos
        for i in range(3):
            auto.swipe("left")
            auto.wait(0.5)

        print("✅ Browsed photos")
    else:
        print("ℹ️ Already in library view")


def automate_clock_timer(auto: Automator, minutes: int = 1):
    """
    Set a timer in the Clock app.

    Args:
        auto: Automator instance
        minutes: Timer duration
    """
    print(f"⏰ Clock: Setting {minutes} minute timer")

    # Launch Clock
    auto.launch_app("com.apple.mobiletimer")
    auto.wait(2)

    # Tap Timer tab
    if auto.tap_text("Timer", timeout=5):
        auto.wait(1)

        # The timer picker is complex, might need direct taps
        # For now, just start existing timer
        if auto.tap_if_exists("Start"):
            print("✅ Timer started")
            auto.wait(2)
            auto.tap_if_exists("Cancel")  # Cancel the timer
        else:
            print("ℹ️ Timer might already be running")


def demo_multi_app_workflow():
    """
    Demo: Multi-app workflow.

    This demonstrates switching between apps and performing
    actions in each one.
    """
    print("\n📱 Multi-App Workflow Demo")
    print("-" * 40)

    with Automator() as auto:
        # 1. Take a screenshot
        print("\n1️⃣ Taking initial screenshot...")
        screenshots_dir = Path(__file__).parent.parent / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        auto.screenshot(str(screenshots_dir / "workflow_start.png"))

        # 2. Check current app
        current_app = auto.get_current_app()
        print(f"   Current app: {current_app}")

        # 3. Go home
        print("\n2️⃣ Going to home screen...")
        auto.press_home()
        auto.wait(1)

        # 4. Get visible app names
        print("\n3️⃣ Reading home screen text...")
        visible_text = auto.get_all_text()
        print(f"   Found {len(visible_text)} text elements")

        # Print some app names
        print("   Sample text found:")
        for text in visible_text[:5]:
            print(f"      • {text}")

        # 5. Final screenshot
        print("\n4️⃣ Taking final screenshot...")
        auto.screenshot_with_ocr_boxes(
            str(screenshots_dir / "workflow_end.png"))

        print("\n✅ Workflow complete!")


if __name__ == "__main__":
    print("=" * 50)
    print("  App-Specific Automation Examples")
    print("=" * 50)

    print("\nAvailable examples:")
    print("1. Safari search")
    print("2. Notes creation")
    print("3. App Store search")
    print("4. Photos browsing")
    print("5. Clock timer")
    print("6. Multi-app workflow demo")

    choice = input("\nSelect example (1-6) or 'q' to quit: ")

    if choice == '1':
        query = input("Search query: ") or "python programming"
        run_automation(lambda auto: automate_safari_search(auto, query))
    elif choice == '2':
        note = input("Note text: ") or "Test note from automation"
        run_automation(lambda auto: automate_notes_creation(auto, note))
    elif choice == '3':
        app = input("App name: ") or "twitter"
        run_automation(lambda auto: automate_app_store_search(auto, app))
    elif choice == '4':
        run_automation(automate_photos_browsing)
    elif choice == '5':
        run_automation(lambda auto: automate_clock_timer(auto, 1))
    elif choice == '6':
        demo_multi_app_workflow()
    elif choice.lower() != 'q':
        print("Invalid choice")
