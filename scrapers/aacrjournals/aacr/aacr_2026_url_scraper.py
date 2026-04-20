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
        self.driver = uc.Chrome(
            options=self.options,
            use_subprocess=True,
            version_main=None,
        )

        # Optional: use a real Chrome profile to carry cookies/history
        # profile_path = os.path.expanduser("~/.config/google-chrome/Default")
        # options.add_argument(f"--user-data-dir={profile_path}")

        self.driver = uc.Chrome(
            options=self.options,
            use_subprocess=True,
            version_main=None,
        )

    def get_driver(self):
        return self.driver

    def close(self):
        self.driver.quit()


class ScrapeAACRLinks():
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
            # If a visual CAPTCHA appeared, let the user solve it
            input(
                ">>> Solve the CAPTCHA in the browser, then press Enter to continue..."
            )

    def scrapp_all_links(self):
        try:
            self.open_page(BASE_URL)
           
        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            scraper.close()
   
        

def main():
    
    driver = Driver()
    scraper = ScrapeAACRLinks(driver.get_driver())
    scraper.scrapp_all_links()
    driver.close()


if __name__ == "__main__":
    main()
