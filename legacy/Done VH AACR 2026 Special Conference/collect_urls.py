import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time
import random
from collections import OrderedDict

def setup_driver():
    # Using undetected_chromedriver to bypass bot detection
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    
    # Add random user agent to appear more human-like
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Create driver with specified options - add version_main parameter to handle version mismatch
    try:
        # Try to create driver with automatic version detection
        driver = uc.Chrome(options=options, version_main=146)
    except Exception as e:
        print(f"Failed with version_main=146, trying without version specification: {e}")
        try:
            # Fallback: let undetected_chromedriver detect version automatically
            driver = uc.Chrome(options=options)
        except Exception as e2:
            print(f"Failed again, trying with version_main=None: {e2}")
            # Another fallback: try with version_main set to None
            driver = uc.Chrome(options=options, version_main=None)
    
    # Set window size to a common resolution
    driver.set_window_size(1920, 1080)
    
    # Execute JavaScript to make navigator.webdriver undefined
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def human_like_scroll(driver):
    """Scroll the page in a human-like manner"""
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    current_position = 0
    
    while current_position < total_height:
        # Random scroll amount
        scroll_amount = random.randint(100, 300)
        current_position += scroll_amount
        
        # Scroll to new position
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        
        # Random pause to simulate reading
        time.sleep(random.uniform(0.5, 2.0))

def extract_urls_from_current_page(driver):
    urls = []
    try:
        print("Attempting to extract URLs...")
        
        # First, try different CSS selectors that might contain article links
        possible_selectors = [
          "h3.customLink.item-title a"
        ]
        
        # Try each selector
        for selector in possible_selectors:
            print(f"Trying selector: {selector}")
            try:
                elements = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    for element in elements:
                        url = element.get_attribute('href')
                        if url and url not in urls:
                            urls.append(url)
            except:
                continue  # Move to next selector if this one fails
        
        # If still no URLs found, try a more general approach - get all links 
        if not urls:
            print("No URLs found with specific selectors. Trying general approach...")
            # Get all links that might be article links
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                try:
                    url = link.get_attribute('href')
                    # Filter for likely article URLs
                    if url and ('article' in url or 'abstract' in url or 'doi' in url):
                        if url not in urls:
                            urls.append(url)
                except:
                    continue
        
        # Last resort - dump the page HTML for manual inspection
        if not urls:
            print("No URLs found. Saving page HTML for manual inspection...")
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Page source saved to 'page_source.html'")
            
        return urls
        
    except Exception as e:
        print(f"Error occurred during URL extraction: {str(e)}")
        # Save page source on error for debugging
        with open('error_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("Error page source saved to 'error_page_source.html'")
        return urls

def extract_all_urls():
    driver = None
    all_urls = OrderedDict()
    
    try:
        driver = setup_driver()
        
        # Start URL
        start_url = "https://aacrjournals.org/cancerres/issue/86/5_Supplement_1"
        print(f"Navigating to URL: {start_url}")
        
        # Add cookies and storage handling to mimic regular browser
        driver.get("https://aacrjournals.org")
        time.sleep(random.uniform(1, 2))
        
        # Now navigate to actual target page
        driver.get(start_url)
        
        # Wait with random delay for initial page load
        time.sleep(random.uniform(3, 7))
        
        # Interactive mode for button click
        print("\n" + "=" * 50)
        print("If you see a button that needs to be clicked to reveal URLs,")
        print("please click it now. The script will wait.")
        print("=" * 50 + "\n")
        
        input("Press Enter after all content is visible...")
        
        # Perform human-like scrolling to ensure all content loads
        human_like_scroll(driver)
        
        # Give extra time for any dynamic content to load
        time.sleep(5)
        
        # Extract URLs from the page
        urls = extract_urls_from_current_page(driver)
        
        if urls:
            all_urls["page_1"] = urls
            print(f"Total URLs collected: {len(urls)}")
            
            # Print first few URLs as a sample
            print("\nSample of URLs found:")
            for i, url in enumerate(urls[:5]):
                print(f"{i+1}. {url}")
                
        else:
            print("No URLs found")
            all_urls["page_1"] = []
        
        return all_urls
        
    except Exception as e:
        print(f"General error in extraction: {str(e)}")
        return all_urls
        
    finally:
        print("Closing browser...")
        try:
            if driver:
                # Add a random delay before quitting to seem more natural
                time.sleep(random.uniform(1, 2))
                driver.quit()
        except Exception as e:
            print(f"Error closing browser: {str(e)}")
            # Ignore errors during browser closing

def save_to_json(urls_dict):
    if urls_dict:
        with open('article_urls.json', 'w', encoding='utf-8') as f:
            json.dump(urls_dict, f, indent=2, ensure_ascii=False)
        
        # Calculate total URLs
        total_urls = sum(len(urls) for urls in urls_dict.values())
        print(f"Successfully saved {total_urls} URLs from {len(urls_dict)} pages to all_article_urls.json")
    else:
        print("No URLs found to save")

if __name__ == "__main__":
    print("Starting URL extraction with improved selectors...")
    # First install undetected-chromedriver if not installed
    try:
        import undetected_chromedriver
    except ImportError:
        print("Installing undetected-chromedriver...")
        import subprocess
        subprocess.check_call(["pip", "install", "undetected-chromedriver"])
        print("Installation complete.")
    
    extracted_urls = extract_all_urls()
    save_to_json(extracted_urls)
    print("Script completed.")