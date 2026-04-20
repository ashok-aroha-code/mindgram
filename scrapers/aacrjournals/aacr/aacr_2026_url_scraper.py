import os
import json
import time
import sys
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Fix sys.path to allow imports from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

from utils import save_json


BASE_URL = "https://aacrjournals.org/cancerres/issue/86/8_Supplement"
FILE_PATH = os.path.join(BASE_DIR, "data", "aacr_2026_urls.json")


class Driver:
    def __init__(self):
        self.options = uc.ChromeOptions()
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")

        self.driver = uc.Chrome(
            options=self.options,
            use_subprocess=True,
            version_main=None,
        )

    def get_driver(self):
        return self.driver

    def close(self):
        self.driver.quit()


class ScrapeAACRLinks:
    def __init__(self, driver):
        self.driver = driver

    def open_page(self, url):
        self.driver.get(url)

        input(">>> Click done on cloudflare\t>>> ")

        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            print("Page loaded successfully — no manual CAPTCHA needed!")
        except Exception:
            input(
                ">>> Solve the CAPTCHA in the browser, then press Enter to continue..."
            )

    def open_all_toggles(self):
        print("🔍 Expanding all toggles...")
        expanded_count = 0
        while True:
            # Find toggles that are still closed (using the right-pointing arrow icon)
            toggles = self.driver.find_elements(
                By.CSS_SELECTOR, "i.js-toggle-icon.icon-general_arrow-right"
            )

            # Filter for visible toggles only
            visible_toggles = [t for t in toggles if t.is_displayed()]

            if not visible_toggles:
                break

            clicked_any = False
            for toggle in visible_toggles:
                try:
                    # Scroll into view to ensure it's clickable
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                        toggle,
                    )
                    time.sleep(0.5)

                    # Try clicking the icon directly, or its parent if it's not clickable
                    try:
                        toggle.click()
                    except Exception:
                        parent = toggle.find_element(By.XPATH, "..")
                        parent.click()

                    clicked_any = True
                    expanded_count += 1
                    time.sleep(3)  # Wait for expansion animation/loading
                except Exception as e:
                    print(f"⚠️ Could not click toggle: {e}")

            if not clicked_any:
                break

        print(f"✅ Expanded {expanded_count} sections.")

    def extract_links(self):
        links_data = []

        try:
            # Find all article links
            articles = self.driver.find_elements(
                By.CSS_SELECTOR, "div.al-article-items a, a.at-articleLink"
            )
            for article in articles:
                href = article.get_attribute("href")
                title = article.text.strip()

                if (
                    href
                    and "/article/" in href
                    and href not in [l["url"] for l in links_data]
                ):
                    if title:  # Avoid empty links
                        links_data.append({"title": title, "url": href})
        except Exception as e:
            print(f"An error occurred: {e}")

        return links_data

    def scrape_all_links(self):
        links_data = []
        try:
            self.open_page(BASE_URL)
            self.open_all_toggles()

            print("🔗 Extracting article links...")
            links_data = self.extract_links()

            print(f"📊 Found {len(links_data)} article links.")

            # Save to JSON
            save_json(links_data, FILE_PATH)
            print(f"💾 Saved {len(links_data)} URLs to {FILE_PATH}")

        except Exception as e:
            print(f"❌ An error occurred: {e}")

        return links_data


def main():
    driver = Driver()
    scraper = ScrapeAACRLinks(driver.get_driver())
    scraper.scrape_all_links()
    driver.close()  # Cleanup happens here, correctly, in main()


if __name__ == "__main__":
    main()
