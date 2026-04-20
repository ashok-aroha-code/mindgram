import sys
import os

# Add the project root to sys.path to allow importing from the root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from loguru import logger
from utils import save_json, load_json, scroll_down_untill_bottom

import json, time, random
import re

# Configure Loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
)
logger.add(
    "logs/scraper.log",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="DEBUG",
)

BASE_DATA_FOLDER_NAME = os.path.join("data", "aacrjournals", "aacr_2026")
LINK_FILE_NAME = os.path.join(BASE_DATA_FOLDER_NAME, "aacr_2026_links.json")
BASE_URL = "https://aacrjournals.org/cancerres/issue/86/8_Supplement"


class Driver:
    def __init__(self):
        self.options = uc.ChromeOptions()
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-popup-blocking")
        self.options.add_argument("--start-maximized")

        # Add random user agent to appear more human-like
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        ]
        self.options.add_argument(f"--user-agent={random.choice(user_agents)}")

        # Create driver with specified options
        try:
            self.driver = uc.Chrome(options=self.options, version_main=146)
        except Exception as e:
            print(
                f"Failed with version_main=146, trying without version specification: {e}"
            )
            try:
                self.driver = uc.Chrome(options=self.options)
            except Exception as e2:
                print(f"Failed again, trying with version_main=None: {e2}")
                self.driver = uc.Chrome(options=self.options, version_main=None)

        # Set window size to a common resolution
        self.driver.set_window_size(1920, 1080)

        # Execute JavaScript to make navigator.webdriver undefined
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def get_driver(self):
        return self.driver

    def quit(self):
        """Safely closes the browser and silences WinError 6."""
        if hasattr(self, "driver") and self.driver:
            logger.info("Closing browser session...")
            driver_ref = self.driver
            try:
                driver_ref.quit()
            except Exception as e:
                if "WinError 6" in str(e) or "invalid handle" in str(e).lower():
                    logger.debug("Silenced WinError 6 during driver shutdown.")
                else:
                    logger.warning(f"Error during browser closure: {e}")
            finally:
                try:
                    driver_ref.quit = lambda: None
                except Exception:
                    pass
                self.driver = None
                logger.info("Browser session closed.")


class ScrapAACRLinks:
    def __init__(self, driver):
        self.driver = driver
        self.all_articles = []

    def fetch_page(self, page_url):
        """Navigates to a specific issue page and waits for content."""

        logger.info(f"Accessing issue: {page_url}")
        self.driver.get(page_url)

        # Wait until human solve the CAPTCHA
        print("Please solve the CAPTCHA manually...")
        input("Press Enter after you have solved the CAPTCHA...")

        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "head > title"))
        )

    # def extract_links(self, page_num):
    #     """Parses the current page source and extracts article links."""
    #     soup = BeautifulSoup(self.driver.page_source, "lxml")
    #     tags = soup.find_all("a", class_="article-content-title")

    #     count = 0
    #     for tag in tags:
    #         href = tag.get("href", "")
    #         if href:
    #             full_url = "https://www.sciencedirect.com" + href
    #             self.all_articles.append(full_url)
    #             count += 1

    #     logger.info(f"  [+] Found {count} articles on issue {page_num}")
    #     return count

    # def save_results(self):
    #     """Saves all collected articles to a JSON file, removing duplicates."""
    #     if not self.all_articles:
    #         logger.warning("No article links collected to save.")
    #         return

    #     # Remove duplicates while preserving order
    #     unique_articles = list(dict.fromkeys(self.all_articles))
    #     duplicate_count = len(self.all_articles) - len(unique_articles)

    #     if duplicate_count > 0:
    #         logger.info(f"Removed {duplicate_count} duplicate links.")

    #     try:
    #         save_json(unique_articles, LINK_FILE_NAME)
    #         logger.success(
    #             f"Saved {len(unique_articles)} article links to {LINK_FILE_NAME}"
    #         )
    #     except Exception as e:
    #         logger.error(f"Failed to save results to {LINK_FILE_NAME}: {e}")

    def scrape_all_issues(self):
        """Orchestrates the scraping of multiple issues."""

        try:
            self.fetch_page(page_url=BASE_URL)
            # self.extract_links(page)

            # Random delay between issues to avoid detection (optimized for speed)
            # logger.debug(f"Sleeping for {delay:.2f}s...")
            # time.sleep(delay)

        except Exception as e:
            logger.warning(f"  [!] Failed to scrape issue {page}: {e}")

        # self.save_results()


if __name__ == "__main__":
    driver_wrapper = None
    try:
        driver_wrapper = Driver()
        driver = driver_wrapper.get_driver()

        scraper = ScrapAACRLinks(driver)
        scraper.scrape_all_issues()
    except Exception as e:
        logger.error(f"Scraper failed: {e}")
    finally:
        if driver_wrapper:
            driver_wrapper.quit()
