import os
import time
from loguru import logger
from scrapers.base import BaseScraper
from utils import (
    safe_click, 
    save_json
)
from selenium.webdriver.common.by import By

class SAWCSpring2026URL(BaseScraper):
    def __init__(self, **kwargs):
        super().__init__(name="SAWC_SPRING_2026_URL", chrome_version=147, **kwargs)
        self.base_url = "https://www.hmpglobalevents.com/sawcspring/agenda"
        self.meeting_name = "SAWC_Spring"
        self.year = "2026"
        self.output_file = os.path.join("data", "sawc", f"{self.meeting_name}_{self.year}_urls.json")
        self.tab_xpath = "//div[contains(@class, 'tabs-wrapper')]//button[@aria-role='tab']"
        self.session_button_xpath = "//div[contains(@class, 'tab-area') and not(contains(@class, 'hidden'))]//button[contains(@class, 'session__header')]"

    def execute(self):
        self.driver.get(self.base_url)
        time.sleep(3)
        
        logger.info("Collecting session URLs and positions...")
        url_data = []
        
        tabs = self.driver.find_elements(By.XPATH, self.tab_xpath)
        tabs_count = len(tabs)
        
        for i in range(1, tabs_count + 1):
            tab_xpath = f"({self.tab_xpath})[{i}]"
            try:
                safe_click(self.driver, tab_xpath, By.XPATH)
                time.sleep(2)
                
                btns = self.driver.find_elements(By.XPATH, self.session_button_xpath)
                for j in range(1, len(btns) + 1):
                    try:
                        btn_xpath = f"({self.session_button_xpath})[{j}]"
                        btn = self.driver.find_element(By.XPATH, btn_xpath)
                        title = btn.find_element(By.CSS_SELECTOR, "h4").text.strip()
                        url_data.append({
                            "title": title, 
                            "tab_index": i, 
                            "session_index": j,
                            "url": self.driver.current_url
                        })
                    except: continue
            except Exception as e:
                logger.error(f"Error on tab {i}: {e}")
                
        save_json(url_data, self.output_file)
        logger.info(f"Collected {len(url_data)} session entries. Saved to {self.output_file}")

if __name__ == "__main__":
    SAWCSpring2026URL().run()
