# Step 1: Go to url  (Done)
# Step 2: Click on tab 
# Step 3: Click session header button
# Step 4: Extract Info
# Step 5: Click on next tab
# Step 6: Repeat Step 4 and step 5 until there is tab button availble 

import os
import time
from loguru import logger
from scrapers.base import BaseScraper
from scrapers.models import Abstract, AbstractMetadata, Meeting
from utils import safe_click, dismiss_cookie_banner, save_json, load_json
from selenium.webdriver.common.by import By



class SAWCSpring2026(BaseScraper):

    def __init__(self):
        super().__init__(name="SAWC_SUMMER_2026",chrome_version=147)
        self.base_url = "https://www.hmpglobalevents.com/sawcspring/agenda"
        self.output_file = os.path.join("data", "sawc", "sawc_spring_2026.json")
        self.tab_xpath = "//*[@id='hmp-content-tweaks-session-agenda']//ul/li/button"
        self.session_button_xpath = "//div[contains(@class, 'tab-area') and not(contains(@class, 'hidden'))]//button[contains(@class, 'session__header')]"
        self.tab_index = 1
        self.link = "https://www.hmpglobalevents.com/sawcspring/agenda"
        self.meeting_name = "SAWC Spring 2026"
        self.meeting_date = "April 8-11, 2026"
        

        self.selector = {
                        "title": "",
                        "doi": "",
                        "number": "",
                        "author_info": "",
                        "abstract": "-",
                        "abstract_html": "",
                        "abstract_markdown": "",
                        "abstract_metadata": {
                            "session_name": "",
                            "session_track": "",
                            "session_id": "",
                            "session_type": "",
                            "ce_credit": "",
                            "date": "",
                            "session_time": "",
                            "presentation_time": "",
                            "presentation_id": "",
                            "location": "",
                            "session_description": "",
                            "attendance_type": "",
                        },
        }

    
    def click_tab(self,index):
        tab_xpath = f"//*[@id='hmp-content-tweaks-session-agenda']/div[4]/div[1]/ul/li[{index}]/button"
        if self.driver.find_element(By.XPATH, tab_xpath).is_enabled():
            try:
                safe_click(self.driver, tab_xpath, By.XPATH)
                return True
            except Exception as e:
                logger.error(f"Failed to click tab {index}: {e}")
        return False

    def click_session_header_button(self, index):
        """Clicks the session header button by index for the currently active tab."""
        # Use the dynamic session_button_xpath and apply the index
        button_xpath = f"({self.session_button_xpath})[{index}]"
        
        try:
            return safe_click(self.driver, button_xpath, By.XPATH)
        except Exception as e:
            logger.error(f"Failed to click session button {index}: {e}")
            return False

    def extract_abstract_info(self):
        """Extracts information for all abstracts within the currently expanded session."""
        from bs4 import BeautifulSoup
        import re
        
        results = []
        try:
            # 1. Find the currently expanded session main area
            # We look for the session__main that is currently visible
            session_main = self.driver.find_element(By.CSS_SELECTOR, "li.session .session__main:not([style*='display: none'])")
            
            # Get the parent container and header to pull common metadata
            session_li = session_main.find_element(By.XPATH, "./..")
            header = session_li.find_element(By.CSS_SELECTOR, "button.session__header")
            
            session_name = header.find_element(By.CSS_SELECTOR, "h4").text.strip()
            session_time = header.find_element(By.CSS_SELECTOR, ".session__date").text.strip()
            
            try:
                track = session_main.find_element(By.CSS_SELECTOR, ".session__track").text.strip()
            except:
                track = ""
                
            try:
                location = session_main.find_element(By.XPATH, ".//li[contains(@class, 'session-faculty-group') and .//div[contains(text(), 'Room')]]//span[contains(@class, 'faculty-name')]").text.strip()
            except:
                location = ""

            # 2. Check for Sub-sessions (Multiple abstracts case)
            sub_sessions = session_main.find_elements(By.CSS_SELECTOR, "li.sub-session")
            
            if sub_sessions:
                for sub in sub_sessions:
                    sub_title_full = sub.find_element(By.CSS_SELECTOR, ".session__title").text.strip()
                    sub_desc_html = sub.find_element(By.CSS_SELECTOR, ".session__description").get_attribute("innerHTML")
                    
                    # Extract number if present (e.g. "K2.01")
                    number_match = re.match(r"^([A-Z0-9\.]+)\s+", sub_title_full)
                    number = number_match.group(1) if number_match else ""
                    title = sub_title_full.replace(number, "").strip() if number else sub_title_full
                    
                    soup = BeautifulSoup(sub_desc_html, 'html.parser')
                    
                    # Create the item
                    metadata = AbstractMetadata(
                        session_name=session_name,
                        session_track=track,
                        date=self.meeting_date,
                        session_time=session_time,
                        location=location,
                        session_type=track
                    )
                    
                    results.append(Abstract(
                        link=self.driver.current_url,
                        title=title,
                        number=number,
                        abstract=soup.get_text(separator="\n").strip(),
                        abstract_html=sub_desc_html,
                        abstract_metadata=metadata
                    ))
            else:
                # 3. Single Session Case
                try:
                    desc_element = session_main.find_element(By.CSS_SELECTOR, ".session__description")
                    desc_html = desc_element.get_attribute("innerHTML")
                    soup = BeautifulSoup(desc_html, 'html.parser')
                    abstract_text = soup.get_text(separator="\n").strip()
                except:
                    desc_html = ""
                    abstract_text = "-"

                metadata = AbstractMetadata(
                    session_name=session_name,
                    session_track=track,
                    date=self.meeting_date,
                    session_time=session_time,
                    location=location,
                    session_type=track
                )
                
                results.append(Abstract(
                    link=self.driver.current_url,
                    title=session_name,
                    abstract=abstract_text,
                    abstract_html=desc_html,
                    abstract_metadata=metadata
                ))
                
        except Exception as e:
            logger.error(f"Error during extraction: {e}")

        return results


    def save_incremental(self, new_abstracts):
        """Saves new abstracts to the JSON file immediately to prevent data loss."""
        from dataclasses import asdict
        
        # Load existing data or create new Meeting structure
        meeting_dict = load_json(self.output_file)
        if not meeting_dict or "abstracts" not in meeting_dict:
            # Initialize new structure
            meeting_dict = Meeting(
                meeting_name=self.meeting_name,
                date=self.meeting_date,
                link=self.base_url,
                abstracts=[]
            ).to_dict()

        # Add new abstracts (converting objects to dicts)
        for abstract in new_abstracts:
            meeting_dict["abstracts"].append(asdict(abstract))

        # Save back to file
        save_json(meeting_dict, self.output_file)

    def execute(self):
        # Step 1: Initialize and load existing progress
        self.driver.get(self.base_url)
        
        # Load existing titles to skip them
        existing_data = load_json(self.output_file)
        scraped_titles = set()
        if existing_data and "abstracts" in existing_data:
            scraped_titles = {a["title"] for a in existing_data["abstracts"]}
            logger.info(f"Resuming: Found {len(scraped_titles)} already scraped items.")

        time.sleep(3)
        
        # Step 2: Identify Tabs
        tabs = self.driver.find_elements(By.XPATH, self.tab_xpath)
        tabs_count = len(tabs)
        logger.info(f"Detected {tabs_count} tabs on page")

        # Step 3: Loop through Tabs
        for i in range(1, tabs_count + 1):
            logger.info(f"Processing Tab {i} of {tabs_count}")
            if not self.click_tab(i):
                break

            time.sleep(2)
            
            # Find all session buttons in current tab
            session_buttons = self.driver.find_elements(By.XPATH, self.session_button_xpath)
            session_buttons_count = len(session_buttons)
            logger.info(f"Tab {i}: Detected {session_buttons_count} session buttons")

            # Step 4: Loop through sessions
            for j in range(1, session_buttons_count + 1):
                # Before clicking, check if we've already done this one
                try:
                    btn_xpath = f"({self.session_button_xpath})[{j}]"
                    btn = self.driver.find_element(By.XPATH, btn_xpath)
                    title = btn.find_element(By.CSS_SELECTOR, "h4").text.strip()
                    
                    if title in scraped_titles:
                        logger.info(f"  Skipping session {j}: '{title}' (Already Scraped)")
                        continue
                except:
                    pass # Continue to click if check fails

                logger.info(f"  Scraping session {j} of {session_buttons_count}...")
                if not self.click_session_header_button(j):
                    continue 
                
                time.sleep(1.5)
                
                # Extract and save immediately
                abstract_list = self.extract_abstract_info()
                if abstract_list:
                    self.save_incremental(abstract_list)
                    # Add to memory cache to avoid re-scraping in the same run
                    for a in abstract_list:
                        scraped_titles.add(a.title)
                    logger.info(f"    Saved {len(abstract_list)} abstracts incrementally.")

            time.sleep(1)

        logger.info(f"Scraping complete. Results saved to {self.output_file}")


if __name__=="__main__":
    SAWCSpring2026().run()
