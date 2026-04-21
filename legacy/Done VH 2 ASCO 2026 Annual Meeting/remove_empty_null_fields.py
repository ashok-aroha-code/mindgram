import json
import re

def clean_abstract_metadata(data):
    """Remove empty/null/None fields from abstract_metadata only"""
    for item in data:
        if 'abstract_metadata' in item and isinstance(item['abstract_metadata'], dict):
            # Create a new dict with only non-empty values
            cleaned_metadata = {}
            for key, value in item['abstract_metadata'].items():
                # Check if value is not empty/None
                if value is not None and value != "" and value != "None":
                    cleaned_metadata[key] = value
            # Replace the original abstract_metadata with cleaned version
            item['abstract_metadata'] = cleaned_metadata
    return data

def clean_extra_spaces(data):
    """Replace multiple spaces with single space in all fields except abstract_html"""
    for item in data:
        for key, value in item.items():
            # Skip abstract_html field
            if key == 'abstract_html':
                continue
                
            # Process only string values
            if isinstance(value, str):
                # Replace multiple spaces with single space
                item[key] = re.sub(r'\s+', ' ', value).strip()
            
            # Also process nested abstract_metadata fields
            elif key == 'abstract_metadata' and isinstance(value, dict):
                for meta_key, meta_value in value.items():
                    if isinstance(meta_value, str):
                        value[meta_key] = re.sub(r'\s+', ' ', meta_value).strip()
    return data

# Load your JSON data
with open('1_presentation_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Clean the abstract_metadata fields
cleaned_data = clean_abstract_metadata(data)

# Clean extra spaces in all fields except abstract_html
cleaned_data = clean_extra_spaces(cleaned_data)

# Save to new JSON file
with open('2_presentation_data.json', 'w', encoding='utf-8') as f:
    json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

print("Data cleaned and saved to '1_presentation_data.json'")