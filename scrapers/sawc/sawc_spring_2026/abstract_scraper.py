# Step 1: Go to url  (Done)
# Step 2: Click on tab 
# Step 3: Click session header button
# Step 4: Extract Info
# Step 5: Click on next tab
# Step 6: Repeat Step 4 and step 5 until there is tab button availble 

import os
import re   
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

    def __init__(self, **kwargs):
        super().__init__(name="SAWC_SPRING_2026", chrome_version=147, **kwargs)
        self.base_url = "https://www.hmpglobalevents.com/sawcspring/agenda"
        self.meeting_name = "SAWC_Spring"
        self.year = "2026"
        
        # New hierarchical output files
        self.urls_file = os.path.join("data", "sawc", f"{self.meeting_name}_{self.year}_urls.json")
        self.raw_file = os.path.join("data", "sawc", f"{self.meeting_name}_{self.year}_raw.json")
        self.duplicates_file = os.path.join("data", "sawc", f"{self.meeting_name}_{self.year}_duplicates.json")
        self.output_file = os.path.join("data", "sawc", f"{self.meeting_name}_{self.year}.json")
        
        self.tab_xpath = "//div[contains(@class, 'tabs-wrapper')]//button[@aria-role='tab']"
        self.session_button_xpath = "//div[contains(@class, 'tab-area') and not(contains(@class, 'hidden'))]//button[contains(@class, 'session__header')]"
        self.meeting_date = "April 8-11, 2026"

    def click_tab(self, index):
        """Clicks a tab by index with retry logic."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        tab_xpath = f"({self.tab_xpath})[{index}]"
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, tab_xpath)))
            return safe_click(self.driver, tab_xpath, By.XPATH)
        except Exception as e:
            logger.error(f"Failed to click tab {index}: {e}")
            return False

    def click_session_header_button(self, index):
        """Clicks the session header button by index for the currently active tab."""
        button_xpath = f"({self.session_button_xpath})[{index}]"
        try:
            return safe_click(self.driver, button_xpath, By.XPATH)
        except Exception as e:
            logger.error(f"Failed to click session button {index}: {e}")
            return False

    def extract_abstract_info(self, session_li, expected_title=""):
        """Extracts information for all abstracts within a specific session element."""
        results = []
        try:
            # Get the header and main area for this specific session
            header = session_li.find_element(By.CSS_SELECTOR, "button.session__header")
            session_main = session_li.find_element(By.CSS_SELECTOR, ".session__main")
            
            session_name_orig = header.find_element(By.CSS_SELECTOR, "h4").text.strip()
            session_time = header.find_element(By.CSS_SELECTOR, ".session__date").text.strip()
            
            # Use expected title as fallback if header is empty or missing
            if not session_name_orig and expected_title:
                session_name_orig = expected_title
            
            # CE Credits
            ce_credit = extract_ce_credits(session_name_orig)

            # 2. Extract Metadata (Extract Location first to use it for filtering authors)
            location = ""
            try:
                # Multiple strategies for Room/Location extraction
                # 1. Look for specific classes
                room_els = session_main.find_elements(By.CSS_SELECTOR, ".session-room, .room, .location, .session__room")
                for r in room_els:
                    txt = r.text.strip()
                    if txt and not any(k in txt.lower() for k in ["faculty", "speaker"]):
                        location = txt.replace("Room", "").strip()
                        break
                
                if not location:
                    # 2. Look for "Room" label followed by text
                    try:
                        room_text = self.driver.execute_script("""
                            var node = document.evaluate("//*[contains(text(), 'Room') or contains(text(), 'Location')]", arguments[0], null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                            if (node) {
                                var txt = node.parentElement.innerText;
                                return txt.replace(/Room|Location/gi, '').trim();
                            }
                            return '';
                        """, session_main)
                        location = room_text
                    except: pass
            except: pass

            # Extract Authors and Affiliations in strict format: 'name; affiliation, name; affiliation'
            author_info_list = []
            try:
                # Target all possible faculty groups
                faculty_groups = session_main.find_elements(By.CSS_SELECTOR, ".session-faculty, .session-faculty-group, .faculty-group, li:has(.faculty-name)")
                
                for group in faculty_groups:
                    # CHECK for Room label
                    try:
                        group_label = group.find_element(By.CSS_SELECTOR, ".faculty-group-name, .session-faculty-group-name").text.strip()
                        if "Room" in group_label:
                            continue
                    except: pass

                    # Find all name elements in this group
                    names_in_el = group.find_elements(By.CSS_SELECTOR, ".faculty-name, a[href*='/faculty/']")
                    for name_el in names_in_el:
                        try:
                            name = name_el.text.strip()
                            # Skip if name is just a number (often room numbers) or empty
                            if not name or name.isdigit() or any(kw in name for kw in ["Room", "Location", "Faculty:", "ISS Speaker", "Moderator"]):
                                continue
                            
                            # If the name matches our location, skip it
                            if location and name.lower() in location.lower():
                                continue
                                
                            # Try to find credentials/titles in the parent container
                            parent = name_el.find_element(By.XPATH, "./..")
                            try:
                                # Try specific credential class first
                                cred_els = parent.find_elements(By.CSS_SELECTOR, ".faculty-credentials, .faculty-title")
                                if not cred_els:
                                    # Fallback: check all elements that aren't the name
                                    cred_els = parent.find_elements(By.XPATH, ".//*[contains(@class, 'faculty-') and not(contains(@class, 'name'))]")
                                
                                if not cred_els:
                                    # Second Fallback: text after name
                                    all_text = parent.text.strip()
                                    title = all_text.replace(name, "").strip().strip(",").strip()
                                else:
                                    title = " ".join([t.text.strip() for t in cred_els if t.text.strip()])
                            except:
                                title = ""
                            
                            # Final Author String
                            author_str = f"{name}; {title}" if title else name
                            
                            # STRIP trailing location info from the string itself
                            # e.g. "John Doe; MD, Richardson A" -> "John Doe; MD"
                            for kw in noise_keywords:
                                author_str = re.sub(rf"[, ]+{kw}.*$", "", author_str, flags=re.IGNORECASE)
                            
                            author_info_list.append(author_str)
                        except:
                            continue
            except:
                pass

            # Final Cleanup of Authors
            seen_authors = set()
            unique_authors = []
            
            # Common Room/Location keywords to exclude from authors
            noise_keywords = ["richardson", "ballroom", "hall", "room", "location", "center", "convention", "moderator", "speaker", "faculty:"]
            
            for a in author_info_list:
                a_clean = a.strip().strip(",").strip()
                if not a_clean:
                    continue
                
                # Check for noise
                is_noise = False
                a_lower = a_clean.lower()
                
                # 1. Check against extracted location
                if location and (location.lower() in a_lower or a_lower in location.lower()):
                    is_noise = True
                
                # 2. Check against known noise keywords (common room names)
                if not is_noise and any(kw in a_lower for kw in noise_keywords):
                    # Be careful not to exclude real names that might contain these strings
                    # Usually room names are short or have a single letter/number
                    if len(a_clean) < 25 or re.search(r'[A-Z] [A-Z]$|\d+$', a_clean):
                        is_noise = True
                
                if not is_noise and a_lower not in seen_authors:
                    # Remove trailing numeric noise or dangling commas
                    clean_a = re.sub(r'[, ]+\d+$', '', a_clean)
                    clean_a = re.sub(r',+', ',', clean_a).strip().strip(",").strip()
                    
                    if clean_a and len(clean_a) > 2:
                        unique_authors.append(clean_a)
                        seen_authors.add(a_lower)
            
            main_author_info = ", ".join(unique_authors)

            # Check for Formal Sub-sessions
            sub_sessions = session_main.find_elements(By.CSS_SELECTOR, "li.sub-session")
            
            if sub_sessions:
                for sub in sub_sessions:
                    sub_title_full = sub.find_element(By.CSS_SELECTOR, ".session__title").text.strip()
                    try:
                        sub_desc_html = sub.find_element(By.CSS_SELECTOR, ".session__description").get_attribute("innerHTML")
                    except:
                        sub_desc_html = ""
                    
                    # Use a stricter pattern for abstract numbers (e.g. PI-023, CR-014) 
                    # to avoid splitting words like "Learning" into "L" and "earning"
                    sub_title_blocks = smart_split_html(f"<b>{sub_title_full}</b>", number_pattern=r"^[A-Z]{2,}-\d+")
                    title = sub_title_blocks[0]["title"] if sub_title_blocks else sub_title_full
                    number = sub_title_blocks[0]["number"] if sub_title_blocks else ""
                    
                    # Ignore 'Learning Objectives' as a standalone sub-title
                    if "learning objectives" in title.lower():
                        continue

                    metadata = AbstractMetadata(
                        session_name="", # Not required per user request
                        session_track="",
                        session_type="",
                        date=self.meeting_date,
                        session_time=session_time,
                        ce_credit=ce_credit,
                        location=location
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
                # 2. Check for "Embedded" Abstracts
                try:
                    desc_element = session_main.find_element(By.CSS_SELECTOR, ".session__description")
                    desc_html = desc_element.get_attribute("innerHTML")
                except:
                    desc_html = ""
                
                abstract_blocks = smart_split_html(desc_html, number_pattern=r"^[A-Z]{2,}-\d+")
                
                # Filter blocks that are too short or just headers
                valid_blocks = [b for b in abstract_blocks if len(b["text"]) > 100 or b["number"]]
                
                if len(valid_blocks) > 1:
                    for block in valid_blocks:
                        # Ignore 'Learning Objectives' as a standalone sub-title
                        if "learning objectives" in block["title"].lower():
                            continue

                        metadata = AbstractMetadata(
                            session_name="",
                            session_track="",
                            session_type="",
                            date=self.meeting_date,
                            session_time=session_time,
                            ce_credit=ce_credit,
                            location=location
                        )
                        
                        results.append(Abstract(
                            link=self.driver.current_url,
                            title=block["title"] or session_name_orig,
                            number=block["number"],
                            author_info=main_author_info,
                            abstract=block["text"],
                            abstract_html=block["html"],
                            abstract_metadata=metadata
                        ))
                else:
                    # 3. Single Session Case
                    metadata = AbstractMetadata(
                        session_name="",
                        session_track="",
                        session_type="",
                        date=self.meeting_date,
                        session_time=session_time,
                        ce_credit=ce_credit,
                        location=location
                    )
                    
                    results.append(Abstract(
                        link=self.driver.current_url,
                        title=session_name_orig,
                        author_info=main_author_info,
                        abstract=clean_html_text(desc_html),
                        abstract_html=desc_html,
                        abstract_metadata=metadata
                    ))
                
        except Exception as e:
            logger.error(f"Error during extraction: {e}")

        return results

    def save_incremental(self, new_abstracts):
        """Saves to raw and final files, filtering empty metadata."""
        from dataclasses import asdict
        
        for file_path in [self.raw_file, self.output_file]:
            data = load_json(file_path)
            if not data or "abstracts" not in data:
                data = Meeting(meeting_name=self.meeting_name, date=self.year, link=self.base_url).to_dict()

            for abstract in new_abstracts:
                d = asdict(abstract)
                if file_path == self.output_file:
                    # Filter out empty fields from abstract_metadata for the final file
                    meta = d.get("abstract_metadata", {})
                    d["abstract_metadata"] = {k: v for k, v in meta.items() if v != "" and v != []}
                data["abstracts"].append(d)

            save_json(data, file_path)

    def detect_duplicates(self):
        """Identifies duplicates for human analysis."""
        data = load_json(self.raw_file)
        if not data or "abstracts" not in data:
            return
            
        abstracts = data["abstracts"]
        seen = {}
        duplicates = []
        
        for a in abstracts:
            keys = []
            if a.get("link"): keys.append(a["link"])
            if a.get("doi"): keys.append(a["doi"])
            if a.get("number") and a.get("title"):
                keys.append(f"{a['number']}_{a['title']}".lower())
            
            is_dup = False
            for k in keys:
                if k in seen:
                    duplicates.append({
                        "reason": f"Matched key: {k}",
                        "entry_1": seen[k],
                        "entry_2": a
                    })
                    is_dup = True
                    break
            
            if not is_dup:
                for k in keys:
                    seen[k] = a
                    
        if duplicates:
            save_json({"duplicates": duplicates}, self.duplicates_file)
            logger.info(f"Found {len(duplicates)} duplicate entries. Saved to {self.duplicates_file}")

    def execute(self):
        # Log the raw file path so the GUI monitors the correct file for live updates
        logger.info(f"[OUTPUT_PATH] {self.raw_file}")
        
        # Step 1: Read URLs from file
        if not os.path.exists(self.urls_file):
            logger.error(f"URLs file not found: {self.urls_file}. Run url_scraper.py first.")
            return

        url_data = load_json(self.urls_file)
        if not url_data:
            logger.error(f"No URLs found in {self.urls_file}")
            return

        logger.info(f"Loaded {len(url_data)} sessions to scrape.")

        # Step 2: Load existing progress from RAW file
        scraped_keys = set()
        existing_raw = load_json(self.raw_file)
        if existing_raw and "abstracts" in existing_raw:
            scraped_keys = {(a["link"], a["title"]) for a in existing_raw["abstracts"]}
            logger.info(f"Resuming: {len(scraped_keys)} items already in raw file.")

        self.driver.get(self.base_url)
        time.sleep(3)

        current_tab = -1
        
        for entry in url_data:
            title = entry["title"]
            tab_idx = entry["tab_index"]
            sess_idx = entry["session_index"]
            link = entry["url"]

            if (link, title) in scraped_keys:
                continue

            logger.info(f"Scraping session: {title}")

            # Navigate to correct tab if needed
            if tab_idx != current_tab:
                if not self.click_tab(tab_idx):
                    logger.error(f"Could not click tab {tab_idx}")
                    continue
                current_tab = tab_idx
                # Wait for tab content to load
                time.sleep(2)
                try:
                    from utils import wait_for_element
                    wait_for_element(self.driver, self.session_button_xpath, By.XPATH, timeout=10)
                except: pass

            # Click session button
            if self.click_session_header_button(sess_idx):
                time.sleep(1.5)
                try:
                    session_li = self.driver.find_element(By.XPATH, f"({self.session_button_xpath})[{sess_idx}]/ancestor::li[contains(@class, 'session')]")
                    abstract_list = self.extract_abstract_info(session_li, expected_title=title)
                    if abstract_list:
                        # Save only to RAW file per FLOW.md
                        self.save_raw_incremental(abstract_list)
                        for a in abstract_list: 
                            scraped_keys.add((a.link, a.title))
                except Exception as e:
                    logger.error(f"Extraction failed for {title}: {e}")

        logger.info(f"Scraping complete. Raw data saved to {self.raw_file}")

    def save_raw_incremental(self, new_abstracts):
        """Saves only to the raw file as per abstract_scraper responsibilities."""
        from dataclasses import asdict
        data = load_json(self.raw_file)
        if not data or "abstracts" not in data:
            data = Meeting(meeting_name=self.meeting_name, date=self.year, link=self.base_url).to_dict()

        for abstract in new_abstracts:
            data["abstracts"].append(asdict(abstract))

        save_json(data, self.raw_file)



if __name__=="__main__":
    SAWCSpring2026().run()
