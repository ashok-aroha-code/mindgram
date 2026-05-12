import time
import os
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapers.base import BaseScraper
from utils import save_json

class AACR2026URLScraper(BaseScraper):
    def __init__(self):
        super().__init__(name="AACR_2026_URL")
        self.base_url = "https://aacrjournals.org/cancerres/issue/86/8_Supplement"
        self.output_file = os.path.join("data", "aacrjournals", "aacr_2026", "aacr_2026_urls.json")

    def execute(self):
        logger.info(f"Opening AACR issue page: {self.base_url}")
        self.driver.get(self.base_url)
        
        print(">>> Please handle Cloudflare/CAPTCHA if it appears, then press Enter here.")
        input(">>> Press Enter when page is ready...")
        
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            logger.info("Page loaded successfully.")
        except Exception:
            logger.warning("Timeout waiting for article tags. Continuing anyway...")

        self.open_all_toggles()
        
        logger.info("Extracting article links...")
        links_data = self.extract_links()
        
        save_json(links_data, self.output_file)
        logger.info(f"Saved {len(links_data)} URLs to {self.output_file}")

    def open_all_toggles(self):
        logger.info("Expanding all sections...")
        expanded_count = 0
        while True:
            toggles = self.driver.find_elements(By.CSS_SELECTOR, "i.js-toggle-icon.icon-general_arrow-right")
            visible_toggles = [t for t in toggles if t.is_displayed()]
            
            if not visible_toggles:
                break
            
            clicked_any = False
            for toggle in visible_toggles:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", toggle)
                    time.sleep(0.5)
                    try:
                        toggle.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", toggle)
                    
                    clicked_any = True
                    expanded_count += 1
                    time.sleep(1.5) # Wait for animation
                except Exception as e:
                    logger.debug(f"Could not click toggle: {e}")
            
            if not clicked_any:
                break
        logger.info(f"Expanded {expanded_count} sections.")

    def extract_links(self):
        links_data = []
        seen_urls = set()
        articles = self.driver.find_elements(By.CSS_SELECTOR, "div.al-article-items a, a.at-articleLink")
        
        for article in articles:
            href = article.get_attribute("href")
            title = article.text.strip()
            
            if href and "/article/" in href and href not in seen_urls:
                if title:
                    links_data.append({"title": title, "url": href})
                    seen_urls.add(href)
        return links_data

if __name__ == "__main__":
    AACR2026URLScraper().run()
