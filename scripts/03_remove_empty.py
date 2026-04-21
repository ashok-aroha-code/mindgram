import json
from pathlib import Path

# Input and output file names
input_file = r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v1\asco_2026_abstracts_cleaned.json"
output_file = r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v1\asco_2026_abstracts_final.json"

def clean_empty_fields():
    # Load JSON data safely
    if not Path(input_file).exists():
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        full_data = json.load(f)

    # Handle both list and dict with 'abstracts' key
    if isinstance(full_data, dict) and "abstracts" in full_data:
        abstracts = full_data["abstracts"]
    elif isinstance(full_data, list):
        abstracts = full_data
    else:
        print("Invalid JSON structure.")
        return

    # Clean each presentation
    for presentation in abstracts:
        metadata = presentation.get("abstract_metadata", {})
        if isinstance(metadata, dict):
            # Keep only non-empty values
            cleaned_metadata = {}
            for k, v in metadata.items():
                # Skip empty strings, None, empty lists, empty dicts
                if v == "" or v is None or v == [] or v == {}:
                    continue
                cleaned_metadata[k] = v
            
            presentation["abstract_metadata"] = cleaned_metadata

    # Save cleaned data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=4, ensure_ascii=False)

    print(f"Cleaning complete. Saved cleaned data to '{output_file}'.")

if __name__ == "__main__":
    clean_empty_fields()