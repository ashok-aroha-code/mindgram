import json

def compare_json_by_link(file1_path, file2_path, output_path):
    """
    Compare two JSON files with the given structure based on the 'link' field.
    Save entries from the first file that do NOT have a matching 'link' in the second file.
    
    Args:
        file1_path (str): Path to first JSON file
        file2_path (str): Path to second JSON file
        output_path (str): Path to save unmatched entries
    """
    # Load both JSON files
    with open(file1_path, 'r', encoding='utf-8') as f1:
        data1 = json.load(f1)
    
    with open(file2_path, 'r', encoding='utf-8') as f2:
        data2 = json.load(f2)
    
    # Extract all links from the second file into a set for fast lookup
    links_in_file2 = set()
    for item in data2.get("abstracts", []):
        link = item.get("link")
        if link:
            links_in_file2.add(link)
    
    # Find unmatched entries from file1 (links not present in file2)
    unmatched_entries = []
    for item in data1.get("abstracts", []):
        link = item.get("link")
        if link not in links_in_file2:
            unmatched_entries.append(item)
    
    # Create output structure similar to original
    output_data = {
        "meeting_id": data1.get("meeting_id"),
        "meeting_name": data1.get("meeting_name"),
        "start_date": data1.get("start_date"),
        "end_date": data1.get("end_date"),
        "from_website": data1.get("from_website"),
        "meeting_bucket_id": data1.get("meeting_bucket_id"),
        "abstracts": unmatched_entries
    }
    
    # Save unmatched entries to new JSON file
    with open(output_path, 'w', encoding='utf-8') as out_f:
        json.dump(output_data, out_f, indent=4, ensure_ascii=False)
    
    print(f"Comparison complete:")
    print(f"  - Total entries in file1: {len(data1.get('abstracts', []))}")
    print(f"  - Total entries in file2: {len(data2.get('abstracts', []))}")
    print(f"  - Unmatched entries saved: {len(unmatched_entries)}")
    print(f"  - Output saved to: {output_path}")

# Example usage
if __name__ == "__main__":
    # Replace these with your actual file paths
    file1 = "D:\mindgram uploaded\AACR 2026 Annual Meeting 15-04-2026.json"
    file2 = "D:\mindgram uploaded\AACR 2026 Annual Meeting 18-03-2026.json"
    output = "unmatched_entries.json"
    
    compare_json_by_link(file1, file2, output)