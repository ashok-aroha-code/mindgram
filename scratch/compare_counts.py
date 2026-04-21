import json
from pathlib import Path

old_file = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v0\ASCO 2026 Annual Meeting.json")
new_file = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v1\asco_2026_abstracts.json")

def load_abstracts(file_path):
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'abstracts' in data:
                return data['abstracts']
            elif isinstance(data, list):
                return data
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return []

old_abs = load_abstracts(old_file)
new_abs = load_abstracts(new_file)

old_titles = {a.get('title') if not isinstance(a.get('title'), list) else a.get('title')[0] for a in old_abs}
new_titles = {a.get('title') if not isinstance(a.get('title'), list) else a.get('title')[0] for a in new_abs}

common = old_titles.intersection(new_titles)
only_old = old_titles - new_titles
only_new = new_titles - old_titles

print(f"Old file (v0): {len(old_titles)} unique titles")
print(f"New file (v1): {len(new_titles)} unique titles")
print(f"Common titles: {len(common)}")
print(f"Titles only in Old: {len(only_old)}")
print(f"Titles only in New: {len(only_new)}")

if only_old:
    print("\nSample titles ONLY in Old:")
    for t in list(only_old)[:5]:
        print(f" - {t}")
