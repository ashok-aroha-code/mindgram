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
from utils import safe_click, dismiss_cookie_banner, save_json
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


    def execute(self):
        # Step 1: Go to url 
        self.driver.get(self.base_url)
        abstracts = []
        
        # logger.info("Dismiss cookie banner")
        # dismiss_cookie_banner()
        # time.sleep(3)


        logger.info("Counting tabs..")
        logger.info(f'Tab XPATH {self.tab_xpath}')
        tabs = self.driver.find_elements(By.XPATH, self.tab_xpath)
        tabs_count = len(tabs)
        logger.info(f"Detected {tabs_count} tabs on page")


        # Step 2: Click on tab 
        for i in range(1, tabs_count + 1):
            logger.info(f"Processing Tab {i} of {tabs_count}")
            if not self.click_tab(i):
                break

            # Wait for tab content to transition (class 'hidden' to be removed)
            time.sleep(2)
            
            session_buttons = self.driver.find_elements(By.XPATH, self.session_button_xpath)
            session_buttons_count = len(session_buttons)
            logger.info(f"Tab {i}: Detected {session_buttons_count} session buttons")

            # Step 3: Loop through session buttons and extract info
            for j in range(1, session_buttons_count + 1):
                logger.info(f"  Clicking session button {j} of {session_buttons_count}")
                if not self.click_session_header_button(j):
                    continue # Try next button if this one fails
                
                # Small wait to allow session info to expand
                time.sleep(1.5)
                
                # Get abstract data object (returns a list)
                abstract_list = self.extract_abstract_info()
                if abstract_list:
                    abstracts.extend(abstract_list)
                    logger.info(f"    Extracted {len(abstract_list)} abstracts from this session")

                # Optional: Close the session again to keep the page clean
                # self.click_session_header_button(j) 
                break
            
            time.sleep(1)
            break

        # Step 4: Bundle everything into the Meeting model and save
        meeting = Meeting(
            meeting_name=self.meeting_name,
            date=self.meeting_date,
            link=self.base_url,
            abstracts=abstracts
        )

        logger.info(f"Scraping complete. Total abstracts: {len(abstracts)}")
        save_json(meeting.to_dict(), self.output_file)

if __name__=="__main__":
    SAWCSpring2026().run()
