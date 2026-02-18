#!/usr/bin/env python3
"""
Complete Navigation to Voice Agent - Refactored
Navigates through all setup steps to voice agent ready state with improved structure
"""
from appium.webdriver.common.appiumby import AppiumBy
from src.appium_driver import AppiumDriver
from selenium.webdriver.common.keys import Keys
import time
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum


class NavigationStep(Enum):
    """Enum for navigation steps to improve tracking"""

    SELECT_QA_ENV = "Select QA Environment"
    FIRST_CONTINUE = "Click Continue (1st)"
    SECOND_CONTINUE = "Click Continue (2nd)"
    LOGIN_BUTTON = "Click Log In Button"
    ENTER_CREDENTIALS = "Enter Credentials"
    HANDLE_DIALOG = "Handle Yes/No Dialog"
    WAIT_HOME_SCREEN = "Wait for Home Screen"
    SELECT_CARRYOUT = "Select Carryout"
    CLICK_LOCATION = "Click Location Address"
    CARRYOUT_FROM_STORE = "Carryout from Store"
    START_VOICE_ORDER = "Click Start Voice Order"
    VERIFY_VOICE_AGENT = "Verify Voice Agent"


@dataclass
class NavigationConfig:
    """Configuration for navigation"""

    username: Optional[str] = None
    password: Optional[str] = None
    keep_session_open: bool = False
    manual_login_timeout: int = 60
    session_duration: int = 600  # 10 minutes
    zip_code: str = "40014"

    # Timeouts
    qa_button_timeout: int = 5
    continue_button_timeout: int = 8
    login_timeout: int = 10
    post_login_wait: int = 8


class ElementLocator:
    """Centralized element locators for better maintainability"""

    # Step 1: QA Environment
    QA_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "QA")

    # Step 2-3: Continue buttons
    CONTINUE_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "Continue")

    # Step 4: Login button
    LOGIN_BUTTON = (AppiumBy.XPATH, "//android.widget.Button[@content-desc='Log In']")

    # Step 5: Input fields
    INPUT_FIELDS = (AppiumBy.CLASS_NAME, "android.widget.EditText")
    LOGIN_SUBMIT = (AppiumBy.ACCESSIBILITY_ID, "Log In")

    # Step 6: Dialog options
    NO_BUTTON_LOCATORS = [
        (AppiumBy.ACCESSIBILITY_ID, "NO"),
        (AppiumBy.ACCESSIBILITY_ID, "No"),
        (AppiumBy.XPATH, "//*[@content-desc='NO']"),
        (AppiumBy.XPATH, "//*[@text='No']"),
        (AppiumBy.XPATH, "//android.widget.Button[@text='No']"),
        (AppiumBy.XPATH, "//*[contains(@text, 'No')]"),
    ]

    # Step 7: Samsung Pass
    SAMSUNG_PASS_BUTTON = (
        AppiumBy.XPATH,
        "//*[contains(@text, 'Never use Samsung Pass')]",
    )

    # Step 8: Carryout
    CARRYOUT_LOCATORS = [
        (AppiumBy.XPATH, "//*[@content-desc='Carryout']"),
        (AppiumBy.ACCESSIBILITY_ID, "Carryout"),
        (AppiumBy.XPATH, "//*[@text='Carryout' or @text='CARRYOUT']"),
        (AppiumBy.XPATH, "//*[contains(@text, 'Carryout')]"),
        (AppiumBy.XPATH, "//android.widget.Button[contains(@text, 'Carryout')]"),
    ]

    # Step 10: Location
    LOCATION_EXACT = (
        AppiumBy.XPATH,
        '//android.widget.ImageView[@content-desc="0.99 miles 6535 W. Hwy 22 Crestwood, KY, 40014 Online ordering Available"]',
    )
    LOCATION_GENERIC = (
        AppiumBy.XPATH,
        '//android.widget.ImageView[contains(@content-desc, "miles") and contains(@content-desc, "Online ordering")]',
    )

    # Step 11: Carryout from store
    CARRYOUT_FROM_STORE = (
        AppiumBy.XPATH,
        '//android.widget.Button[@content-desc="Carryout from this Store"]',
    )

    # Already-configured home screen: Carryout/store banner (tap to reach order screen)
    CARRYOUT_BANNER_LOCATORS = [
        (AppiumBy.XPATH, '//*[contains(@content-desc, "CARRYOUT") and contains(@content-desc, "ASAP")]'),
        (AppiumBy.XPATH, '//*[contains(@content-desc, "Carryout") and contains(@content-desc, "ASAP")]'),
        (AppiumBy.XPATH, '//*[contains(@content-desc, "CARRYOUT")]'),
    ]

    # Step 11 (fresh) / Step 1 (configured): Start Voice Order link
    START_VOICE_ORDER_LOCATORS = [
        (AppiumBy.ACCESSIBILITY_ID, "Start Voice Order"),
        (AppiumBy.XPATH, '//*[@content-desc="Start Voice Order"]'),
        (AppiumBy.XPATH, '//*[@text="Start Voice Order"]'),
        (AppiumBy.XPATH, '//android.widget.TextView[@text="Start Voice Order"]'),
        (AppiumBy.XPATH, '//*[contains(@content-desc, "Start Voice Order")]'),
    ]


