import json
import os
import sys
from pathlib import Path

# Fix sys.path to allow imports from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

# File paths
FILE1 = os.path.join(BASE_DIR, "data", "aacrjournals", "aacr_2026", "v1", "AACR 2026 Special Conference.json")
FILE2 = os.path.join(BASE_DIR, "data", "aacrjournals", "aacr_2026", "aacr_2026_urls.json")

def normalize_url(url):
    if not url:
        return ""
    if isinstance(url, list):
        url = " ".join(str(x) for x in url)
    return url.strip().lower().rstrip('/')

def normalize_title(title):
    if not title:
        return ""
    if isinstance(title, list):
        title = " ".join(str(x) for x in title)
    t = title.strip().lower()
    # Remove "Abstract XXX: " prefix if present (common in aacrjournals.org)
    if t.startswith("abstract "):
        if ":" in t:
            t = t.split(":", 1)[1].strip()
        else:
            # Maybe just "Abstract XXX " without colon
            parts = t.split(" ", 2)
            if len(parts) > 2:
                t = parts[2].strip()
    return t

class AACR2026URLMatcher:
    def run(self):
        if not os.path.exists(FILE1):
            print(f"Error: File 1 not found at {FILE1}")
            return
        if not os.path.exists(FILE2):
            print(f"Error: File 2 not found at {FILE2}")
            return

        # Load File 1 (v1 Special Conference)
        print(f"Loading {FILE1}...")
        with open(FILE1, "r", encoding="utf-8") as f:
            data1 = json.load(f)

        items1 = data1.get("abstracts", [])
        urls1 = set()
        titles1 = set()
        for item in items1:
            u = normalize_url(item.get("link", ""))
            t = normalize_title(item.get("title", ""))
            if u:
                urls1.add(u)
            if t:
                titles1.add(t)

        # Load File 2 (New URLs)
        print(f"Loading {FILE2}...")
        with open(FILE2, "r", encoding="utf-8") as f:
            items2 = json.load(f)

        urls2 = set()
        titles2 = set()
        for item in items2:
            u = normalize_url(item.get("url", ""))
            t = normalize_title(item.get("title", ""))
            if u:
                urls2.add(u)
            if t:
                titles2.add(t)

        print("\n" + "=" * 40)
        print(f"{'STATISTICS':^40}")
        print("=" * 40)
        print(f"File 1 (v1): {len(items1)} abstracts")
        print(f"File 2 (New): {len(items2)} URLs")
        print("-" * 40)

        # URL Comparison
        same_urls = urls1.intersection(urls2)
        print(f"MATCH BY URL:")
        print(f"  Same URLs:       {len(same_urls)}")
        print(f"  Unique to v1:    {len(urls1 - urls2)}")
        print(f"  Unique to New:   {len(urls2 - urls1)}")
        print("-" * 40)

        # Title Comparison
        same_titles = titles1.intersection(titles2)
        print(f"MATCH BY NORMALIZED TITLE:")
        print(f"  Same Titles:     {len(same_titles)}")
        if len(same_titles) > 0:
            print("  Matched Titles:")
            for t in list(same_titles)[:5]:  # Print first 5
                print(f"    - {t}")
        print(f"  Unique to v1:    {len(titles1 - titles2)}")
        print(f"  Unique to New:   {len(titles2 - titles1)}")
        print("=" * 40)

        # Combined Comparison
        # Count how many items in File 1 have a match in File 2 by either URL or Title
        matches_combined = 0
        for item in items1:
            u = normalize_url(item.get("link", ""))
            t = normalize_title(item.get("title", ""))
            if (u and u in urls2) or (t and t in titles2):
                matches_combined += 1

        print(f"COMBINED MATCH (URL OR TITLE):")
        print(f"  Total Overlap:   {matches_combined}")
        print(f"  Missing in New:  {len(items1) - matches_combined}")
        print("=" * 40)

        if matches_combined > 0 and len(same_urls) == 0:
            print("\nNote: Matches were found by Title, but not by URL.")
            print(
                "This is common when the same abstracts are hosted on different domains."
            )


if __name__ == "__main__":
    matcher = AACR2026URLMatcher()
    matcher.run()
