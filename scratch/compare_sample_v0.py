import json
from pathlib import Path

sample_file = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v1\asco_2026_abstracts_sample.json")
old_file = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v0\ASCO 2026 Annual Meeting.json")

def compare_full():
    with open(sample_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)["abstracts"]
    with open(old_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)["abstracts"]
        
    print(f"Sample count: {len(new_data)}")
    print(f"Old count: {len(old_data)}")
    
    # Check for specific session 17066
    sid = "17066"
    new_sample_abs = [a for a in new_data if a.get("abstract_metadata", {}).get("session_id") == sid]
    old_sample_abs = [a for a in old_data if a.get("abstract_metadata", {}).get("session_id") == sid]
    
    print(f"\n--- Parity Check for Session {sid} ---")
    print(f"New has {len(new_sample_abs)} records | Old had {len(old_sample_abs)} records")
    
    # Check if all old titles are in new
    old_titles = {a.get("title")[0] if isinstance(a.get("title"), list) else a.get("title") for a in old_sample_abs}
    new_titles = {a.get("title") for a in new_sample_abs}
    
    missing = old_titles - new_titles
    print(f"Missing Titles from Old: {len(missing)}")
    if missing:
        print(f"Titles missing: {missing}")
        
    # Check fields for a common title
    common_title = "When Representation Becomes Survival: Changing My Perspective on Clinical Trials"
    old_rec = next((a for a in old_sample_abs if (a.get("title")[0] if isinstance(a.get("title"), list) else a.get("title")) == common_title), None)
    new_rec = next((a for a in new_sample_abs if a.get("title") == common_title), None)
    
    if old_rec and new_rec:
        print(f"\n[Field Verification: {common_title}]")
        print(f"Author Match: {old_rec.get('author_info') == new_rec.get('author_info')}")
        print(f"  Old: {old_rec.get('author_info')}")
        print(f"  New: {new_rec.get('author_info')}")
        
        print(f"Abstract Match: {old_rec.get('abstract') == new_rec.get('abstract')}")
        
        print(f"Session Name Match: {old_rec.get('abstract_metadata', {}).get('session_name') == new_rec.get('abstract_metadata', {}).get('session_name')}")
        print(f"Session Time Match: {old_rec.get('abstract_metadata', {}).get('session_time') == new_rec.get('abstract_metadata', {}).get('session_time')}")

if __name__ == "__main__":
    compare_full()
