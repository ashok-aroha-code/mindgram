import json
from collections import Counter, defaultdict

def find_duplicate_dois(json_file_path):
    try:
        # Read the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Extract DOIs, titles, links and their associated information
        doi_info = defaultdict(list)
        title_info = defaultdict(list)
        link_info = defaultdict(list)
        
        # Check if data has 'abstracts' key (based on your sample structure)
        if 'abstracts' in data:
            abstracts = data['abstracts']
        else:
            # If the JSON is directly a list of abstracts
            abstracts = data
        
        # Process each abstract
        for abstract in abstracts:
            doi = abstract.get('doi', '').strip()
            link = abstract.get('link', '').strip()
            title = abstract.get('title', '').strip()
            
            # Process DOIs
            if doi:
                doi_info[doi].append({
                    'link': link,
                    'title': title
                })
            
            # Process titles
            if title:
                title_info[title].append({
                    'doi': doi,
                    'link': link
                })
            
            # Process links
            if link:
                link_info[link].append({
                    'doi': doi,
                    'title': title
                })
        
        # Find duplicates
        duplicate_dois = {doi: entries for doi, entries in doi_info.items() if len(entries) > 1}
        duplicate_titles = {title: entries for title, entries in title_info.items() if len(entries) > 1}
        duplicate_links = {link: entries for link, entries in link_info.items() if len(entries) > 1}
        
        # Count statistics
        total_entries = len(abstracts)
        unique_dois = len(doi_info)
        unique_titles = len(title_info)
        unique_links = len(link_info)
        duplicate_dois_count = len(duplicate_dois)
        duplicate_titles_count = len(duplicate_titles)
        duplicate_links_count = len(duplicate_links)
        total_duplicate_doi_entries = sum(len(entries) for entries in duplicate_dois.values())
        total_duplicate_title_entries = sum(len(entries) for entries in duplicate_titles.values())
        total_duplicate_link_entries = sum(len(entries) for entries in duplicate_links.values())
        
        return {
            'statistics': {
                'total_entries': total_entries,
                'unique_dois': unique_dois,
                'unique_titles': unique_titles,
                'unique_links': unique_links,
                'duplicate_dois_count': duplicate_dois_count,
                'duplicate_titles_count': duplicate_titles_count,
                'duplicate_links_count': duplicate_links_count,
                'total_duplicate_doi_entries': total_duplicate_doi_entries,
                'total_duplicate_title_entries': total_duplicate_title_entries,
                'total_duplicate_link_entries': total_duplicate_link_entries
            },
            'duplicate_dois': duplicate_dois,
            'duplicate_titles': duplicate_titles,
            'duplicate_links': duplicate_links
        }
    
    except FileNotFoundError:
        print(f"Error: File '{json_file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file '{json_file_path}'.")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def print_duplicate_report(results):
    
    if not results:
        return
    
    stats = results['statistics']
    duplicate_dois = results['duplicate_dois']
    duplicate_titles = results['duplicate_titles']
    duplicate_links = results['duplicate_links']
    
    print("=" * 80)
    print("DUPLICATE ANALYSIS REPORT (DOI, TITLE, LINK)")
    print("=" * 80)
    
    print(f"\nSTATISTICS:")
    print(f"  Total entries in file: {stats['total_entries']}")
    print(f"  Unique DOIs found: {stats['unique_dois']}")
    print(f"  Unique titles found: {stats['unique_titles']}")
    print(f"  Unique links found: {stats['unique_links']}")
    print(f"  Number of duplicate DOIs: {stats['duplicate_dois_count']}")
    print(f"  Number of duplicate titles: {stats['duplicate_titles_count']}")
    print(f"  Number of duplicate links: {stats['duplicate_links_count']}")
    print(f"  Total entries with duplicate DOIs: {stats['total_duplicate_doi_entries']}")
    print(f"  Total entries with duplicate titles: {stats['total_duplicate_title_entries']}")
    print(f"  Total entries with duplicate links: {stats['total_duplicate_link_entries']}")
    
    # Report duplicate DOIs
    if duplicate_dois:
        print(f"\nDUPLICATE DOIs FOUND:")
        print("-" * 80)
        
        for i, (doi, entries) in enumerate(duplicate_dois.items(), 1):
            print(f"\n{i}. DOI: {doi}")
            print(f"   Appears {len(entries)} times:")
            
            for j, entry in enumerate(entries, 1):
                print(f"   {j}. Link: {entry['link']}")
                if entry['title']:
                    # Truncate long titles for better display
                    title = entry['title'][:100] + "..." if len(entry['title']) > 100 else entry['title']
                    print(f"      Title: {title}")
            print("-" * 40)
    else:
        print(f"\n No duplicate DOIs found! All DOIs are unique.")
    
    # Report duplicate titles
    if duplicate_titles:
        print(f"\nDUPLICATE TITLES FOUND:")
        print("-" * 80)
        
        for i, (title, entries) in enumerate(duplicate_titles.items(), 1):
            # Truncate long titles for better display
            display_title = title[:100] + "..." if len(title) > 100 else title
            print(f"\n{i}. Title: {display_title}")
            print(f"   Appears {len(entries)} times:")
            
            for j, entry in enumerate(entries, 1):
                print(f"   {j}. DOI: {entry['doi']}")
                print(f"      Link: {entry['link']}")
            print("-" * 40)
    else:
        print(f"\n No duplicate titles found! All titles are unique.")
    
    # Report duplicate links
    if duplicate_links:
        print(f"\nDUPLICATE LINKS FOUND:")
        print("-" * 80)
        
        for i, (link, entries) in enumerate(duplicate_links.items(), 1):
            print(f"\n{i}. Link: {link}")
            print(f"   Appears {len(entries)} times:")
            
            for j, entry in enumerate(entries, 1):
                print(f"   {j}. DOI: {entry['doi']}")
                if entry['title']:
                    # Truncate long titles for better display
                    title = entry['title'][:100] + "..." if len(entry['title']) > 100 else entry['title']
                    print(f"      Title: {title}")
            print("-" * 40)
    else:
        print(f"\n No duplicate links found! All links are unique.")

