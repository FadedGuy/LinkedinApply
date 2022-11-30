from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By

from constants import LINKEDIN_URL, LINKEDIN_EASY_APPLY_TAG, ERROR_EXIT
from job import Job
from time import sleep

def main():
    profile = FirefoxProfile('./profile/')
    with webdriver.Firefox(profile) as driver:
        print(f"Opening browser")
        driver.get(LINKEDIN_URL+LINKEDIN_EASY_APPLY_TAG)


        title = "software"
        location = "Guadalajara"
        job = Job(driver, title, location)
        sucess, first_job_handle = job.search_jobs()
        if sucess is ERROR_EXIT:
            return sucess

        exitCode = job.job_loop(first_job_handle)
        sleep(10)
        return exitCode


if __name__ == '__main__':
    exit_code = main()
    print(f"Exiting program with exit code {exit_code}")
    exit(exit_code)