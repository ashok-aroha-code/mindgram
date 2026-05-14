import time
import re
import os
from bs4 import BeautifulSoup
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapers.base import BaseScraper
from utils import load_json, save_json, dismiss_cookie_banner, safe_click

class ASEScraper2024Abstract(BaseScraper):
    def __init__(self, **kwargs):
        super().__init__(name="ASE_2024_Abstract", **kwargs)
        self.link_file = os.path.join("data", "sciencedirect", "ase_2024", "ase_2024_links.json")
        self.output_file = os.path.join("data", "sciencedirect", "ase_2024", "ase_2024_abstracts.json")
        self.base_url = "https://www.sciencedirect.com/journal/journal-of-the-american-society-of-echocardiography"
        
        self.selectors = {
            "title": "#screen-reader-main-title > span",
            "doi": "#article-identifier-links > a.anchor.doi.anchor-primary > span > span",
            "author_info": ".AuthorGroups",
            "abstract": "#abstracts",
        }

    def execute(self):
        links = load_json(self.link_file)
        if not links:
            logger.error("No links found to scrape.")
            return

        final_data = load_json(self.output_file)
        if not final_data or not isinstance(final_data, dict):
            final_data = {
                "meeting_name": "ASE 2024",
                "date": "2024",
                "link": self.base_url,
                "abstracts": [],
            }
        
        existing_links = {a.get("link") for a in final_data.get("abstracts", [])}
        logger.info(f"Resuming with {len(existing_links)} existing abstracts.")

        for index, link in enumerate(links[:5], start=1): # Limit for testing or as per original
            if link in existing_links:
                continue
            
            abstract_data = self.process_abstract(link, index)
            if abstract_data:
                final_data["abstracts"].append(abstract_data)
                save_json(final_data, self.output_file)
                self.hb.wait_randomly(2.0, 5.0)

    def process_abstract(self, url, index):
        try:
            logger.info(f"Scraping: {url}")
            self.driver.get(url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "screen-reader-main-title"))
            )
            dismiss_cookie_banner(self.driver)
            self.hb.humanize()
            
            soup = BeautifulSoup(self.driver.page_source, "lxml")
            
            title_tag = soup.select_one(self.selectors["title"])
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            doi_tag = soup.select_one(self.selectors["doi"])
            doi = re.sub(r"https?://doi\.org/", "", doi_tag.get_text(strip=True)) if doi_tag else ""
            
            authors = self.extract_authors(soup)
            affiliations = self.extract_affiliations(soup)
            
            abstract_tag = soup.select_one(self.selectors["abstract"])
            abstract_text = abstract_tag.get_text(separator="\n\n", strip=True) if abstract_tag else "-"
            abstract_html = str(abstract_tag) if abstract_tag else "-"

            return {
                "link": url,
                "title": title,
                "doi": doi,
                "number": str(index),
                "author_info": f"{authors}; {affiliations}" if affiliations else authors,
                "abstract": abstract_text,
                "abstract_html": abstract_html,
                "abstract_markdown": "",
                "abstract_metadata": {},
            }
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None

    def extract_authors(self, soup):
        authors = []
        for group in soup.select(self.selectors["author_info"]):
            for tag in group.select(".author-group button, .author-group a"):
                name_tag = tag.select_one(".react-xocs-alternative-link")
                if name_tag:
                    name = name_tag.get_text(" ", strip=True)
                    refs = " ".join([ref.get_text(strip=True) for ref in tag.select(".author-ref")])
                    authors.append(f"{name} {refs}".strip())
        return ", ".join(authors)

    def extract_affiliations(self, soup):
        if soup.select_one("#show-more-btn"):
            if safe_click(self.driver, "#show-more-btn", timeout=5):
                time.sleep(1)
                soup = BeautifulSoup(self.driver.page_source, "lxml")
        return " ".join([aff.get_text(" ", strip=True) for aff in soup.select("dl.affiliation")])

if __name__ == "__main__":
    ASEScraper2024Abstract().run()
