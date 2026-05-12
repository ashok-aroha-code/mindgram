import os
import time
import random
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import safe_click
from scrapers.base import BaseScraper

class SAWCSpring2026(BaseScraper):
    def __init__(self):
        super().__init__(name="SAWCSpring2026")
        self.output_file = os.path.join("data", "sawc", "sawc_spring_2026", "sawc_spring_2026_links.json")
        self.base_url = "https://www.hmpglobalevents.com/sawcspring/agenda"
        self.all_articles = []

    def execute(self):
        logger.info("Starting SAWCSpring2026 scraper...")
        self.driver.get(self.base_url)

        safe_click(self.driver, "#hmp-content-tweaks-session-agenda > div.agenda-view.agenda-session-groups > div.tabs-wrapper > ul > li:nth-child(1) > button")
        
        while self.driver.find_element(By.XPATH, "#hmp-content-tweaks-session-agenda > div.agenda-view.agenda-session-groups > div.tabs-wrapper > button.tabs-wrapper__arrow.tabs-wrapper__arrow--next").is_enabled():
            safe_click(self.driver, "#hmp-content-tweaks-session-agenda > div.agenda-view.agenda-session-groups > div.tabs-wrapper > button.tabs-wrapper__arrow.tabs-wrapper__arrow--next")
        

if __name__ == "__main__":
    print("Starting scraper...")
    
    