class VoiceAgentNavigator:
    """Main navigator class with separated concerns"""

    def __init__(self, config: NavigationConfig):
        self.config = config
        self.driver: Optional[AppiumDriver] = None
        self.current_step: Optional[NavigationStep] = None
        self.is_fresh_install: Optional[bool] = None

    def _print_step(self, step: NavigationStep, message: str = ""):
        """Print formatted step information"""
        self.current_step = step
        step_number = list(NavigationStep).index(step) + 1
        print(f"\n{'='*60}")
        print(f"Step {step_number}: {step.value}")
        if message:
            print(f"   {message}")
        print(f"{'='*60}")

    def _print_info(self, message: str, icon: str = "ℹ️"):
        """Print formatted info message"""
        print(f"   {icon} {message}")

    def _print_success(self, message: str):
        """Print success message"""
        self._print_info(message, "✅")

    def _print_warning(self, message: str):
        """Print warning message"""
        self._print_info(message, "⚠️")

    def _print_error(self, message: str):
        """Print error message"""
        self._print_info(message, "❌")

    def _find_element_with_fallbacks(
        self, locators: List[Tuple], timeout: int = 3, description: str = "element"
    ):
        """Try multiple locators and return first match"""
        for by, value in locators:
            element = self.driver.find_element_safe(by, value, timeout=timeout)
            if element:
                self._print_success(f"Found {description} using: {by}='{value}'")
                return element
        return None

    def _click_element(self, element, description: str, wait_after: float = 2):
        """Click element with consistent logging"""
        if element:
            self._print_info(f"Clicking {description}...", "👆")
            element.click()
            time.sleep(wait_after)
            return True
        self._print_error(f"{description} not found")
        return False

    def _show_debug_info(self):
        """Show debug information about current screen"""
        visible_texts = self.driver.get_visible_text_elements()
        self._print_info(f"Visible texts: {visible_texts}")

        clickable = self.driver.driver.find_elements(
            AppiumBy.XPATH, "//*[@clickable='true']"
        )
        self._print_info(f"Clickable elements ({len(clickable)}):")
        for i, elem in enumerate(clickable[:20], 1):
            text = elem.get_attribute("text") or ""
            desc = elem.get_attribute("content-desc") or ""
            resource_id = elem.get_attribute("resource-id") or ""
            print(f"      [{i}] Text: '{text}', Desc: '{desc}', ID: '{resource_id}'")

    def scroll_down(self):
        """Scroll down one screen to reveal off-screen elements"""
        self._print_info("Scrolling down to reveal more content...", "📜")
        # Use W3C swipe: finger starts at 70% and moves to 30% of screen height
        size = self.driver.driver.get_window_size()
        width = size["width"]
        height = size["height"]
        self.driver.driver.execute_script("mobile: swipeGesture", {
            "left": width // 4,
            "top": int(height * 0.3),
            "width": width // 2,
            "height": int(height * 0.4),
            "direction": "up",
            "percent": 0.8,
        })
        time.sleep(1)

    def start_app(self) -> bool:
        """Initialize driver and start app"""
        try:
            self._print_info("Starting app...", "🚀")
            self.driver = AppiumDriver("config/appium_config.yaml")
            self.driver.start()
            time.sleep(3)
            self._print_success("App launched")
            return True
        except Exception as e:
            self._print_error(f"Failed to start app: {e}")
            return False

    def detect_app_state(self) -> str:
        """
        Detect whether app is freshly installed or already configured

        Returns:
            'fresh_install' - QA environment selection visible (needs full setup)
            'already_configured' - Skip to order screen (user already logged in)
        """
        self._print_info("Detecting app state...", "🔍")
        time.sleep(2)  # Wait for screen to stabilize

        # Check for QA environment button (indicates fresh install)
        qa_button = self.driver.find_element_safe(*ElementLocator.QA_BUTTON, timeout=3)

        if qa_button:
            self._print_info(
                "QA environment button found - Fresh install detected", "🆕"
            )
            self.is_fresh_install = True
            return "fresh_install"

        # Dump what's currently on screen to identify element names
        self._print_info("QA button not found - dumping screen elements for diagnosis:", "🔍")
        self._show_debug_info()

        # Check if already on the order screen (Start Voice Order visible after scrolling)
        start_voice_btn = None
        for attempt in range(1, 4):
            start_voice_btn = self._find_element_with_fallbacks(
                ElementLocator.START_VOICE_ORDER_LOCATORS,
                timeout=3,
                description="Start Voice Order",
            )
            if start_voice_btn:
                break
            if attempt < 3:
                self._print_info(
                    f"Start Voice Order not visible - scrolling down (attempt {attempt}/3)...", "📜"
                )
                self.scroll_down()

        if start_voice_btn:
            self._print_info("'Start Voice Order' found - already on order screen", "✓")
            self.is_fresh_install = False
            return "already_configured"

        # Check if on home screen (Carryout banner visible — need to tap it first)
        carryout_banner = self._find_element_with_fallbacks(
            ElementLocator.CARRYOUT_BANNER_LOCATORS,
            timeout=3,
            description="Carryout banner",
        )
        if carryout_banner:
            self._print_info("Carryout banner found - on home screen, need to tap it", "🏠")
            self.is_fresh_install = False
            return "home_screen"

        # Unknown state — dump debug info
        self._print_warning("Unable to determine app state clearly - assuming fresh install")
        self._show_debug_info()
        self.is_fresh_install = True
        return "fresh_install"

    def select_qa_environment(self) -> bool:
        """Step 1: Select QA environment"""
        self._print_step(NavigationStep.SELECT_QA_ENV)

        qa_button = self.driver.find_element_safe(
            *ElementLocator.QA_BUTTON, timeout=self.config.qa_button_timeout
        )
        return self._click_element(qa_button, "QA button")

    def click_first_continue(self) -> bool:
        """Step 2: Click first continue button"""
        self._print_step(NavigationStep.FIRST_CONTINUE)
        time.sleep(2)

        continue_button = self.driver.find_element_safe(
            *ElementLocator.CONTINUE_BUTTON, timeout=self.config.continue_button_timeout
        )
        return self._click_element(continue_button, "Continue button", wait_after=3)

    def click_second_continue(self) -> bool:
        """Step 3: Click second continue button"""
        self._print_step(NavigationStep.SECOND_CONTINUE)
        time.sleep(3)

        continue_button = self.driver.find_element_safe(
            *ElementLocator.CONTINUE_BUTTON, timeout=self.config.continue_button_timeout
        )
        return self._click_element(continue_button, "Continue button", wait_after=3)

    def click_login_button(self) -> bool:
        """Step 4: Click login button"""
        self._print_step(NavigationStep.LOGIN_BUTTON)

        login_button = self.driver.find_element_safe(
            *ElementLocator.LOGIN_BUTTON, timeout=self.config.login_timeout
        )
        return self._click_element(login_button, "Log In button")

    def enter_credentials(self) -> bool:
        """Step 5: Enter credentials (automated or manual)"""
        self._print_step(NavigationStep.ENTER_CREDENTIALS)

        if self.config.username and self.config.password:
            return self._automated_login()
        else:
            return self._manual_login()

    def _automated_login(self) -> bool:
        """Perform automated login"""
        self._print_info("Entering username and password...", "📝")

        try:
            # Enter username
            input_fields = self.driver.driver.find_elements(
                *ElementLocator.INPUT_FIELDS
            )
            if len(input_fields) < 2:
                self._print_error("Not enough input fields found")
                return False

            input_fields[0].click()
            time.sleep(0.5)
            input_fields[0].send_keys(self.config.username)
            time.sleep(0.5)

            # Re-find password field to avoid stale element
            input_fields = self.driver.driver.find_elements(
                *ElementLocator.INPUT_FIELDS
            )
            input_fields[1].click()
            time.sleep(0.5)
            input_fields[1].send_keys(self.config.password)
            time.sleep(1)

            # Submit login
            login_submit = self.driver.find_element_safe(
                *ElementLocator.LOGIN_SUBMIT, timeout=5
            )
            if login_submit:
                self._click_element(
                    login_submit, "Log In", wait_after=self.config.post_login_wait
                )
                return True

            self._print_warning("Log In submit button not found")
            return False

        except Exception as e:
            self._print_error(f"Automated login failed: {e}")
            return False

    def _manual_login(self) -> bool:
        """Wait for manual login"""
        self._print_info("Please enter credentials manually...", "⏸️")
        self._print_info(f"Waiting {self.config.manual_login_timeout} seconds...")
        time.sleep(self.config.manual_login_timeout)
        return True

    def handle_post_login_dialog(self) -> bool:
        """Step 6: Handle Yes/No dialog after login"""
        self._print_step(NavigationStep.HANDLE_DIALOG)
        self._print_info(f"Current activity: {self.driver.driver.current_activity}")
        time.sleep(2)

        self._show_debug_info()

        no_button = self._find_element_with_fallbacks(
            ElementLocator.NO_BUTTON_LOCATORS, timeout=2, description="No button"
        )

        if no_button:
            return self._click_element(no_button, "No button")
        else:
            self._print_warning(
                "No button not found - showing available elements above"
            )
            return True  # Continue anyway

    def wait_for_home_screen(self) -> bool:
        """Step 7: Wait for home screen and handle Samsung Pass"""
        self._print_step(NavigationStep.WAIT_HOME_SCREEN)
        time.sleep(2)

        return self._handle_samsung_pass_dialog()

    def _handle_samsung_pass_dialog(self, max_attempts: int = 3) -> bool:
        """Handle Samsung Pass dialog if it appears"""
        self._print_info("Checking for Samsung Pass dialog...")

        for attempt in range(1, max_attempts + 1):
            visible = self.driver.get_visible_text_elements()

            if not any("Samsung Pass" in str(t) for t in visible):
                self._print_success("No Samsung Pass dialog visible")
                return True

            self._print_warning(f"Samsung Pass dialog detected (attempt {attempt})")

            samsung_button = self.driver.find_element_safe(
                *ElementLocator.SAMSUNG_PASS_BUTTON, timeout=2
            )

            if samsung_button:
                self._click_element(samsung_button, "Samsung Pass button")
                continue

            # Fallback: try clicking first button
            try:
                buttons = self.driver.driver.find_elements(
                    AppiumBy.CLASS_NAME, "android.widget.Button"
                )
                if buttons:
                    self._print_info(f"Trying first button as fallback...", "👆")
                    buttons[0].click()
                    time.sleep(2)
            except Exception as e:
                self._print_error(f"Error clicking buttons: {e}")

        return True

    def select_carryout(self) -> bool:
        """Step 8: Select carryout option"""
        self._print_step(NavigationStep.SELECT_CARRYOUT)
        self._print_info(f"Current activity: {self.driver.driver.current_activity}")

        visible_texts = self.driver.get_visible_text_elements()
        self._print_info(f"Visible texts: {visible_texts}")

        carryout_button = self._find_element_with_fallbacks(
            ElementLocator.CARRYOUT_LOCATORS, timeout=3, description="Carryout option"
        )

        if carryout_button:
            return self._click_element(carryout_button, "Carryout", wait_after=3)
        else:
            self._print_warning("Carryout option not found")
            self._show_debug_info()
            return False

    def click_location_address(self) -> bool:
        """Step 10: Click on location address"""
        self._print_step(NavigationStep.CLICK_LOCATION)
        time.sleep(2)

        # Try exact location first
        location = self.driver.find_element_safe(
            *ElementLocator.LOCATION_EXACT, timeout=3
        )

        if not location:
            self._print_warning("Exact location not found, trying generic selector...")
            location = self.driver.find_element_safe(
                *ElementLocator.LOCATION_GENERIC, timeout=3
            )

            if location:
                desc = location.get_attribute("content-desc") or ""
                self._print_success(f"Found location: {desc[:60]}...")

        return self._click_element(location, "Location", wait_after=4)

    def carryout_from_store(self) -> bool:
        """Step 11: Click 'Carryout from this Store' button"""
        self._print_step(NavigationStep.CARRYOUT_FROM_STORE)
        time.sleep(2)

        carryout_button = self.driver.find_element_safe(
            *ElementLocator.CARRYOUT_FROM_STORE, timeout=5
        )
        return self._click_element(
            carryout_button, "Carryout from this Store", wait_after=4
        )

    def click_carryout_banner(self) -> bool:
        """Click the Carryout/store banner on the home screen to reach the order screen"""
        self._print_info("Clicking Carryout banner to reach order screen...", "🏠")
        time.sleep(1)
        banner = self._find_element_with_fallbacks(
            ElementLocator.CARRYOUT_BANNER_LOCATORS,
            timeout=5,
            description="Carryout banner",
        )
        return self._click_element(banner, "Carryout banner", wait_after=3)

    def click_start_voice_order(self) -> bool:
        """Click 'Start Voice Order' link to invoke voice agent"""
        self._print_step(NavigationStep.START_VOICE_ORDER)
        time.sleep(2)

        button = None
        for attempt in range(1, 4):
            button = self._find_element_with_fallbacks(
                ElementLocator.START_VOICE_ORDER_LOCATORS,
                timeout=5,
                description="Start Voice Order",
            )
            if button:
                break
            if attempt < 3:
                self._print_info(
                    f"Start Voice Order not visible - scrolling down (attempt {attempt}/3)...", "📜"
                )
                self.scroll_down()
        return self._click_element(button, "Start Voice Order", wait_after=4)

    def verify_voice_agent(self) -> bool:
        """Step 14: Verify voice agent is ready"""
        self._print_step(NavigationStep.VERIFY_VOICE_AGENT)
        time.sleep(2)

        visible_texts = self.driver.get_visible_text_elements()
        self._print_info(f"Visible elements: {len(visible_texts)} items", "📱")

        keywords = [
            "listen",
            "listening",
            "speak",
            "voice",
            "microphone",
            "ready",
            "talk",
        ]
        agent_ready = any(
            any(kw in text.lower() for kw in keywords) for text in visible_texts if text
        )

        if agent_ready:
            self._print_success("Voice agent appears to be ready!")
        else:
            self._print_warning("Voice agent readiness unclear - check screen manually")

        return agent_ready

    def navigate(self) -> bool:
        """Execute complete navigation flow based on app state"""
        try:
            # Start app first
            if not self.start_app():
                return False

            # Detect app state by checking for QA button
            app_state = self.detect_app_state()

            if app_state == "fresh_install":
                # Full setup flow for fresh install (QA button present)
                self._print_info("QA button detected - Executing FULL SETUP flow", "📋")
                fresh_install_steps = [
                    self.select_qa_environment,
                    self.click_first_continue,
                    self.click_second_continue,
                    self.click_login_button,
                    self.enter_credentials,
                    self.handle_post_login_dialog,
                    self.wait_for_home_screen,
                    self.select_carryout,
                    self.click_location_address,
                    self.carryout_from_store,
                    self.click_start_voice_order,
                    self.verify_voice_agent,
                ]

                for step_func in fresh_install_steps:
                    if not step_func():
                        self._print_error(f"Navigation failed at: {step_func.__name__}")
                        return False

            elif app_state == "home_screen":
                # On home screen — tap Carryout banner first, then Start Voice Order
                self._print_info(
                    "On home screen - tapping Carryout banner then Start Voice Order", "⚡"
                )
                configured_steps = [
                    self.click_carryout_banner,
                    self.click_start_voice_order,
                    self.verify_voice_agent,
                ]
                for step_func in configured_steps:
                    if not step_func():
                        self._print_error(f"Navigation failed at: {step_func.__name__}")
                        return False

            else:  # already_configured — already on order screen
                # Direct flow - click Start Voice Order and verify
                self._print_info(
                    "Already on order screen - Going directly to Start Voice Order", "⚡"
                )
                configured_steps = [
                    self.click_start_voice_order,
                    self.verify_voice_agent,
                ]
                for step_func in configured_steps:
                    if not step_func():
                        self._print_error(f"Navigation failed at: {step_func.__name__}")
                        return False

            self._print_completion()
            return True

        except Exception as e:
            self._print_error(f"Navigation error: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _print_completion(self):
        """Print completion message"""
        print("\n" + "=" * 60)
        print("✅ NAVIGATION COMPLETE - VOICE AGENT READY!")
        print("=" * 60)

        if self.is_fresh_install is not None:
            flow_type = "FULL SETUP" if self.is_fresh_install else "SHORT"
            print(f"   Flow executed: {flow_type}")

        print(f"   Current activity: {self.driver.driver.current_activity}")
        print("\n   You can now interact with the voice agent!")

        if self.config.keep_session_open:
            print(
                f"\n📋 Session will stay open for {self.config.session_duration // 60} minutes"
            )

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.stop()
            except:
                pass


def navigate_to_voice_agent(
    username: Optional[str] = None,
    password: Optional[str] = None,
    keep_session_open: bool = False,
):
    """
    Navigate from app launch through all steps until voice agent is invoked

    Args:
        username: Login username
        password: Login password
        keep_session_open: If True, keeps session open for 10 minutes.
                          If False, returns driver for caller to manage

    Returns:
        Driver object if successful, False otherwise
    """
    config = NavigationConfig(
        username=username, password=password, keep_session_open=keep_session_open
    )

    navigator = VoiceAgentNavigator(config)

    try:
        success = navigator.navigate()

        if not success:
            navigator.cleanup()
            return False

        if keep_session_open:
            time.sleep(config.session_duration)
            navigator.cleanup()
            return True
        else:
            # Return driver for caller to manage
            return navigator.driver

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        navigator.cleanup()
        return False


if __name__ == "__main__":
    import sys

    username = sys.argv[1] if len(sys.argv) > 1 else None
    password = sys.argv[2] if len(sys.argv) > 2 else None
    navigate_to_voice_agent(username, password, keep_session_open=True)
