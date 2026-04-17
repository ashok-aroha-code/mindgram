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

LINK_FILE_NAME = os.path.join(
    "data", "sciencedirect", "ase_2024", "ase_2024_links.json"
)
ABSTRACT_FILE_NAME = os.path.join(
    "data", "sciencedirect", "ase_2024", "ase_2024_abstracts.json"
)
BASE_URL = "https://www.sciencedirect.com/journal/journal-of-the-american-society-of-echocardiography/vol/37/issue"


def load_json(file_path):
    """Safely loads data from a JSON file."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        return []


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
                # Silence WinError 6 (The handle is invalid) which is common on Windows with undetected_chromedriver
                if "WinError 6" in str(e) or "invalid handle" in str(e).lower():
                    logger.debug("Silenced WinError 6 during driver shutdown.")
                else:
                    logger.warning(f"Error during browser closure: {e}")
            finally:
                # Prevent the object's __del__ method from throwing the same error later during garbage collection
                try:
                    driver_ref.quit = lambda: None
                except Exception:
                    pass
                self.driver = None
                logger.info("Browser session closed.")


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
        """Saves all collected articles to a JSON file, removing duplicates."""
        if not self.all_articles:
            logger.warning("No article links collected to save.")
            return

        # Remove duplicates while preserving order
        unique_articles = list(dict.fromkeys(self.all_articles))
        duplicate_count = len(self.all_articles) - len(unique_articles)

        if duplicate_count > 0:
            logger.info(f"Removed {duplicate_count} duplicate links.")

        try:
            # Ensure the directory exists before saving
            os.makedirs(os.path.dirname(LINK_FILE_NAME), exist_ok=True)
            with open(LINK_FILE_NAME, "w", encoding="utf-8") as f:
                json.dump(unique_articles, f, indent=4, ensure_ascii=False)
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

                    # Random delay between issues to avoid detection (optimized for speed)
                    delay = random.uniform(1.5, 3.0)
                    logger.debug(f"Sleeping for {delay:.2f}s...")
                    time.sleep(delay)

                except Exception as e:
                    logger.warning(f"  [!] Failed to scrape issue {page}: {e}")
                    continue

            self.save_results()

        except Exception as e:
            logger.critical(f"Critical error in scraping orchestration: {e}")


class ScrapAbstracts:
    def __init__(self, driver):

        self.driver = driver

        self.url = ""
        self.title = "#screen-reader-main-title > span"
        self.doi = (
            "#article-identifier-links > a.anchor.doi.anchor-primary > span > span"
        )
        self.author_info = "#author-group"
        self.affiliation = ""
        self.abstract = "#abstracts"
        self.abstract_html = "#abstracts"
        self.abstract_markdown = ""
        self.abstract_metadata = {}

    def load_page(self, url):
        """Navigates to the abstract page and waits for content."""
        logger.info(f"Accessing abstract: {url}")
        self.driver.get(url)

        # Wait for the main title to be present to indicate page load
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "screen-reader-main-title"))
        )
        return BeautifulSoup(self.driver.page_source, "lxml")

    def extract_title(self, soup):
        """Extracts the abstract title."""
        title_tag = soup.select_one(self.title)
        return title_tag.get_text(strip=True) if title_tag else ""

    def extract_author_info(self, soup):
        """Extracts author information as a single string."""
        authors = []
        author_tags = soup.select(self.author_info)
        for tag in author_tags:
            authors.append(tag.get_text(strip=True))
        return ", ".join(authors)

    def extract_abstract_text(self, soup):
        """Extracts the main body of the abstract in plain text."""
        abstract_tag = soup.select_one(self.abstract)
        return abstract_tag.get_text(strip=True) if abstract_tag else "-"

    def extract_abstract_html(self, soup):
        """Extracts the HTML of the main body of the abstract."""
        abstract_tag = soup.select_one(self.abstract_html)
        return str(abstract_tag) if abstract_tag else "-"

    def extract_doi(self, soup):
        """Extracts the DOI link."""
        doi_tag = soup.select_one(self.doi)
        return doi_tag.get("href", "") if doi_tag else ""

    def extract_metadata(self, soup):
        """
        Extracts site-specific metadata dynamically based on the selectors
        provided in self.abstract_metadata.
        """
        metadata = {}
        for key, selector in self.abstract_metadata.items():
            if selector:
                tag = soup.select_one(selector)
                metadata[key] = tag.get_text(strip=True) if tag else ""
        return metadata

    def process_abstract(self, url, abstract_number=""):
        """Orchestrates loading the page and returning data formatted per format.json."""
        try:
            soup = self.load_page(url)

            data = {
                "link": url,
                "title": self.extract_title(soup),
                "doi": self.extract_doi(soup),
                "number": abstract_number,  # Placeholder or explicitly passed
                "author_info": self.extract_author_info(soup),
                "abstract": self.extract_abstract_text(soup),
                "abstract_html": self.extract_abstract_html(soup),
                "abstract_markdown": "",  # Optional: Markdown extraction (if a library is added)
                "abstract_metadata": self.extract_metadata(soup),
            }

            logger.info(f"  [+] Scraped: {data.get('title', '')[:50]}...")
            return data
        except Exception as e:
            logger.error(f"  [!] Failed to scrape abstract {url}: {e}")
            return None


class ASEScraper2024:

    def __init__(self):
        self.all_abstracts = []

    def run(self):
        """Orchestrates the full scraping run."""
        logger.info("Starting ASEScraper2024 full run...")
        try:
            driver_wrapper = Driver()
            driver = driver_wrapper.get_driver()

            # Step 1: Collect All Links (if not already done)
            if not os.path.exists(LINK_FILE_NAME):
                link_scraper = ScrapAbstractsLinks(driver)
                link_scraper.scrape_all_issues(1, 12)
            else:
                logger.info("Links file already exists. Skipping step 1.")

            # Step 2: Load Links and Scrape Abstracts
            links = load_json(LINK_FILE_NAME)
            if not links:
                logger.error("No links found to scrape abstracts.")
                return

            abstract_scraper = ScrapAbstracts(driver)

            # Prepare final structure with resume logic
            if os.path.exists(ABSTRACT_FILE_NAME):
                final_data = load_json(ABSTRACT_FILE_NAME)
                existing_links = {
                    a.get("link") for a in final_data.get("abstracts", [])
                }
                logger.info(
                    f"Loaded {len(existing_links)} existing abstracts. Resuming..."
                )
            else:
                final_data = {
                    "meeting_name": "ASE 2024",
                    "date": "2024",
                    "link": BASE_URL.rsplit("/", 2)[0],  # Root journal link
                    "abstracts": [],
                }
                existing_links = set()

            for index, link in enumerate(links[0:5], start=1):
                # Skip if already in the final structure
                if link in existing_links:
                    logger.info(f"  [-] Skipping already scraped abstract: {link}")
                    continue

                abstract_data = abstract_scraper.process_abstract(
                    link, abstract_number=str(index)
                )
                if abstract_data:
                    final_data["abstracts"].append(abstract_data)
                    # Incremental save to prevent data loss
                    save_json(final_data, ABSTRACT_FILE_NAME)

                    # Random delay between abstract pages
                    delay = random.uniform(2.0, 4.5)
                    logger.debug(f"Sleeping for {delay:.2f}s before next abstract...")
                    time.sleep(delay)

            logger.info(
                f"ASEScraper2024 run completed. {len(final_data['abstracts'])} abstracts saved."
            )
        except Exception as e:
            logger.error(f"ASEScraper2024 task failed: {e}")
        finally:
            if "driver_wrapper" in locals():
                driver_wrapper.quit()


if __name__ == "__main__":
    scraper = ASEScraper2024()
    scraper.run()