def save_duplicates_to_file(results, output_file='duplicate_analysis.json'):

    if not results or (not results['duplicate_dois'] and not results['duplicate_titles'] and not results['duplicate_links']):
        print("No duplicates to save.")
        return
    
    with open("only_title.txt", 'w', encoding='utf-8') as file:
        for k in results['duplicate_titles'].keys():
            file.write(k + "\n")
    
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(results, file, indent=4, ensure_ascii=False)
    
    print(f"\n Duplicate analysis saved to: {output_file}")

# Main execution
if __name__ == "__main__":
    # Default ASCO 2026 path
    json_file_path = r"D:\Workspace\Projects\mindgram\data\meetings.asco.org\asco_2026\v1\asco_2026_abstracts.json"
    
    print("Analyzing JSON file for duplicate DOIs, titles, and links...")
    
    # Find duplicates
    results = find_duplicate_dois(json_file_path)
    
    if results:
        # Print report
        print_duplicate_report(results)
        
        # Save results to file (optional)
        save_duplicates_to_file(results)
        
        # Quick summary
        duplicate_dois_count = results['statistics']['duplicate_dois_count']
        duplicate_titles_count = results['statistics']['duplicate_titles_count']
        duplicate_links_count = results['statistics']['duplicate_links_count']
        
        print(f"\n SUMMARY:")
        print(f"  Found {duplicate_dois_count} duplicate DOI(s)")
        print(f"  Found {duplicate_titles_count} duplicate title(s)")
        print(f"  Found {duplicate_links_count} duplicate link(s)")
    
    print("\nAnalysis complete!")