#!/usr/bin/env python3
"""
Step-by-step Appium script: Navigate to and invoke the Voice Agent
Step 1: Launch the application
Step 2: Scroll until 'Start Voice Order' is visible
Step 3: Click 'Start Voice Order'
Step 4: Click the arrow on the 'Pizza Assistant is Ready' screen
Step 5: Grant microphone permission (optional)
Step 6: Verify voice agent is active (keywords: 'welcome to papa johns')
"""

from appium.webdriver.common.appiumby import AppiumBy
from src.appium_driver import AppiumDriver
import subprocess
import time


def launch_app() -> AppiumDriver:
    print(f"\n{'='*50}")
    print("Step 1: Launch Application")
    print(f"{'='*50}")

    driver = AppiumDriver("config/appium_config.yaml")
    driver.start()

    # Explicitly launch the app (in case it's closed)
    app_package = driver.config['capabilities']['appPackage']
    print(f"  Launching {app_package}...")
    driver.driver.activate_app(app_package)

    time.sleep(3)  # Wait for app to fully load

    activity = driver.driver.current_activity
    print(f"  Current activity: {activity}")
    driver.take_screenshot("step1_app_launched")
    print("  Screenshot saved: step1_app_launched")

    return driver


def scroll_to_start_voice_order(driver: AppiumDriver):
    print(f"\n{'='*50}")
    print("Step 2: Scroll to 'Start Voice Order'")
    print(f"{'='*50}")

    # UiScrollable instructs Android to scroll the scrollable container until
    # the matching element is visible — no manual swipe coordinates needed
    uia_strategies = [
        "new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView("
        'new UiSelector().descriptionContains("voice order"))',
        "new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView("
        'new UiSelector().textContains("voice order"))',
    ]

    for uia in uia_strategies:
        element = driver.find_element_safe(
            AppiumBy.ANDROID_UIAUTOMATOR, uia, timeout=10
        )
        if element:
            print("  Found 'Start voice order' via UiScrollable")
            driver.take_screenshot("step2_start_voice_order_visible")
            return element

    print("  'Start voice order' not found")
    return None


def click_start_voice_order(driver: AppiumDriver, element):
    print(f"\n{'='*50}")
    print("Step 3: Click 'Start Voice Order'")
    print(f"{'='*50}")

    element.click()
    time.sleep(3)  # Wait for voice agent screen to load

    activity = driver.driver.current_activity
    print(f"  Current activity: {activity}")
    driver.take_screenshot("step3_voice_agent_launched")
    print("  Screenshot saved: step3_voice_agent_launched")


def click_arrow_on_ready_screen(driver: AppiumDriver):
    print(f"\n{'='*50}")
    print("Step 4: Click arrow on 'Pizza Assistant is Ready' screen")
    print(f"{'='*50}")

    # Arrow (▶) is in the toolbar below the status bar, not in the status bar itself.
    # Status bar occupies ~6-7% of height; toolbar center is at ~10-11% of height.
    # Using 7.6% width (left side) and 10.5% height (toolbar center) to reliably land on ▶.
    size = driver.driver.get_window_size()
    x = int(size["width"] * 0.076)
    y = int(size["height"] * 0.105)

    print(f"  Tapping top-left arrow at ({x}, {y})...")
    driver.driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
    time.sleep(2)

    activity = driver.driver.current_activity
    print(f"  Current activity: {activity}")
    driver.take_screenshot("step4_after_arrow_click")
    print("  Screenshot saved: step4_after_arrow_click")


def grant_microphone_permission(driver: AppiumDriver):
    print(f"\n{'='*50}")
    print("Step 5: Grant microphone permission (if shown)")
    print(f"{'='*50}")

    # Only act if the permission dialog is currently on screen — otherwise skip.
    # implicitly_wait(0) ensures this check is instant with no waiting.
    locators = [
        (AppiumBy.XPATH, '//*[@text="While using the app"]'),
        (AppiumBy.XPATH, '//*[@text="Only this time"]'),
        (AppiumBy.XPATH, '//*[contains(@text, "While using")]'),
    ]

    driver.driver.implicitly_wait(0)
    element = None
    try:
        for by, value in locators:
            element = driver.find_element_safe(by, value, timeout=2)
            if element:
                print(f"  Found permission button: '{value}'")
                break
    finally:
        driver.driver.implicitly_wait(10)

    if element:
        element.click()
        time.sleep(2)
        print("  Microphone permission granted")
    else:
        print("  No permission dialog — skipping")


