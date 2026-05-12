import os
import time
from bs4 import BeautifulSoup
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapers.base import BaseScraper
from utils import load_json, save_json, dismiss_cookie_banner, safe_click

class SkeletonScraper(BaseScraper):
    """
    A template scraper that inherits from BaseScraper.
    Copy this file to create new scrapers.
    """
    def __init__(self):
        # Set a unique name for logging and output tracking
        super().__init__(name="Skeleton_Scraper", headless=False)
        
        # Define your file paths
        self.input_file = os.path.join("data", "source_name", "topic_name", "input_data.json")
        self.output_file = os.path.join("data", "source_name", "topic_name", "results.json")
        
        # Define your CSS or XPath selectors
        self.selectors = {
            "item_container": ".article-item",
            "title": "h1.title",
            "abstract": "#abstract-content",
            "authors": ".author-list"
        }

    def execute(self):
        """
        Main logic for the scraper.
        This is called by self.run().
        """
        logger.info(f"Starting {self.name} execution...")
        
        # 1. Load input data
        items_to_scrape = load_json(self.input_file)
        if not items_to_scrape:
            logger.warning(f"No items found in {self.input_file}. Check the path.")
            # return # Uncomment to stop if no input

        # 2. Resuming logic (optional)
        results = load_json(self.output_file)
        if not isinstance(results, list):
            results = []
        
        # 3. Scraping Loop
        # Example: Loop through a list of URLs or a range of pages
        test_urls = ["https://example.com/article1", "https://example.com/article2"]
        
        for index, url in enumerate(test_urls):
            try:
                data = self.process_page(url)
                if data:
                    results.append(data)
                    # 4. Checkpoint save
                    save_json(results, self.output_file)
                
                # Human-like delay between pages
                self.hb.wait_randomly(2.0, 5.0)
                
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")

        logger.info(f"Scraping complete. Collected {len(results)} items.")

    def process_page(self, url):
        """
        Scrapes a single page.
        """
        logger.info(f"Navigating to: {url}")
        self.driver.get(url)
        
        # Wait for a core element to load
        # WebDriverWait(self.driver, 15).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["title"]))
        # )
        
        # Dismiss cookie banners if they block the UI
        dismiss_cookie_banner(self.driver)
        
        # Simulate human scrolling/movement
        self.hb.humanize(probability=0.5)
        
        # Parse with BeautifulSoup for faster extraction once page is loaded
        soup = BeautifulSoup(self.driver.page_source, "lxml")
        
        # Extract data using helper or directly
        title = soup.select_one(self.selectors["title"])
        title_text = title.get_text(strip=True) if title else "N/A"
        
        logger.info(f"Successfully scraped: {title_text}")
        
        return {
            "url": url,
            "title": title_text,
            "timestamp": time.time()
        }

if __name__ == "__main__":
    # Create an instance and run it
    # All driver management and logging are handled by BaseScraper.run()
    SkeletonScraper().run()
