import json
import re
from pathlib import Path

old_file = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v0\ASCO 2026 Annual Meeting.json")
new_file = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v1\asco_2026_abstracts.json")

def normalize(text):
    if not text:
        return ""
    # Remove all non-alphanumeric characters and lowercase
    return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()

def filter_new_only(old_p, new_p):
    try:
        # Load old titles
        with open(old_p, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        old_abs = old_data.get("abstracts", [])
        
        old_titles_norm = set()
        for a in old_abs:
            title = a.get("title")
            if isinstance(title, list) and len(title) > 0:
                title = title[0]
            old_titles_norm.add(normalize(title))
            
        # Load new data
        with open(new_p, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
        new_abs = new_data.get("abstracts", [])
        
        # Keep only if NOT in old
        filtered_abs = []
        for a in new_abs:
            if normalize(a.get("title")) not in old_titles_norm:
                filtered_abs.append(a)
        
        # Update and save
        new_data["abstracts"] = filtered_abs
        
        with open(new_p, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=4, ensure_ascii=False)
            
        print(f"Successfully filtered {len(filtered_abs)} new abstracts. Removed {len(new_abs) - len(filtered_abs)} old ones.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    filter_new_only(old_file, new_file)
