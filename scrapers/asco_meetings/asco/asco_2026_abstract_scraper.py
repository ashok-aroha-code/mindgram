import requests
import json
import time
import re
import sys
import random
from pathlib import Path
from datetime import datetime
import pytz
from html import unescape
from loguru import logger

# Constants
BASE_DIR = Path(r"D:\Workspace\Projects\mindgram")
API_URL = "https://api.asco.org/graphql2"

# EXACT HEADERS FROM LEGACY
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

# EXACT GRAPHQL QUERY FROM LEGACY
GRAPHQL_QUERY = """query getSession($sessionId: String!) {
  session(sessionId: $sessionId) {
    result {
      ...main
      ...presentations
      persons {
        presentationId
        chairs {
          displayName
          publicationOrganization
        }
        speakers {
          displayName
          publicationOrganization
        }
        panelists {
          displayName
          publicationOrganization
        }
      }
      __typename
    }
    status
    errors {
      code
      message
      __typename
    }
    __typename
  }
}

fragment main on Session {
  attendanceType
  sessionLocation
  cmeCredits
  fullSummary
  contentId
  title
  sessionType
  tracks {
    track
    __typename
  }
  sessionDates {
    start
    end
    timeZone
    __typename
  }
  __typename
}

fragment presentations on Session {
  presentations {
    contentId
    presentation {
      doiUrl {
        path
        __typename
      }
      title
      abstractNumber
      posterBoardNumber
      presentationDates {
        start
        end
        timeZone
        __typename
      }
      __typename
    }
    abstract {
      abstractAuthorsString
      authorInstitutionsString
      subTrack {
        subTrack
        __typename
      }
      doi
      abstractTitle
      abstractNumber
      fullBody
      posterBoardNumber
      clinicalTrialRegistryNumber
      __typename
    }
    __typename
  }
  __typename
}"""

