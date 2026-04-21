import requests
import json
import time
import re
import sys
import random
from pathlib import Path
from datetime import datetime
from html import unescape
from loguru import logger

# Constants
BASE_DIR = Path(r"D:\Workspace\Projects\mindgram")
API_URL = "https://api.asco.org/graphql2"

HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'None',
    'content-type': 'application/json',
    'origin': 'https://meetings.asco.org',
    'referer': 'https://meetings.asco.org/',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'x-api-key': 'da2-wgzqv6hk3bea3axyz6hslo33my'
}

# GraphQL Queries
SEARCH_QUERY = """query search($q: String, $filters: [SearchFilter], $from: Int, $size: Int, $sort: [SearchSort]) {
  search(q: $q, filters: $filters, from: $from, size: $size, sort: $sort) {
    result {
      groups {
        total
        hits {
          contentId
        }
      }
    }
    status
  }
}"""

SESSION_QUERY = """query session($id: String!) {
  session(id: $id) {
    sessionTitle
    sessionType
    sessionLocation
    fullSummary
    attendanceType
    cmeCredits
    sessionDates {
      start
      end
    }
    tracks {
      track
    }
    presentations {
      presentation {
        id
        title
        presentationDates {
          start
          end
        }
        posterBoardNumber
        abstractNumber
        doiUrl {
          path
        }
      }
      abstract {
        abstractTitle
        abstractNumber
        posterBoardNumber
        abstractAuthorsString
        authorInstitutionsString
        fullBody
        doi
        clinicalTrialRegistryNumber
        subTrack {
          subTrack
        }
      }
    }
    persons {
      presentationId
      personId
      firstName
      lastName
      degree
      institution
    }
    status
    errors {
      code
      message
    }
  }
}"""

