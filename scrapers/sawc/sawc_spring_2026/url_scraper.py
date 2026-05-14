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
        logger.info("Waiting for agenda to load...")
        time.sleep(8)
        
        url_data = []
        tab_ids = [
            "wednesday-april-08-2026",
            "thursday-april-09-2026",
            "friday-april-10-2026",
            "saturday-april-11-2026",
            "sunday-april-12-2026"
        ]

        for i, day_id in enumerate(tab_ids, 1):
            try:
                logger.info(f"Processing Tab {i} ({day_id})...")
                # Click the tab button
                tab_xpath = f"(//div[contains(@class, 'tabs-wrapper')]//button[@aria-role='tab'])[{i}]"
                tab_btn = self.driver.find_element(By.XPATH, tab_xpath)
                self.driver.execute_script("arguments[0].click();", tab_btn)
                time.sleep(3) # Wait for content to swap
                
                # Find the specific area by ID
                area = self.driver.find_element(By.ID, day_id)
                
                # Scroll within the area or just find all sessions
                sessions = area.find_elements(By.CSS_SELECTOR, ".session")
                logger.info(f"Found {len(sessions)} sessions in tab {i}")
                
                for j, session in enumerate(sessions, 1):
                    try:
                        header = session.find_element(By.CSS_SELECTOR, ".session__header")
                        title = header.find_element(By.CSS_SELECTOR, "h4").text.strip()
                        
                        try:
                            time_info = session.find_element(By.CSS_SELECTOR, ".session__time").text.strip()
                        except:
                            time_info = ""

                        url_data.append({
                            "title": title,
                            "time": time_info,
                            "tab_index": i,
                            "session_index": j,
                            "url": self.base_url
                        })
                    except: continue
            except Exception as e:
                logger.error(f"Error on tab {i}: {e}")
                
        save_json(url_data, self.output_file)
        logger.info(f"Collected {len(url_data)} total sessions. Saved to {self.output_file}")

if __name__ == "__main__":
    SAWCSpring2026URL().run()
