import time
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from loguru import logger

class HumanBehaviors:
    def __init__(self, driver=None):
        self.driver = driver

    def scroll_randomly(self, driver=None):
        """Scrolls the page randomly to simulate reading."""
        driver = driver or self.driver
        if not driver:
            logger.error("No driver provided to scroll_randomly")
            return
            
        try:
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            current_scroll = 0
            
            # Scroll down in increments
            while current_scroll < scroll_height:
                step = random.randint(200, viewport_height // 2)
                current_scroll += step
                driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                time.sleep(random.uniform(0.5, 1.5))
                
                # Occasionally scroll back up a bit
                if random.random() < 0.2:
                    back_step = random.randint(50, 150)
                    current_scroll -= back_step
                    driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                    time.sleep(random.uniform(0.2, 0.5))
                
                # Re-check height in case of lazy loading
                scroll_height = driver.execute_script("return document.body.scrollHeight")
                if current_scroll > scroll_height:
                    break
            logger.debug("Finished random scrolling.")
        except Exception as e:
            logger.warning(f"Scroll failed: {e}")

    def mouse_move(self, driver=None):
        """Moves the mouse to random visible elements to simulate user focus."""
        driver = driver or self.driver
        if not driver:
            logger.error("No driver provided to mouse_move")
            return

        try:
            # Find common visible tags
            elements = driver.find_elements(By.XPATH, "//*[self::div or self::span or self::a or self::p]")
            visible_elements = [e for e in elements if e.is_displayed()]
            
            if not visible_elements:
                return
            
            # Select 2-4 random elements to hover over
            targets = random.sample(visible_elements, min(len(visible_elements), random.randint(2, 4)))
            actions = ActionChains(driver)
            
            for target in targets:
                try:
                    actions.move_to_element(target).pause(random.uniform(0.2, 0.6))
                except:
                    continue
            
            actions.perform()
            logger.debug(f"Simulated mouse movement over {len(targets)} elements.")
        except Exception as e:
            logger.debug(f"Mouse move simulation skipped: {e}")

    def type_randomly(self, element, text):
        """Types text into an element char by char with random human-like delays."""
        try:
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            logger.debug(f"Physically typed {len(text)} characters.")
        except Exception as e:
            logger.error(f"Typing simulation failed: {e}")

    def click_randomly(self, driver=None):
        """Clicks a random safe element (like a div or span) to simulate interaction."""
        driver = driver or self.driver
        if not driver:
            logger.error("No driver provided to click_randomly")
            return

        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "div, span, section")
            visible_elements = [e for e in elements if e.is_displayed() and e.size.get('width') > 0]
            
            if not visible_elements:
                return
                
            target = random.choice(visible_elements)
            # Use ActionChains to move and click (more human-like than .click())
            actions = ActionChains(driver)
            actions.move_to_element(target).pause(random.uniform(0.1, 0.4)).click().perform()
            logger.debug("Performed a simulated random click.")
        except Exception as e:
            logger.debug(f"Random click simulation skipped: {e}")

    def wait_randomly(self, min_wait=1.0, max_wait=3.5):
        """Pauses execution for a random duration."""
        duration = random.uniform(min_wait, max_wait)
        logger.debug(f"Waiting for {duration:.2f}s...")
        time.sleep(duration)

    def humanize(self, driver=None):
        """
        Orchestrates multiple random behaviors.
        Useful when arriving on a new page or after a significant action.
        """
        driver = driver or self.driver
        if not driver:
            logger.error("No driver provided to humanize")
            return

        behaviors = [
            lambda: self.scroll_randomly(driver),
            lambda: self.mouse_move(driver),
            lambda: self.wait_randomly(1, 2),
            lambda: self.click_randomly(driver)
        ]
        
        # Pick 2-3 random behaviors to execute
        to_run = random.sample(behaviors, random.randint(2, 3))
        logger.info(f"Humanizing session with {len(to_run)} actions...")
        for behavior in to_run:
            try:
                behavior()
            except:
                continue
