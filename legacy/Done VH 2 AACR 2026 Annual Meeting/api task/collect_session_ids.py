import json

# Step 1: Read the original JSON file
with open('session_api_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Step 2: Collect all Ids
ids = []

for page in data:
    for result in page.get("Results", []):
        ids.append(result.get("Id"))

# Step 3: Save the ids into a new JSON file
with open('session_ids.json', 'w') as f:
    json.dump(ids, f, indent=2)

print(f"Collected {len(ids)} ids and saved to collected_ids.json")
