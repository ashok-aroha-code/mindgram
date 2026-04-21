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


class ScrapAbstracts:
    def __init__(self, driver):
        self.driver = driver
        self.hb = HumanBehaviors(driver)
        self.url = ""
        self.title = "#screen-reader-main-title > span"
        self.doi = (
            "#article-identifier-links > a.anchor.doi.anchor-primary > span > span"
        )
        self.author_info = "#banner > div.wrapper.truncated > div.AuthorGroups"
        self.affiliation = ""
        self.abstract = "#abstracts"
        self.abstract_html = "#abstracts"
        self.abstract_markdown = ""
        self.abstract_metadata = {}

    def load_page(self, url):
        """Navigates to the abstract page and waits for content."""
        logger.info(f"Accessing abstract: {url}")
        self.driver.get(url)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "screen-reader-main-title"))
        )
        utils.dismiss_cookie_banner(self.driver)
        self.hb.humanize()
        return BeautifulSoup(self.driver.page_source, "lxml")

    def extract_title(self, soup):
        """Extracts the abstract title."""
        title_tag = soup.select_one(self.title)
        title = title_tag.get_text(strip=True) if title_tag else ""
        logger.info(f"  [+] Scraped Title: {title}")
        return title

    def extract_author_info(self, soup):
        """Extracts author information as a single string."""
        processed_authors = []
        author_groups = soup.select(".AuthorGroups")
        if not author_groups:
            logger.debug("  [!] No AuthorGroups container found.")
            return ""
        for group in author_groups:
            author_tags = group.select(".author-group button, .author-group a")
            for tag in author_tags:
                name_tag = tag.select_one(".react-xocs-alternative-link")
                if not name_tag:
                    continue
                name = name_tag.get_text(" ", strip=True)
                ref_tags = tag.select(".author-ref")
                refs = [ref.get_text(strip=True) for ref in ref_tags]
                ref_str = " ".join(refs)
                author_str = f"{name} {ref_str}".strip()
                processed_authors.append(author_str)
                logger.info(f"  [+] Scraped Author: {author_str}")
        return ", ".join(processed_authors)

    def extract_author_affiliation(self, soup):
        """Clicks 'show more' to reveal affiliations and extracts them."""
        selector = "#show-more-btn"
        if not soup.select_one(selector):
            affiliations = soup.select("dl.affiliation")
            affiliation_list = [aff.get_text(" ", strip=True) for aff in affiliations]
            return " ".join(affiliation_list) if affiliation_list else ""
        if utils.safe_click(self.driver, selector, timeout=5):
            time.sleep(1)
            soup = BeautifulSoup(self.driver.page_source, "lxml")
        affiliations = soup.select("dl.affiliation")
        affiliation_list = [aff.get_text(" ", strip=True) for aff in affiliations]
        return " ".join(affiliation_list) if affiliation_list else ""

    def extract_abstract_text(self, soup):
        """Extracts the main body of the abstract in plain text with section spacing."""
        abstract_tag = soup.select_one(self.abstract)
        if not abstract_tag:
            return "-"
        text = abstract_tag.get_text(separator="\n\n", strip=True)
        text = text.replace("\n\n•\n\n", " ")
        text = text.replace("\n•\n", " ")
        text = re.sub(r" +", " ", text)
        return text.strip()

    def extract_abstract_html(self, soup):
        """Extracts the HTML of the main body of the abstract."""
        abstract_tag = soup.select_one(self.abstract_html)
        return str(abstract_tag) if abstract_tag else "-"

    def extract_doi(self, soup):
        """Extracts the DOI link from text content, removing the protocol and domain prefix."""
        doi_tag = soup.select_one(self.doi)
        if not doi_tag:
            return ""
        text_content = doi_tag.get_text(strip=True)
        return re.sub(r"https?://doi\.org/", "", text_content)

    def extract_metadata(self, soup):
        """Extracts site-specific metadata dynamically."""
        metadata = {}
        for key, selector in self.abstract_metadata.items():
            if selector:
                tag = soup.select_one(selector)
                metadata[key] = tag.get_text(strip=True) if tag else ""
        return metadata

    def process_abstract(self, url, abstract_number=""):
        """Orchestrates loading the page and returning data."""
        try:
            soup = self.load_page(url)
            author_info = self.extract_author_info(soup)
            affiliations = self.extract_author_affiliation(soup)
            data = {
                "link": url,
                "title": self.extract_title(soup),
                "doi": self.extract_doi(soup),
                "number": abstract_number,
                "author_info": (
                    f"{author_info}; {affiliations}" if affiliations else author_info
                ),
                "abstract": self.extract_abstract_text(soup),
                "abstract_html": self.extract_abstract_html(soup),
                "abstract_markdown": "",
                "abstract_metadata": self.extract_metadata(soup),
            }
            logger.info(f"  [+] Scraped: {data.get('title', '')[:50]}...")
            return data
        except Exception as e:
            logger.error(f"  [!] Failed to scrape abstract {url}: {e}")
            return None


class ASEScraper2024Abstract:
    def run(self):
        """Orchestrates the abstract scraping run."""
        timer = ScraperTimer().start()
        logger.info("Starting ASEScraper2024 Abstract scraper...")
        try:
            driver_wrapper = Driver()
            driver = driver_wrapper.get_driver()
            links = load_json(LINK_FILE_NAME)
            if not links:
                logger.error("No links found to scrape abstracts.")
                return

            abstract_scraper = ScrapAbstracts(driver)
            loaded_data = load_json(ABSTRACT_FILE_NAME)
            if loaded_data and isinstance(loaded_data, dict):
                final_data = loaded_data
                existing_links = {
                    a.get("link") for a in final_data.get("abstracts", [])
                }
                logger.info(f"Loaded {len(existing_links)} existing abstracts. Resuming...")
            else:
                final_data = {
                    "meeting_name": "ASE 2024",
                    "date": "2024",
                    "link": BASE_URL.rsplit("/", 2)[0],
                    "abstracts": [],
                }
                existing_links = set()

            for index, link in enumerate(links[:5], start=1):
                if link in existing_links:
                    logger.info(f"  [-] Skipping already scraped abstract: {link}")
                    continue
                abstract_data = abstract_scraper.process_abstract(
                    link, abstract_number=str(index)
                )
                if abstract_data:
                    final_data["abstracts"].append(abstract_data)
                    save_json(final_data, ABSTRACT_FILE_NAME)
                    abstract_scraper.hb.wait_randomly(2.0, 5.0)

            logger.info(
                f"ASEScraper2024 Abstract run completed. {len(final_data['abstracts'])} abstracts saved. "
                f"Total time: {timer.format_elapsed()}"
            )
        except Exception as e:
            logger.error(f"ASEScraper2024 Abstract task failed: {e}")
        finally:
            if "driver_wrapper" in locals():
                driver_wrapper.quit()


if __name__ == "__main__":
    scraper = ASEScraper2024Abstract()
    scraper.run()
