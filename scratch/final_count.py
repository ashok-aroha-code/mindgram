import json
from pathlib import Path

v0_path = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v0\ASCO 2026 Annual Meeting.json")
v1_path = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v1\asco_2026_abstracts.json")

def count_data():
    with open(v0_path, 'r', encoding='utf-8') as f:
        v0_data = json.load(f)
    with open(v1_path, 'r', encoding='utf-8') as f:
        v1_data = json.load(f)
        
    print(f"Original Records (v0): {len(v0_data['abstracts'])}")
    print(f"New Delta Records (v1): {len(v1_data['abstracts'])}")
    print(f"Total Combined Potential: {len(v0_data['abstracts']) + len(v1_data['abstracts'])}")

if __name__ == "__main__":
    count_data()
