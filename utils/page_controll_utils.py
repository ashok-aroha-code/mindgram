import time
from loguru import logger

def scroll_down_untill_bottom(driver):
    """Scrolls until the bottom of the page is reached."""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
    except Exception as e:
        logger.error(f"Failed to scroll to bottom: {e}")