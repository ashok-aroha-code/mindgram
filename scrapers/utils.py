from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger
import time

def safe_click(driver, selector, by=By.CSS_SELECTOR, timeout=15):
    """
    Wait for an element to be clickable, scroll to it, and perform a click.
    Uses JS click as a fallback if the standard click fails due to obstruction.
    
    Args:
        driver: Selenium webdriver instance
        selector: The locator string (CSS selector, ID, etc.)
        by: The Selenium By strategy (default By.CSS_SELECTOR)
        timeout: Maximum wait time in seconds
        
    Returns:
        bool: True if click was successful, False otherwise
    """
    try:
        # 1. Wait for element to be present and clickable
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        
        # 2. Scroll element into view (center)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", element)
        time.sleep(0.5)  # Brief pause for any scrolling animations or dynamic overlays
        
        # 3. Try standard Selenium click
        try:
            element.click()
            logger.debug(f"Successfully clicked element: {selector}")
            return True
        except Exception as e:
            logger.warning(f"Standard click failed for {selector}, trying JS click: {e}")
            
            # 4. Fallback to JavaScript click
            driver.execute_script("arguments[0].click();", element)
            logger.debug(f"Successfully clicked element (JS fallback): {selector}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to click element {selector} after {timeout}s: {e}")
        return False

def scroll_to_element(driver, element):
    """Scrolls an element into the center of the viewport."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        return True
    except Exception as e:
        logger.error(f"Failed to scroll to element: {e}")
        return False
