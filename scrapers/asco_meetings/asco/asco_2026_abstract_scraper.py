import requests
import json
import time
import re
import os
import sys
from datetime import datetime
from pathlib import Path
from html import unescape
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

# Fix sys.path to allow imports from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

# GraphQL endpoint
API_URL = "https://api.asco.org/graphql2"

# Headers from legacy scripts
HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyMDIzMDEwMSIsIm5hbWUiOiJQdWJsaWNBY2Nlc3MiLCJzY29wZSI6ImFwaS5hc2NvLm9yZy9ncmFwaHFsLnB1YmxpYyIsImNsaWVudF9pZCI6InB1YmxpYyIsImlhdCI6MTY3MjUzMTIwMH0.8aei14SeARjdpov618hKodzJLwnQuW6c4WuBg6PZPcU',
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
    errors {
      code
      message
    }
  }
}"""

GET_SESSION_QUERY = """query getSession($sessionId: String!) {
  session(sessionId: $sessionId) {
    result {
      contentId
      title
      sessionType
      sessionLocation
      cmeCredits
      fullSummary
      attendanceType
      sessionDates {
        start
        end
        timeZone
      }
      tracks {
        track
      }
      presentations {
        contentId
        presentation {
          title
          abstractNumber
          posterBoardNumber
          presentationDates {
            start
            end
            timeZone
          }
          disclosureUrl {
            queryParams
          }
          doiUrl {
            path
          }
        }
        abstract {
          abstractAuthorsString
          authorInstitutionsString
          subTrack {
            subTrack
          }
          doi
          abstractTitle
          abstractNumber
          abstractId
          fullBody
          clinicalTrialRegistryNumber
        }
      }
    }
    status
    errors {
      code
      message
    }
  }
}"""

GET_PERSONS_QUERY = """query getPersons($sessionId: String!) {
  session(sessionId: $sessionId) {
    result {
      contentId
      persons {
        presentationId
        chairs {
          displayName
          publicationOrganization
          role
        }
        speakers {
          displayName
          publicationOrganization
          role
        }
      }
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
        
        # Setup logging
        logger.remove()
        logger.add(sys.stderr, level="INFO")
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
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def format_timestamp(self, ts, tz_name="America/Chicago"):
        """Convert MS timestamp to local date and time."""
        if not ts:
            return None, None
        try:
            # Simple conversion without pytz for now to avoid dependency issues
            # If accuracy in timezone conversion is critical, we can add pytz
            dt = datetime.fromtimestamp(ts / 1000)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
        except Exception as e:
            logger.debug(f"Error formatting timestamp {ts}: {e}")
            return None, None

    def post_query(self, query, variables, max_retries=3):
        """Send a GraphQL POST request with retry logic."""
        # Clean query for API
        clean_query = " ".join(query.split())
        payload = {
            "operationName": None,
            "variables": variables,
            "query": clean_query
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(API_URL, json=payload, timeout=30)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait = (attempt + 1) * 5
                    logger.warning(f"Rate limited (429). Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"HTTP {response.status_code} for variables {variables}")
                    if response.status_code in [401, 403]:
                        logger.critical("Authentication failed. Tokens might be expired.")
                        return None
            except Exception as e:
                logger.error(f"Request error: {e}")
                time.sleep(2)
        
        return None

    def fetch_all_session_ids(self):
        """Fetch all session IDs for the meeting dynamically."""
        logger.info(f"Fetching all session IDs for meeting {self.meeting_id}...")
        variables = {
            "q": "",
            "filters": [
                {"field": "meetingId", "values": [str(self.meeting_id)]},
                {"field": "contentTypeGroupLabel", "values": ["Sessions"]}
            ],
            "from": 0,
            "size": 1000
        }
        
        response = self.post_query(SEARCH_QUERY, variables)
        if not response:
            return []
            
        try:
            hits = response.get("data", {}).get("search", {}).get("result", {}).get("groups", {}).get("hits", [])
            ids = [hit["contentId"] for hit in hits if hit.get("contentId")]
            logger.info(f"Successfully fetched {len(ids)} session IDs from API.")
            return ids
        except Exception as e:
            logger.error(f"Error parsing session IDs: {e}")
            return []

    def fetch_session_details(self, session_id):
        """Fetch session and presentation details."""
        return self.post_query(GET_SESSION_QUERY, {"sessionId": str(session_id)})

    def fetch_participant_info(self, session_id):
        """Fetch authors and speakers info."""
        return self.post_query(GET_PERSONS_QUERY, {"sessionId": str(session_id)})

    def extract_presentation_id(self, presentation):
        """Extract presentation ID from disclosureUrl queryParams."""
        try:
            disclosure_url = presentation.get("disclosureUrl")
            if disclosure_url and disclosure_url.get("queryParams"):
                params = json.loads(disclosure_url["queryParams"])
                return str(params.get("id", ""))
        except Exception:
            pass
        return ""

    def parse_author_info(self, persons_data, presentation_id):
        """Extract author info for a specific presentation ID."""
        if not persons_data:
            return ""
        
        try:
            persons_list = persons_data.get("data", {}).get("session", {}).get("result", {}).get("persons", [])
            for p in persons_list:
                if str(p.get("presentationId")) == str(presentation_id):
                    # Try chairs first, then speakers
                    authors = []
                    for role_key in ["chairs", "speakers"]:
                        role_list = p.get(role_key, [])
                        if role_list:
                            for person in role_list:
                                name = self.clean_text(person.get("displayName"))
                                aff = self.clean_text(person.get("publicationOrganization"))
                                if name:
                                    authors.append(f"{name}; {aff}" if aff else name)
                    return ", ".join(authors)
        except Exception as e:
            logger.debug(f"Error parsing author info for {presentation_id}: {e}")
        
        return ""

    def process_session(self, session_id):
        """Process a single session and return list of abstract objects."""
        logger.info(f"Processing session {session_id}...")
        
        raw_session = self.fetch_session_details(session_id)
        raw_persons = self.fetch_participant_info(session_id)
        
        if not raw_session:
            logger.error(f"Failed to fetch session {session_id}")
            return []

        session_res = raw_session.get("data", {}).get("session", {}).get("result")
        if not session_res:
            logger.warning(f"No result found for session {session_id}")
            return []

        # Session level metadata
        session_name = self.clean_text(session_res.get("title"))
        session_type = self.clean_text(session_res.get("sessionType"))
        location = self.clean_text(session_res.get("sessionLocation"))
        ce_credit = self.clean_text(str(session_res.get("cmeCredits") or ""))
        session_description = self.clean_text(session_res.get("fullSummary"))
        attendance_type = self.clean_text(session_res.get("attendanceType"))
        
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
                "title": [title], # Legacy format uses a list for title
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

    def run(self, session_ids=None):
        """Main execution loop."""
        if session_ids is None:
            # Default to loading from legacy folder if not provided
            ids_file = Path(r"D:\Workspace\Projects\mindgram\legacy\Done VH 2 ASCO 2026 Annual Meeting\session_ids.json")
            if ids_file.exists():
                with open(ids_file, 'r') as f:
                    session_ids = json.load(f)
                logger.info(f"Loaded {len(session_ids)} session IDs from legacy folder.")
            else:
                logger.error("No session IDs provided and legacy session_ids.json not found.")
                return

        all_abstracts = []
        existing_titles = set()
        
        # Load existing data to identify "new" entries
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    for abs_item in existing_data.get("abstracts", []):
                        title = abs_item.get("title")
                        if title:
                            title_str = title[0] if isinstance(title, list) else title
                            existing_titles.add(self.clean_text(title_str))
                logger.info(f"Loaded {len(existing_titles)} existing abstracts for duplicate check.")
            except Exception as e:
                logger.error(f"Error loading existing data: {e}")

        total = len(session_ids)
        new_count = 0
        duplicate_count = 0
        
        logger.info(f"Starting crawl for {total} sessions...")
        
        # Process sequentially to be safe
        for idx, sid in enumerate(session_ids, 1):
            try:
                results = self.process_session(sid)
                for res in results:
                    title = res.get("title")[0]
                    if self.clean_text(title) not in existing_titles:
                        all_abstracts.append(res)
                        existing_titles.add(self.clean_text(title))
                        new_count += 1
                    else:
                        duplicate_count += 1
                
                logger.info(f"[{idx}/{total}] Session {sid}: {len(results)} abstracts ({new_count} new so far)")
                time.sleep(0.5) 
            except Exception as e:
                logger.error(f"Error processing session {sid}: {e}")
        
        if not all_abstracts and duplicate_count > 0:
            logger.info("No new abstracts found. All captured data already exists in the output file.")
            return

        # If we have existing data, we might want to append or just save the new ones
        # User said "collect new data as well", usually implies merging or just identifying them.
        # I will merge them into the final list.
        
        final_abstracts = []
        if self.output_file.exists():
             with open(self.output_file, 'r', encoding='utf-8') as f:
                final_data = json.load(f)
                final_abstracts = final_data.get("abstracts", [])
        
        final_abstracts.extend(all_abstracts)

        # Wrap in final structure
        final_output = {
            "meeting_id": self.meeting_id,
            "meeting_name": "ASCO 2026 Annual Meeting",
            "start_date": "Tue, 26 May 2026 00:00:00 GMT",
            "end_date": "Tue, 02 Jun 2026 00:00:00 GMT",
            "from_website": "https://meetings.asco.org",
            "abstracts": final_abstracts,
            "summary": {
                "new_entries": new_count,
                "duplicates_skipped": duplicate_count,
                "total_count": len(final_abstracts)
            }
        }
        
        # Save to file
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(final_output, f, indent=4, ensure_ascii=False)
            logger.success(f"Successfully saved {new_count} new abstracts (Total: {len(final_abstracts)}) to {self.output_file}")
        except Exception as e:
            logger.error(f"Failed to save data: {e}")

if __name__ == "__main__":
    scraper = ASCO2026AbstractScraper()
    
    # Priority 1: Fetch dynamic IDs from API
    session_ids = scraper.fetch_all_session_ids()
    
    # Priority 2: Fallback to legacy session_ids.json if API fetch fails
    if not session_ids:
        ids_file = Path(r"D:\Workspace\Projects\mindgram\legacy\Done VH 2 ASCO 2026 Annual Meeting\session_ids.json")
        if ids_file.exists():
            with open(ids_file, 'r') as f:
                session_ids = json.load(f)
            logger.info(f"Loaded {len(session_ids)} session IDs from legacy folder.")
    
    if not session_ids:
        logger.error("No session IDs found. Scraper cannot proceed.")
        sys.exit(1)

    # Run the full scraper
    scraper.run(session_ids)
