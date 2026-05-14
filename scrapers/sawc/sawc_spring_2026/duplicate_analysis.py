import os
from loguru import logger
from scrapers.base import BaseScraper
from utils import load_json, save_json

class SAWCSpring2026DuplicateAnalysis(BaseScraper):
    def __init__(self, **kwargs):
        super().__init__(name="SAWC_SPRING_2026_DUP", **kwargs)
        self.meeting_name = "SAWC_Spring"
        self.year = "2026"
        self.raw_file = os.path.join("data", "sawc", f"{self.meeting_name}_{self.year}_raw.json")
        self.duplicates_file = os.path.join("data", "sawc", f"{self.meeting_name}_{self.year}_duplicates.json")

    def run(self):
        """Override run to avoid driver initialization for local file processing."""
        # Log output path for GUI
        logger.info(f"[OUTPUT_PATH] {self.duplicates_file}")
        self.execute()

    def execute(self):
        logger.info(f"Running duplicate analysis on {self.raw_file}...")
        if not os.path.exists(self.raw_file):
            logger.error(f"Raw file not found: {self.raw_file}")
            return

        data = load_json(self.raw_file)
        if not data or "abstracts" not in data:
            logger.error("No abstracts found in raw file.")
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
        else:
            logger.info("No duplicates found.")

if __name__ == "__main__":
    SAWCSpring2026DuplicateAnalysis().run()
