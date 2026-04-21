import json

# Read the original JSON file
with open('2_presentation_data.json', 'r', encoding='utf-8') as f:
    # Load the JSON data from the file
    original_data = json.load(f)

# Create the new JSON structure
croi_data = {
    "meeting_name": "ASCO 2026 Annual Meeting",
    "date": "2026-05-29",
    "link": "https://meetings.asco.org/meetings/2026-asco-annual-meeting/335/program-guide/scheduled-sessions",
    "abstracts": original_data  # Directly use the entire list of abstracts
}

# Write to a new JSON file
with open("0_ASCO 2026 Annual Meeting.json", 'w', encoding='utf-8') as f:
    json.dump(croi_data, f, indent=4, ensure_ascii=False)

print("JSON file created successfully: complete_abstracts.json")

# Optional: Print the number of abstracts added
print(f"Total number of abstracts added: {len(original_data)}")