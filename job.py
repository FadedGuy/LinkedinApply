from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from bs4 import BeautifulSoup

import logging
from time import sleep
from webpage import Webpage
from parser import Parser
from constants import *
from langdetect import detect
from typing import Any


class Job:
    def __init__(self, driver: WebDriver, job_title: str = "", location: str = ""):
        self.driver = driver
        self.job_title = job_title
        self.location = location
        self.job_count = 0
        self.webpage = Webpage(driver)


    def search_for_job(self, search_bar):
        print(f"Searching jobs for \"{self.job_title}\" at \"{self.location}\"")
        logging.info(f"Searching jobs for \"{self.job_title}\" at \"{self.location}\"")
        sleep(0.5)
        ActionChains(self.driver)\
                .send_keys_to_element(search_bar, self.job_title)\
                .pause(0.5)\
                .send_keys(Keys.TAB)\
                .pause(1)\
                .send_keys(self.location)\
                .send_keys(Keys.ENTER)\
                .perform()

        sleep(2)
        return self.webpage.wait_to_load(By.CLASS_NAME, "jobs-search-results__list-item")


    def search_jobs(self) -> tuple():
        search_bar = self.webpage.wait_to_load(By.CLASS_NAME, 'jobs-search-box__text-input')
        if search_bar is None:
            return (ERROR_EXIT, None)

        first_job = self.search_for_job(search_bar)
        if first_job is None:
            return (ERROR_EXIT, None)

        return (True, first_job)


    def after_apply_page(self) -> bool:
        sleep(1)
        print("Checking for post-apply LinkedinPremium or post-apply confirmation")
        body = self.webpage.wait_to_load(By.TAG_NAME, "body")
        if body is None:
            return False

        close_btn = self.webpage.wait_to_load(By.CLASS_NAME, "artdeco-modal__dismiss")
        # Upsell existing
        if close_btn is None:
            return False

        ActionChains(self.driver)\
            .move_to_element(close_btn)\
            .pause(0.2)\
            .click()\
            .pause(0.5)\
            .perform()

        return True


    def cv_picker(self, lang: str) -> bool:
        print(f"Picking CV with language {lang}")
        logging.info(f"Picking CV with language {lang}")
        cv_driver = self.webpage.wait_to_load(By.CLASS_NAME, "artdeco-button--1")
        if cv_driver is None:
            print(f"Error while picking CV 1")
            logging.info(f"Error while picking CV 1")
            return False

        cv_driver.click()
        cv_picker = self.webpage.wait_to_load(By.CLASS_NAME, "jobs-resume-picker__resume-list")
        if cv_picker is None:
            print(f"Error while picking CV 2")
            logging.info(f"Error while picking CV 2")
            return False
        
        cv_names = self.driver.find_elements(By.CLASS_NAME, "jobs-resume-picker__resume-label")
        index = 0
        for i in range(len(cv_names)):
            text = cv_names[i].text.lower()

            if lang in text:
                index = i
                break
        
        cv_picker = self.driver.find_elements(By.CLASS_NAME, "artdeco-button--1")
        cv_picker[index*2].click()

        print(f"CV picked")
        logging.info(f"CV picked")
        return True


    def unfollow_company(self) -> bool:
        ActionChains(self.driver)\
            .send_keys(Keys.SPACE*15)\
            .pause(0.5)\
            .perform()

        follow_company = self.webpage.wait_to_load(By.ID, "follow-company-checkbox")
        if follow_company is None:
            return False
        
        # Revise to send actual click on real
        ActionChains(self.driver)\
            .send_keys_to_element(follow_company, Keys.SPACE*2)\
            .pause(0.2)\
            .perform()

        return True

    
    def send_application(self) -> bool:
        send_application = self.webpage.wait_to_load(By.CLASS_NAME, "artdeco-button--primary")
        if send_application is None:
            return False
        
        send_application.click()
        return True


    def apply_one_page(self, lang: str) -> bool:
        if not (lang == "en" or lang == "es" or lang == "fr"):
            lang = "en"
        
        self.cv_picker(lang)
        self.unfollow_company()
        self.send_application()

        return self.after_apply_page()


    def go_next_page_application(self, element, cnt: int = 0) -> tuple():
        if cnt < 5:            
            ActionChains(self.driver)\
                    .send_keys_to_element(element, Keys.ENTER)\
                    .perform()
                
            newModal = self.webpage.wait_to_load(By.CLASS_NAME, "jobs-easy-apply-content")
            if newModal is None:
                return (False, None)
            
            wasError = self.webpage.wait_to_load(By.CLASS_NAME, "fb-form-element__error-text", 3)
            if wasError is not None:
                # NEED TO INTRODUCE ANSWER
                # Missing number
                # Missing checkbox
                # Missing selection
                print("There is an answer missing, insert answers in browser")
                input_ans = ""
                while input_ans != "ok":
                    input_ans = input("Type \"ok\" when answers are registered: ")

                sleep(0.2)
                next_button = self.webpage.wait_to_load(By.CLASS_NAME, "artdeco-button--primary")
                if next_button is None:
                    return (False, None)

                self.go_next_page_application(next_button, cnt+1)
            
            modal = self.webpage.wait_to_load(By.CLASS_NAME, "jobs-easy-apply-content")
            if modal is None:
                return (False, None)

            logging.info("Next page reached sucessfully")
            return (True, modal)

        print("Max tries for registering answer reached")
        logging.info("Max tries for registering answer reached")
        return (False, None)


    def apply_multiple_pages(self, lang: str, modal) -> bool:
         # Buscar boton siguiente mientras haya 100%
        complete_percent = self.webpage.wait_to_load(By.TAG_NAME, "progress")
        if complete_percent is None:
            return False
        
        percent = int(complete_percent.get_attribute('value'))
        if percent != 100:
            soup = BeautifulSoup(modal.get_attribute('innerHTML'), 'html.parser')
            if len(soup.find_all('div', class_='jobs-document-upload__attachment')) > 0:
                self.cv_picker(lang)  
            
            next_button = self.webpage.wait_to_load(By.CLASS_NAME, "artdeco-button--primary")
            if next_button is None:
                return False

            success, modal = self.go_next_page_application(next_button)
            if not success:
                return False

        else:
            self.unfollow_company()
            self.send_application()

            sleep(1)
            return self.after_apply_page()
        
        return self.apply_multiple_pages(lang, modal)

  
    def apply_job(self, job_JSON: dict):
        sleep(0.5)

        apply_btn = self.webpage.wait_to_load(By.CLASS_NAME, "jobs-apply-button")
        if apply_btn is None:
            already_applied = self.webpage.wait_to_load(By.CLASS_NAME, "artdeco-inline-feedback--success")
            
            if already_applied is None:
                return None
            else:
                print("Already applied to this job! Skipping")
                logging.info("Already applied to this job! Skipping")

                job_JSON['applyStatus'] = "Repeated"
                return job_JSON

        text_area = self.webpage.wait_to_load(By.ID, "job-details")
        if text_area is None:
            return None

        language = detect(text_area.text)
        job_JSON['language'] = language
        
        if job_JSON['applyMethod'] == 'Easy Apply':
            ActionChains(self.driver)\
                .move_to_element(apply_btn)\
                .click()\
                .pause(0.5)\
                .perform()

            modal = self.webpage.wait_to_load(By.CLASS_NAME, "jobs-easy-apply-content")
            if modal is None:
                return None

            ok_check = False
            progress = self.webpage.wait_to_load(By.TAG_NAME, "progress")
            if progress is None:
                ok_check = self.apply_one_page(job_JSON['language'])
            else:
                ok_check = self.apply_multiple_pages(job_JSON['language'], modal)

            if ok_check is False:
                print("Error appliying to job")
                logging.warning("Error appliying to job")
                job_JSON['applyStatus'] = "Error"

            job_JSON['applyLink'] = "N/A"
            job_JSON['applyStatus'] = "Applied"
        else:
            print("Opening external site")
            logging.info("Opening external site")

            original_window = self.driver.current_window_handle
            apply_btn.click()
            WebDriverWait(self.driver, 10).until(EC.number_of_windows_to_be(2))
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            
            self.webpage.wait_to_load(By.TAG_NAME, "body")
            sleep(2)
            externalUrl = self.driver.current_url
            print("Retrieving external URL")
            logging.info("Retrieving external URL")
            self.driver.close()
            self.driver.switch_to.window(original_window)
            print("Closing new window and switching to old")
            logging.info("Closing new window and switching to old")

            sleep(2)

            job_JSON['applyLink'] = externalUrl
            job_JSON['applyStatus'] = "Pending"

        return job_JSON


    def go_next_page_jobs(self, count_jobs: int) -> tuple():
        print("Searching for next page of jobs")
        logging.info("Searching for next page of jobs")

        url = str(self.driver.current_url)
        newUrl = url
        if LINKEDIN_START_JOB_TAG+str(self.job_count) in url:
            # Change only number which should be last digits
            newUrl = url.split(LINKEDIN_START_JOB_TAG+str(self.job_count))[0]

        self.job_count += len(count_jobs)
        self.driver.get(newUrl+LINKEDIN_START_JOB_TAG+str(self.job_count))

        sleep(1)
        new_job_handle = self.webpage.wait_to_load(By.CLASS_NAME, "jobs-search-results__list-item")
        if new_job_handle is None:
            print("Error loading next page")
            logging.warning("Error loading next page")
            return (False, None)

        print("Next page has loaded, applying in new page")
        logging.info("Next page has loaded, applying in new page")
        return (True, new_job_handle)


    def job_loop(self, first_job_handle) -> bool:
        jobs_parsed = Webpage(self.driver).new_page_loaded(first_job_handle, self.job_count)
        jobs_element = self.driver.find_elements(By.CLASS_NAME, "jobs-search-results__list-item")
    
        for i in range(len(jobs_parsed)):
            job = jobs_parsed[i]
            print(f"Applying to jobId: {job['id']}")
            logging.info(f"Applying to jobId: {job['id']}")

            ActionChains(self.driver)\
                .move_to_element(jobs_element[i])\
                .click()\
                .key_down(Keys.LEFT_SHIFT)\
                .key_down(Keys.TAB)\
                .key_up(Keys.TAB)\
                .key_up(Keys.LEFT_SHIFT)\
                .pause(0.2)\
                .perform()

            jobTemp = self.apply_job(job)
            if jobTemp is None:
                return ERROR_EXIT
            
            job = jobTemp
        
        
        if self.job_count == 0:
            Parser.save_to_JSON(jobs_parsed, JSON_PARSED_FILENAME, True)
        else:
            Parser.save_to_JSON(jobs_parsed, JSON_PARSED_FILENAME)

        sucess, jobs_current_handle = self.go_next_page_jobs(len(jobs_parsed))
        if sucess:
            self.job_loop(jobs_current_handle, self.job_count)
        
        return SUCESS_EXIT
