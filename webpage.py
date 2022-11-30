from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import logging
from time import sleep
from parser import Parser
from constants import HTML_CURRENT_FILENAME


class Webpage:
    def __init__(self, driver: WebDriver):
        self.driver = driver


    def wait_to_load(self, locator: str, locator_name: str, verbose: bool=False, delay: int= 5):
        item = ""
        if verbose:
            print(f"Waiting to load")
            logging.info(f"Waiting to load {locator}->{locator_name}")
        
        try:
            item = WebDriverWait(self.driver, delay).until(EC.presence_of_element_located((locator, locator_name)))
        except TimeoutException:
            if verbose:
                print(f"Unable to load in the alloted time {delay}")
                logging.warning(f"Unable to load {locator} in the alloted time {delay}")
            return None
        
        if verbose:
            print(f"Element has loaded")
            logging.info(f"Element has loaded")
        sleep(0.4)
        return item


    def new_page_loaded(self, job_element, job_id_cnt: int) -> list:
        print(f"Scanning page")
        logging.info(f"Scanning page")

        ActionChains(self.driver)\
            .move_to_element(job_element)\
            .click()\
            .key_down(Keys.LEFT_SHIFT)\
            .key_down(Keys.TAB)\
            .key_up(Keys.TAB)\
            .key_up(Keys.LEFT_SHIFT)\
            .pause(0.8)\
            .send_keys(Keys.SPACE)\
            .pause(0.8)\
            .send_keys(Keys.SPACE)\
            .pause(0.8)\
            .send_keys(Keys.SPACE)\
            .pause(0.8)\
            .send_keys(Keys.SPACE)\
            .pause(0.8)\
            .send_keys(Keys.SPACE)\
            .pause(0.8)\
            .key_down(Keys.LEFT_SHIFT)\
            .key_down(Keys.TAB)\
            .key_up(Keys.TAB)\
            .key_up(Keys.LEFT_SHIFT)\
            .pause(0.4)\
            .send_keys(Keys.TAB)\
            .perform()

        sleep(2)
        print(f"Page scanned")
        logging.info(f"Page scanned")

        with open(HTML_CURRENT_FILENAME, "w") as f:
            f.write(self.driver.page_source)

        parser = Parser(self.driver.page_source, job_id_cnt)
        newJobs = parser.parse_html_page()
        return newJobs