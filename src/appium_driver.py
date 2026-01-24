"""
Appium Driver Wrapper for Papa John's Voice Ordering App
"""
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import yaml
import time
from typing import Optional, List


class AppiumDriver:
    """Wrapper for Appium WebDriver with helper methods"""
    
    def __init__(self, config_path: str = "config/appium_config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.driver: Optional[webdriver.Remote] = None
        self.wait: Optional[WebDriverWait] = None
    
    def start(self):
        """Initialize and start Appium driver"""
        print("🚀 Starting Appium driver...")
        
        options = UiAutomator2Options()
        for key, value in self.config['capabilities'].items():
            options.set_capability(key, value)
        
        self.driver = webdriver.Remote(
            self.config['appium']['server_url'],
            options=options
        )
        
        # Set implicit wait
        timeout = self.config['timeouts']['implicit_wait']
        self.driver.implicitly_wait(timeout)
        
        # Initialize WebDriverWait
        self.wait = WebDriverWait(
            self.driver,
            self.config['timeouts']['explicit_wait']
        )
        
        print("✅ Appium driver started successfully")
        return self
    
    def stop(self):
        """Stop Appium driver"""
        if self.driver:
            print("🛑 Stopping Appium driver...")
            self.driver.quit()
            self.driver = None
    
    def find_element_safe(self, by, value, timeout=10):
        """Find element with explicit wait and error handling"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            print(f"⚠️  Element not found: {by}={value}, Error: {e}")
            return None
    
    def tap_by_coordinates(self, x: int, y: int):
        """Tap at specific coordinates"""
        from appium.webdriver.common.touch_action import TouchAction
        action = TouchAction(self.driver)
        action.tap(x=x, y=y).perform()
    
    def get_visible_text_elements(self) -> List[str]:
        """Get all visible text elements on screen for AI validation"""
        try:
            elements = self.driver.find_elements(AppiumBy.XPATH, "//*[@text]")
            texts = [elem.get_attribute('text') for elem in elements if elem.get_attribute('text')]
            return [t for t in texts if t and len(t.strip()) > 0]
        except:
            return []
    
    def get_screen_state(self) -> dict:
        """Get current screen state for validation"""
        return {
            "activity": self.driver.current_activity,
            "package": self.driver.current_package,
            "visible_texts": self.get_visible_text_elements(),
            "screenshot": self.take_screenshot_base64()
        }
    
    def take_screenshot(self, name: str):
        """Take screenshot and save to file"""
        screenshot_dir = self.config['test']['screenshot_dir']
        import os
        os.makedirs(screenshot_dir, exist_ok=True)
        
        filepath = f"{screenshot_dir}/{name}.png"
        self.driver.save_screenshot(filepath)
        print(f"📸 Screenshot saved: {filepath}")
        return filepath
    
    def take_screenshot_base64(self) -> str:
        """Get screenshot as base64 string"""
        return self.driver.get_screenshot_as_base64()
    
    def wait_for_activity(self, activity_name: str, timeout: int = 10) -> bool:
        """Wait for specific activity to appear"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            current = self.driver.current_activity
            if activity_name in current:
                return True
            time.sleep(0.5)
        return False
    
    def is_element_visible(self, by, value) -> bool:
        """Check if element is visible"""
        try:
            element = self.driver.find_element(by, value)
            return element.is_displayed()
        except:
            return False


if __name__ == "__main__":
    # Test the driver
    driver = AppiumDriver()
    try:
        driver.start()
        print(f"Current activity: {driver.driver.current_activity}")
        print(f"Visible texts: {driver.get_visible_text_elements()[:5]}")
        driver.take_screenshot("test_screenshot")
    finally:
        driver.stop()
