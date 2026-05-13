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
from utils import (
    safe_click, 
    dismiss_cookie_banner, 
    save_json, 
    load_json,
    extract_ce_credits,
    clean_html_text,
    normalize_authors,
    smart_split_html
)
from selenium.webdriver.common.by import By



class SAWCSpring2026(BaseScraper):

    def __init__(self):
        super().__init__(name="SAWC_SUMMER_2026",chrome_version=147)
        self.base_url = "https://www.hmpglobalevents.com/sawcspring/agenda"
        self.output_file = os.path.join("data", "sawc", "sawc_spring_2026.json")
        self.tab_xpath = "//div[contains(@class, 'tabs-wrapper')]//button[@aria-role='tab']"
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
                            "attendance_type": ""
                        }
        }

    
    def click_tab(self, index):
        """Clicks a tab by index with retry logic."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Use the class-level tab_xpath which is more robust
        tab_xpath = f"({self.tab_xpath})[{index}]"
        
        try:
            # Wait up to 10 seconds for the tab to be clickable
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, tab_xpath)))
            return safe_click(self.driver, tab_xpath, By.XPATH)
        except Exception as e:
            logger.error(f"Failed to click tab {index} using {tab_xpath}: {e}")
            return False

    def click_session_header_button(self, index):
        """Clicks the session header button by index for the currently active tab."""
        button_xpath = f"({self.session_button_xpath})[{index}]"
        
        try:
            return safe_click(self.driver, button_xpath, By.XPATH)
        except Exception as e:
            logger.error(f"Failed to click session button {index}: {e}")
            return False

    def extract_abstract_info(self, session_li):
        """Extracts information for all abstracts within a specific session element."""
        results = []
        try:
            # Get the header and main area for this specific session
            header = session_li.find_element(By.CSS_SELECTOR, "button.session__header")
            session_main = session_li.find_element(By.CSS_SELECTOR, ".session__main")
            
            session_name = header.find_element(By.CSS_SELECTOR, "h4").text.strip()
            session_time = header.find_element(By.CSS_SELECTOR, ".session__date").text.strip()
            
            # CE Credits (Using Utility)
            ce_credit = extract_ce_credits(session_name)

            try:
                track = session_main.find_element(By.CSS_SELECTOR, ".session__track").text.strip()
            except:
                track = ""
                
            try:
                location_el = session_main.find_element(By.XPATH, ".//li[contains(@class, 'session-faculty-group') and .//div[contains(text(), 'Room')]]//span[contains(@class, 'faculty-name')]")
                location = location_el.text.strip()
            except:
                location = ""

            # Extract main authors (Using Utility)
            raw_authors = []
            try:
                faculty_names = session_main.find_elements(By.CSS_SELECTOR, "a.faculty-name, span.faculty-name")
                raw_authors = [f.text.strip() for f in faculty_names if f.text.strip()]
            except:
                pass
            main_author_info = normalize_authors(raw_authors, exclude_keywords=["Room"])

            # 1. Check for Formal Sub-sessions
            sub_sessions = session_main.find_elements(By.CSS_SELECTOR, "li.sub-session")
            
            if sub_sessions:
                for sub in sub_sessions:
                    sub_title_full = sub.find_element(By.CSS_SELECTOR, ".session__title").text.strip()
                    try:
                        sub_desc_html = sub.find_element(By.CSS_SELECTOR, ".session__description").get_attribute("innerHTML")
                    except:
                        sub_desc_html = ""
                    
                    # Split title into number and text
                    sub_title_blocks = smart_split_html(f"<b>{sub_title_full}</b>")
                    title = sub_title_blocks[0]["title"] if sub_title_blocks else sub_title_full
                    number = sub_title_blocks[0]["number"] if sub_title_blocks else ""
                    
                    metadata = AbstractMetadata(
                        session_name=session_name,
                        session_track=track,
                        date=self.meeting_date,
                        session_time=session_time,
                        location=location,
                        session_type=track,
                        ce_credit=ce_credit
                    )
                    
                    results.append(Abstract(
                        link=self.driver.current_url,
                        title=title,
                        number=number,
                        author_info=main_author_info,
                        abstract=clean_html_text(sub_desc_html),
                        abstract_html=sub_desc_html,
                        abstract_metadata=metadata
                    ))
            else:
                # 2. Check for "Embedded" Abstracts (Oral Abstracts style)
                try:
                    desc_element = session_main.find_element(By.CSS_SELECTOR, ".session__description")
                    desc_html = desc_element.get_attribute("innerHTML")
                except:
                    desc_html = ""
                
                # Use Smart Splitter for embedded abstracts
                abstract_blocks = smart_split_html(desc_html)
                
                if len(abstract_blocks) > 1:
                    for block in abstract_blocks:
                        metadata = AbstractMetadata(
                            session_name=session_name,
                            session_track=track,
                            date=self.meeting_date,
                            session_time=session_time,
                            location=location,
                            ce_credit=ce_credit
                        )
                        
                        results.append(Abstract(
                            link=self.driver.current_url,
                            title=block["title"],
                            number=block["number"],
                            author_info=main_author_info,
                            abstract=block["text"],
                            abstract_html=block["html"],
                            abstract_metadata=metadata
                        ))
                else:
                    # 3. Single Session Case
                    metadata = AbstractMetadata(
                        session_name=session_name,
                        session_track=track,
                        date=self.meeting_date,
                        session_time=session_time,
                        location=location,
                        session_type=track,
                        ce_credit=ce_credit
                    )
                    
                    results.append(Abstract(
                        link=self.driver.current_url,
                        title=session_name,
                        author_info=main_author_info,
                        abstract=clean_html_text(desc_html),
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
                
                # Extract and save immediately (passing the specific session element)
                try:
                    session_li = self.driver.find_element(By.XPATH, f"({self.session_button_xpath})[{j}]/ancestor::li[contains(@class, 'session')]")
                    abstract_list = self.extract_abstract_info(session_li)
                except Exception as e:
                    logger.error(f"Failed to find session element for extraction: {e}")
                    continue

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
