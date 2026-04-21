import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(r"D:\Workspace\Projects\mindgram")))

from scrapers.asco_meetings.asco.asco_2026_abstract_scraper import ASCO2026AbstractScraper

def test_comparison():
    # 1. Process a sample session (17066)
    session_id = "17066"
    scraper = ASCO2026AbstractScraper()
    new_data = scraper.process_session(session_id)
    
    # 2. Load the same session from old v0 data
    old_file = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v0\ASCO 2026 Annual Meeting.json")
    with open(old_file, 'r', encoding='utf-8') as f:
        old_full_data = json.load(f)
    
    old_data = [a for a in old_full_data["abstracts"] if a.get("abstract_metadata", {}).get("session_id") == session_id]
    
    print(f"--- Comparison for Session {session_id} ---")
    print(f"Old count: {len(old_data)}")
    print(f"New count: {len(new_data)}")
    
    old_titles = sorted([a.get('title') if not isinstance(a.get('title'), list) else a.get('title')[0] for a in old_data])
    new_titles = sorted([a.get('title') for a in new_data])
    
    print(f"\nOld Titles: {old_titles}")
    print(f"New Titles: {new_titles}")
    
    if len(new_data) > 0 and len(old_data) > 0:
        # Match by title for field comparison
        target_title = 'When Representation Becomes Survival: Changing My Perspective on Clinical Trials'
        old_sample = next((a for a in old_data if (a.get('title')[0] if isinstance(a.get('title'), list) else a.get('title')) == target_title), None)
        new_sample = next((a for a in new_data if a.get('title') == target_title), None)
        
        if old_sample and new_sample:
            print(f"\n[Field Comparison for: {target_title}]")
            print(f"Author Info Match: {old_sample.get('author_info') == new_sample.get('author_info')}")
            print(f"Old Author: {old_sample.get('author_info')}")
            print(f"New Author: {new_sample.get('author_info')}")
            
            # Check Abstract
            old_abs = old_sample.get('abstract')
            new_abs = new_sample.get('abstract')
            print(f"Abstract Match: {old_abs == new_abs}")
            if not (old_abs == new_abs):
                print(f"Old Abs Start: {old_abs[:50]}...")
                print(f"New Abs Start: {new_abs[:50]}...")
        
        # Check Metadata Fields
        print("\n[Metadata Check]")
        for key in ["session_name", "date", "session_time", "presentation_id", "location"]:
            old_val = old_sample.get("abstract_metadata", {}).get(key)
            new_val = new_sample.get("abstract_metadata", {}).get(key)
            print(f"{key}: Old='{old_val}' | New='{new_val}' | Match={old_val == new_val}")

if __name__ == "__main__":
    test_comparison()
