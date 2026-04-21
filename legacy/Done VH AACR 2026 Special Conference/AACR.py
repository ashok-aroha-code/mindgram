import json
import time
import logging
import random
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

def setup_driver():
    """Setup and return a configured undetected Chrome driver instance to bypass bot detection."""
    # Using undetected_chromedriver to bypass bot detection
    options = uc.ChromeOptions()
    options.headless = False
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Add random user agent to appear more human-like
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Add more anti-detection options
    options.add_argument("--disable-automation")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    
    # Random viewport size - more natural than fixed size
    viewports = [
        (1920, 1080),
        (1366, 768),
        (1440, 900),
        (1536, 864),
        (1680, 1050),
        (2560, 1440)
    ]
    viewport = random.choice(viewports)
    
    # Create driver with specified options - add version handling
    try:
        # Try to create driver with version 146 to match current Chrome browser
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
    
    # Set random window size
    driver.set_window_size(*viewport)
    
    # Execute JavaScript to make navigator.webdriver undefined
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Additional anti-fingerprinting JavaScript
    driver.execute_script("""
    // Hide automation-specific properties
    navigator.__defineGetter__('languages', () => ['en-US', 'en']);
    navigator.__defineGetter__('plugins', () => {
        return [1, 2, 3, 4, 5];  // Fake plugins number
    });
    
    // Randomize canvas fingerprint
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (type === 'image/png' && this.width === 16 && this.height === 16) {
            // This could be a favicon check
            return originalToDataURL.apply(this, arguments);
        }
        return originalToDataURL.apply(this, [type]);
    };
    """)
    
    # Add cookies to simulate a real user
    driver.get("https://aacrjournals.org")
    cookies = [
        {'name': 'visited', 'value': 'true'},
        {'name': 'session_depth', 'value': '1'},
        {'name': 'user_pref', 'value': 'site_viewed'},
        {'name': 'cookie_consent', 'value': 'accepted'}
    ]
    for cookie in cookies:
        driver.add_cookie(cookie)
    
    return driver

def wait_for_element(driver, selector, by=By.XPATH, timeout=10):
    """Wait for element to be present and return it."""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    except TimeoutException:
        logging.error(f"Timeout waiting for element: {selector}")
        return None

def get_text_safely(driver, selector, by=By.XPATH):
    """Safely get text from an element with error handling."""
    try:
        element = wait_for_element(driver, selector, by)
        if element:
            return element.text.strip().replace("\n", " ").replace("\r", " ")
        return ""
    except (TimeoutException, NoSuchElementException) as e:
        logging.error(f"Error getting text for selector {selector}: {str(e)}")
        return ""

def scrape_article(driver, url):
    """Scrape a single article's data using the provided driver."""
    failures = []
    try:
        # Navigate to actual target page with random delay
        driver.get(url)
        time.sleep(random.uniform(3, 7))  # Random initial load wait
        
        # Scraping logic - now using XPath instead of CSS selectors
        title = get_text_safely(driver, "//h1[contains(@class, 'wi-article-title') and contains(@class, 'article-title-main')]")
        if not title:
            failures.append("Missing title")   
            
        # Extract number from title (text before colon)
        number = ""
        processed_title = title
        if title and ":" in title:
            parts = title.split(":", 1)
            number = parts[0].strip().replace("Abstract ", "")

        doi = get_text_safely(driver, "//div[contains(@class, 'citation-doi')]/a") 
        if not doi:
            failures.append("missing doi")

        session_name = get_text_safely(driver, "//div[contains(@class, 'article-groups') and contains(@class, 'left-flag')]/span[contains(@class, 'article-client_type')]")
        if not session_name:
            failures.append("missing session name")    

        date = get_text_safely(driver, "//div[contains(@class, 'article-groups') and contains(@class, 'left-flag')]/span[contains(@class, 'article-date')]")  
        if not date:
            failures.append("missing date") 

        # Use BeautifulSoup to extract all authors and affiliations
        author_info = ""
        try:
            # Get the page HTML
            page_html = driver.page_source
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # Try multiple selector patterns to find authors
            authors_list = []
            
            # Strategy 1: Look for common author list containers
            author_elements = soup.select('.info-card-name, .author-name, .wi-authors .author-item')
            if author_elements:
                authors_list = [element.text.strip() for element in author_elements if element.text.strip()]
            
            # Strategy 2: If no results, try alternative selectors
            if not authors_list:
                author_elements = soup.select('[class*="author-name"], [class*="authorName"], .contributor-name')
                authors_list = [element.text.strip() for element in author_elements if element.text.strip()]
            
            # Strategy 3: Try to find a container with authors
            if not authors_list:
                # Look for containers that might hold authors
                author_containers = soup.select('.authors-list, .author-group, .contribs, .contributors')
                for container in author_containers:
                    names = container.select('li, .name, span[class*="name"]')
                    if names:
                        authors_list = [name.text.strip() for name in names if name.text.strip()]
                        break
            
            # Get affiliations using the specified tag
            affiliation_elements = soup.select('div.info-card-affilitation')
            affiliations_list = []
            for element in affiliation_elements:
                if element.text.strip():
                    # Extract the span label text and the rest of the text separately
                    span_label = element.select_one('span.label.title-label')
                    if span_label:
                        span_text = span_label.text.strip()
                        full_text = element.text.strip()
                        remaining_text = full_text[len(span_text):].strip()
                        affiliations_list.append(f"{span_text} {remaining_text}")
                    else:
                        affiliations_list.append(element.text.strip())
            
            # Combine authors and affiliations
            combined_list = []
            for i in range(max(len(authors_list), len(affiliations_list))):
                author = authors_list[i] if i < len(authors_list) else "Unknown Author"
                affiliation = affiliations_list[i] if i < len(affiliations_list) else ""
                
                if affiliation:
                    combined_list.append(f"{author}; {affiliation}")
                else:
                    combined_list.append(author)
            
            # Join all combined author-affiliation pairs
            if combined_list:
                author_info = " ".join(combined_list)
            else:
                # Fallback to just author names if pairing fails
                author_info = " ".join(authors_list) if authors_list else ""
            
        except Exception as e:
            failures.append(f"Error extracting authors/affiliations with BeautifulSoup: {str(e)}")
        
        if not author_info:
            failures.append("missing author info")    

        abstract = get_text_safely(driver, "//div[contains(@class, 'article-section-wrapper') and contains(@class, 'js-article-section') and contains(@class, 'js-content-section')]")
        if not abstract:
            failures.append("missing abstract")    
            
        abstract_html = ""
        try:
            abstract_element = wait_for_element(driver, "//div[contains(@class, 'article-section-wrapper') and contains(@class, 'js-article-section') and contains(@class, 'js-content-section')]")
            if abstract_element:
                abstract_html = abstract_element.get_attribute("outerHTML")
                # Prettify the HTML using BeautifulSoup
                soup = BeautifulSoup(abstract_html, 'html.parser')
                abstract_html = soup.prettify()  # Prettify the HTML
        except Exception as e:
            failures.append(f"missing abstract_HTML: {str(e)}")    

        result = {
            "link": url,
            "doi": doi,
            "number": number,  
            "title": processed_title,  
            "author_info": author_info,
            "abstract": abstract,
            "abstract_htm": abstract_html,
            "abstract_markdown": "",
            "abstract_metadata": {
                "session_name": session_name,
                "date": date
            }
        }
        return result, failures
        
    except Exception as e:
        logging.error(f"General error scraping {url}: {str(e)}")
        failures.append(f"General error: {str(e)}")
        return None, failures

