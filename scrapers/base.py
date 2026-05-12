import time
import random
import logging
import sys
from loguru import logger
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from utils import (
    setup_driver_options,
    ScraperTimer,
    HumanBehaviors,
    save_json,
    load_json,
    ensure_dir
)

class BaseScraper:
    def __init__(self, name="BaseScraper", headless=False):
        self.name = name
        self.headless = headless
        self.driver = None
        self.timer = ScraperTimer()
        self.hb = None
        self.setup_logging()

    def setup_logging(self):
        """Configures Loguru for the scraper."""
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
            level="INFO",
        )
        ensure_dir("logs")
        logger.add(
            f"logs/{self.name.lower()}.log",
            rotation="10 MB",
            retention="10 days",
            compression="zip",
            level="DEBUG",
        )

    def init_driver(self):
        """Initializes the Chrome driver."""
        logger.info(f"Initializing driver for {self.name}...")
        options = setup_driver_options(headless=self.headless)
        try:
            self.driver = uc.Chrome(options=options)
            self.hb = HumanBehaviors(self.driver)
            return self.driver
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            raise

    def close_driver(self):
        """Safely closes the driver."""
        if self.driver:
            logger.info("Closing browser session...")
            try:
                self.driver.quit()
            except Exception as e:
                logger.debug(f"Error during browser closure: {e}")
            finally:
                self.driver = None

    def wait_for_element(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Wait for element to be present."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {selector}")
            return None

    def get_text_safely(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Safely extracts text from an element."""
        element = self.wait_for_element(selector, by, timeout)
        if element:
            return element.text.strip().replace("\n", " ").replace("\r", " ")
        return ""

    def run(self):
        """Main execution logic to be overridden by subclasses."""
        with self.timer:
            try:
                self.init_driver()
                self.execute()
            except Exception as e:
                logger.error(f"Scraper execution failed: {e}")
            finally:
                self.close_driver()
                logger.info(f"Run completed in {self.timer.format_elapsed()}")

    def execute(self):
        """Subclasses should implement this."""
        raise NotImplementedError("Subclasses must implement execute()")
