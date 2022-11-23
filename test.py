from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from time import sleep
from bs4 import BeautifulSoup
import json
from os import rename
from langdetect import detect

LINKEDIN_URL = "https://www.linkedin.com/jobs/search/?"
LINKEDIN_EASY_APPLY_TAG = "f_AL=true"

JSON_PARSED_FILENAME = "result.json"
HTML_CURRENT_FILENAME = "parseHTML.html"

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
        # Create a dictionary as to simulate JSON object
        jobParsed = {"id": "", "jobTitle" : "", "companyName" : "", "location" : "", "applyMethod" : "", "workType" : "", "language": "", "applyLink": "", "applyStatus": "", "jobLink" : "", "companyLink" : "", "jobId": "","applicantCount" : ""}

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

        jobInternalId = job.find_all("div", class_="job-card-list")
        if(len(jobInternalId) > 0):
            jobParsed.update({"jobId": jobInternalId[0]['data-job-id']})

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


def saveToJSON(jobs, filename, new=False, backup=False):   
    print(f"Saving new jobs to {filename}")

    if new:
        print(f"Creating new file")
        f = open(filename, "w")
        f.close()

    jobsFile = ""
    try:
        with open(filename, "r") as f:
            jobsFile = json.load(f)
    except FileNotFoundError:
        print(f"File doesn't exist, creating a new file with the name {filename}")
        f = open(filename, "w")
        f.close()
    except json.JSONDecodeError:
        print(f"Existing file does not contain a valid JSON object, overwriting file")
    

    if jobsFile == "":
        jsonJobs = json.dumps(jobs, ensure_ascii=False)

        with open(filename, "w") as f:
            f.write(jsonJobs)
    else:
        for job in jobs:
            jobsFile.append(job)

        jsonJobs = json.dumps(jobsFile, ensure_ascii=False)
        if(backup):
            print(f"Doing a backup of {filename} to {filename+'.old'}")
            rename(filename, filename+".old")

        with open(filename, "w") as f:
            f.write(jsonJobs)

    print(f"New jobs saved to {filename}")
        

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

    with open(HTML_CURRENT_FILENAME, "w") as f:
        f.write(driver.page_source)

    newJobs = parsePage(driver.page_source, jobIdCnt)
    return newJobs

def upsellLinkedinPremium(driver):
    print("Checking for post-apply LinkedinPremium")

    upsell = waitToLoad(By.CLASS_NAME, "premium-upsell-link", driver)
    return upsell is not None


def easyApplyOnePage(lang, driver):
    if not (lang == "en" or lang == "es" or lang == "fr"):
        lang = "en"

    cv_driver = waitToLoad(By.CLASS_NAME, "artdeco-button--1", driver)
    if cv_driver is None:
        return None

    cv_driver.click()
    cv_picker = waitToLoad(By.CLASS_NAME, "jobs-resume-picker__resume-list", driver)
    if cv_picker is None:
        return None
    
    cv_names = driver.find_elements(By.CLASS_NAME, "jobs-resume-picker__resume-label")
    index = -1
    for i in range(len(cv_names)):
        text = cv_names[i].text.lower()

        if lang in text:
            index = i
            break
    
    cv_picker = driver.find_elements(By.CLASS_NAME, "artdeco-button--1")
    print(index)
    print(len(cv_picker))
    cv_picker[i*2].click()    

    follow_company = waitToLoad(By.ID, "follow-company-checkbox", driver)
    if follow_company is None:
        return None
    
    ActionChains(driver)\
        .move_to_element(follow_company)\
        .click()\
        .send_keys(Keys.TAB*3)\
        .send_keys(Keys.ENTER)\
        .perform()

    return upsellLinkedinPremium(driver)


def applyJob(jobJSON, driver):
    applyButton = waitToLoad(By.CLASS_NAME, "jobs-apply-button", driver)
    if applyButton is None:
        return None

    textArea = waitToLoad(By.ID, "job-details", driver)
    if textArea is None:
        return None

    language = detect(textArea.text)
    jobJSON['language'] = language

    if jobJSON['applyMethod'] == 'Easy Apply':
        applyButton.click()
        modal = waitToLoad(By.CLASS_NAME, "jobs-easy-apply-content", driver)
        if modal is None:
            return None

        progress = waitToLoad(By.TAG_NAME, "progress", driver, 3)
        if progress is None:
            upsell = easyApplyOnePage(jobJSON['language'], driver)
            if upsell is None:
                print("Error")
                return None
            elif upsell == True:
                quitButton = driver.find_element(By.CLASS_NAME, "artdeco-modal__dismiss")
                quitButton.click()

            print("One pager")
        else:
            print("Multiple pager")
            exit(SUCESS_EXIT)
            
        jobJSON['applyLink'] = "N/A"
        jobJSON['applyStatus'] = "Applied"
    else:
        original_window = driver.current_window_handle
        print("Opening external site")
        applyButton.click()
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        
        waitToLoad(By.TAG_NAME, "body", driver)
        sleep(2)
        externalUrl = driver.current_url
        print("Retrieving external URL")
        driver.close()
        driver.switch_to.window(original_window)
        print("Closing new window and switching to old")

        sleep(2)

        jobJSON['applyLink'] = externalUrl
        jobJSON['applyStatus'] = "Pending"

    return jobJSON
        

def jobLoop(firstJobHandle, jobIdCnt, driver, jobLoopCnt):
    jobsParsed = newPageLoaded(firstJobHandle, jobIdCnt, driver)
    jobsElement = driver.find_elements(By.CLASS_NAME, "jobs-search-results__list-item")

    for i in range(len(jobsParsed)):
        job = jobsParsed[i]
        print(f"Applying to jobId: {job['id']}")

        ActionChains(driver)\
            .move_to_element(jobsElement[i])\
            .click()\
            .key_down(Keys.LEFT_SHIFT)\
            .key_down(Keys.TAB)\
            .key_up(Keys.TAB)\
            .key_up(Keys.LEFT_SHIFT)\
            .pause(0.2)\
            .perform()

        jobTemp = applyJob(job, driver)
        if jobTemp is None:
            return ERROR_EXIT
        
        job = jobTemp
        
        if job['id'] == 10:
            break

    if jobLoopCnt == 0:
        saveToJSON(jobsParsed, JSON_PARSED_FILENAME, True)
        jobIdCnt = 0
    else:
        saveToJSON(jobsParsed, JSON_PARSED_FILENAME)
        jobIdCnt += len(jobsParsed)
    
    return SUCESS_EXIT

def main():
    profile = FirefoxProfile('./profile/')
    with webdriver.Firefox(profile) as driver:
        print(f"Opening browser")
        driver.get(LINKEDIN_URL + LINKEDIN_EASY_APPLY_TAG)
        search_bar = waitToLoad(By.CLASS_NAME, 'jobs-search-box__text-input', driver)
        if search_bar is None:
            return ERROR_EXIT

        first_job = searchJob("", "Mexico", driver, search_bar)
        if first_job is None:
            return ERROR_EXIT
        
        exitCode = jobLoop(first_job, 0, driver, 0)
        sleep(10)
        return exitCode


if __name__ == '__main__':
    exit_code = main()
    print(f"Exiting program with exit code {exit_code}")
    exit(exit_code)
