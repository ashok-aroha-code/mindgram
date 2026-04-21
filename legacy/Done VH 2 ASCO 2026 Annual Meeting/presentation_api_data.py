import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# GraphQL endpoint
URL = "https://api.asco.org/graphql2"

# Updated Headers from your new request - WITHOUT pseudo-headers (:authority, :method, :path, :scheme)
HEADERS = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyMDIzMDEwMSIsIm5hbWUiOiJQdWJsaWNBY2Nlc3MiLCJzY29wZSI6ImFwaS5hc2NvLm9yZy9ncmFwaHFsLnB1YmxpYyIsImNsaWVudF9pZCI6InB1YmxpYyIsImlhdCI6MTY3MjUzMTIwMH0.8aei14SeARjdpov618hKodzJLwnQuW6c4WuBg6PZPcU',
    'content-type': 'application/json',
    'origin': 'https://meetings.asco.org',
    'priority': 'u=1, i',
    'referer': 'https://meetings.asco.org/',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'x-api-key': 'da2-wgzqv6hk3bea3axyz6hslo33my'
}

# Updated GraphQL query template (from your new payload)
GRAPHQL_QUERY = """query getSession($sessionId: String!) {
  __typename
  session(sessionId: $sessionId) {
    result {
      ...main
      ...ceRecord
      ...presentations
      __typename
    }
    status
    errors {
      code
      message
      __typename
    }
    __typename
  }
}

fragment main on Session {
  edBookReference {
    doi
    url {
      fqdn
      path
      queryParams
      target
      title
      __typename
    }
    __typename
  }
  inpersonContent
  onlineContent
  sponsoredCompanyName
  isOnDemandOnly
  feedbackFormId
  attendanceType
  sessionLocation
  cmeCredits
  fullSummary
  ceParsActivity {
    activityId
    __typename
  }
  sessionNotes {
    notes
    timeStamp
    __typename
  }
  isInPerson
  uid
  contentId
  title
  sessionType
  playerEmbed {
    fqdn
    path
    queryParams
    target
    title
    __typename
  }
  sessionLiveBroadcastFlag
  hasSlidesAccess
  hasVideosAccess
  tracks {
    track
    __typename
  }
  url {
    path
    target
    title
    fqdn
    queryParams
    __typename
  }
  claimCEurl {
    path
    target
    title
    fqdn
    queryParams
    __typename
  }
  frontMatterInfo {
    activityType
    coiLink
    funders
    __typename
  }
  mediaVideos {
    m3u8 {
      path
      target
      title
      fqdn
      queryParams
      __typename
    }
    mp4 {
      path
      target
      title
      fqdn
      queryParams
      __typename
    }
    mediaDuration
    previewLowRes {
      path
      target
      title
      fqdn
      queryParams
      __typename
    }
    previewHiRes {
      path
      target
      title
      fqdn
      queryParams
      __typename
    }
    chapterMeta {
      path
      target
      title
      fqdn
      queryParams
      __typename
    }
    chapterMarker {
      path
      target
      title
      fqdn
      queryParams
      __typename
    }
    slideMarker {
      path
      target
      title
      fqdn
      queryParams
      __typename
    }
    __typename
  }
  sessionDates {
    start
    end
    timeZone
    __typename
  }
  liveBroadcastUrl {
    path
    target
    title
    fqdn
    queryParams
    __typename
  }
  meeting {
    uid
    contentId
    title
    abstractTitleReleaseDate {
      start
      __typename
    }
    abstractReleaseDate {
      start
      __typename
    }
    productBundlePurchaseUrl {
      path
      target
      title
      fqdn
      queryParams
      __typename
    }
    registrationURL {
      path
      target
      title
      fqdn
      queryParams
      __typename
    }
    meetingDates {
      end
      __typename
    }
    meetingChatPasscode
    meetingYear
    meetingType {
      meetingType
      name
      active
      displayOrder
      __typename
    }
    ceMeeting {
      displayClaimEndDate
      isAbimAvailable
      isAbpAvailable
      feedbackFormId
      feedbackEndDate
      frontMatterTemplate
      __typename
    }
    __typename
  }
  downloadAllUrl {
    path
    target
    title
    fqdn
    queryParams
    __typename
  }
  isBookMarked
  isInAgenda
  __typename
}

fragment ceRecord on Session {
  contentId
  hasSlidesAccess
  hasVideosAccess
  ceRecord {
    ascoId
    ceCreditsClaimed
    buttonStatus
    ceStatus
    buttonProps {
      cssClass
      icon
      text
      __typename
    }
    claimCreditPercent
    accreditationType
    feedbackQuestionAnswers {
      questionNo
      answer
      __typename
    }
    cePersonalInfo {
      firstName
      lastName
      birthDateTs
      licenseState
      licenseId
      abimId
      abpId
      absId
      showPersonalInfo
      __typename
    }
    __typename
  }
  __typename
}

fragment presentations on Session {
  presentations {
    contentId
    url {
      path
      target
      title
      fqdn
      queryParams
      __typename
    }
    tracks {
      track
      __typename
    }
    presentation {
      slidesUrl {
        path
        target
        title
        fqdn
        queryParams
        __typename
      }
      videoUrl {
        path
        target
        title
        fqdn
        queryParams
        __typename
      }
      doiUrl {
        path
        target
        title
        fqdn
        queryParams
        __typename
      }
      title
      isInAgenda
      abstractNumber
      posterBoardNumber
      disclosureUrl {
        path
        target
        title
        fqdn
        queryParams
        __typename
      }
      recordable
      orderWithinSession
      presentationType
      presentationDates {
        start
        end
        timeZone
        __typename
      }
      discussedAbstracts {
        contentId
        abstractId
        abstractNumber
        abstractTitle
        __typename
      }
      discussedPosters
      __typename
    }
    abstract {
      abstractAuthorsString
      authorInstitutionsString
      disclosureUrl {
        path
        target
        title
        fqdn
        queryParams
        __typename
      }
      subTrack {
        subTrack
        __typename
      }
      doi
      abstractTitle
      abstractNumber
      abstractId
      fullBody
      fundingSources {
        __typename
        organizationType
        organizationName
      }
      tempAbstractId
      journalCitation
      posterBoardNumber
      abstractType
      originalResearchFlag
      clinicalTrialRegistryNumber
      downloadUrl {
        path
        target
        title
        fqdn
        queryParams
        __typename
      }
      __typename
    }
    mediaVideos {
      m3u8 {
        path
        target
        title
        fqdn
        queryParams
        __typename
      }
      mp4 {
        path
        target
        title
        fqdn
        queryParams
        __typename
      }
      mediaDuration
      previewHiRes {
        path
        target
        title
        fqdn
        queryParams
        __typename
      }
      previewLowRes {
        path
        target
        title
        fqdn
        queryParams
        __typename
      }
      __typename
    }
    mediaSlides {
      pptDeck {
        path
        target
        title
        fqdn
        queryParams
        __typename
      }
      __typename
    }
    visibleDates {
      posters
      __typename
    }
    __typename
  }
  __typename
}"""

