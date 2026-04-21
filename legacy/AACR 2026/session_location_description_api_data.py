import requests
import json
import time
from datetime import datetime

def collect_session_data(ids_file_path, output_file=None):
    """
    Collect data from session URLs and save to a JSON file.
    
    Args:
        ids_file_path: Path to the JSON file containing session IDs
        output_file: Optional output file path, defaults to timestamped filename
    """
    # Set up timestamp for the output file if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"session_location_description_data.json"
    
    # Read session IDs from JSON file
    try:
        with open(ids_file_path, 'r') as f:
            session_ids = json.load(f)
        
        if not isinstance(session_ids, list):
            print("Error: JSON file should contain a list of session IDs")
            return
            
        print(f"Loaded {len(session_ids)} session IDs from {ids_file_path}")
    except Exception as e:
        print(f"Error loading session IDs: {str(e)}")
        return
    
    # Set up the session with headers from the new request
    session = requests.session()
    headers = {
        'accept': 'application/json',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-US,en;q=0.9',
        'backpack': 'fc1c7fbf-ad1b-4394-ad77-6a0275642b11',
        'connection': 'keep-alive',
        'content-type': 'application/json',
        'host': 'www.abstractsonline.com',
        'referer': 'https://www.abstractsonline.com/pp8/',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }
    session.headers.update(headers)
    
    # Collect data for each session ID
    all_session_data = {}
    total_ids = len(session_ids)
    
    for index, session_id in enumerate(session_ids, 1):
        # Construct URL for this session ID using the new URL pattern
        url = f"https://www.abstractsonline.com/oe3/Program/21436/Session/{session_id}"
        
        print(f"[{index}/{total_ids}] Fetching session ID {session_id} - {url}")
        
        try:
            # Make the request
            response = session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                all_session_data[session_id] = data
                print(f"  ✓ Success - Retrieved data for session ID {session_id}")
            else:
                print(f"  ✗ Error - HTTP {response.status_code} for session ID {session_id}")
                all_session_data[session_id] = {"error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            print(f"  ✗ Exception for session ID {session_id}: {str(e)}")
            all_session_data[session_id] = {"error": str(e)}
        
        # Be nice to the server with a delay between requests
        if index < total_ids:
            delay = 1.5  # seconds
            print(f"  Waiting {delay} seconds before next request...")
            time.sleep(delay)
    
    # Save the collected data
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_session_data, f, ensure_ascii=False, indent=2)
        print(f"\nData collection complete! Saved to {output_file}")
        print(f"Successfully collected data for {sum(1 for v in all_session_data.values() if 'error' not in v)} sessions")
        print(f"Failed to collect data for {sum(1 for v in all_session_data.values() if 'error' in v)} sessions")
    except Exception as e:
        print(f"Error saving data: {str(e)}")
    
    return all_session_data

if __name__ == "__main__":
    # Replace with your actual file path containing session IDs
    ids_file_path = "session_ids.json"
    collect_session_data(ids_file_path)