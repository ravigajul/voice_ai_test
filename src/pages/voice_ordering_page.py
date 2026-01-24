"""
Page Object for Papa John's Voice Ordering Screen
Uses Appium element locators instead of hard-coded coordinates
"""
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time


class VoiceOrderingPage:
    """Page object for voice ordering screen with robust Appium element finding"""

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver.driver, 10)

        # Multiple locator strategies for Order button
        self.ORDER_BUTTON_LOCATORS = [
            # Try by text
            (AppiumBy.XPATH, "//*[@text='Order' or @text='ORDER']"),
            # Try by content description
            (AppiumBy.ACCESSIBILITY_ID, "Order"),
            (AppiumBy.ACCESSIBILITY_ID, "order"),
            # Try by partial text match
            (AppiumBy.XPATH, "//*[contains(@text, 'Order')]"),
            # Try by class and text
            (AppiumBy.XPATH, "//android.widget.Button[@text='Order']"),
            (AppiumBy.XPATH, "//android.widget.TextView[@text='Order']"),
        ]

        # Multiple locator strategies for Back/Arrow button
        self.BACK_ARROW_LOCATORS = [
            # Try by content description (common for nav buttons)
            (AppiumBy.ACCESSIBILITY_ID, "Navigate up"),
            (AppiumBy.ACCESSIBILITY_ID, "Back"),
            # Try by class (ImageButton is common for nav icons)
            (AppiumBy.CLASS_NAME, "android.widget.ImageButton"),
            # Try by resource ID
            (AppiumBy.ID, "com.papajohns.android.debug.qa:id/back_button"),
            (AppiumBy.ID, "android:id/home"),
            # XPath for toolbar back button
            (AppiumBy.XPATH, "//android.widget.ImageButton"),
            (AppiumBy.XPATH, "//*[@content-desc='Navigate up']"),
        ]

    def find_element_with_fallback(self, locators, element_name="element"):
        """Try multiple locator strategies until one works"""
        for i, (by, value) in enumerate(locators, 1):
            try:
                print(f"   Trying locator {i}/{len(locators)}: {by}='{value}'")
                element = self.driver.find_element_safe(by, value, timeout=3)
                if element:
                    print(f"   ✅ Found {element_name} using: {by}='{value}'")
                    return element
            except (NoSuchElementException, TimeoutException) as e:
                print(f"   ❌ Locator {i} failed: {str(e)[:50]}")
                continue

        print(f"   ⚠️  Could not find {element_name} with any locator strategy")
        return None

    def navigate_from_home(self):
        """Navigate from home screen to voice ordering screen using element locators"""
        print("📱 Navigating to voice ordering screen...")

        # Step 1: Find and tap Order button
        print("\n   🔍 Looking for Order button...")
        order_button = self.find_element_with_fallback(
            self.ORDER_BUTTON_LOCATORS,
            "Order button"
        )

        if order_button:
            print("   👆 Tapping Order button...")
            order_button.click()
            time.sleep(4)
        else:
            print("   ❌ Order button not found - listing all clickable elements:")
            self._list_clickable_elements()
            return False

        # Verify we're on the right screen
        state = self.driver.get_screen_state()
        print(f"   Current activity: {state['activity']}")

        # Step 2: Find and tap back/arrow button to activate voice agent
        print("\n   🔍 Looking for arrow/back button...")
        arrow_button = self.find_element_with_fallback(
            self.BACK_ARROW_LOCATORS,
            "Arrow button"
        )

        if arrow_button:
            print("   👆 Tapping arrow button...")
            arrow_button.click()
            time.sleep(3)
        else:
            print("   ❌ Arrow button not found - listing all elements:")
            self._list_all_elements()
            return False

        # Wait for voice agent to initialize
        print("   ⏳ Waiting for voice agent to initialize...")
        time.sleep(2)

        return self.is_agent_ready()

    def _list_clickable_elements(self):
        """Helper to list all clickable elements for debugging"""
        try:
            clickable = self.driver.driver.find_elements(
                AppiumBy.XPATH,
                "//*[@clickable='true']"
            )
            print(f"\n   Found {len(clickable)} clickable elements:")
            for elem in clickable[:10]:  # Show first 10
                text = elem.get_attribute('text') or elem.get_attribute('content-desc') or 'No text'
                class_name = elem.get_attribute('class')
                resource_id = elem.get_attribute('resource-id')
                print(f"     - {class_name}: '{text}' (ID: {resource_id})")
        except Exception as e:
            print(f"   Error listing elements: {e}")

    def _list_all_elements(self):
        """Helper to list all elements on screen for debugging"""
        try:
            all_elems = self.driver.driver.find_elements(AppiumBy.XPATH, "//*")
            print(f"\n   Found {len(all_elems)} total elements (showing first 15):")
            for elem in all_elems[:15]:
                text = elem.get_attribute('text') or elem.get_attribute('content-desc') or ''
                class_name = elem.get_attribute('class')
                resource_id = elem.get_attribute('resource-id')
                if text or resource_id:
                    print(f"     - {class_name}: '{text}' (ID: {resource_id})")
        except Exception as e:
            print(f"   Error listing elements: {e}")

    def is_agent_ready(self) -> bool:
        """Check if voice agent is ready and listening"""
        try:
            # Check for listening indicators
            visible_texts = self.driver.get_visible_text_elements()

            # Look for common indicators
            keywords = ['listen', 'listening', 'speak', 'voice', 'microphone', 'ready', 'talk']
            for text in visible_texts:
                if any(kw in text.lower() for kw in keywords):
                    print(f"   ✅ Agent ready - found indicator: '{text}'")
                    return True

            # Try to find voice-related UI elements
            voice_indicators = [
                (AppiumBy.XPATH, "//*[contains(@text, 'Listen')]"),
                (AppiumBy.XPATH, "//*[contains(@text, 'Speak')]"),
                (AppiumBy.XPATH, "//*[contains(@text, 'Voice')]"),
                (AppiumBy.XPATH, "//*[contains(@content-desc, 'microphone')]"),
            ]

            for by, value in voice_indicators:
                try:
                    elem = self.driver.find_element_safe(by, value, timeout=2)
                    if elem:
                        print(f"   ✅ Agent ready - found UI element: {value}")
                        return True
                except:
                    continue

            # If no keywords, assume ready if we're still on the app
            current_activity = self.driver.driver.current_activity
            if 'MainActivity' in current_activity:
                print("   ✅ Agent likely ready (still on main activity)")
                return True

            return False
        except Exception as e:
            print(f"   ⚠️  Error checking agent readiness: {e}")
            return False

    def get_agent_response_text(self) -> str:
        """Get the text response from the voice agent displayed on screen"""
        try:
            visible_texts = self.driver.get_visible_text_elements()

            # Filter out common UI elements
            filtered = [t for t in visible_texts
                       if t and len(t) > 10  # Longer text likely to be agent response
                       and not t.startswith('$')  # Not a price
                       and not t.isdigit()  # Not a number
                       and 'order' not in t.lower()]  # Not the "Order" button

            if filtered:
                # Return the longest text (likely the agent response)
                response = max(filtered, key=len)
                print(f"   📱 Extracted response: '{response[:50]}...'")
                return response

            return ""
        except Exception as e:
            print(f"   ⚠️  Error getting agent response: {e}")
            return ""

    def verify_screen_state(self, expected_state: str, ollama_client=None) -> dict:
        """Verify current screen state matches expected state using AI"""
        state = self.driver.get_screen_state()
        visible_elements = state['visible_texts']

        print(f"📊 Verifying screen state: {expected_state}")
        print(f"   Visible elements: {visible_elements[:5]}...")

        if ollama_client:
            # Use AI to validate
            validation = ollama_client.validate_screen_state(
                ui_elements=visible_elements,
                expected_screen=expected_state
            )

            if validation['matches']:
                print(f"   ✅ Screen state validated (confidence: {validation['confidence']}%)")
            else:
                print(f"   ❌ Screen state mismatch: {validation['reasoning']}")

            return validation
        else:
            # Simple keyword matching
            keywords = expected_state.lower().split()
            visible_lower = ' '.join(visible_elements).lower()
            matches = any(kw in visible_lower for kw in keywords)

            return {
                "matches": matches,
                "confidence": 70 if matches else 30,
                "reasoning": f"Keyword matching for: {expected_state}"
            }

    def wait_for_agent_response(self, timeout: int = 10) -> bool:
        """Wait for agent to show a response on screen"""
        start_time = time.time()
        initial_texts = set(self.driver.get_visible_text_elements())

        while time.time() - start_time < timeout:
            current_texts = set(self.driver.get_visible_text_elements())
            new_texts = current_texts - initial_texts

            if new_texts:
                print(f"   📱 New text appeared: {list(new_texts)[:3]}")
                return True

            time.sleep(0.5)

        return False
    
    def is_agent_ready(self) -> bool:
        """Check if voice agent is ready and listening"""
        try:
            # Check for listening indicators
            visible_texts = self.driver.get_visible_text_elements()
            
            # Look for common indicators
            keywords = ['listen', 'listening', 'speak', 'voice', 'microphone']
            for text in visible_texts:
                if any(kw in text.lower() for kw in keywords):
                    print(f"   ✅ Agent ready - found indicator: '{text}'")
                    return True
            
            # If no keywords, assume ready if we're still on the app
            current_activity = self.driver.driver.current_activity
            if 'MainActivity' in current_activity:
                print("   ✅ Agent likely ready (still on main activity)")
                return True
            
            return False
        except Exception as e:
            print(f"   ⚠️  Error checking agent readiness: {e}")
            return False
    
    def get_agent_response_text(self) -> str:
        """
        Get the text response from the voice agent displayed on screen
        This needs to be customized based on your app's UI structure
        """
        try:
            # Try common text view IDs or XPath
            visible_texts = self.driver.get_visible_text_elements()
            
            # Filter out common UI elements
            filtered = [t for t in visible_texts 
                       if t and len(t) > 10  # Longer text likely to be agent response
                       and not t.startswith('$')  # Not a price
                       and not t.isdigit()]  # Not a number
            
            if filtered:
                # Return the longest text (likely the agent response)
                return max(filtered, key=len)
            
            return ""
        except:
            return ""
    
    def verify_screen_state(self, expected_state: str, ollama_client=None) -> dict:
        """
        Verify current screen state matches expected state
        Uses AI if Ollama client is provided
        """
        state = self.driver.get_screen_state()
        visible_elements = state['visible_texts']
        
        print(f"📊 Verifying screen state: {expected_state}")
        print(f"   Visible elements: {visible_elements[:5]}...")
        
        if ollama_client:
            # Use AI to validate
            validation = ollama_client.validate_screen_state(
                ui_elements=visible_elements,
                expected_screen=expected_state
            )
            
            if validation['matches']:
                print(f"   ✅ Screen state validated (confidence: {validation['confidence']}%)")
            else:
                print(f"   ❌ Screen state mismatch: {validation['reasoning']}")
            
            return validation
        else:
            # Simple keyword matching
            keywords = expected_state.lower().split()
            visible_lower = ' '.join(visible_elements).lower()
            matches = any(kw in visible_lower for kw in keywords)
            
            return {
                "matches": matches,
                "confidence": 70 if matches else 30,
                "reasoning": f"Keyword matching for: {expected_state}"
            }
    
    def wait_for_agent_response(self, timeout: int = 10) -> bool:
        """Wait for agent to show a response on screen"""
        start_time = time.time()
        initial_texts = set(self.driver.get_visible_text_elements())
        
        while time.time() - start_time < timeout:
            current_texts = set(self.driver.get_visible_text_elements())
            new_texts = current_texts - initial_texts
            
            if new_texts:
                print(f"   📱 New text appeared: {new_texts}")
                return True
            
            time.sleep(0.5)
        
        return False
