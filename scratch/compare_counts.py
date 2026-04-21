import json
from pathlib import Path

old_file = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v0\ASCO 2026 Annual Meeting.json")
new_file = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v1\asco_2026_abstracts.json")

def count_abstracts(file_path):
    if not file_path.exists():
        return 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Both formats have 'abstracts' as a list
            if isinstance(data, dict) and 'abstracts' in data:
                return len(data['abstracts'])
            elif isinstance(data, list):
                return len(data)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return 0

old_count = count_abstracts(old_file)
new_count = count_abstracts(new_file)

print(f"Old file (v0): {old_count} abstracts")
print(f"New file (v1): {new_count} abstracts")
print(f"New abstracts added: {new_count - old_count}")
