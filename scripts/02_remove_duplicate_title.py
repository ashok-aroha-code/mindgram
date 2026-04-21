import json
import re

# Titles to remove
titles_to_remove = {
    "Introduction",
    "T.B.A.",
    "Welcome and Introductions",
    "Welcome",
    "Panel Discussion",
    "Question and Answer",
    "Closing Remarks",
    "Break",
    "Lunch",
    "Opening Remarks",
    "Introductions",
    "Discussion",
    "Q&A",
    "Award Presentation",
    "Chair",
    "Moderator",
    "Moderators",
    "Panel Question and Answer",
    "Award Recipient",
    "Guest Speaker Address 1",
    "Guest Speaker Address 2",
    "Introduction of Dr. Eric J. Small"
}

def clean_text(text):
    """Remove HTML tags and extra spaces from text"""
    if not isinstance(text, str):
        return text
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
    text = re.sub(r"\s+", " ", text).strip()  # Normalize spaces
    return text

def clean_dict(d):
    """Recursively clean string values in nested dicts, except abstract_html"""
    cleaned = {}
    for key, value in d.items():
        if isinstance(value, dict):
            cleaned[key] = clean_dict(value)
        elif key != "abstract_html" and isinstance(value, str):
            cleaned[key] = clean_text(value)
        else:
            cleaned[key] = value
    return cleaned

def process_json(input_file, output_file):
    # Load JSON data
    with open(input_file, "r", encoding="utf-8") as f:
        full_data = json.load(f)

    # Handle both list and dict with 'abstracts' key
    if isinstance(full_data, dict) and "abstracts" in full_data:
        abstracts = full_data["abstracts"]
    elif isinstance(full_data, list):
        abstracts = full_data
    else:
        raise ValueError("Invalid JSON structure.")

    seen_titles = set()
    filtered_abstracts = []

    removed_count = 0
    duplicate_count = 0

    for abstract in abstracts:
        # Ensure abstract_metadata exists
        if "abstract_metadata" not in abstract or not isinstance(abstract["abstract_metadata"], dict):
            abstract["abstract_metadata"] = {}

        # --- Handle missing title using session_name ---
        session_name = abstract["abstract_metadata"].get("session_name")
        if not abstract.get("title") and session_name:
            abstract["title"] = session_name
            abstract["abstract_metadata"]["abs_type"] = "session"

        title = abstract.get("title", "").strip()

        # Skip unwanted titles
        if title in titles_to_remove:
            removed_count += 1
            continue

        # Skip duplicates
        if title in seen_titles:
            duplicate_count += 1
            continue

        seen_titles.add(title)

        # Clean all data deeply
        cleaned_abstract = clean_dict(abstract)

        # ✅ Reapply abs_type after cleaning to ensure it is not lost
        if abstract["abstract_metadata"].get("abs_type"):
            cleaned_abstract["abstract_metadata"]["abs_type"] = abstract["abstract_metadata"]["abs_type"]

        filtered_abstracts.append(cleaned_abstract)

    # Update the data structure
    if isinstance(full_data, dict):
        full_data["abstracts"] = filtered_abstracts
    else:
        full_data = filtered_abstracts

    # Save processed data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=4, ensure_ascii=False)

    print(f"Processed data saved to {output_file}")
    print(f"Original count: {len(abstracts)}")
    print(f"Removed unwanted titles: {removed_count}")
    print(f"Skipped duplicates: {duplicate_count}")
    print(f"Final abstracts count: {len(filtered_abstracts)}")

# Example usage
if __name__ == "__main__":
    input_json_file = r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v1\asco_2026_abstracts.json"
    output_json_file = r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v1\asco_2026_abstracts_cleaned.json"
    process_json(input_json_file, output_json_file)