import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from scrapers.sawc.sawc_spring_2026.abstract_scraper import SAWCSpring2026
from selenium.webdriver.common.by import By
import time

def test_extraction():
    scraper = SAWCSpring2026(headless=True)
    scraper.init_driver()
    try:
        scraper.driver.get(scraper.base_url)
        time.sleep(3)
        
        # Click on tab 1
        scraper.click_tab(1)
        time.sleep(2)
        
        # Get the first session
        sess_btn = scraper.driver.find_element(By.XPATH, f"({scraper.session_button_xpath})[1]")
        sess_idx = 1
        
        scraper.click_session_header_button(sess_idx)
        time.sleep(2)
        
        session_li = scraper.driver.find_element(By.XPATH, f"({scraper.session_button_xpath})[{sess_idx}]/ancestor::li[contains(@class, 'session')]")
        
        # Test with empty header title fallback
        results = scraper.extract_abstract_info(session_li, expected_title="TEST FALLBACK TITLE")
        
        print("--- Extraction Results ---")
        for a in results:
            print(f"Title: {a.title}")
            print(f"Number: {a.number}")
            print(f"Authors: {a.author_info}")
            print("-" * 20)
            
    finally:
        scraper.driver.quit()

if __name__ == "__main__":
    test_extraction()
