import json
from pathlib import Path

file_path = Path(r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v1\asco_2026_abstracts.json")

def reformat_file(path):
    if not path.exists():
        print(f"Error: {path} does not exist.")
        return
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        abstracts = data.get("abstracts", [])
        new_abstracts = []
        
        for abs_obj in abstracts:
            # Reformat title from list to string if necessary
            title = abs_obj.get("title")
            if isinstance(title, list) and len(title) > 0:
                abs_obj["title"] = title[0]
            elif not title:
                abs_obj["title"] = ""
                
            # Ensure all abstract_metadata fields are present (from your list)
            meta = abs_obj.get("abstract_metadata", {})
            required_meta = [
                "sub_track", "session_name", "session_track", "abstract_number",
                "poster_board_number", "session_id", "session_type", "ce_credit",
                "date", "session_time", "presentation_time", "presentation_id",
                "location", "session_description", "attendance_type", "clinical_TrialRegistry_Number"
            ]
            for key in required_meta:
                if key not in meta:
                    meta[key] = ""
            
            abs_obj["abstract_metadata"] = meta
            new_abstracts.append(abs_obj)
            
        # Create final structure
        final_output = {
            "meeting_name": "ASCO 2026 Annual Meeting",
            "date": "2026-05-26", # Representative start date
            "link": "https://meetings.asco.org",
            "abstracts": new_abstracts
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=4, ensure_ascii=False)
            
        print(f"Successfully reformatted {len(new_abstracts)} abstracts in {path}")
        
    except Exception as e:
        print(f"Failed to reformat: {e}")

if __name__ == "__main__":
    reformat_file(file_path)
