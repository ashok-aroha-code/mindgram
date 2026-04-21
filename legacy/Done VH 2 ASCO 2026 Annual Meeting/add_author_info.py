import json

def merge_author_info(first_file_path, second_file_path, output_file_path):
    """
    Match entries from two JSON files using presentation_id and add author_info
    from first file to second file.
    
    Args:
        first_file_path (str): Path to first JSON file containing author_info
        second_file_path (str): Path to second JSON file to update with author_info
        output_file_path (str): Path where the merged JSON will be saved
    """
    
    # Read the first JSON file
    with open(first_file_path, 'r', encoding='utf-8') as file:
        first_data = json.load(file)
    
    # Read the second JSON file
    with open(second_file_path, 'r', encoding='utf-8') as file:
        second_data = json.load(file)
    
    # Create a dictionary mapping presentation_id to author_info from first file
    author_map = {}
    for item in first_data:
        presentation_id = item.get('presentation_id')
        author_info = item.get('author_info', '')
        if presentation_id:  # Only add if presentation_id exists
            author_map[presentation_id] = author_info
    
    print(f"Loaded {len(author_map)} author entries from first file")
    
    # Update second file with author_info where presentation_id matches
    updated_count = 0
    for item in second_data:
        # Get presentation_id from abstract_metadata
        abstract_metadata = item.get('abstract_metadata', {})
        presentation_id = abstract_metadata.get('presentation_id')
        
        if presentation_id and presentation_id in author_map:
            # Update author_info in the main object
            item['author_info'] = author_map[presentation_id]
            updated_count += 1
            print(f"Updated presentation_id {presentation_id} with author: {author_map[presentation_id]}")
    
    print(f"\nTotal updates: {updated_count} out of {len(second_data)} entries")
    
    # Save the updated data to a new JSON file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump(second_data, file, indent=4, ensure_ascii=False)
    
    print(f"Updated data saved to: {output_file_path}")
    
    return second_data

# Example usage
if __name__ == "__main__":
    # Replace these with your actual file paths
    first_file = "author_info_data.json"      # Path to your first JSON file
    second_file = "presentation_data.json"    # Path to your second JSON file
    output_file = "1_presentation_data.json"  # Path for the output file
    
    try:
        merged_data = merge_author_info(first_file, second_file, output_file)
        print("\nMerge completed successfully!")
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
    except Exception as e:
        print(f"Error: {e}")