def get_voice_session_id(driver: AppiumDriver) -> str:
    """
    Tap the '#' debug button on the voice ordering screen, which copies the
    session ID to the Android clipboard, then read and return that value.

    Returns:
        Session ID string, or empty string if the button wasn't found or
        the clipboard could not be read.
    """
    print(f"\n{'='*50}")
    print("Step 7: Capture Voice Session ID (# button)")
    print(f"{'='*50}")

    # ── Dump every visible text / content-desc for diagnosis ──────
    print("  Scanning all visible elements on screen:")
    driver.driver.implicitly_wait(0)
    try:
        all_els = driver.driver.find_elements(AppiumBy.XPATH, "//*")
        for el in all_els:
            txt  = el.get_attribute("text") or ""
            desc = el.get_attribute("content-desc") or ""
            cls  = el.get_attribute("class") or ""
            if txt.strip() or desc.strip():
                print(f"    class={cls!r}  text={txt!r}  content-desc={desc!r}")
    except Exception as e:
        print(f"    (dump failed: {e})")
    finally:
        driver.driver.implicitly_wait(10)

    locators = [
        (AppiumBy.XPATH, "//*[@text='#']"),
        (AppiumBy.XPATH, "//*[@content-desc='#']"),
        (AppiumBy.XPATH, "//*[contains(@text,'#')]"),
        (AppiumBy.XPATH, "//*[contains(@content-desc,'#')]"),
    ]

    driver.driver.implicitly_wait(0)
    element = None
    try:
        for by, value in locators:
            elements = driver.driver.find_elements(by, value)
            if elements:
                element = elements[0]
                print(f"  Found '#' button via {value}")
                print(f"    text={element.get_attribute('text')!r}  "
                      f"content-desc={element.get_attribute('content-desc')!r}")
                break
    finally:
        driver.driver.implicitly_wait(10)

    if not element:
        print("  ⚠️  '#' debug button not found — check element dump above for the right locator")
        return ""

    try:
        # Snapshot clipboard before click
        before = _read_clipboard(driver)
        print(f"  Clipboard before click: {before!r}")

        element.click()
        time.sleep(1.5)  # give the app a moment to write to clipboard

        session_id = _read_clipboard(driver)
        print(f"  Clipboard after click : {session_id!r}")

        if session_id and session_id != before:
            print(f"  ✅ Session ID captured: {session_id}")
        elif session_id and session_id == before:
            print("  ⚠️  Clipboard unchanged after clicking '#' — value may be stale")
        else:
            print("  ⚠️  Clipboard empty after clicking '#'")

        return session_id
    except Exception as e:
        print(f"  ⚠️  Could not read clipboard: {e}")
        return ""


def _read_clipboard(driver: AppiumDriver) -> str:
    """
    Read the Android clipboard text, trying Appium first then ADB as fallback.
    Returns empty string if nothing can be read.
    """
    # 1. Appium native
    try:
        text = driver.driver.get_clipboard_text() or ""
        if text:
            return text
    except Exception as e:
        print(f"    (Appium clipboard read failed: {e})")

    # 2. ADB fallback — works on most Android versions for locally connected devices
    try:
        result = subprocess.run(
            ["adb", "shell", "am", "broadcast", "-a", "clipper.get"],
            capture_output=True, text=True, timeout=5,
        )
        # clipper.get broadcasts aren't standard; try a simpler read via input manager
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["adb", "shell", "content", "query",
             "--uri", "content://com.android.externalstorage.documents/",
             "--projection", "label"],
            capture_output=True, text=True, timeout=5,
        )
    except Exception:
        pass

    # Most reliable ADB clipboard read: paste into a temp input and read back
    # via UiAutomator's getText. Simpler: just try the clipboard service call.
    try:
        result = subprocess.run(
            ["adb", "shell", "service", "call", "clipboard", "2",
             "s16", "com.android.shell"],
            capture_output=True, text=True, timeout=5,
        )
        raw = result.stdout
        # Output looks like: Result: Parcel(... "\nsome-text\n" ...)
        # Extract text between quotes
        import re
        match = re.search(r'"([^"]+)"', raw)
        if match:
            return match.group(1).strip()
    except Exception as e:
        print(f"    (ADB clipboard read failed: {e})")

    return ""


def verify_voice_agent_active(driver: AppiumDriver) -> bool:
    print(f"\n{'='*50}")
    print("Step 6: Verify voice agent is active")
    print(f"{'='*50}")

    # Wait up to 15s for agent greeting to appear on screen.
    # Check both @text and @content-desc — the greeting may be in a custom/WebView
    # element that only exposes content-desc, not text.
    keywords = ["welcome to papa john", "papa john", "how can i help", "what can i get","ready","take your time"]
    timeout = 15
    poll_interval = 1
    elapsed = 0

    while elapsed < timeout:
        texts = []
        driver.driver.implicitly_wait(0)
        try:
            elements = driver.driver.find_elements(
                AppiumBy.XPATH, "//*[@text != '' or @content-desc != '']"
            )
            for el in elements:
                for attr in ("text", "content-desc"):
                    val = el.get_attribute(attr)
                    if val and val.strip():
                        texts.append(val.strip())
        except Exception:
            pass
        finally:
            driver.driver.implicitly_wait(10)

        combined = " ".join(texts).lower()
        matched = [kw for kw in keywords if kw in combined]
        if matched:
            print(f"  Agent verified! Matched keyword(s): {matched}")
            print(f"  Visible text: {texts}")
            driver.take_screenshot("step6_agent_verified")
            return True

        time.sleep(poll_interval)
        elapsed += poll_interval
        print(f"  Waiting for agent greeting... ({elapsed}s)")

    print("  Agent greeting not detected within timeout")
    driver.take_screenshot("step6_agent_not_verified")
    return False


if __name__ == "__main__":
    driver = None
    try:
        driver = launch_app()
        element = scroll_to_start_voice_order(driver)
        if element:
            click_start_voice_order(driver, element)
            click_arrow_on_ready_screen(driver)
            # grant_microphone_permission(driver)
            verify_voice_agent_active(driver)
        else:
            print("\n'Start Voice Order' not found — check screen manually.")
        time.sleep(5)
    finally:
        if driver:
            driver.stop()
