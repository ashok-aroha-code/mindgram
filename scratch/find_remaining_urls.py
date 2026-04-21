import json
import os

def main():
    base_dir = r"d:\Workspace\Projects\mindgram\data\aacrjournals\aacr_2026\v2"
    urls_file = os.path.join(base_dir, "aacr_2026_urls.json")
    abstracts_file = os.path.join(base_dir, "aacr_2026_abstracts.json")
    output_file = os.path.join(base_dir, "aacr_2026_remaining_urls.json")

    # Load all URLs
    with open(urls_file, "r", encoding="utf-8") as f:
        all_url_items = json.load(f)
    
    # Load successful URLs
    with open(abstracts_file, "r", encoding="utf-8") as f:
        scraped_items = json.load(f)
    
    scraped_urls = {item.get("link", "").strip().lower() for item in scraped_items}
    
    remaining = []
    for item in all_url_items:
        url = item.get("url", "").strip().lower()
        if url not in scraped_urls:
            remaining.append(item)
    
    print(f"Total URLs: {len(all_url_items)}")
    print(f"Scraped Abstracts: {len(scraped_items)}")
    print(f"Remaining URLs: {len(remaining)}")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(remaining, f, indent=4)
    
    print(f"Saved remaining URLs to: {output_file}")

if __name__ == "__main__":
    main()
