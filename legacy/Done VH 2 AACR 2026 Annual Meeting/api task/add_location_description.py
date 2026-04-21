import json
import re
from bs4 import BeautifulSoup

def clean_text(text):
    """
    Clean text by removing HTML tags, unescaping characters, and replacing newlines.
    """
    if not text or not isinstance(text, str):
        return text
    
    # Remove HTML tags using BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()
    
    # Unescape common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&ldquo;': '"',
        '&rdquo;': '"',
        '&lsquo;': "'",
        '&rsquo;': "'",
        '&nbsp;': ' ',
        '&ndash;': '-',
        '&mdash;': '-'
    }
    
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    
    # Replace newlines and multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def clean_author_info(text):
    """
    Specifically clean author_info field: replace ' . ' with '; ' and normalize spaces.
    """
    if not text or not isinstance(text, str):
        return text
    
    # Replace ' . ' with '; ' (exact pattern with spaces around the dot)
    text = re.sub(r'\s\.\s', '; ', text)
    
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def clean_all_fields_except_html(item):
    """
    Clean all fields in the item except abstract_html.
    Also handle special cleaning for author_info.
    """
    if not isinstance(item, dict):
        return item
    
    for key, value in item.items():
        # Skip abstract_html field
        if key == 'abstract_html':
            continue
        
        if isinstance(value, str):
            if key == 'author_info':
                # Special handling for author_info
                item[key] = clean_author_info(value)
            else:
                # Regular cleaning for other string fields
                item[key] = clean_text(value)
        elif isinstance(value, dict):
            # Recursively clean nested dictionaries
            clean_all_fields_except_html(value)
        elif isinstance(value, list):
            # Recursively clean lists
            for i, list_item in enumerate(value):
                if isinstance(list_item, dict):
                    clean_all_fields_except_html(list_item)
                elif isinstance(list_item, str) and key != 'abstract_html':
                    if key == 'author_info':
                        value[i] = clean_author_info(list_item)
                    else:
                        value[i] = clean_text(list_item)
    
    return item

def remove_empty_fields_from_metadata(item):
    """
    Remove null and empty fields from abstract_metadata.
    """
    if 'abstract_metadata' in item and isinstance(item['abstract_metadata'], dict):
        # Create a new dictionary without empty or null values
        cleaned_metadata = {}
        for key, value in item['abstract_metadata'].items():
            # Keep only non-empty values (not None, not empty string, not empty list/dict)
            if value is not None and value != "" and value != [] and value != {}:
                cleaned_metadata[key] = value
        
        # Replace the original metadata with cleaned version
        item['abstract_metadata'] = cleaned_metadata
    
    return item

def get_session_track(additional_fields):
    """Extract session track from AdditionalFields where Key is 'AACRTrackAll'"""
    if not additional_fields:
        return ""
    
    for field in additional_fields:
        if field.get('Key') == 'AACRTrackAll':
            return field.get('Value', '')
    return ""

def get_session_type(additional_fields):
    """Extract session type from AdditionalFields where Key is 'SessionName'"""
    if not additional_fields:
        return ""
    
    for field in additional_fields:
        if field.get('Key') == 'SessionName':
            return field.get('Value', '')
    return ""

def merge_json_files(first_file_path, second_file_path, output_file_path):
    """
    Merge data from two JSON files based on session_id/Id match.
    """
    # Load the first JSON file (list of presentations)
    with open(first_file_path, 'r', encoding='utf-8') as f:
        first_data = json.load(f)
    
    # Load the second JSON file (dictionary with session data)
    with open(second_file_path, 'r', encoding='utf-8') as f:
        second_data = json.load(f)
    
    # Create a mapping of session IDs to session data from second file
    session_map = {}
    for session_id, session_info in second_data.items():
        session_map[session_id] = session_info
    
    # Process each item in the first data
    matched_count = 0
    for item in first_data:
        session_id = item.get('abstract_metadata', {}).get('session_id')
        
        if session_id and session_id in session_map:
            # Get matching session from second file
            matching_session = session_map[session_id]
            
            # Add description and location with cleaning
            if 'abstract_metadata' not in item:
                item['abstract_metadata'] = {}
            
            # Clean and add description
            raw_description = matching_session.get('Description', '')
            item['abstract_metadata']['description'] = clean_text(raw_description)
            
            # Clean and add location
            raw_location = matching_session.get('Location', '')
            item['abstract_metadata']['location'] = clean_text(raw_location)
            
            # Get and add session track from AdditionalFields
            additional_fields = matching_session.get('AdditionalFields', [])
            session_track = get_session_track(additional_fields)
            item['abstract_metadata']['session_track'] = clean_text(session_track)
            
            # Get and add session type from AdditionalFields
            session_type = get_session_type(additional_fields)
            item['abstract_metadata']['session_type'] = clean_text(session_type)
            
            matched_count += 1
    
    # Clean all fields in the merged data except abstract_html
    for item in first_data:
        clean_all_fields_except_html(item)
        # Remove empty fields from abstract_metadata
        remove_empty_fields_from_metadata(item)
    
    # Save the merged data to a new JSON file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(first_data, f, indent=4, ensure_ascii=False)
    
    print(f"Merged data saved to {output_file_path}")
    print(f"Processed {len(first_data)} items, matched {matched_count} sessions")

# Example usage
if __name__ == "__main__":
    # Replace these with your actual file paths
    first_file = "presentation_data.json"  # Path to your first JSON file
    second_file = "session_location_description_data.json"  # Path to your second JSON file
    output_file = "1_presentation_data.json"  # Path for the output file
    
    try:
        merge_json_files(first_file, second_file, output_file)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
    except Exception as e:
        print(f"Error: {e}")