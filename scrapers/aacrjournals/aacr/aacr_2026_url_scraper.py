import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "https://aacrjournals.org/cancerres/issue/86/8_Supplement"


class Driver:
    def __init__(self):
        self.options = uc.ChromeOptions()
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")

        # FIX 1: Removed duplicate uc.Chrome() initialization — only one instance now
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
            print("✅ Page loaded successfully — no manual CAPTCHA needed!")
        except Exception:
            input(
                ">>> Solve the CAPTCHA in the browser, then press Enter to continue..."
            )

    def scrapp_all_links(self):
        # FIX 2: Removed the finally block calling scraper.close() — 'scraper' was
        # not in scope here. Cleanup is handled by driver.close() in main().
        try:
            self.open_page(BASE_URL)
        except Exception as e:
            print(f"An error occurred: {e}")


def main():
    driver = Driver()
    scraper = ScrapeAACRLinks(driver.get_driver())
    scraper.scrapp_all_links()
    driver.close()  # Cleanup happens here, correctly, in main()


if __name__ == "__main__":
    main()
