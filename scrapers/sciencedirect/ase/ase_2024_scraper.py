import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from loguru import logger
import json, time, random, sys, os

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

FILE_NAME = os.path.join("data", "sciencedirect", "ase_2024", "ase_2024_links.json")
BASE_URL = "https://www.sciencedirect.com/journal/journal-of-the-american-society-of-echocardiography/vol/37/issue"


class Driver:
    def __init__(self):
        self.options = uc.ChromeOptions()
        self.options.add_argument("--window-size=1280,800")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        try:
            self.driver = uc.Chrome(options=self.options)
        except Exception as e:
            logger.error(f"Failed to initialize Chrome Driver: {e}")
            raise

    def get_driver(self):
        return self.driver


class ScrapAbstractsLinks:
    def __init__(self, driver):
        self.driver = driver
        self.all_articles = []

    def fetch_issue_page(self, page_num):
        """Navigates to a specific issue page and waits for content."""
        page_url = f"{BASE_URL}/{page_num}"
        logger.info(f"Accessing issue: {page_url}")
        self.driver.get(page_url)

        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "article-content-title"))
        )

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
        """Saves all collected articles to a JSON file."""
        if not self.all_articles:
            logger.warning("No article links collected to save.")
            return

        try:
            # Ensure the directory exists before saving
            os.makedirs(os.path.dirname(FILE_NAME), exist_ok=True)
            with open(FILE_NAME, "w", encoding="utf-8") as f:
                json.dump(self.all_articles, f, indent=4, ensure_ascii=False)
            logger.success(
                f"Saved {len(self.all_articles)} article links to {FILE_NAME}"
            )
        except Exception as e:
            logger.error(f"Failed to save results to {FILE_NAME}: {e}")

    def scrape_all_issues(self, start_page, end_page):
        """Orchestrates the scraping of multiple issues."""
        try:
            for page in range(start_page, end_page + 1):
                try:
                    self.fetch_issue_page(page)
                    self.extract_links(page)

                    # Random delay between issues to avoid detection
                    delay = random.uniform(3, 6)
                    logger.debug(f"Sleeping for {delay:.2f}s...")
                    time.sleep(delay)

                except Exception as e:
                    logger.warning(f"  [!] Failed to scrape issue {page}: {e}")
                    continue

            self.save_results()

        except Exception as e:
            logger.critical(f"Critical error in scraping orchestration: {e}")



class ASEScraper2024:
    def run(self):
        logger.info("Starting ASEScraper2024 run...")
        try:
            driver_wrapper = Driver()
            driver = driver_wrapper.get_driver()

            scraper = ScrapAbstractsLinks(driver)
            scraper.scrape_all_issues(1, 12)
            logger.info("ASEScraper2024 run completed.")
        except Exception as e:
            logger.error(f"ASEScraper2024 task failed: {e}")


if __name__ == "__main__":
    scraper = ASEScraper2024()
    scraper.run()
