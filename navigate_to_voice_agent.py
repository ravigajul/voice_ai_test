no#!/usr/bin/env python3
"""
Complete Navigation to Voice Agent
Navigates through all setup steps to voice agent ready state
"""
from appium.webdriver.common.appiumby import AppiumBy
from src.appium_driver import AppiumDriver
from selenium.webdriver.common.keys import Keys
import time

def navigate_to_voice_agent(username=None, password=None, keep_session_open=False):
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
    driver = AppiumDriver('config/appium_config.yaml')

    try:
        # Start app
        print("🚀 Starting app...")
        driver.start()
        time.sleep(3)
        print("✅ App launched\n")

        # Step 1: Click QA button
        print("Step 1: Selecting QA environment...")
        qa_button = driver.find_element_safe(AppiumBy.ACCESSIBILITY_ID, "QA", timeout=5)
        if qa_button:
            print("   👆 Clicking QA...")
            qa_button.click()
            time.sleep(2)
        else:
            print("   ❌ QA button not found")
            return False

        # Step 2: Click Continue (first time)
        print("\nStep 2: Clicking Continue (1st)...")
        time.sleep(2)  # Wait for screen to load
        continue_button = driver.find_element_safe(AppiumBy.ACCESSIBILITY_ID, "Continue", timeout=8)
        if continue_button:
            print("   👆 Clicking Continue...")
            continue_button.click()
            time.sleep(3)  # Wait for next screen to load
        else:
            print("   ❌ Continue button not found")
            return False

        # Step 3: Click Continue (second time)
        print("\nStep 3: Clicking Continue (2nd)...")
        time.sleep(3)  # Wait longer for next screen to load
        continue_button2 = driver.find_element_safe(AppiumBy.ACCESSIBILITY_ID, "Continue", timeout=8)
        if continue_button2:
            print("   👆 Clicking Continue...")
            continue_button2.click()
            time.sleep(3)  # Wait for next screen
        else:
            print("   ❌ Continue button not found")
            return False

        # Step 4: Click "Log In" button
        print("\nStep 4: Clicking Log In...")
        login_button = driver.find_element_safe(AppiumBy.XPATH, "//android.widget.Button[@content-desc='Log In']", timeout=10)
        if login_button:
            print("   👆 Clicking Log In...")
            login_button.click()
            time.sleep(2)
        else:
            print("   ❌ Log In button not found")
            return False

        # Step 5: Enter credentials
        print("\nStep 5: Entering credentials...")
        
        if username and password:
            print(f"   📝 Entering username and password...")
            
            # Find username field
            input_fields = driver.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
            if len(input_fields) >= 1:
                input_fields[0].click()
                time.sleep(0.5)
                input_fields[0].send_keys(username)
                time.sleep(0.5)
            
            # Find password field (find fresh to avoid stale element)
            input_fields = driver.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
            if len(input_fields) >= 2:
                input_fields[1].click()
                time.sleep(0.5)
                input_fields[1].send_keys(password)
                time.sleep(1)

            # Click Log In button
            login_submit = driver.find_element_safe(AppiumBy.ACCESSIBILITY_ID, "Log In", timeout=5)
            if login_submit:
                print("   👆 Clicking Log In...")
                login_submit.click()
                time.sleep(8)  # Wait longer for login to complete
            else:
                print("   ⚠️  Log In button not found")
        else:
            print("   ⏸️  Please enter credentials manually...")
            print("   Waiting 60 seconds for you to enter credentials and click Log In...")
            time.sleep(60)

        # Step 6: Check for Yes/No dialog box after login
        print("\nStep 6: Checking for Yes/No dialog box...")
        print(f"   Current activity: {driver.driver.current_activity}")
        time.sleep(2)
        
        # First, show what's on screen
        visible_texts = driver.get_visible_text_elements()
        print(f"   Visible texts: {visible_texts}")
        
        clickable = driver.driver.find_elements(AppiumBy.XPATH, "//*[@clickable='true']")
        print(f"   Clickable elements ({len(clickable)}):")
        for i, elem in enumerate(clickable[:20], 1):
            text = elem.get_attribute('text') or ''
            desc = elem.get_attribute('content-desc') or ''
            resource_id = elem.get_attribute('resource-id') or ''
            print(f"      [{i}] Text: '{text}', Desc: '{desc}', ID: '{resource_id}'")
        
        no_locators = [
            (AppiumBy.ACCESSIBILITY_ID, "NO"),
            (AppiumBy.ACCESSIBILITY_ID, "No"),
            (AppiumBy.XPATH, "//*[@content-desc='NO']"),
            (AppiumBy.XPATH, "//*[@text='No']"),
            (AppiumBy.XPATH, "//android.widget.Button[@text='No']"),
            (AppiumBy.XPATH, "//*[contains(@text, 'No')]"),
        ]
        
        no_button = None
        for by, value in no_locators:
            try:
                no_button = driver.find_element_safe(by, value, timeout=2)
                if no_button:
                    print(f"   ✅ Found No button using: {by}='{value}'")
                    break
            except:
                continue
        
        if no_button:
            print("   👆 Clicking No...")
            no_button.click()
            time.sleep(2)
        else:
            print("   ⚠️  No button not found - showing available elements above")
        
        # # Step 6b: Check for Allow permission prompt (optional - may or may not appear)
        # print("\nStep 6b: Checking for Allow permission prompt...")
        # time.sleep(1)
        
        # allow_locators = [
        #     (AppiumBy.ACCESSIBILITY_ID, "Allow"),
        #     (AppiumBy.XPATH, "//*[@text='Allow']"),
        #     (AppiumBy.XPATH, "//android.widget.Button[@text='Allow']"),
        # ]
        
        # allow_button = None
        # for by, value in allow_locators:
        #     try:
        #         allow_button = driver.find_element_safe(by, value, timeout=1)
        #         if allow_button:
        #             print(f"   ✅ Found Allow button, clicking...")
        #             allow_button.click()
        #             time.sleep(2)
        #             break
        #     except:
        #         continue
        
        # if not allow_button:
        #     print("   ⓘ Allow button not found (may or may not appear - continuing anyway)")

        # Step 7: Wait for home screen to load
        print("\nStep 7: Waiting for home screen...")
        time.sleep(2)
        
        # Handle Samsung Pass dialog if it appears
        print("   Checking for Samsung Pass dialog...")
        for attempt in range(1, 4):  # Try multiple times
            visible = driver.get_visible_text_elements()
            if 'Never use Samsung Pass' in visible or any('Samsung Pass' in str(t) for t in visible):
                print(f"   ⚠️  Samsung Pass dialog still visible (attempt {attempt})")
                print(f"      Visible texts: {visible}")
                
                try:
                    # Try to click the "Never use Samsung Pass for this app" button
                    samsung_button = driver.find_element_safe(
                        AppiumBy.XPATH, 
                        "//*[contains(@text, 'Never use Samsung Pass')]",
                        timeout=2
                    )
                    if samsung_button:
                        print(f"   ✅ Found Samsung Pass button, clicking...")
                        samsung_button.click()
                        time.sleep(2)
                        continue
                except:
                    pass
                
                # If that didn't work, try clicking buttons by finding them all
                try:
                    buttons = driver.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.Button")
                    print(f"      Found {len(buttons)} buttons on screen")
                    for i, btn in enumerate(buttons):
                        btn_text = btn.get_attribute('text') or ''
                        btn_desc = btn.get_attribute('content-desc') or ''
                        print(f"         Button {i}: text='{btn_text}', desc='{btn_desc}'")
                    
                    # Click the first button (usually "Never use Samsung Pass")
                    if len(buttons) >= 1:
                        print(f"   👆 Clicking first button...")
                        buttons[0].click()
                        time.sleep(2)
                except Exception as e:
                    print(f"      Error clicking buttons: {e}")
            else:
                print("   ✅ No Samsung Pass dialog visible")
                break

        # Step 8: Click Carryout option
        print("\nStep 8: Looking for Carryout option...")
        print(f"   Current activity: {driver.driver.current_activity}")
        
        visible_texts = driver.get_visible_text_elements()
        print(f"   Visible texts on screen: {visible_texts}")
        
        carryout_locators = [
            (AppiumBy.XPATH, "//*[@content-desc='Carryout']"),
            (AppiumBy.ACCESSIBILITY_ID, "Carryout"),
            (AppiumBy.XPATH, "//*[@text='Carryout' or @text='CARRYOUT']"),
            (AppiumBy.XPATH, "//*[contains(@text, 'Carryout')]"),
            (AppiumBy.XPATH, "//android.widget.Button[contains(@text, 'Carryout')]"),
        ]
        
        carryout_button = None
        for by, value in carryout_locators:
            try:
                carryout_button = driver.find_element_safe(by, value, timeout=3)
                if carryout_button:
                    print(f"   ✅ Found Carryout option")
                    break
            except:
                continue
        
        if carryout_button:
            print("   👆 Clicking Carryout...")
            carryout_button.click()
            time.sleep(3)
        else:
            print("   ⚠️  Carryout option not found, showing available elements:")
            clickable = driver.driver.find_elements(AppiumBy.XPATH, "//*[@clickable='true']")
            print(f"   Clickable elements ({len(clickable)}):")
            for i, elem in enumerate(clickable[:20], 1):
                text = elem.get_attribute('text') or ''
                desc = elem.get_attribute('content-desc') or ''
                print(f"      [{i}] Text: '{text}', Desc: '{desc}'")
            return False

        # # Step 9: Enter Zip code
        # print("\nStep 9: Entering zip code...")
        # time.sleep(2)
        
        # zip_input_fields = driver.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
        
        # if zip_input_fields:
        #     print(f"   Found {len(zip_input_fields)} input fields")
        #     print("   📝 Entering zip code...")
        #     try:
        #         zip_field = zip_input_fields[0]
        #         zip_field.click()
        #         time.sleep(0.5)
        #         # Select all and delete
        #         zip_field.send_keys(Keys.CONTROL + 'a')
        #         time.sleep(0.2)
        #         zip_field.send_keys(Keys.DELETE)
        #         time.sleep(0.5)
        #         # Type zip code
        #         zip_field.send_keys("40014")
        #         time.sleep(1)
        #         print("   ✅ Zip code entered: 40014")
        #     except Exception as e:
        #         print(f"   ⚠️  Error entering zip: {str(e)[:50]}")
        #         return False
            
        #     # Look for search/submit button or just proceed to location selection
        #     time.sleep(2)
            
        #     visible_texts = driver.get_visible_text_elements()
        #     print(f"   Visible texts after zip entry: {visible_texts}")
            
        #     clickable = driver.driver.find_elements(AppiumBy.XPATH, "//*[@clickable='true']")
        #     print(f"   Clickable elements ({len(clickable)}):")
        #     for i, elem in enumerate(clickable[:20], 1):
        #         text = elem.get_attribute('text') or ''
        #         desc = elem.get_attribute('content-desc') or ''
        #         print(f"      [{i}] Text: '{text}', Desc: '{desc}'")
            
        #     # Press ENTER to trigger search after magnifying glass
        #     print("   👆 Pressing ENTER to trigger search...")
        #     zip_field.send_keys(Keys.RETURN)
        #     time.sleep(3)
        # else:
        #     print("   ⚠️  No input fields found for zip code, returning False")
        #     return False

        # Step 10: Click on the location address
        print("\nStep 10: Clicking on location address...")
        time.sleep(2)
        
        try:
            # First try the exact XPath provided
            location_element = driver.find_element_safe(
                AppiumBy.XPATH,
                '//android.widget.ImageView[@content-desc="0.99 miles 6535 W. Hwy 22 Crestwood, KY, 40014 Online ordering Available"]',
                timeout=3
            )
            if location_element:
                print("   ✅ Found exact location address element")
                print("   👆 Clicking location...")
                location_element.click()
                time.sleep(4)
            else:
                raise Exception("Element not found")
        except:
            # Fallback: find any ImageView with location-like content-desc
            print("   ⚠️  Exact location not found, trying generic location selector...")
            try:
                location_element = driver.find_element_safe(
                    AppiumBy.XPATH,
                    '//android.widget.ImageView[contains(@content-desc, "miles") and contains(@content-desc, "Online ordering")]',
                    timeout=3
                )
                if location_element:
                    desc = location_element.get_attribute('content-desc') or ''
                    print(f"   ✅ Found location: {desc[:60]}...")
                    print("   👆 Clicking location...")
                    location_element.click()
                    time.sleep(4)
                else:
                    raise Exception("Generic location not found")
            except Exception as e:
                print(f"   ❌ Location element not found: {str(e)[:100]}")
                return False

        # Step 11: Click "Carryout from this Store" button
        print("\nStep 11: Clicking 'Carryout from this Store' button...")
        time.sleep(2)
        
        try:
            carryout_button = driver.find_element_safe(
                AppiumBy.XPATH,
                '//android.widget.Button[@content-desc="Carryout from this Store"]',
                timeout=5
            )
            if carryout_button:
                print("   ✅ Found Carryout button")
                print("   👆 Clicking Carryout from this Store...")
                carryout_button.click()
                time.sleep(4)
            else:
                print("   ❌ Carryout button not found")
                return False
        except Exception as e:
            print(f"   ❌ Error finding Carryout button: {str(e)[:100]}")
            return False

        # Step 12: Click "Order" button
        print("\nStep 12: Clicking 'Order' button...")
        time.sleep(2)
        
        try:
            order_button = driver.find_element_safe(
                AppiumBy.XPATH,
                '//android.widget.Button[@content-desc="Order"]',
                timeout=5
            )
            if order_button:
                print("   ✅ Found Order button")
                print("   👆 Clicking Order...")
                order_button.click()
                time.sleep(4)
            else:
                print("   ❌ Order button not found")
                return False
        except Exception as e:
            print(f"   ❌ Error finding Order button: {str(e)[:100]}")
            return False

        # Step 13: Click VOICE ORDERING arrow/button to invoke voice agent
        print("\nStep 13: Clicking VOICE ORDERING to invoke voice agent...")
        time.sleep(2)
        
        try:
            voice_button = driver.find_element_safe(
                AppiumBy.XPATH,
                '//android.view.View[@content-desc="VOICE ORDERING"]',
                timeout=5
            )
            if voice_button:
                print("   ✅ Found VOICE ORDERING button")
                print("   👆 Clicking VOICE ORDERING...")
                voice_button.click()
                time.sleep(4)
            else:
                print("   ❌ VOICE ORDERING button not found")
                return False
        except Exception as e:
            print(f"   ❌ Error finding VOICE ORDERING button: {str(e)[:100]}")
            return False

        # Verification and completion
        print("\nStep 14: Verifying voice agent is ready...")
        time.sleep(2)

        visible_texts = driver.get_visible_text_elements()
        print(f"   📱 Visible elements on screen: {len(visible_texts)} items")

        keywords = ['listen', 'listening', 'speak', 'voice', 'microphone', 'ready', 'talk']
        agent_ready = any(any(kw in text.lower() for kw in keywords) for text in visible_texts if text)

        if agent_ready:
            print("   ✅ Voice agent appears to be ready!")
        else:
            print("   ⚠️  Voice agent readiness unclear - check screen manually")

        print("\n" + "="*60)
        print("✅ NAVIGATION COMPLETE - VOICE AGENT READY!")
        print("="*60)
        print("   Current activity:", driver.driver.current_activity)
        print("\n   You can now interact with the voice agent!")

        if keep_session_open:
            print("\n📋 Session will stay open for 10 minutes for testing")
            # Keep session open
            time.sleep(600)  # 10 minutes
            return True
        else:
            # Return driver for caller to manage (don't close it here)
            return driver

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        # Close on error
        try:
            driver.stop()
        except:
            pass
        return False

if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else None
    password = sys.argv[2] if len(sys.argv) > 2 else None
    navigate_to_voice_agent(username, password, keep_session_open=True)
