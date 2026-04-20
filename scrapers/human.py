import time
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from loguru import logger

class HumanBehaviors:
    def __init__(self, driver=None):
        self.driver = driver

    def scroll_randomly(self, driver=None):
        """Scrolls a random section of the page quickly to simulate 'scanning'."""
        driver = driver or self.driver
        if not driver:
            return
            
        try:
            viewport_height = driver.execute_script("return window.innerHeight")
            # Only scroll a random 30-50% of the page height to save time
            total_height = driver.execute_script("return document.body.scrollHeight")
            max_scroll = min(total_height, random.randint(viewport_height, total_height // 4))
            
            current_scroll = 0
            while current_scroll < max_scroll:
                # Larger, faster steps
                step = random.randint(300, 600)
                current_scroll += step
                driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                time.sleep(random.uniform(0.3, 0.7)) # Faster pause
                
                if random.random() < 0.1: # Less frequent backtracking
                    current_scroll -= random.randint(50, 100)
                    driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                    time.sleep(0.2)
            
            logger.debug("Finished quick random scroll.")
        except Exception as e:
            logger.debug(f"Scroll skipped: {e}")

    def mouse_move(self, driver=None):
        """Moves the mouse to 1-2 random visible elements quickly."""
        driver = driver or self.driver
        if not driver:
            return

        try:
            elements = driver.find_elements(By.XPATH, "//*[self::div or self::span or self::a or self::p]")
            visible_elements = [e for e in elements if e.is_displayed()]
            
            if not visible_elements:
                return
            
            # Select only 1-2 random elements
            targets = random.sample(visible_elements, min(len(visible_elements), random.randint(1, 2)))
            actions = ActionChains(driver)
            
            for target in targets:
                try:
                    actions.move_to_element(target).pause(random.uniform(0.1, 0.3))
                except:
                    continue
            
            actions.perform()
            logger.debug(f"Quick mouse move over {len(targets)} elements.")
        except Exception as e:
            logger.debug(f"Mouse move skipped: {e}")

    def type_randomly(self, element, text):
        """Types text with fast, slight variable delays."""
        try:
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.02, 0.1)) # Faster typing
            logger.debug(f"Fast typed {len(text)} characters.")
        except Exception as e:
            logger.debug(f"Typing skipped: {e}")

    def click_randomly(self, driver=None):
        """Clicks a random safe element quickly."""
        driver = driver or self.driver
        if not driver:
            return

        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "div, span")
            visible_elements = [e for e in elements if e.is_displayed() and e.size.get('width', 0) > 0]
            
            if not visible_elements:
                return
                
            target = random.choice(visible_elements)
            actions = ActionChains(driver)
            actions.move_to_element(target).click().perform()
            logger.debug("Performed a quick random click.")
        except Exception as e:
            logger.debug(f"Click skipped: {e}")

    def wait_randomly(self, min_wait=0.5, max_wait=2.0):
        """Short random pause."""
        duration = random.uniform(min_wait, max_wait)
        time.sleep(duration)

    def humanize(self, driver=None, probability=0.4):
        """
        Orchestrates 1-2 random behaviors on some calls (default probability=0.4).
        Maintains enough variability to avoid detection while ensuring coverage.
        """
        if random.random() > probability:
            return

        driver = driver or self.driver
        if not driver:
            return

        behaviors = [
            lambda: self.scroll_randomly(driver),
            lambda: self.mouse_move(driver),
            lambda: self.wait_randomly(0.5, 1.5),
            lambda: self.click_randomly(driver)
        ]
        
        # Pick 1-2 random behaviors to execute
        to_run = random.sample(behaviors, random.randint(1, 2))
        
        mode = "every page" if probability >= 1.0 else "randomly"
        logger.info(f"Humanizing session ({mode}) with {len(to_run)} quick actions...")
        for behavior in to_run:
            try:
                behavior()
            except:
                continue
