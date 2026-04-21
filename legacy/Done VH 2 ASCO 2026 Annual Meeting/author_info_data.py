import json
import re
from html import unescape

def remove_html_tags(text):
    """Remove HTML tags from text using regex"""
    if not text or not isinstance(text, str):
        return text
    
    # First unescape HTML entities
    text = unescape(text)
    
    # Remove HTML tags using regex
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove any remaining HTML entities
    text = unescape(text)
    
    return text.strip()

def extract_presentation_author_info(input_file, output_file):
    """
    Extract presentation_id and author_info from the JSON structure
    Try chairs first, then speakers if chairs not found
    Format: "author; affiliation, author; affiliation"
    """
    try:
        # Load the JSON data from the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create a list to store the extracted data
        extracted_data = []
        
        # Iterate through each item in the main array
        for item in data:
            if isinstance(item, dict) and "data" in item:
                # Navigate through the nested structure
                session_data = item["data"]
                if isinstance(session_data, dict) and "session" in session_data:
                    session = session_data["session"]
                    if isinstance(session, dict) and "result" in session:
                        result = session["result"]
                        
                        # Check if persons array exists in result
                        if isinstance(result, dict) and "persons" in result:
                            persons = result["persons"]
                            
                            # Iterate through each person item in persons array
                            for person_item in persons:
                                if isinstance(person_item, dict):
                                    # Extract presentation_id
                                    presentation_id = person_item.get("presentationId", "")
                                    
                                    # Initialize author_info
                                    author_info = ""
                                    
                                    # FIRST TRY: Check chairs array
                                    chairs = person_item.get("chairs", [])
                                    if isinstance(chairs, list) and chairs:
                                        # Get the first chair's displayName and affiliation
                                        first_chair = chairs[0]
                                        if isinstance(first_chair, dict):
                                            display_name = first_chair.get("displayName", "")
                                            affiliation = first_chair.get("publicationOrganization", "")
                                            if display_name:
                                                if affiliation:
                                                    author_info = f"{remove_html_tags(display_name)}; {remove_html_tags(affiliation)}"
                                                else:
                                                    author_info = remove_html_tags(display_name)
                                    
                                    # SECOND TRY: If no chairs found, check speakers array
                                    if not author_info:
                                        speakers = person_item.get("speakers", [])
                                        if isinstance(speakers, list) and speakers:
                                            # Get the first speaker's displayName and affiliation
                                            first_speaker = speakers[0]
                                            if isinstance(first_speaker, dict):
                                                display_name = first_speaker.get("displayName", "")
                                                affiliation = first_speaker.get("publicationOrganization", "")
                                                if display_name:
                                                    if affiliation:
                                                        author_info = f"{remove_html_tags(display_name)}; {remove_html_tags(affiliation)}"
                                                    else:
                                                        author_info = remove_html_tags(display_name)
                                    
                                    # Only add if we have at least one field
                                    if presentation_id or author_info:
                                        extracted_data.append({
                                            "presentation_id": presentation_id,
                                            "author_info": author_info
                                        })
        
        # Save the extracted data to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=4, ensure_ascii=False)
        
        print(f"Successfully extracted {len(extracted_data)} items.")
        print(f"Data saved to {output_file}")
        
        # Print first few items as example
        print("\nFirst 5 items as example:")
        for i, item in enumerate(extracted_data[:5]):
            print(f"{i+1}. Presentation ID: {item['presentation_id']}")
            print(f"   Author Info: {item['author_info']}\n")
        
        return extracted_data
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

def extract_presentation_author_info_all_authors(input_file, output_file):
    """
    Alternative version that collects ALL authors from chairs or speakers
    Format: "author1; affiliation1, author2; affiliation2"
    """
    try:
        # Load the JSON data from the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create a list to store the extracted data
        extracted_data = []
        
        # Iterate through each item in the main array
        for item in data:
            if isinstance(item, dict) and "data" in item:
                # Navigate through the nested structure
                session_data = item["data"]
                if isinstance(session_data, dict) and "session" in session_data:
                    session = session_data["session"]
                    if isinstance(session, dict) and "result" in session:
                        result = session["result"]
                        
                        # Check if persons array exists in result
                        if isinstance(result, dict) and "persons" in result:
                            persons = result["persons"]
                            
                            # Iterate through each person item in persons array
                            for person_item in persons:
                                if isinstance(person_item, dict):
                                    # Extract presentation_id
                                    presentation_id = person_item.get("presentationId", "")
                                    
                                    # Initialize list to store author;affiliation strings
                                    author_affiliation_list = []
                                    
                                    # FIRST TRY: Check chairs array
                                    chairs = person_item.get("chairs", [])
                                    if isinstance(chairs, list) and chairs:
                                        for chair in chairs:
                                            if isinstance(chair, dict):
                                                display_name = chair.get("displayName", "")
                                                affiliation = chair.get("publicationOrganization", "")
                                                if display_name:
                                                    if affiliation:
                                                        author_affiliation_list.append(f"{remove_html_tags(display_name)}; {remove_html_tags(affiliation)}")
                                                    else:
                                                        author_affiliation_list.append(remove_html_tags(display_name))
                                    
                                    # SECOND TRY: If no chairs found, check speakers array
                                    if not author_affiliation_list:
                                        speakers = person_item.get("speakers", [])
                                        if isinstance(speakers, list) and speakers:
                                            for speaker in speakers:
                                                if isinstance(speaker, dict):
                                                    display_name = speaker.get("displayName", "")
                                                    affiliation = speaker.get("publicationOrganization", "")
                                                    if display_name:
                                                        if affiliation:
                                                            author_affiliation_list.append(f"{remove_html_tags(display_name)}; {remove_html_tags(affiliation)}")
                                                        else:
                                                            author_affiliation_list.append(remove_html_tags(display_name))
                                    
                                    # Combine author names with affiliations
                                    author_info = ", ".join(author_affiliation_list) if author_affiliation_list else ""
                                    
                                    # Only add if we have at least one field
                                    if presentation_id or author_info:
                                        extracted_data.append({
                                            "presentation_id": presentation_id,
                                            "author_info": author_info
                                        })
        
        # Save the extracted data to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=4, ensure_ascii=False)
        
        print(f"Successfully extracted {len(extracted_data)} items (all authors version).")
        print(f"Data saved to {output_file}")
        
        return extracted_data
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

# Example usage
if __name__ == "__main__":
    input_file = "author_info_api_data.json"  # Replace with your input file path
    output_file = "author_info_data.json"  # Output file
    
    # Version that tries chairs first, then speakers (takes first author only)
    print("Using chairs-first, then speakers approach (first author only):")
    extract_presentation_author_info(input_file, output_file)
    
    # Uncomment below if you want ALL authors instead of just first one
    # print("\nUsing chairs-first, then speakers approach (ALL authors):")
    # extract_presentation_author_info_all_authors(input_file, "author_info_all_data.json")