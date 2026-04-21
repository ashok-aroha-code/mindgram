import json
from datetime import datetime
import pytz
import re
from html import unescape

def convert_timestamp_to_local_time(timestamp, timezone_str="America/Los_Angeles"):
    """Convert Unix timestamp in milliseconds to local date and time string in specified timezone"""
    if not timestamp:
        return "", ""
    
    try:
        # Create timezone object
        timezone = pytz.timezone(timezone_str)
        
        # Convert milliseconds to seconds and create datetime object in UTC
        dt_utc = datetime.utcfromtimestamp(timestamp / 1000)
        
        # Convert UTC datetime to target timezone
        dt_local = dt_utc.replace(tzinfo=pytz.UTC).astimezone(timezone)
        
        # Format date as YYYY-MM-DD
        date_str = dt_local.strftime("%Y-%m-%d")
        
        # Format time as HH:MM (24-hour format)
        time_str = dt_local.strftime("%H:%M")
        
        return date_str, time_str
    except Exception:
        return "", ""

def remove_html_tags(text):
    """Remove HTML tags from text using regex"""
    if not text or not isinstance(text, str):
        return text
    
    # First unescape HTML entities
    text = unescape(text)
    
    # Remove HTML tags using regex
    # This regex handles nested tags and self-closing tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove any remaining HTML entities
    text = unescape(text)
    
    return text.strip()

