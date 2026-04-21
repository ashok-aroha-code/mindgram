import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from loguru import logger
from scrapers import utils, HumanBehaviors, ScraperTimer

import json, time, random, sys, os
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

LINK_FILE_NAME = os.path.join(
    "data", "sciencedirect", "ase_2024", "ase_2024_links.json"
)
BASE_URL = "https://www.sciencedirect.com/journal/journal-of-the-american-society-of-echocardiography/vol/37/issue"


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
        self.options.add_argument("--window-size=1280,800")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")

        # Speed optimizations: don't wait for full page load and block heavy resources
        self.options.page_load_strategy = "eager"
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.fonts": 2,
        }
        self.options.add_experimental_option("prefs", prefs)

        try:
            self.driver = uc.Chrome(options=self.options)
        except Exception as e:
            logger.error(f"Failed to initialize Chrome Driver: {e}")
            raise

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


class ScrapAbstractsLinks:
    def __init__(self, driver):
        self.driver = driver
        self.hb = HumanBehaviors(driver)
        self.all_articles = []

    def fetch_issue_page(self, page_num):
        """Navigates to a specific issue page and waits for content."""
        page_url = f"{BASE_URL}/{page_num}"
        logger.info(f"Accessing issue: {page_url}")
        self.driver.get(page_url)

        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "article-content-title"))
        )
        self.hb.humanize()

    def extract_links(self, page_num):
        """Parses the current page source and extracts article links."""
        soup = BeautifulSoup(self.driver.page_source, "lxml")
        tags = soup.find_all("a", class_="article-content-title")

        count = 0
        for tag in tags:
            href = tag.get("href", "")
            if href:
                full_url = "https://www.sciencedirect.com" + href
                self.all_articles.append(full_url)
                count += 1

        logger.info(f"  [+] Found {count} articles on issue {page_num}")
        return count

    def save_results(self):
        """Saves all collected articles to a JSON file, removing duplicates."""
        if not self.all_articles:
            logger.warning("No article links collected to save.")
            return

        unique_articles = list(dict.fromkeys(self.all_articles))
        duplicate_count = len(self.all_articles) - len(unique_articles)

        if duplicate_count > 0:
            logger.info(f"Removed {duplicate_count} duplicate links.")

        try:
            save_json(unique_articles, LINK_FILE_NAME)
            logger.success(
                f"Saved {len(unique_articles)} article links to {LINK_FILE_NAME}"
            )
        except Exception as e:
            logger.error(f"Failed to save results to {LINK_FILE_NAME}: {e}")

    def scrape_all_issues(self, start_page, end_page):
        """Orchestrates the scraping of multiple issues."""
        try:
            for page in range(start_page, end_page + 1):
                try:
                    self.fetch_issue_page(page)
                    self.extract_links(page)
                    delay = random.uniform(1.5, 3.0)
                    logger.debug(f"Sleeping for {delay:.2f}s...")
                    time.sleep(delay)
                except Exception as e:
                    logger.warning(f"  [!] Failed to scrape issue {page}: {e}")
                    continue
            self.save_results()
        except Exception as e:
            logger.critical(f"Critical error in scraping orchestration: {e}")


class ASEScraper2024URL:
    def run(self):
        """Orchestrates the URL scraping run."""
        timer = ScraperTimer().start()
        logger.info("Starting ASEScraper2024 URL scraper...")
        try:
            driver_wrapper = Driver()
            driver = driver_wrapper.get_driver()
            link_scraper = ScrapAbstractsLinks(driver)
            link_scraper.scrape_all_issues(1, 12)
            logger.info(f"ASEScraper2024 URL run completed. Total time: {timer.format_elapsed()}")
        except Exception as e:
            logger.error(f"ASEScraper2024 URL task failed: {e}")
        finally:
            if "driver_wrapper" in locals():
                driver_wrapper.quit()


if __name__ == "__main__":
    scraper = ASEScraper2024URL()
    scraper.run()
