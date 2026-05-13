import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from loguru import logger

def setup_driver_options(headless=False, images=False):
    """Configures Chrome options for scraping."""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    
    if headless:
        options.add_argument("--headless=new")
        
    options.page_load_strategy = "eager"
    
    prefs = {
        "profile.managed_default_content_settings.images": 1 if images else 2,
        "profile.managed_default_content_settings.fonts": 2,
    }
    options.add_experimental_option("prefs", prefs)
    return options

def wait_for_element(driver, selector, by=By.CSS_SELECTOR, timeout=10):
    """Wait for element to be present."""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    except TimeoutException:
        logger.warning(f"Timeout waiting for element: {selector}")
        return None

def get_text_safely(driver, selector, by=By.CSS_SELECTOR, timeout=10):
    """Safely extracts text from an element."""
    element = wait_for_element(driver, selector, by, timeout)
    if element:
        return element.text.strip().replace("\n", " ").replace("\r", " ")
    return ""

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
    """
    Attempts to dismiss cookie consent banners by clicking common 'Accept' buttons.
    Uses a combination of CSS selectors and text-based keyword matching.
    """
    # Common CSS selectors for cookie banners
    common_selectors = [
        "#onetrust-accept-btn-handler",
        ".onetrust-close-btn-handler",
        "#accept-cookies",
        "#accept-all-cookies",
        ".accept-cookies",
        "button[aria-label*='Accept']",
        "button[aria-label*='Cookie']",
        "div[class*='cookie'] button",
        "div[id*='cookie'] button",
        "a[class*='cookie'][href*='javascript']",
        ".sc-consent-banner-accept",
        ".gdpr-banner-accept",
        "button[id*='accept']",
        "button[class*='accept']"
    ]
    
    # Common keywords for 'Accept' buttons (case-insensitive search)
    keywords = [
        "Accept", "Agree", "Allow", "Consent", "OK", "I understand", "Got it",
        "Confirm", "Enable all", "Accept all", "Agree to all", "Accept cookies"
    ]
    
    try:
        # 1. Try CSS Selectors first (combined for speed)
        combined_selector = ",".join(common_selectors)
        try:
            # Short wait for any of the elements to be present
            elements = WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, combined_selector))
            )
            for element in elements:
                if element.is_displayed():
                    try:
                        driver.execute_script("arguments[0].click();", element)
                        logger.info(f"Dismissed cookie banner via CSS: {element.get_attribute('outerHTML')[:60]}")
                        time.sleep(1)
                        return True
                    except:
                        continue
        except TimeoutException:
            pass

        # 2. Try text-based matching for buttons/links via XPath
        # We search for elements with role='button', <button>, or <a> containing keywords
        xpath_keywords = " or ".join([
            f"contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{k.lower()}')" 
            for k in keywords
        ])
        
        xpath = f"//button[{xpath_keywords}] | //a[{xpath_keywords}] | //div[@role='button'][{xpath_keywords}]"
        
        elements = driver.find_elements(By.XPATH, xpath)
        for element in elements:
            if element.is_displayed():
                try:
                    driver.execute_script("arguments[0].click();", element)
                    logger.info(f"Dismissed cookie banner via text: {element.text.strip()[:40]}")
                    time.sleep(1)
                    return True
                except:
                    continue
                    
    except Exception as e:
        logger.debug(f"Error while dismissing cookie banner: {e}")

    return False
