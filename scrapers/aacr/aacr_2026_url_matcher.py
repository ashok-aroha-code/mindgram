import os
from loguru import logger
from utils import load_json

class AACR2026URLMatcher:
    def __init__(self):
        self.file1 = os.path.join("data", "aacrjournals", "aacr_2026", "v1", "AACR 2026 Special Conference.json")
        self.file2 = os.path.join("data", "aacrjournals", "aacr_2026", "aacr_2026_urls.json")

    def normalize_url(self, url):
        if not url: return ""
        if isinstance(url, list): url = " ".join(str(x) for x in url)
        return url.strip().lower().rstrip('/')

    def normalize_title(self, title):
        if not title: return ""
        if isinstance(title, list): title = " ".join(str(x) for x in title)
        t = title.strip().lower()
        if t.startswith("abstract "):
            if ":" in t: t = t.split(":", 1)[1].strip()
            else:
                parts = t.split(" ", 2)
                if len(parts) > 2: t = parts[2].strip()
        return t

    def run(self):
        data1 = load_json(self.file1)
        items1 = data1.get("abstracts", []) if isinstance(data1, dict) else []
        
        items2 = load_json(self.file2)
        if not items2:
            logger.error("File 2 is empty or not found.")
            return

        urls2 = {self.normalize_url(item.get("url", "")) for item in items2}
        titles2 = {self.normalize_title(item.get("title", "")) for item in items2}

        matches = 0
        for item in items1:
            u = self.normalize_url(item.get("link", ""))
            t = self.normalize_title(item.get("title", ""))
            if (u and u in urls2) or (t and t in titles2):
                matches += 1

        logger.info(f"Statistics:")
        logger.info(f"  File 1 (v1): {len(items1)} abstracts")
        logger.info(f"  File 2 (New): {len(items2)} URLs")
        logger.info(f"  Combined Matches: {matches}")
        logger.info(f"  Missing in New: {len(items1) - matches}")

if __name__ == "__main__":
    AACR2026URLMatcher().run()
