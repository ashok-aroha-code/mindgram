import time
import random
import os
from bs4 import BeautifulSoup
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapers.base import BaseScraper
from utils import save_json

class ASEScraper2024URL(BaseScraper):
    def __init__(self, **kwargs):
        super().__init__(name="ASE_2024_URL", **kwargs)
        self.output_file = os.path.join("data", "sciencedirect", "ase_2024", "ase_2024_links.json")
        self.base_url = "https://www.sciencedirect.com/journal/journal-of-the-american-society-of-echocardiography/vol/37/issue"
        self.all_articles = []

    def execute(self):
        logger.info("Starting ASEScraper2024 URL scraper...")
        for page in range(1, 13): # Issues 1 to 12
            try:
                self.scrape_issue(page)
                time.sleep(random.uniform(1.5, 3.0))
            except Exception as e:
                logger.warning(f"Failed to scrape issue {page}: {e}")
        
        self.save_results()

    def scrape_issue(self, page_num):
        url = f"{self.base_url}/{page_num}"
        logger.info(f"Accessing issue: {url}")
        self.driver.get(url)
        
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "article-content-title"))
        )
        self.hb.humanize()
        
        soup = BeautifulSoup(self.driver.page_source, "lxml")
        tags = soup.find_all("a", class_="article-content-title")
        
        count = 0
        for tag in tags:
            href = tag.get("href", "")
            if href:
                self.all_articles.append("https://www.sciencedirect.com" + href)
                count += 1
        logger.info(f"Found {count} articles in issue {page_num}")

    def save_results(self):
        if not self.all_articles:
            logger.warning("No article links collected.")
            return

        unique_articles = list(dict.fromkeys(self.all_articles))
        save_json(unique_articles, self.output_file)
        logger.info(f"Saved {len(unique_articles)} unique links to {self.output_file}")

if __name__ == "__main__":
    ASEScraper2024URL().run()
