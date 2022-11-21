from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from time import sleep
from bs4 import BeautifulSoup
import json

LINKEDIN_URL = "https://www.linkedin.com/jobs/search/?"
LINKEDIN_EASY_APPLY_TAG = "f_AL=true"

JSON_PARSED_FILENAME = "result"

SUCESS_EXIT = 0
ERROR_EXIT = 1

def waitToLoad(locator, locator_name, driver, delay=10):
    item = ""
    try:
        print(f"Waiting to load")
        item = WebDriverWait(driver, delay).until(EC.presence_of_element_located((locator, locator_name)))
        print(f"Element has loaded")
    except TimeoutException:
        print(f"Unable to load in the alloted time {delay}")
        return None
    
    sleep(2)
    return item


def searchJob(title, location, driver, search_bar):
    print(f"Searching jobs for \"{title}\" at \"{location}\"")
    ActionChains(driver)\
            .send_keys_to_element(search_bar, title)\
            .pause(0.5)\
            .send_keys(Keys.TAB)\
            .pause(1)\
            .send_keys(location)\
            .send_keys(Keys.ENTER)\
            .perform()

    sleep(2)
    return waitToLoad(By.CLASS_NAME, "jobs-search-results__list-item", driver)


def parsePage(src, jobId):
    print(f"Parsing page...")
    soup = BeautifulSoup(src, 'html.parser')

    # Get all the jobs
    jobsHTML = soup.find_all("li", class_="jobs-search-results__list-item")
    jobsParsed = list()
    for job in jobsHTML:
        jobParsed = dict()

        title = job.find_all("a", class_="job-card-list__title")
        if(len(title) > 0):
            jobParsed.update({"jobLink": title[0]['href']})
            jobParsed.update({"jobTitle": title[0].string.strip()})
        
        companyName = job.find_all("a", class_="job-card-container__company-name")
        if(len(companyName) > 0):
            jobParsed.update({"companyLink": companyName[0]['href']})
            jobParsed.update({"companyName": companyName[0].string.strip()})

        easyApply = job.find_all("li-icon", "mr1")
        if(len(easyApply) > 0):
            jobParsed.update({"applyMethod": "Easy Apply"})
        else:
            jobParsed.update({"applyMethod": "External"})

        metadata = job.find_all("li")
        for m in metadata:
            listClass = m['class']
            if(len(listClass) > 1):
                for _class in listClass:
                    # In case there is no content, dont search
                    if m.string is None:
                        break

                    if(_class.find("workplace") != -1):
                        jobParsed.update({"workType": m.string.strip()})
                    elif(_class.find("applicant-count") != -1):
                        jobParsed.update({"applicantCount": m.string.strip()})

            elif(len(listClass) == 1 and listClass[0].find("")):
                jobParsed.update({"location": m.string.strip()})
        
        if len(jobParsed) != 0:
            jobParsed.update({"id": jobId})
            jobId += 1
            jobsParsed.append(jobParsed) 


    print(f"Page parsed with {len(jobsParsed)} jobs")
    return jobsParsed


def saveToJSON(jobs, filename):
    jsonJobs = json.dumps(jobs, ensure_ascii=False)

    with open(filename+".json", "w") as f:
        f.write(jsonJobs)


def newPageLoaded(jobElement, jobIdCnt, driver):
    print(f"Scanning page")
    ActionChains(driver)\
        .move_to_element(jobElement)\
        .click()\
        .key_down(Keys.LEFT_SHIFT)\
        .key_down(Keys.TAB)\
        .key_up(Keys.TAB)\
        .key_up(Keys.LEFT_SHIFT)\
        .pause(0.5)\
        .send_keys(Keys.SPACE*2)\
        .pause(1)\
        .send_keys(Keys.SPACE*3)\
        .pause(1)\
        .key_down(Keys.LEFT_SHIFT)\
        .key_down(Keys.TAB)\
        .key_up(Keys.TAB)\
        .key_up(Keys.LEFT_SHIFT)\
        .pause(0.2)\
        .send_keys(Keys.TAB)\
        .perform()

    sleep(2)
    print(f"Page scanned")

    with open("parseHTML.html", "w") as f:
        f.write(driver.page_source)

    newJobs = parsePage(driver.page_source, jobIdCnt)
    saveToJSON(newJobs, JSON_PARSED_FILENAME)

    return newJobs


def jobLoop(jobs, jobIdCnt):
    jobIdN = 0


def main():
    profile = FirefoxProfile('./profile/')
    with webdriver.Firefox(profile) as driver:
        print(f"Opening browser")
        driver.get(LINKEDIN_URL)

        search_bar = waitToLoad(By.CLASS_NAME, 'jobs-search-box__text-input', driver)
        if search_bar is None:
            return ERROR_EXIT

        first_job = searchJob("IT", "Guadalajara", driver, search_bar)
        if first_job is None:
            return ERROR_EXIT
        
        jobIdCnt = 0
        jobsParsed = newPageLoaded(first_job, jobIdCnt, driver)
        jobIdCnt = len(jobsParsed)

        jobLoop(jobsParsed, jobIdCnt)

        sleep(10)
    return SUCESS_EXIT


if __name__ == '__main__':
    exit_code = main()
    print(f"Exiting program with exit code {exit_code}")
    exit(exit_code)
