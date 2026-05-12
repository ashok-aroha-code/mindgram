import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger

def setup_driver_options(headless=False, images=False):
    """Configures Chrome options for scraping."""
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,800")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    
    if headless:
        options.add_argument("--headless")
        
    # Page load strategy: eager waits for DOMContentLoaded
    options.page_load_strategy = "eager"
    
    prefs = {
        "profile.managed_default_content_settings.images": 1 if images else 2,
        "profile.managed_default_content_settings.fonts": 2,
    }
    options.add_experimental_option("prefs", prefs)
    return options

def safe_click(driver, selector, by=By.CSS_SELECTOR, timeout=15):
    """Wait for an element to be clickable and perform a click."""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", element)
        time.sleep(0.5)
        
        try:
            element.click()
            logger.debug(f"Clicked element: {selector}")
            return True
        except Exception:
            driver.execute_script("arguments[0].click();", element)
            logger.debug(f"Clicked element (JS fallback): {selector}")
            return True
    except Exception as e:
        logger.error(f"Failed to click element {selector}: {e}")
        return False

def scroll_to_element(driver, element):
    """Scrolls an element into view."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        return True
    except Exception as e:
        logger.error(f"Failed to scroll to element: {e}")
        return False

def scroll_down_to_bottom(driver):
    """Scrolls until the bottom of the page is reached."""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
    except Exception as e:
        logger.error(f"Failed to scroll to bottom: {e}")

def dismiss_cookie_banner(driver, timeout=5):
    """Attempts to dismiss cookie consent banners."""
    selectors = [
        "#onetrust-accept-btn-handler",
        ".onetrust-close-btn-handler",
        "#accept-cookies",
        "button[aria-label='Accept all cookies']"
    ]
    for selector in selectors:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            logger.info(f"Dismissed cookie banner: {selector}")
            time.sleep(1)
            return True
        except:
            continue
    return False