def scrape_articles_single_window(urls):
    """Scrape multiple articles using a single window."""
    articles_data = []
    failed_urls = {}
    total_urls = len(urls)
    completed_urls = 0
    
    print(f"Starting to scrape {total_urls} URLs with a single window...")
    
    # Setup a single driver
    driver = None
    try:
        driver = setup_driver()
        
        # Add cookies and storage handling to mimic regular browser first
        driver.get("https://aacrjournals.org")
        time.sleep(random.uniform(2, 5))
        
        # Process each URL sequentially
        for url in urls:
            try:
                print(f"Scraping URL {completed_urls + 1}/{total_urls}: {url}")
                data, failures = scrape_article(driver, url)
                
                if data:
                    articles_data.append(data)
                
                if failures:
                    failed_urls[url] = failures
                    
                completed_urls += 1
                print(f"Completed {completed_urls}/{total_urls} URLs")
                
                # Add random delay between requests to seem more natural
                time.sleep(random.uniform(3, 7))
                
            except Exception as e:
                logging.error(f"Error processing {url}: {str(e)}")
                failed_urls[url] = ["Failed to process URL"]
                completed_urls += 1
                print(f"Failed URL {completed_urls}/{total_urls}")
    
    except Exception as e:
        logging.error(f"Error setting up driver: {str(e)}")
        print(f"Error setting up driver: {str(e)}")
    
    finally:
        if driver:
            # Add a random delay before quitting to seem more natural
            time.sleep(random.uniform(2, 5))
            try:
                driver.quit()
            except Exception as e:
                print(f"Error closing browser: {e}")
    
    # Save failed URLs to JSON
    if failed_urls:
        try:
            with open('failed_urls.json', 'w', encoding='utf-8') as f:
                json.dump(failed_urls, f, indent=4, ensure_ascii=False)
            print(f"Saved {len(failed_urls)} failed URLs to failed_urls.json")
        except Exception as e:
            logging.error(f"Error saving failed URLs: {str(e)}")
    
    return articles_data

def main():
    """Main function to run the scraper."""
    logging.basicConfig(
        filename='scraper.log',
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Load URLs
    try:
        with open('article_urls.json', 'r') as f:
            urls = json.load(f)
        print(f"Loaded {len(urls)} URLs from article_urls.json")
    except Exception as e:
        logging.error(f"Error loading URLs: {str(e)}")
        print(f"Error loading URLs: {str(e)}")
        return
    
    # Scrape articles using a single window
    articles_data = scrape_articles_single_window(urls)
    
    # Save results
    if articles_data:
        try:
            output_filename = 'scraped_data.json'
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(articles_data, f, indent=4, ensure_ascii=False)
            print(f"Successfully scraped {len(articles_data)} articles. Data saved to {output_filename}")
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            print(f"Error saving data: {str(e)}")
    else:
        print("No articles were successfully scraped")

if __name__ == "__main__":
    main()