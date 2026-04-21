import json
from pathlib import Path

# File paths
file1_path = r"D:\mindgram uploaded\ASCO 2026 Annual Meeting 07-04-2026.json"
file2_path = r"D:\mindgram uploaded\ASCO 2026 Annual Meeting.json"
output_path = "ASCO 2026 Annual Meeting new entries.json"

# Load both JSON files
print("Loading JSON files...")
with open(file1_path, 'r', encoding='utf-8') as f:
    data1 = json.load(f)

with open(file2_path, 'r', encoding='utf-8') as f:
    data2 = json.load(f)

# Extract titles from file2
titles_in_file2 = set()
for abstract in data2.get('abstracts', []):
    title = abstract.get('title')
    if title:
        title_str = title[0] if isinstance(title, list) else title
        titles_in_file2.add(title_str)

print(f"Found {len(titles_in_file2)} unique titles in file2")

# Find unmatched entries in file1
unmatched_entries = []
matched_count = 0

for abstract in data1.get('abstracts', []):
    title = abstract.get('title')
    if title:
        title_str = title[0] if isinstance(title, list) else title
        if title_str not in titles_in_file2:
            unmatched_entries.append(abstract)
        else:
            matched_count += 1
    else:
        # If no title, add to unmatched
        unmatched_entries.append(abstract)

print(f"Matched entries: {matched_count}")
print(f"Unmatched entries: {len(unmatched_entries)}")

# Create output structure
output_data = {
    "meeting_id": data1.get("meeting_id"),
    "meeting_name": data1.get("meeting_name"),
    "start_date": data1.get("start_date"),
    "end_date": data1.get("end_date"),
    "from_website": data1.get("from_website"),
    "meeting_bucket_id": data1.get("meeting_bucket_id"),
    "abstracts": unmatched_entries,
    "summary": {
        "total_in_original": len([a for a in data1.get('abstracts', []) if a]),
        "unmatched_count": len(unmatched_entries),
        "matched_count": matched_count
    }
}

# Save unmatched entries to new file
print(f"Saving {len(unmatched_entries)} unmatched entries to {output_path}...")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=4, ensure_ascii=False)

print("Done!")
print(f"Unmatched entries saved to: {output_path}")
