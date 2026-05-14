import os
import time
from loguru import logger
from scrapers.base import BaseScraper
from utils import save_json
from selenium.webdriver.common.by import By

class SAWCURLTab(BaseScraper):
    def __init__(self, tab_index, day_name, **kwargs):
        super().__init__(name=f"SAWC_URL_TAB_{tab_index}", chrome_version=147, **kwargs)
        self.base_url = "https://www.hmpglobalevents.com/sawcspring/agenda"
        self.tab_index = tab_index
        self.day_name = day_name
        self.output_file = os.path.join("data", "sawc", f"urls_tab_{tab_index}.json")

    def execute(self):
        self.driver.get(self.base_url)
        time.sleep(5)
        
        logger.info(f"Scraping Tab {self.tab_index} ({self.day_name})...")
        
        # Click the tab
        tab_xpath = f"(//div[contains(@class, 'tabs-wrapper')]//button[@aria-role='tab'])[{self.tab_index}]"
        tab_btn = self.driver.find_element(By.XPATH, tab_xpath)
        self.driver.execute_script("arguments[0].click();", tab_btn)
        time.sleep(3)
        
        # Target only the active tab area
        # We find the one that is displayed
        areas = self.driver.find_elements(By.CSS_SELECTOR, ".tab-area")
        active_area = None
        for area in areas:
            if area.is_displayed():
                active_area = area
                break
        
        if not active_area:
            logger.error("Could not find active tab area!")
            return

        sessions = active_area.find_elements(By.CSS_SELECTOR, ".session")
        logger.info(f"Found {len(sessions)} sessions in {self.day_name}")
        
        url_data = []
        for j, session in enumerate(sessions, 1):
            try:
                header = session.find_element(By.CSS_SELECTOR, ".session__header")
                title = header.find_element(By.CSS_SELECTOR, "h4").text.strip()
                url_data.append({
                    "title": title,
                    "tab_index": self.tab_index,
                    "session_index": j,
                    "url": self.base_url
                })
            except: continue
            
        save_json(url_data, self.output_file)
        logger.info(f"Saved {len(url_data)} sessions to {self.output_file}")

if __name__ == "__main__":
    import sys
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    days = ["WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    SAWCURLTab(idx, days[idx-1]).run()
