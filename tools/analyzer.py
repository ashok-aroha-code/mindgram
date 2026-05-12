import argparse
import json
import random
import sys
import os
import time
import requests
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

prompt_template = """
You are an expert system designed to analyze HTML structures and provide robust CSS selectors for web scraping.
I will provide you with the minified HTML of an academic abstract or journal page.

Your task is to identify and return the CSS selectors for the following core fields, ensuring every field from the schema is represented. 
If a field is inherently dynamic (like the URL itself), specify that string instead of a selector.

1. link (This is the URL itself, just output "RUNTIME_VAR")
2. title
3. doi
4. number (The abstract ID or issue number if available, else empty)
5. author_info (the elements containing author names)
6. abstract (the main wrapper containing the abstract text)
7. abstract_html (Use the exact same CSS selector as you did for `abstract`)
8. abstract_markdown (Use the exact same CSS selector as you did for `abstract`)

Additionally, review the page for any other valuable dynamic metadata fields (e.g., publication date, keywords, volume, issue, metrics) and provide their names and selectors under `abstract_metadata`.

Respond ONLY with a valid JSON object that follows this exact format strictly:
{{
  "core_fields": {{
    "link": "RUNTIME_VAR",
    "title": "selector",
    "doi": "selector",
    "number": "selector",
    "author_info": "selector",
    "abstract": "selector",
    "abstract_html": "selector",
    "abstract_markdown": "selector"
  }},
  "abstract_metadata": {{
    "metadata_field_1": "selector",
    "metadata_field_2": "selector"
  }}
}}

Do not provide explanations, warnings, or format the text outside of the raw JSON blocks.

Here is the HTML to analyze:
{html_content}
"""

def clean_html(html_source):
    soup = BeautifulSoup(html_source, 'lxml')
    for tag in soup(['script', 'style', 'svg', 'nav', 'footer', 'noscript', 'meta', 'link', 'header', 'form', 'button', 'iframe']):
        tag.decompose()
        
    for tag in soup.find_all(True):
        for attr in ['style', 'd', 'xmlns', 'viewBox', 'path', 'onchange', 'onclick']:
            if attr in tag.attrs:
                del tag.attrs[attr]
                
    return str(soup)

def json_to_yaml_str(data_dict):
    """Converts the specific dict structure to a YAML string without PyYAML dependency."""
    lines = []
    
    if "core_fields" in data_dict:
        lines.append("core_fields:")
        for k, v in data_dict["core_fields"].items():
            v_safe = str(v).replace('"', '\\"') if v else ""
            lines.append(f'  {k}: "{v_safe}"')
            
    if "abstract_metadata" in data_dict:
        lines.append("\nabstract_metadata:")
        for k, v in data_dict["abstract_metadata"].items():
            v_safe = str(v).replace('"', '\\"') if v else ""
            lines.append(f'  {k}: "{v_safe}"')
            
    return "\n".join(lines)


def call_mistral(html_content):
    if not MISTRAL_API_KEY:
        print("ERROR: MISTRAL_API_KEY not found in .env")
        sys.exit(1)
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MISTRAL_API_KEY}"
    }
    
    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "user", "content": prompt_template.format(html_content=html_content[:50000])}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    print("Calling Mistral API for analysis (this may take a moment)...")
    resp = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
    if resp.status_code != 200:
        print(f"Mistral API Error: {resp.text}")
        sys.exit(1)
        
    return resp.json()['choices'][0]['message']['content']

def run():
    parser = argparse.ArgumentParser(description="Global DOM Analyzer for Smart Scraping")
    parser.add_argument("--input", required=True, help="Path to JSON file containing list of URLs")
    parser.add_argument("--output", required=True, help="Path to save the YAML selector report")
    
    args = parser.parse_args()
    
    with open(args.input, "r", encoding="utf-8") as f:
        urls = json.load(f)
        
    if not urls:
        print("Input file is empty!")
        sys.exit(1)
        
    max_attempts = 5
    successful_data = None
    
    for attempt in range(1, max_attempts + 1):
        target_url = random.choice(urls)
        print(f"\n--- Attempt {attempt}/{max_attempts} ---")
        print(f"Target URL: {target_url}")
        
        # Setup Driver Options freshly for each attempt to avoid reuse errors
        options = uc.ChromeOptions()
        options.page_load_strategy = 'eager'
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1280,800")
        options.add_argument("--disable-dev-shm-usage")
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.fonts": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        driver = None
        raw_html = ""
        try:
            driver = uc.Chrome(options=options)
            print("Loading page to extract DOM...")
            driver.get(target_url)
            time.sleep(5) # Allow internal dynamics to build DOM
            
            raw_html = driver.page_source
            
        except Exception as e:
            print(f"Error launching browser: {e}")
            sys.exit(1)
        finally:
            if driver:
                try:
                    driver_ref = driver
                    driver_ref.quit()
                    driver_ref.quit = lambda: None
                except Exception:
                    pass
                    
        clean_dom = clean_html(raw_html)
        print(f"Minified DOM footprint: {len(clean_dom)} chars.")
        
        json_resp = call_mistral(clean_dom)
        
        try:
            data = json.loads(json_resp)
        except json.JSONDecodeError:
            print("Failed to decode JSON from Mistral. Retrying...")
            continue
            
        core = data.get("core_fields", {})
        
        # Validation Check
        title = core.get("title", "")
        author_info = core.get("author_info", "")
        abstract = core.get("abstract", "")
        doi = core.get("doi", "")
        
        missing = []
        if not title: missing.append("title")
        if not author_info: missing.append("author_info")
        if not abstract: missing.append("abstract")
        if not doi: missing.append("doi")
        
        if missing:
            print(f"Validation Failed! Missing mandatory fields: {', '.join(missing)}")
            print("Likely an irregularly formatted page (erratum, index, etc.). Retrying...")
            continue
            
        # If we reach here, it's successful
        successful_data = data
        break
        
    if not successful_data:
        print("\nERROR: Failed to extract a valid mapped schema after 5 attempts. The site layout may be incompatible or all sampled links lacked abstracts.")
        sys.exit(1)
        
    yaml_content = json_to_yaml_str(successful_data)
    
    output_dir = os.path.dirname(os.path.abspath(args.output))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(yaml_content)
        
    print(f"\nSuccess! Verified selectors report written to: {args.output}")

if __name__ == "__main__":
    run()
