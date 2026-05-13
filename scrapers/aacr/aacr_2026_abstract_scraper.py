import time
import random
import os
from bs4 import BeautifulSoup
from loguru import logger
from selenium.webdriver.common.by import By

from scrapers.base import BaseScraper
from utils import load_json, save_json, wait_for_element, get_text_safely

class AACR2026AbstractScraper(BaseScraper):
    def __init__(self):
        super().__init__(name="AACR_2026_Abstract")
        self.input_file = os.path.join("data", "aacrjournals", "aacr_2026", "aacr_2026_urls.json")
        self.output_file = os.path.join("data", "aacrjournals", "aacr_2026", "aacr_2026_abstracts.json")
        self.failed_file = os.path.join("data", "aacrjournals", "aacr_2026", "failed_abstract_urls.json")

    def execute(self):
        data = load_json(self.input_file)
        urls = [item["url"] for item in data if "url" in item]
        if not urls:
            logger.error("No URLs found to scrape.")
            return

        logger.info(f"Loaded {len(urls)} URLs. Starting scrape...")
        self.driver.get("https://aacrjournals.org") # Initial visit for cookies
        time.sleep(random.uniform(2, 5))

        articles_data = []
        failed_urls = {}

        for index, url in enumerate(urls):
            try:
                logger.info(f"Scraping {index+1}/{len(urls)}: {url}")
                result, failures = self.scrape_article(url)
                if result:
                    articles_data.append(result)
                if failures:
                    failed_urls[url] = failures
                
                # Checkpoint saving every 10 articles
                if (index + 1) % 10 == 0:
                    save_json(articles_data, self.output_file)
                
                time.sleep(random.uniform(3, 7))
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                failed_urls[url] = [str(e)]

        save_json(articles_data, self.output_file)
        if failed_urls:
            save_json(failed_urls, self.failed_file)

    def scrape_article(self, url):
        failures = []
        try:
            self.driver.get(url)
            time.sleep(random.uniform(3, 7))
            
            title = get_text_safely(self.driver, "//h1[contains(@class, 'wi-article-title')]", by=By.XPATH)
            if not title: failures.append("Missing title")
            
            number = title.split(":", 1)[0].replace("Abstract ", "").strip() if ":" in title else ""
            doi = get_text_safely(self.driver, "//div[contains(@class, 'citation-doi')]/a", by=By.XPATH)
            session_name = get_text_safely(self.driver, "//span[contains(@class, 'article-client_type')]", by=By.XPATH)
            date = get_text_safely(self.driver, "//span[contains(@class, 'article-date')]", by=By.XPATH)
            
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            author_info = self.extract_authors_and_affiliations(soup)
            
            abstract_element = wait_for_element(self.driver, "//div[contains(@class, 'js-article-section')]", by=By.XPATH)
            abstract_text = abstract_element.text.strip() if abstract_element else "-"
            abstract_html = soup.find("div", class_="js-article-section").prettify() if soup.find("div", class_="js-article-section") else "-"

            return {
                "link": url,
                "doi": doi,
                "number": number,
                "title": title,
                "author_info": author_info,
                "abstract": abstract_text,
                "abstract_htm": abstract_html,
                "abstract_markdown": "",
                "abstract_metadata": {"session_name": session_name, "date": date},
            }, failures
        except Exception as e:
            return None, [str(e)]

    def extract_authors_and_affiliations(self, soup):
        authors = [e.text.strip() for e in soup.select(".info-card-name, .author-name, .wi-authors .author-item")]
        affs = []
        for e in soup.select("div.info-card-affilitation"):
            label = e.select_one("span.label.title-label")
            text = e.text.strip()
            affs.append(f"{label.text.strip()} {text[len(label.text.strip()):].strip()}" if label else text)
        
        combined = []
        for i in range(max(len(authors), len(affs))):
            a = authors[i] if i < len(authors) else "Unknown"
            af = affs[i] if i < len(affs) else ""
            combined.append(f"{a}; {af}" if af else a)
        return " ".join(combined)

if __name__ == "__main__":
    AACR2026AbstractScraper().run()
