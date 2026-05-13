import sys
from loguru import logger
import undetected_chromedriver as uc

from utils import (
    setup_driver_options,
    ScraperTimer,
    HumanBehaviors,
    ensure_dir
)

class BaseScraper:
    def __init__(self, name="BaseScraper", headless=False, chrome_version=None):
        self.name = name
        self.headless = headless
        self.chrome_version = chrome_version
        self.driver = None
        self.timer = ScraperTimer()
        self.hb = None
        self.setup_logging()

    def setup_logging(self):
        """Configures Loguru for the scraper."""
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
            level="INFO",
        )
        ensure_dir("logs")
        logger.add(
            f"logs/{self.name.lower()}.log",
            rotation="10 MB",
            retention="10 days",
            compression="zip",
            level="DEBUG",
        )

    def init_driver(self):
        """Initializes the Chrome driver."""
        logger.info(f"Initializing driver for {self.name}...")
        options = setup_driver_options(headless=self.headless)
        try:
            # Use chrome_version if provided (for version mismatches)
            self.driver = uc.Chrome(
                options=options, 
                version_main=self.chrome_version, 
                use_subprocess=True
            )
            self.driver.maximize_window()
            self.hb = HumanBehaviors(self.driver)
            return self.driver
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            raise

    def close_driver(self):
        """Safely closes the driver and prevents double-quit errors."""
        if self.driver:
            logger.info("Closing browser session...")
            driver_ref = self.driver
            try:
                driver_ref.quit()
            except Exception as e:
                if "WinError 6" in str(e) or "invalid handle" in str(e).lower():
                    logger.debug("Silenced WinError 6 during driver shutdown.")
                else:
                    logger.warning(f"Error during browser closure: {e}")
            finally:
                # Monkeypatch quit to be a no-op to prevent UC's __del__ from crashing
                try:
                    driver_ref.quit = lambda: None
                except:
                    pass
                self.driver = None

    def run(self):
        """Main execution logic."""
        with self.timer:
            try:
                self.init_driver()
                self.execute()
            except Exception as e:
                logger.error(f"Scraper execution failed: {e}")
            finally:
                self.close_driver()
                logger.info(f"Run completed in {self.timer.format_elapsed()}")

    def execute(self):
        """Subclasses must implement this."""
        raise NotImplementedError("Subclasses must implement execute()")
