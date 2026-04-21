import json

# Load the JSON file
with open('session_api_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract all contentId values using list comprehension
content_ids = [
    hit["contentId"] 
    for hit in data["data"]["search"]["result"]["groups"]["hits"] 
    if "contentId" in hit and hit["contentId"] is not None
]

# Save to new JSON file
with open('content_ids.json', 'w') as f:
    json.dump(content_ids, f, indent=2)

print(f"Extracted {len(content_ids)} content IDs")
print(f"Saved to content_ids.json")