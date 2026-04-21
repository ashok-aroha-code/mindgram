import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(r"D:\Workspace\Projects\mindgram")))

from scrapers.asco_meetings.asco.asco_2026_abstract_scraper import ASCO2026AbstractScraper

def compare_batch(limit=40):
    # 1. Get first 40 IDs
    ids_file = Path(r"D:\Workspace\Projects\mindgram\legacy\Done VH 2 ASCO 2026 Annual Meeting\session_ids.json")
    with open(ids_file, 'r') as f:
        session_ids = json.load(f)[:limit]
    
    # 2. Process them
    scraper = ASCO2026AbstractScraper()
    new_abstracts = []
    print(f"Processing first {limit} sessions...")
    for i, sid in enumerate(session_ids, 1):
        new_abstracts.extend(scraper.process_session(sid))
        if i % 10 == 0:
            print(f" - [{i}/{limit}] done...")
            
    # 3. Load v0 data for these sessions
    old_file = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v0\ASCO 2026 Annual Meeting.json")
    with open(old_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)["abstracts"]
    
    old_filtered = [a for a in old_data if a.get("abstract_metadata", {}).get("session_id") in session_ids]
    
    # 4. Compare
    print(f"\n--- Batch Comparison (First {limit} Sessions) ---")
    print(f"Total Old Records: {len(old_filtered)}")
    print(f"Total New Records: {len(new_abstracts)}")
    
    old_titles = set()
    for a in old_filtered:
        t = a.get("title")
        old_titles.add(t[0] if isinstance(t, list) else t)
        
    new_titles = {a.get("title") for a in new_abstracts}
    
    common = old_titles.intersection(new_titles)
    only_old = old_titles - new_titles
    only_new = new_titles - old_titles
    
    print(f"Common Titles: {len(common)}")
    print(f"Titles only in Old: {len(only_old)}")
    print(f"Titles only in New: {len(only_new)}")
    
    if only_old:
        print("\n[!] Discrepancy Found - Titles missing in New:")
        for t in list(only_old)[:5]:
            print(f" - {t}")
            
    if only_new:
        print("\n[+] New Content Found - Titles only in New:")
        for t in list(only_new)[:5]:
            print(f" - {t}")

if __name__ == "__main__":
    compare_batch(40)
