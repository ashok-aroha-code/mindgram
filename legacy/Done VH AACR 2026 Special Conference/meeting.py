import json

# Read the original JSON file
with open('scraped_data.json', 'r', encoding='utf-8') as f:
    # Load the JSON data from the file
    original_data = json.load(f)

# Create the new JSON structure
croi_data = {
    "meeting_name": "AACR 2026 Special Conference",
    "date": "2026-03-05",
    "link": "https://aacrjournals.org/cancerres/issue/86/5_Supplement_1",
    "abstracts": original_data  # Directly use the entire list of abstracts
}

# Write to a new JSON file
with open("0_AACR 2026 Special Conference.json", 'w', encoding='utf-8') as f:
    json.dump(croi_data, f, indent=4, ensure_ascii=False)

print("JSON file created successfully: complete_abstracts.json")

# Optional: Print the number of abstracts added
print(f"Total number of abstracts added: {len(original_data)}")