class ASCO2026AbstractScraper:
    def __init__(self, meeting_id="335", output_file=None):
        self.meeting_id = meeting_id
        # Updated output directory to include v1 as requested
        self.output_dir = BASE_DIR / "data" / "meetings.asco.org" / "asco_2026" / "v1"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = output_file or self.output_dir / "asco_2026_abstracts.json"
        
        # Setup logging with colors
        logger.remove()
        # Console logging with color for levels (ERROR will be red)
        logger.add(sys.stderr, 
                   format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                   level="INFO")
        logger.add(self.output_dir / "scraper.log", rotation="10 MB", level="DEBUG")
        
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def clean_text(self, text):
        """Remove HTML tags and normalize whitespace."""
        if not text or not isinstance(text, str):
            return text or ""
        
        # Unescape HTML entities
        text = unescape(text)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Normalize whitespace (multiple spaces/newlines to single space)
        text = " ".join(text.split())
        return text

    def format_timestamp(self, ts):
        """Format ISO timestamp to date and time."""
        if not ts:
            return "", ""
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
        except:
            return "", ""

    def post_query(self, query, variables, retries=3):
        """Send a GraphQL POST request with retries."""
        payload = {
            "query": " ".join(query.split()),
            "variables": variables
        }
        for attempt in range(retries):
            try:
                response = self.session.post(API_URL, json=payload, timeout=30)
                if response.status_code == 403:
                    logger.warning(f"403 Forbidden on attempt {attempt + 1}. Retrying with backoff...")
                    time.sleep(5 * (attempt + 1) + random.uniform(1, 5))
                    continue
                    
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Request failed (Attempt {attempt + 1}/{retries}): {e}")
                time.sleep(2 * (attempt + 1))
        return None

    def fetch_all_session_ids(self):
        """Discover all session IDs for the meeting using the search API."""
        logger.info("Discovering session IDs via search API...")
        variables = {
            "q": "",
            "filters": [
                {"field": "meetingId", "value": self.meeting_id},
                {"field": "contentType", "value": "Session"}
            ],
            "from": 0,
            "size": 1000,
            "sort": [{"field": "sessionDate", "order": "asc"}]
        }
        
        data = self.post_query(SEARCH_QUERY, variables)
        if not data:
            return []
            
        hits = []
        try:
            groups = data.get("data", {}).get("search", {}).get("result", {}).get("groups", [])
            for group in groups:
                hits.extend(group.get("hits", []))
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
            
        session_ids = [hit.get("contentId") for hit in hits if hit.get("contentId")]
        logger.info(f"Discovered {len(session_ids)} session IDs.")
        return session_ids

    def extract_presentation_id(self, pres_data):
        """Extract the simple numeric ID from the presentation ID."""
        raw_id = pres_data.get("id") or ""
        if "::" in raw_id:
            return raw_id.split("::")[-1]
        return raw_id

    def parse_author_info(self, raw_persons, presentation_id):
        """Parse persons data into a formatted author string."""
        if not raw_persons:
            return ""
            
        presentation_persons = [p for p in raw_persons if p.get("presentationId") == presentation_id]
        if not presentation_persons:
            # Try to match without prefixes if needed
            presentation_persons = [p for p in raw_persons if self.extract_presentation_id(p) == presentation_id]
            
        authors = []
        for p in presentation_persons:
            name = f"{p.get('firstName', '')} {p.get('lastName', '')}".strip()
            degree = p.get('degree')
            if degree:
                name = f"{name}, {degree}"
            inst = p.get('institution')
            if inst:
                authors.append(f"{name}; {inst}")
            else:
                authors.append(name)
        
        return ", ".join(authors)

    def process_session(self, session_id):
        """Fetch and process a single session's data."""
        variables = {"id": session_id}
        data = self.post_query(SESSION_QUERY, variables)
        
        if not data:
            return []
            
        session_res = data.get("data", {}).get("session")
        if not session_res:
            logger.warning(f"No session data found for ID {session_id}")
            return []

        session_name = self.clean_text(session_res.get("sessionTitle"))
        session_type = self.clean_text(session_res.get("sessionType"))
        location = self.clean_text(session_res.get("sessionLocation"))
        ce_credit = self.clean_text(str(session_res.get("cmeCredits") or ""))
        session_description = self.clean_text(session_res.get("fullSummary"))
        attendance_type = self.clean_text(session_res.get("attendanceType"))
        raw_persons = session_res.get("persons", [])
        
        tracks = [self.clean_text(t.get("track")) for t in session_res.get("tracks", []) if t.get("track")]
        session_track = " ".join(tracks)

        s_dates = session_res.get("sessionDates") or {}
        s_date, s_start_time = self.format_timestamp(s_dates.get("start"))
        _, s_end_time = self.format_timestamp(s_dates.get("end"))
        session_time = f"{s_start_time} - {s_end_time}" if s_start_time and s_end_time else (s_start_time or "")

        abstracts = []
        presentations = session_res.get("presentations", [])
        
        for pres_item in presentations:
            pres = pres_item.get("presentation") or {}
            abs_data = pres_item.get("abstract") or {}
            
            title = self.clean_text(pres.get("title") or abs_data.get("abstractTitle") or "")
            if not title:
                continue

            pres_id = self.extract_presentation_id(pres)
            
            # Extract DOI from various possible locations
            doi = self.clean_text(abs_data.get("doi") or (pres.get("doiUrl") or {}).get("path") or "")
            
            # Author info from persons data (more detailed)
            author_info = self.parse_author_info(raw_persons, pres_id)
            
            # Fallback author info from abstract data
            if not author_info:
                authors_str = self.clean_text(abs_data.get("abstractAuthorsString"))
                inst_str = self.clean_text(abs_data.get("authorInstitutionsString"))
                if authors_str and inst_str:
                    author_info = f'"{authors_str}"; "{inst_str}"'
                else:
                    author_info = authors_str or inst_str or ""

            # Presentation time
            p_dates = pres.get("presentationDates") or {}
            _, p_start_time = self.format_timestamp(p_dates.get("start"))
            _, p_end_time = self.format_timestamp(p_dates.get("end"))
            pres_time = f"{p_start_time} - {p_end_time}" if p_start_time and p_end_time else (p_start_time or "")

            abstract_number = self.clean_text(pres.get("abstractNumber") or abs_data.get("abstractNumber") or "")
            poster_board = self.clean_text(pres.get("posterBoardNumber") or abs_data.get("posterBoardNumber") or "")
            sub_track = self.clean_text((abs_data.get("subTrack") or {}).get("subTrack") or "")
            clinical_trial = self.clean_text(str(abs_data.get("clinicalTrialRegistryNumber") or ""))
            
            # Abstract Body
            full_body = abs_data.get("fullBody") or ""
            abstract_text = self.clean_text(full_body) if full_body else "-"

            abstract_obj = {
                "link": f"https://meetings.asco.org/meetings/2026-asco-annual-meeting/{self.meeting_id}/{session_id}",
                "title": title,
                "doi": doi,
                "number": "", # Consistent with legacy structure
                "author_info": author_info,
                "abstract": abstract_text,
                "abstract_html": full_body if full_body else "",
                "abstract_markdown": "",
                "abstract_metadata": {
                    "sub_track": sub_track,
                    "session_name": session_name,
                    "session_track": session_track,
                    "abstract_number": abstract_number,
                    "poster_board_number": poster_board,
                    "session_id": session_id,
                    "session_type": session_type,
                    "ce_credit": ce_credit,
                    "date": s_date,
                    "session_time": session_time,
                    "presentation_time": pres_time,
                    "presentation_id": pres_id,
                    "location": location,
                    "session_description": session_description,
                    "attendance_type": attendance_type,
                    "clinical_TrialRegistry_Number": clinical_trial
                }
            }
            abstracts.append(abstract_obj)
            
        return abstracts

    def load_existing_data(self):
        """Load existing data to avoid duplicates."""
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("abstracts", [])
            except:
                return []
        return []

    def run(self, session_ids=None):
        """Main execution loop."""
        if session_ids is None:
            # Try dynamic fetch first
            session_ids = self.fetch_all_session_ids()
            
            # Fallback to loading from legacy folder if API fails
            if not session_ids:
                ids_file = Path(r"D:\Workspace\Projects\mindgram\legacy\Done VH 2 ASCO 2026 Annual Meeting\session_ids.json")
                if ids_file.exists():
                    with open(ids_file, 'r') as f:
                        session_ids = json.load(f)
                    logger.info(f"Loaded {len(session_ids)} session IDs from legacy folder.")
                else:
                    logger.error("No session IDs found.")
                    return

        # Initialize existing data trackers
        existing_abstracts = self.load_existing_data()
        existing_keys = set()
        if isinstance(existing_abstracts, list):
            for abs_obj in existing_abstracts:
                s_id = abs_obj.get("abstract_metadata", {}).get("session_id", "")
                title = abs_obj.get("title", "")
                existing_keys.add(f"{s_id}|{title}")
        
        all_abstracts = []
        new_count = 0
        duplicate_count = 0

        logger.info(f"Starting crawl for {len(session_ids)} sessions...")
        
        for i, session_id in enumerate(session_ids, 1):
            try:
                abstracts = self.process_session(session_id)
                if abstracts:
                    # Filter out duplicates
                    new_session_abstracts = []
                    for a in abstracts:
                        key = f"{session_id}|{a['title']}"
                        if key not in existing_keys:
                            new_session_abstracts.append(a)
                            existing_keys.add(key)
                        else:
                            duplicate_count += 1
                    
                    if new_session_abstracts:
                        all_abstracts.extend(new_session_abstracts)
                        new_count += len(new_session_abstracts)
                
                if i % 10 == 0 or i == len(session_ids):
                    logger.info(f"[{i}/{len(session_ids)}] Progress: {new_count} new abstracts collected so far...")
                
                # Random sleep between 1 and 3 seconds to avoid rate limits
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                logger.error(f"Error processing session {session_id}: {e}")
        
        # Merge new with existing
        final_abstracts = existing_abstracts + all_abstracts

        # Strictly match the requested format
        final_output = {
            "meeting_name": "ASCO 2026 Annual Meeting",
            "date": "2026-05-26",
            "link": "https://meetings.asco.org",
            "abstracts": final_abstracts
        }
        
        logger.info(f"Crawl complete. New: {new_count}, Skipped: {duplicate_count}, Total in file: {len(final_abstracts)}")
        
        # Save to file
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(final_output, f, indent=4, ensure_ascii=False)
            logger.success(f"Successfully saved {new_count} new abstracts (Total: {len(final_abstracts)}) to {self.output_file}")
        except Exception as e:
            logger.error(f"Failed to save data: {e}")

if __name__ == "__main__":
    scraper = ASCO2026AbstractScraper()
    scraper.run()
