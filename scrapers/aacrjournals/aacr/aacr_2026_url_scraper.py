import sys
import os

# Add the project root to sys.path to allow importing 'scrapers' when run directly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from loguru import logger
from scrapers import utils, ScraperTimer
import json
import time
import random
import sys
import os

# Configure Loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
)

# Paths and Constants
DATA_DIR = os.path.join("data", "aacrjournals", "aacr_2026")
LINK_FILE_NAME = os.path.join(DATA_DIR, "aacr_2026_urls.json")
BASE_URL = "https://aacrjournals.org/cancerres/issue/86/8_Supplement"


def load_json(file_path):
    """Safely loads data from a JSON file."""
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        return {}


def save_json(data, file_path):
    """Saves data to a JSON file with pretty formatting."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")


class Driver:
    def __init__(self):
        self.options = uc.ChromeOptions()
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-blink-features=AutomationControlled")

        # Add random user agent to appear more human-like
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        ]
        self.options.add_argument(f"--user-agent={random.choice(user_agents)}")

        try:
            # Try with version_main if needed, or fallback to auto
            self.driver = uc.Chrome(options=self.options, version_main=146)
        except Exception:
            logger.debug("Retrying uc.Chrome without version_main...")
            self.driver = uc.Chrome(options=self.options)

    def get_driver(self):
        return self.driver

    def quit(self):
        """Safely closes the browser session and silences WinError 6."""
        if hasattr(self, "driver") and self.driver:
            logger.info("Closing browser session...")
            driver_ref = self.driver
            try:
                driver_ref.quit()
            except Exception as e:
                # Silence WinError 6 (The handle is invalid) which is common on Windows with undetected_chromedriver
                if "WinError 6" in str(e) or "invalid handle" in str(e).lower():
                    logger.debug("Silenced WinError 6 during driver shutdown.")
                else:
                    logger.warning(f"Error during browser closure: {e}")
            finally:
                # Prevent __del__ from throwing the same error
                try:
                    driver_ref.quit = lambda: None
                except Exception:
                    pass
                self.driver = None
                logger.info("Browser session closed.")


class ScrapPresentationLinks:
    def __init__(self, driver):
        self.driver = driver
        self.all_links = []

    def navigate_to_issue(self):
        """Navigates to the journal issue page with retries."""
        logger.info(f"Navigating to: {BASE_URL}")
        self.driver.get(BASE_URL)

        # Wait for content to stabilize
        time.sleep(random.uniform(5, 8))

        # Optional: Interactive wait if automation is blocked
        logger.warning(
            "Please ensure all content is expanded. Press Enter in the terminal to continue..."
        )
        input(">>> Press Enter when the page is ready for extraction...")

    def extract_links(self):
        """Extracts article links from the current page."""
        logger.info("Extracting links...")

        # Comprehensive set of selectors for Silverchair/HighWire platforms
        selectors = [
            "h3.customLink.item-title a",
            "a.at-articleLink",
            "a.article-title-link",
            ".viewArticleLink",
            "h3.item-title a",
            "a[id^='aria-item-title']",
            ".al-article-title a"
        ]
        
        extracted = []
        total_anchors = len(self.driver.find_elements(By.TAG_NAME, "a"))
        logger.info(f"Found {total_anchors} total anchor tags on the page.")

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"  [>] Selector '{selector}' found {len(elements)} elements.")
                    for el in elements:
                        href = el.get_attribute("href")
                        if href:
                            full_url = "https://aacrjournals.org" + href if href.startswith("/") else href
                            if full_url not in extracted:
                                extracted.append(full_url)
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
        
        # Fallback to BeautifulSoup if Selenium missed something
        if not extracted:
            logger.debug("Selenium extraction found nothing, trying BeautifulSoup fallback...")
            soup = BeautifulSoup(self.driver.page_source, "lxml")
            for selector in selectors:
                found = soup.select(selector)
                if found:
                    logger.info(f"  [>] BS4 Selector '{selector}' found {len(found)} elements.")
                    for a in found:
                        href = a.get("href")
                        if href:
                            full_url = "https://aacrjournals.org" + href if href.startswith("/") else href
                            if full_url not in extracted:
                                extracted.append(full_url)

        self.all_links = list(dict.fromkeys(extracted))
        
        if not self.all_links:
            logger.error("No links extracted! Saving page source to 'debug_page.html' for inspection.")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)

        logger.info(f"  [+] Extracted {len(self.all_links)} unique links.")
        return len(self.all_links)

    def save_results(self):
        """Saves collected links to the structured JSON file."""
        if not self.all_links:
            logger.warning("No links collected to save.")
            return

        result = {
            "source": "Cancer Research, Volume 86, Issue 8_Supplement",
            "count": len(self.all_links),
            "urls": self.all_links,
        }

        save_json(result, LINK_FILE_NAME)
        logger.success(
            f"Successfully saved {len(self.all_links)} links to {LINK_FILE_NAME}"
        )


class AACR2026URLScraper:
    def run(self):
        timer = ScraperTimer().start()
        logger.info("Starting AACR2026URLScraper...")

        driver_wrapper = None
        try:
            driver_wrapper = Driver()
            driver = driver_wrapper.get_driver()

            scraper = ScrapPresentationLinks(driver)
            scraper.navigate_to_issue()
            
            # Simple scrolling before extraction to ensure all content is loaded
            logger.info("Performing scrolling...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            scraper.extract_links()
            scraper.save_results()

            logger.info(f"Run completed in {timer.format_elapsed()}")
        except Exception as e:
            logger.error(f"AACR2026URLScraper failed: {e}")
        finally:
            if driver_wrapper:
                driver_wrapper.quit()


if __name__ == "__main__":
    scraper = AACR2026URLScraper()
    scraper.run()
