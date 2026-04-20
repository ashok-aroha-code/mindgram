import json
import os
import re
from html import unescape
from datetime import datetime

def extract_data(input_file, output_file):
    """
    Extract title, link, session_link, and author_info from JSON file.
    All other fields are kept empty.
    """
    try:
        # Load the JSON data
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        extracted_data = []
        
        # Base URLs
        presentation_base_url = "https://www.abstractsonline.com/pp8/#!/21436/presentation/"
        session_base_url = "https://www.abstractsonline.com/pp8/#!/21436/session/"
        
        # Process each session in the data
        if isinstance(data, dict):
            print(f"Found {len(data)} sessions in the data")
            
            for session_id, session_data in data.items():
                print(f"Processing session {session_id}...")
                
                # Process each presentation in the session
                if isinstance(session_data, list):
                    for presentation in session_data:
                        if isinstance(presentation, dict):
                            # Extract title from SearchResultBody
                            title = clean_text(presentation.get("SearchResultBody", ""))
                            
                            # Extract and format author_info from AuthorBlock
                            author_info_raw = presentation.get("AuthorBlock", "")
                            author_info = format_author_info(author_info_raw)
                            
                            # Extract number from PresentationNumber
                            number = presentation.get("PresentationNumber", "")
                            
                            # Extract abstract (cleaned text) and abstract_html (raw)
                            abstract_raw = presentation.get("Abstract", "")
                            abstract = clean_text(abstract_raw)
                            abstract_html = abstract_raw  # Keep raw HTML as is
                            
                            # Build links
                            presentation_id = presentation.get("Id", "")
                            session_id_value = presentation.get("SessionId", "")
                            
                            link = f"{presentation_base_url}{presentation_id}" if presentation_id else ""
                            session_link = f"{session_base_url}{session_id_value}" if session_id_value else ""
                            
                            # Extract additional metadata fields
                            session_name = clean_text(presentation.get("SessionTitle", ""))
                            session_id_meta = presentation.get("SessionId", "")
                            presentation_id_meta = presentation.get("Id", "")
                            
                            # Format date
                            start_datetime = presentation.get("Start", "")
                            date_formatted = format_date(start_datetime)
                            
                            # Format time range
                            end_datetime = presentation.get("End", "")
                            time_range = format_time_range(start_datetime, end_datetime)
                            
                            # Location (if available, otherwise empty string)
                            location = ""  # No location field in sample data
                            
                            # Create entry with only the six required fields populated
                            entry = {
                                "link": link,
                                "title": title,
                                "doi": "",
                                "number": number,
                                "author_info": author_info,
                                "abstract": abstract,
                                "abstract_html": abstract_html,
                                "abstract_markdown": "",
                                "abstract_metadata": {
                                    "session_link": session_link,
                                    "session_name": session_name,
                                    "presentation_id": presentation_id_meta,
                                    "date": date_formatted,
                                    "time": time_range,
                                    "location": location,
                                    "session_track": "",
                                    "session_type": "",
                                    "description": "",
                                    "session_id": session_id_meta,
                                }
                            }
                            
                            extracted_data.append(entry)
                    
                    print(f"  Added {len(session_data)} presentations from session")
        
        else:
            print("Unexpected data format. Expected a dictionary.")
            return
        
        # Save the extracted data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=4, ensure_ascii=False)
        
        print(f"\nSuccessfully processed {len(extracted_data)} total entries.")
        
        # Print sample data
        if extracted_data:
            print("\nSample extracted data (first 3 entries):")
            for i, item in enumerate(extracted_data[:3]):
                print(f"\nEntry {i + 1}:")
                print(f"  Title: {item['title']}")
                print(f"  Link: {item['link']}")
                print(f"  Number: {item['number']}")
                print(f"  Abstract: {item['abstract'][:100]}..." if len(item['abstract']) > 100 else f"  Abstract: {item['abstract']}")
                print(f"  Abstract HTML: {item['abstract_html'][:100]}..." if len(item['abstract_html']) > 100 else f"  Abstract HTML: {item['abstract_html']}")
                print(f"  Session Link: {item['abstract_metadata']['session_link']}")
                print(f"  Author Info: {item['author_info']}")
                print(f"  Session Name: {item['abstract_metadata']['session_name']}")
                print(f"  Session ID: {item['abstract_metadata']['session_id']}")
                print(f"  Presentation ID: {item['abstract_metadata']['presentation_id']}")
                print(f"  Date: {item['abstract_metadata']['date']}")
                print(f"  Time: {item['abstract_metadata']['time']}")
                print(f"  Location: {item['abstract_metadata']['location']}")
        
    except json.JSONDecodeError as e:
        print(f"JSON syntax error in input file: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

def format_author_info(author_block):
    """Format author information by separating authors and affiliations with semicolon"""
    if not author_block or not isinstance(author_block, str):
        return ""
    
    # Add spaces around sup tags to ensure proper spacing
    author_block = re.sub(r'<sup>', ' <sup>', author_block)
    author_block = re.sub(r'</sup>', '</sup> ', author_block)
    
    # Check if there's a double br tag separating authors and affiliations
    if "<br><br/>" in author_block:
        # Split into authors and affiliations parts
        parts = author_block.split("<br><br/>")
        authors_part = parts[0]
        affiliations_part = parts[1] if len(parts) > 1 else ""
        
        # Clean the authors part
        authors_cleaned = clean_text(authors_part)
        
        # Clean the affiliations part but preserve superscript numbers
        # First, temporarily mark sup tags to preserve them
        affiliations_part = re.sub(r'<sup>(\d+)</sup>', r'[[SUP:\1]]', affiliations_part)
        affiliations_cleaned = clean_text(affiliations_part)
        # Restore sup numbers with proper formatting
        affiliations_cleaned = re.sub(r'\[\[SUP:(\d+)\]\]', r' \1', affiliations_cleaned)
        
        # Combine with semicolon
        return f"{authors_cleaned}; {affiliations_cleaned}"
    else:
        # If no double br tag, just clean the text normally
        return clean_text(author_block)

def clean_text(text):
    """Clean text by removing HTML tags, unescaping entities, and normalizing whitespace"""
    if text is None:
        return ""
    
    # Convert to string if not already
    if not isinstance(text, str):
        text = str(text)
    
    # Unescape HTML entities
    text = unescape(text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def format_date(date_string):
    """
    Convert date string from format "4/17/2026 1:00:00 PM" to "Tuesday, 17 March, 2026"
    """
    if not date_string:
        return ""
    
    try:
        # Parse the date string
        # Example: "4/17/2026 1:00:00 PM"
        dt = datetime.strptime(date_string, "%m/%d/%Y %I:%M:%S %p")
        
        # Format as "Tuesday, 17 March, 2026"
        return dt.strftime("%A, %d %B, %Y")
    except (ValueError, TypeError):
        return ""

def format_time_range(start_string, end_string):
    """
    Convert start and end time strings to format "1:00:00 - 4:00:00"
    """
    if not start_string or not end_string:
        return ""
    
    try:
        # Parse the start time string
        # Example: "4/17/2026 1:00:00 PM"
        start_dt = datetime.strptime(start_string, "%m/%d/%Y %I:%M:%S %p")
        
        # Parse the end time string
        end_dt = datetime.strptime(end_string, "%m/%d/%Y %I:%M:%S %p")
        
        # Format times as "HH:MM:SS"
        start_time = start_dt.strftime("%H:%M:%S")
        end_time = end_dt.strftime("%H:%M:%S")
        
        return f"{start_time} - {end_time}"
    except (ValueError, TypeError):
        return ""

if __name__ == "__main__":
    # Input and output file paths
    input_file = "session_presentation_api_data.json"  # Replace with your input JSON file path
    output_file = "presentation_data.json"  # Output file path
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Files in directory: {os.listdir('.')}")
    else:
        print(f"Input file found: {input_file}")
        extract_data(input_file, output_file)
        print(f"\nData extracted and saved to: {output_file}")