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
        if not driver: return
        try:
            viewport_height = driver.execute_script("return window.innerHeight")
            total_height = driver.execute_script("return document.body.scrollHeight")
            max_scroll = min(total_height, random.randint(viewport_height, total_height // 4))
            current_scroll = 0
            while current_scroll < max_scroll:
                step = random.randint(300, 600)
                current_scroll += step
                driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                time.sleep(random.uniform(0.3, 0.7))
                if random.random() < 0.1:
                    current_scroll -= random.randint(50, 100)
                    driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                    time.sleep(0.2)
            logger.debug("Finished random scroll.")
        except Exception as e:
            logger.debug(f"Scroll skipped: {e}")

    def mouse_move(self, driver=None):
        """Moves mouse to random elements."""
        driver = driver or self.driver
        if not driver: return
        try:
            elements = driver.find_elements(By.XPATH, "//*[self::div or self::span or self::a or self::p]")
            visible = [e for e in elements if e.is_displayed()]
            if not visible: return
            targets = random.sample(visible, min(len(visible), random.randint(1, 2)))
            actions = ActionChains(driver)
            for target in targets:
                try:
                    actions.move_to_element(target).pause(random.uniform(0.1, 0.3))
                except: continue
            actions.perform()
            logger.debug(f"Mouse move over {len(targets)} elements.")
        except Exception as e:
            logger.debug(f"Mouse move skipped: {e}")

    def type_randomly(self, element, text):
        """Types text with human-like delays."""
        try:
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.02, 0.1))
            logger.debug(f"Typed {len(text)} characters.")
        except Exception as e:
            logger.debug(f"Typing skipped: {e}")

    def click_randomly(self, driver=None):
        """Clicks a random safe element."""
        driver = driver or self.driver
        if not driver: return
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "div, span")
            visible = [e for e in elements if e.is_displayed() and e.size.get('width', 0) > 0]
            if not visible: return
            target = random.choice(visible)
            actions = ActionChains(driver)
            actions.move_to_element(target).click().perform()
            logger.debug("Performed random click.")
        except Exception as e:
            logger.debug(f"Click skipped: {e}")

    def wait_randomly(self, min_wait=0.5, max_wait=2.0):
        """Random pause."""
        time.sleep(random.uniform(min_wait, max_wait))

    def humanize(self, driver=None, probability=0.4):
        """Orchestrates random behaviors."""
        if random.random() > probability: return
        driver = driver or self.driver
        if not driver: return
        behaviors = [
            lambda: self.scroll_randomly(driver),
            lambda: self.mouse_move(driver),
            lambda: self.wait_randomly(0.5, 1.5),
            lambda: self.click_randomly(driver)
        ]
        to_run = random.sample(behaviors, random.randint(1, 2))
        for behavior in to_run:
            try: behavior()
            except: continue