# Thread-safe print lock
print_lock = threading.Lock()

# Read session IDs from JSON file
def load_session_ids_from_file(file_path):
    """Load session IDs from a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ids_data = json.load(f)
        
        # Handle if IDs are in a nested structure
        if isinstance(ids_data, dict):
            # Try common key names for session IDs
            for key in ['session_ids', 'sessions', 'ids', 'data', 'sessionIds']:
                if key in ids_data:
                    ids_data = ids_data[key]
                    break
        
        # Convert all IDs to strings (GraphQL expects String type)
        if isinstance(ids_data, list):
            session_ids = [str(session_id) for session_id in ids_data]
        elif isinstance(ids_data, dict):
            # If it's a dict with IDs as keys
            session_ids = [str(session_id) for session_id in ids_data.keys()]
        else:
            raise ValueError("Session IDs must be in a list or dict format")
        
        print(f"✓ Loaded {len(session_ids)} session IDs from {file_path}")
        return session_ids
    
    except FileNotFoundError:
        print(f"✗ Error: File '{file_path}' not found")
        return None
    except json.JSONDecodeError:
        print(f"✗ Error: Invalid JSON format in '{file_path}'")
        return None
    except Exception as e:
        print(f"✗ Error loading session IDs: {e}")
        return None

# Create GraphQL payload for a specific session ID
def create_payload(session_id):
    """Create GraphQL payload with the given session ID"""
    payload = {
        "operationName": None,
        "variables": {
            "sessionId": str(session_id)
        },
        "query": GRAPHQL_QUERY
    }
    return payload

# Fetch data for a single session ID - returns raw API response
def fetch_session_data(session_id, max_retries=3):
    """Fetch GraphQL data for a single session ID and return raw response"""
    payload = create_payload(session_id)
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                URL, 
                headers=HEADERS, 
                json=payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                # Return the raw JSON response exactly as it comes
                return response.json()
                    
            elif response.status_code == 429:
                # Rate limited - wait and retry
                wait_time = (attempt + 1) * 2  # Exponential backoff
                with print_lock:
                    print(f"  ⚠ Session {session_id}: Rate limited, waiting {wait_time}s (attempt {attempt + 1})")
                time.sleep(wait_time)
                continue
                
            else:
                with print_lock:
                    print(f"  ✗ Session {session_id}: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            with print_lock:
                print(f"  ⚠ Session {session_id}: Timeout (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return None
            
        except requests.exceptions.RequestException as e:
            with print_lock:
                print(f"  ✗ Session {session_id}: Request error - {e}")
            return None
            
        except json.JSONDecodeError:
            with print_lock:
                print(f"  ✗ Session {session_id}: Invalid JSON response")
            return None
            
        except Exception as e:
            with print_lock:
                print(f"  ✗ Session {session_id}: Unexpected error - {e}")
            return None
    
    return None

# Main function with sequential processing
def main_sequential():
    # Input file containing session IDs
    ids_file = 'session_ids.json'  # Change this to your JSON file name
    
    # Output file - raw API data
    output_file = 'asco_raw_api_data.json'
    
    print("=" * 60)
    print("ASCO Raw API Data Collection Script (Sequential)")
    print("=" * 60)
    
    # Load session IDs from file
    session_ids = load_session_ids_from_file(ids_file)
    
    if not session_ids:
        print("\n✗ No session IDs to process. Exiting.")
        return
    
    total_ids = len(session_ids)
    print(f"\nStarting data collection for {total_ids} sessions...")
    print("-" * 60)
    
    collected_data = []
    successful = 0
    failed = 0
    
    # Process all session IDs sequentially
    for idx, session_id in enumerate(session_ids, 1):
        print(f"[{idx}/{total_ids}] Fetching session {session_id}...", end=" ")
        
        raw_response = fetch_session_data(session_id)
        
        if raw_response:
            # Store the raw response directly
            collected_data.append(raw_response)
            successful += 1
            print("✓")
        else:
            failed += 1
            print("✗")
        
        # Add delay to avoid overwhelming the server
        time.sleep(1)
    
    # Save all collected raw data to a single JSON file
    if collected_data:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(collected_data, f, indent=4, ensure_ascii=False)
            
            print(f"\n✓ All raw API data saved to '{output_file}'")
            print(f"  • Successfully collected: {successful}")
            print(f"  • Failed: {failed}")
            
        except Exception as e:
            print(f"\n✗ Error saving data: {e}")
    else:
        print(f"\n✗ No data was collected")
    
    # Print final summary
    print("\n" + "=" * 60)
    print("Raw API data collection completed!")
    print("=" * 60)
    
    print(f"\nOverall Summary:")
    print(f"  • Total sessions processed: {total_ids}")
    print(f"  • Successfully collected: {successful}")
    print(f"  • Failed: {failed}")
    
    print("\n" + "=" * 60)

# Main function with parallel processing (faster)
def main_parallel(max_workers=5):
    """Process sessions in parallel for faster collection - save raw API data"""
    # Input file containing session IDs
    ids_file = 'session_ids.json'  # Change this to your JSON file name
    
    # Output file - raw API data
    output_file = 'asco_raw_api_data_parallel.json'
    
    print("=" * 60)
    print(f"ASCO Raw API Data Collection Script (Parallel - {max_workers} workers)")
    print("=" * 60)
    
    # Load session IDs from file
    session_ids = load_session_ids_from_file(ids_file)
    
    if not session_ids:
        print("\n✗ No session IDs to process. Exiting.")
        return
    
    total_ids = len(session_ids)
    print(f"\nStarting parallel data collection for {total_ids} sessions...")
    print("-" * 60)
    
    collected_data = []
    successful = 0
    failed = 0
    
    # Process session IDs in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_session = {
            executor.submit(fetch_session_data, session_id): session_id 
            for session_id in session_ids
        }
        
        # Process completed tasks
        for idx, future in enumerate(as_completed(future_to_session), 1):
            session_id = future_to_session[future]
            
            try:
                raw_response = future.result()
                if raw_response:
                    # Store the raw response directly
                    collected_data.append(raw_response)
                    successful += 1
                    with print_lock:
                        print(f"[{idx}/{total_ids}] Session {session_id}: ✓")
                else:
                    failed += 1
                    with print_lock:
                        print(f"[{idx}/{total_ids}] Session {session_id}: ✗")
            except Exception as e:
                failed += 1
                with print_lock:
                    print(f"[{idx}/{total_ids}] Session {session_id}: Error - {e}")
    
    # Save all collected raw data to a single JSON file
    if collected_data:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(collected_data, f, indent=4, ensure_ascii=False)
            
            print(f"\n✓ All raw API data saved to '{output_file}'")
            print(f"  • Successfully collected: {successful}")
            print(f"  • Failed: {failed}")
            
        except Exception as e:
            print(f"\n✗ Error saving data: {e}")
    else:
        print(f"\n✗ No data was collected")
    
    # Print final summary
    print("\n" + "=" * 60)
    print("Raw API data collection completed!")
    print("=" * 60)
    
    print(f"\nOverall Summary:")
    print(f"  • Total sessions processed: {total_ids}")
    print(f"  • Successfully collected: {successful}")
    print(f"  • Failed: {failed}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Choose which method to use:
    # 1. Sequential (safer, avoids rate limiting)
    main_sequential()
    
    # 2. Parallel (faster, but might hit rate limits)
    # main_parallel(max_workers=3)  # Start with 3 workers, adjust as needed
    
    # Note: If you get rate limited, use main_sequential() instead
    # or reduce max_workers in main_parallel()