def extract_titles_from_new_structure(input_file, output_file):
    try:
        # Load the JSON data from the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create a list to store the extracted titles as dictionaries
        extracted_titles = []
        
        # Base URL for the link field
        base_url = "https://meetings.asco.org/meetings/2026-asco-annual-meeting/335/"
        
        # Iterate through each item in the main array
        for item in data:
            if isinstance(item, dict) and "data" in item:
                # Navigate through the nested structure
                session_data = item["data"]
                if isinstance(session_data, dict) and "session" in session_data:
                    session = session_data["session"]
                    if isinstance(session, dict) and "result" in session:
                        result = session["result"]
                        
                        # Extract session information
                        session_name = result.get("title", "")
                        session_id = result.get("contentId", "")
                        session_type = result.get("sessionType", "")
                        location = result.get("sessionLocation", "")
                        session_description = result.get("fullSummary", "")
                        attendance_type = result.get("attendanceType", "")
                        ce_credit = result.get("cmeCredits", "")  # Extract CE credit
                        
                        # Extract session tracks
                        session_track = ""
                        tracks = result.get("tracks", [])
                        if isinstance(tracks, list):
                            track_names = []
                            for track_item in tracks:
                                if isinstance(track_item, dict) and "track" in track_item:
                                    track_name = track_item.get("track", "")
                                    if track_name:
                                        track_names.append(track_name)
                            if track_names:
                                session_track = " ".join(track_names)
                        
                        # Create link using base_url and session_id
                        link = f"{base_url}{session_id}" if session_id else ""
                        
                        # Extract and convert session date and time
                        date = ""
                        session_time = ""
                        
                        session_dates = result.get("sessionDates")
                        if isinstance(session_dates, dict):
                            start_timestamp = session_dates.get("start")
                            end_timestamp = session_dates.get("end")
                            
                            # Get timezone (default to America/Los_Angeles if not specified)
                            timezone = session_dates.get("timeZone", "America/Los_Angeles")
                            
                            if start_timestamp:
                                # Convert start timestamp to date and time
                                start_date, start_time = convert_timestamp_to_local_time(start_timestamp, timezone)
                                date = start_date  # Use start date as the session date
                                
                                if end_timestamp:
                                    # Convert end timestamp to time
                                    _, end_time = convert_timestamp_to_local_time(end_timestamp, timezone)
                                    if start_time and end_time:
                                        session_time = f"{start_time} - {end_time}"
                                    elif start_time:
                                        session_time = start_time
                                elif start_time:
                                    session_time = start_time
                        
                        if isinstance(result, dict) and "presentations" in result:
                            presentations = result["presentations"]
                            
                            # Iterate through each presentation
                            for presentation_item in presentations:
                                if isinstance(presentation_item, dict):
                                    # Check if presentation field exists
                                    if "presentation" in presentation_item:
                                        presentation = presentation_item["presentation"]
                                        if isinstance(presentation, dict) and "title" in presentation:
                                            title = presentation["title"]
                                            
                                            # Extract presentation ID from disclosureUrl.queryParams
                                            presentation_id = ""
                                            disclosure_url = presentation.get("disclosureUrl")
                                            if isinstance(disclosure_url, dict):
                                                query_params = disclosure_url.get("queryParams", "{}")
                                                if query_params and query_params != "{}":
                                                    try:
                                                        # Parse the JSON string in queryParams
                                                        params_dict = json.loads(query_params)
                                                        presentation_id = params_dict.get("id", "")
                                                    except (json.JSONDecodeError, AttributeError):
                                                        # If parsing fails, try to extract ID using regex
                                                        id_match = re.search(r'"id":\s*"(\d+)"', query_params)
                                                        if id_match:
                                                            presentation_id = id_match.group(1)
                                                        else:
                                                            presentation_id = ""
                                            
                                            # Extract presentation time
                                            presentation_time = ""
                                            presentation_dates = presentation.get("presentationDates")
                                            if isinstance(presentation_dates, dict):
                                                pres_start_timestamp = presentation_dates.get("start")
                                                pres_end_timestamp = presentation_dates.get("end")
                                                
                                                # Get timezone for presentation (default to America/Los_Angeles)
                                                pres_timezone = presentation_dates.get("timeZone", "America/Los_Angeles")
                                                
                                                if pres_start_timestamp:
                                                    # Convert presentation start timestamp to time
                                                    pres_start_date, pres_start_time = convert_timestamp_to_local_time(pres_start_timestamp, pres_timezone)
                                                    
                                                    if pres_end_timestamp:
                                                        # Convert presentation end timestamp to time
                                                        _, pres_end_time = convert_timestamp_to_local_time(pres_end_timestamp, pres_timezone)
                                                        if pres_start_time and pres_end_time:
                                                            presentation_time = f"{pres_start_time} - {pres_end_time}"
                                                        elif pres_start_time:
                                                            presentation_time = pres_start_time
                                                    elif pres_start_time:
                                                        presentation_time = pres_start_time
                                            
                                            # Extract abstract number
                                            abstract_number = presentation.get("abstractNumber", "")
                                            
                                            # Extract doi - get path from doiUrl
                                            doi = ""
                                            doi_url = presentation.get("doiUrl")
                                            if isinstance(doi_url, dict) and "path" in doi_url:
                                                doi = doi_url["path"]
                                            
                                            # Extract poster board number
                                            poster_board_number = presentation.get("posterBoardNumber", "")
                                            
                                            # Extract author_info and sub_track from abstract
                                            author_info = ""
                                            sub_track = ""
                                            clinical_trial_registry_number = ""  # New field
                                            
                                            # Check if abstract exists
                                            abstract_data = presentation_item.get("abstract")
                                            if isinstance(abstract_data, dict):
                                                # Extract author_info from both abstractAuthorsString and authorInstitutionsString
                                                abstract_authors = abstract_data.get("abstractAuthorsString", "")
                                                author_institutions = abstract_data.get("authorInstitutionsString", "")
                                                
                                                # Remove HTML tags from author info
                                                abstract_authors = remove_html_tags(abstract_authors)
                                                author_institutions = remove_html_tags(author_institutions)
                                                
                                                # Format author_info: "abstractAuthorsString"; "authorInstitutionsString"
                                                if abstract_authors and author_institutions:
                                                    author_info = f'"{abstract_authors}"; "{author_institutions}"'
                                                elif abstract_authors:
                                                    author_info = abstract_authors
                                                elif author_institutions:
                                                    author_info = author_institutions
                                                
                                                # Extract sub_track
                                                sub_track_dict = abstract_data.get("subTrack")
                                                if isinstance(sub_track_dict, dict) and "subTrack" in sub_track_dict:
                                                    sub_track = sub_track_dict["subTrack"]
                                                else:
                                                    sub_track = ""
                                                
                                                # Extract clinical trial registry number
                                                clinical_trial_registry_number = abstract_data.get("clinicalTrialRegistryNumber", "")
                                                # Remove HTML tags if present
                                                clinical_trial_registry_number = remove_html_tags(str(clinical_trial_registry_number))
                                            
                                            # Remove HTML tags from all fields
                                            title = remove_html_tags(title)
                                            session_name = remove_html_tags(session_name)
                                            location = remove_html_tags(location)
                                            session_description = remove_html_tags(session_description)
                                            attendance_type = remove_html_tags(attendance_type)
                                            ce_credit = remove_html_tags(str(ce_credit))  # Added HTML tag removal
                                            doi = remove_html_tags(doi)
                                            abstract_number = remove_html_tags(abstract_number)
                                            poster_board_number = remove_html_tags(poster_board_number)
                                            sub_track = remove_html_tags(sub_track)
                                            session_type = remove_html_tags(session_type)
                                            session_track = remove_html_tags(session_track)
                                            link = remove_html_tags(link)
                                            date = remove_html_tags(date) if date else date
                                            session_time = remove_html_tags(session_time) if session_time else session_time
                                            presentation_time = remove_html_tags(presentation_time) if presentation_time else presentation_time
                                            presentation_id = remove_html_tags(presentation_id) if presentation_id else presentation_id
                                            
                                            # Create a dictionary for each title with all fields
                                            extracted_titles.append({
                                                "link": link,
                                                "title": title,
                                                "doi": doi,
                                                "number": "",
                                                "author_info": author_info,
                                                "abstract": "",
                                                "abstract_html": "",
                                                "abstract_markdown": "",
                                                "abstract_metadata": {
                                                    "sub_track": sub_track,
                                                    "session_name": session_name,
                                                    "session_track": session_track,
                                                    "abstract_number": abstract_number,
                                                    "poster_board_number": poster_board_number,
                                                    "session_id": session_id,
                                                    "session_type": session_type,
                                                    "ce_credit": ce_credit,  # Added new field
                                                    "date": date,
                                                    "session_time": session_time,
                                                    "presentation_time": presentation_time,
                                                    "presentation_id": presentation_id,  # New field added here
                                                    "location": location,
                                                    "session_description": session_description,
                                                    "attendance_type": attendance_type,
                                                    "clinical_TrialRegistry_Number": clinical_trial_registry_number
                                                }
                                            })
        
        # Save the extracted titles to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_titles, f, indent=4, ensure_ascii=False)
        
        print(f"Successfully extracted {len(extracted_titles)} titles.")
        print(f"Data saved to {output_file}")
        
        # Print first few titles as example
        print("\nFirst 5 items as example:")
        for i, item_dict in enumerate(extracted_titles[:5]):
            print(f"{i+1}. Title: {item_dict['title']}")
            print(f"   Abstract Number: {item_dict['abstract_metadata']['abstract_number']}")
            print(f"   DOI: {item_dict['doi']}")
            print(f"   Poster Board Number: {item_dict['abstract_metadata']['poster_board_number']}")
            print(f"   Author Info: {item_dict['author_info'][:100]}...")
            print(f"   Sub Track: {item_dict['abstract_metadata']['sub_track']}")
            print(f"   Session Name: {item_dict['abstract_metadata']['session_name']}")
            print(f"   Session Track: {item_dict['abstract_metadata']['session_track']}")
            print(f"   Session ID: {item_dict['abstract_metadata']['session_id']}")
            print(f"   Session Type: {item_dict['abstract_metadata']['session_type']}")
            print(f"   CE Credit: {item_dict['abstract_metadata']['ce_credit']}")  # Added
            print(f"   Date: {item_dict['abstract_metadata']['date']}")
            print(f"   Session Time: {item_dict['abstract_metadata']['session_time']}")
            print(f"   Presentation Time: {item_dict['abstract_metadata']['presentation_time']}")
            print(f"   Presentation ID: {item_dict['abstract_metadata']['presentation_id']}")  # New field in output
            print(f"   Location: {item_dict['abstract_metadata']['location']}")
            print(f"   Session Description: {item_dict['abstract_metadata']['session_description'][:100]}...")
            print(f"   Attendance Type: {item_dict['abstract_metadata']['attendance_type']}")
            print(f"   Clinical Trial Registry Number: {item_dict['abstract_metadata']['clinical_TrialRegistry_Number']}")
            print(f"   Link: {item_dict['link']}\n")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
if __name__ == "__main__":
    input_file = "presentation_api_data.json"  # Replace with your input file path
    output_file = "presentation_data.json"  # Output file
    extract_titles_from_new_structure(input_file, output_file)