class ASCO2026AbstractScraper:
    def __init__(self, meeting_id="335", output_file=None):
        self.meeting_id = meeting_id
        self.output_dir = BASE_DIR / "data" / "meetings.asco.org" / "asco_2026" / "v1"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = output_file or self.output_dir / "asco_2026_abstracts.json"
        
        logger.remove()
        logger.add(sys.stderr, 
                   format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                   level="INFO")
        logger.add(self.output_dir / "scraper.log", rotation="10 MB", level="DEBUG")
        
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def clean_text(self, text):
        if not text or not isinstance(text, str):
            return str(text) if text is not None else ""
        text = unescape(text)
        text = re.sub(r'<[^>]+>', '', text)
        text = " ".join(text.split())
        return text

    def convert_timestamp(self, timestamp, timezone_str="America/Chicago"):
        """Convert Unix timestamp in ms to local date and time."""
        if not timestamp:
            return "", ""
        try:
            timezone = pytz.timezone(timezone_str)
            dt_utc = datetime.utcfromtimestamp(int(timestamp) / 1000)
            dt_local = dt_utc.replace(tzinfo=pytz.UTC).astimezone(timezone)
            return dt_local.strftime("%Y-%m-%d"), dt_local.strftime("%H:%M")
        except:
            return "", ""

    def post_query(self, session_id, retries=3):
        payload = {
            "variables": {"sessionId": str(session_id)},
            "query": GRAPHQL_QUERY
        }
        for attempt in range(retries):
            try:
                response = self.session.post(API_URL, json=payload, timeout=30)
                if response.status_code == 403:
                    logger.warning(f"403 Forbidden for {session_id}. Retrying {attempt+1}...")
                    time.sleep(5 + random.uniform(1, 5))
                    continue
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error for {session_id}: {e}")
                time.sleep(2 * (attempt + 1))
        return None

    def parse_author_info(self, raw_persons, presentation_id):
        """Parse persons data into a formatted author string."""
        if not raw_persons:
            return ""
        
        # Match persons for this presentation
        p_item = next((p for p in raw_persons if str(p.get("presentationId")) == str(presentation_id)), None)
        if not p_item:
            return ""
        
        authors_list = []
        # Combine all roles for author_info
        for role in ["speakers", "chairs", "panelists"]:
            persons = p_item.get(role)
            if persons and isinstance(persons, list):
                for p in persons:
                    name = p.get("displayName", "").strip()
                    org = p.get("publicationOrganization", "").strip()
                    if name and org:
                        authors_list.append(f"{name}; {org}")
                    elif name:
                        authors_list.append(name)
        
        return ", ".join(authors_list)

    def process_session(self, session_id):
        data = self.post_query(session_id)
        if not data: return []
            
        res_wrapper = data.get("data", {}).get("session", {})
        if res_wrapper.get("status") != "SUCCESS":
            return []
            
        result = res_wrapper.get("result", {})
        raw_persons = result.get("persons", [])
        
        # Session Metadata
        session_name = self.clean_text(result.get("title"))
        session_type = self.clean_text(result.get("sessionType"))
        location = self.clean_text(result.get("sessionLocation"))
        ce_credit = self.clean_text(str(result.get("cmeCredits") or ""))
        session_description = self.clean_text(result.get("fullSummary"))
        attendance_type = self.clean_text(result.get("attendanceType"))
        
        tracks = [t.get("track") for t in result.get("tracks", []) if t.get("track")]
        session_track = " ".join(tracks)

        s_dates = result.get("sessionDates") or {}
        s_date, s_start_v = self.convert_timestamp(s_dates.get("start"), s_dates.get("timeZone", "America/Chicago"))
        _, s_end_v = self.convert_timestamp(s_dates.get("end"), s_dates.get("timeZone", "America/Chicago"))
        session_time = f"{s_start_v} - {s_end_v}" if s_start_v and s_end_v else s_start_v

        abstracts = []
        for p_item in result.get("presentations", []):
            pres = p_item.get("presentation") or {}
            abs_data = p_item.get("abstract") or {}
            
            title = self.clean_text(pres.get("title") or abs_data.get("abstractTitle") or "")
            if not title: continue

            pres_id = str(p_item.get("contentId") or "")
            
            # Author Info logic: Try persons first (matches legacy enrichment), then fallback to strings
            author_info = self.parse_author_info(raw_persons, pres_id)
            
            if not author_info:
                authors = self.clean_text(abs_data.get("abstractAuthorsString"))
                insts = self.clean_text(abs_data.get("authorInstitutionsString"))
                if authors and insts:
                    author_info = f'"{authors}"; "{insts}"'
                else:
                    author_info = authors or insts

            # Times
            p_dates = pres.get("presentationDates") or {}
            _, p_start = self.convert_timestamp(p_dates.get("start"), p_dates.get("timeZone", "America/Chicago"))
            _, p_end = self.convert_timestamp(p_dates.get("end"), p_dates.get("timeZone", "America/Chicago"))
            pres_time = f"{p_start} - {p_end}" if p_start and p_end else p_start

            abstract_obj = {
                "link": f"https://meetings.asco.org/meetings/2026-asco-annual-meeting/335/{session_id}",
                "title": title,
                "doi": self.clean_text(abs_data.get("doi") or (pres.get("doiUrl") or {}).get("path") or ""),
                "number": "",
                "author_info": author_info,
                "abstract": self.clean_text(abs_data.get("fullBody") or "-"),
                "abstract_html": abs_data.get("fullBody") or "",
                "abstract_markdown": "",
                "abstract_metadata": {
                    "sub_track": self.clean_text((abs_data.get("subTrack") or {}).get("subTrack") or ""),
                    "session_name": session_name,
                    "session_track": session_track,
                    "abstract_number": self.clean_text(pres.get("abstractNumber") or abs_data.get("abstractNumber") or ""),
                    "poster_board_number": self.clean_text(pres.get("posterBoardNumber") or abs_data.get("posterBoardNumber") or ""),
                    "session_id": str(session_id),
                    "session_type": session_type,
                    "ce_credit": ce_credit,
                    "date": s_date,
                    "session_time": session_time,
                    "presentation_time": pres_time,
                    "presentation_id": str(p_item.get("contentId") or ""),
                    "location": location,
                    "session_description": session_description,
                    "attendance_type": attendance_type,
                    "clinical_TrialRegistry_Number": self.clean_text(abs_data.get("clinicalTrialRegistryNumber") or "")
                }
            }
            abstracts.append(abstract_obj)
        return abstracts

    def run(self, session_ids=None):
        if session_ids is None:
            ids_file = Path(r"D:\Workspace\Projects\mindgram\legacy\Done VH 2 ASCO 2026 Annual Meeting\session_ids.json")
            if ids_file.exists():
                with open(ids_file, 'r') as f:
                    session_ids = json.load(f)
            else:
                logger.error("No session IDs found.")
                return

        all_abstracts = []
        logger.info(f"Starting legacy-compatible crawl for {len(session_ids)} sessions...")
        
        for i, sid in enumerate(session_ids, 1):
            abs_list = self.process_session(sid)
            all_abstracts.extend(abs_list)
            if i % 10 == 0 or i == len(session_ids):
                logger.info(f"[{i}/{len(session_ids)}] Total collected: {len(all_abstracts)}")
                # Save progress
                self.save_data(all_abstracts)
            time.sleep(random.uniform(1, 2))

        logger.success(f"Final Save: {len(all_abstracts)} entries to {self.output_file}")

    def save_data(self, abstracts):
        final_output = {
            "meeting_name": "ASCO 2026 Annual Meeting",
            "date": "2026-05-26",
            "link": "https://meetings.asco.org",
            "abstracts": abstracts
        }
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    ASCO2026AbstractScraper().run()
