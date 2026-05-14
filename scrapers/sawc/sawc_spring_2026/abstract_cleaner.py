import os
from loguru import logger
from scrapers.base import BaseScraper
from utils import load_json, save_json

class SAWCSpring2026Cleaner(BaseScraper):
    def __init__(self, **kwargs):
        super().__init__(name="SAWC_SPRING_2026_CLEANER", **kwargs)
        self.meeting_name = "SAWC_Spring"
        self.year = "2026"
        self.raw_file = os.path.join("data", "sawc", f"{self.meeting_name}_{self.year}_raw.json")
        self.output_file = os.path.join("data", "sawc", f"{self.meeting_name}_{self.year}.json")

    def run(self):
        """Override run to avoid driver initialization for local file processing."""
        # Log output path for GUI
        logger.info(f"[OUTPUT_PATH] {self.output_file}")
        self.execute()

    def execute(self):
        logger.info(f"Running cleaner on {self.raw_file}...")
        if not os.path.exists(self.raw_file):
            logger.error(f"Raw file not found: {self.raw_file}")
            return

        data = load_json(self.raw_file)
        if not data or "abstracts" not in data:
            logger.error("No abstracts found in raw file.")
            return

        cleaned_abstracts = []
        for a in data["abstracts"]:
            # 1. Ensure abstract_markdown is ""
            a["abstract_markdown"] = ""
            
            # 2. Filter empty fields from abstract_metadata
            meta = a.get("abstract_metadata", {})
            a["abstract_metadata"] = {k: v for k, v in meta.items() if v != "" and v != []}
            
            cleaned_abstracts.append(a)
            
        data["abstracts"] = cleaned_abstracts
        save_json(data, self.output_file)
        logger.info(f"Cleaning complete. Final file: {self.output_file}")

if __name__ == "__main__":
    SAWCSpring2026Cleaner().run()
