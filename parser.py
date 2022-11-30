from bs4 import BeautifulSoup
import logging
import json
from os import rename

class Parser:
    def __init__(self, src: str, job_id: int, parser: str = "html.parser"):
        self.src = src
        self.job_id = job_id
        self.parser = parser

    def update_dict_object(self, object: dict, key: str, value: str) -> dict:
        logging.info(f"Saving {value} to {key} in dictionary")
        object.update({key:value})

        return object


    def parse_html_page(self) -> list:
        print(f"Parsing page starting with {self.job_id} job id")
        logging.info(f"Parsing page starting with {self.job_id} job id")

        soup = BeautifulSoup(self.src, self.parser)

        # Get all the jobs
        jobs_HTML = soup.find_all("li", class_="jobs-search-results__list-item")
        jobs_parsed = list()
        for job in jobs_HTML:
            # Create a dictionary as to simulate JSON object
            job_parsed = {
                "id": "", "jobTitle" : "", "companyName" : "", "location" : "", 
                "applyMethod" : "", "workType" : "", "language": "", 
                "applyLink": "", "applyStatus": "", "jobLink" : "", 
                "companyLink" : "", "jobId": "", "applicantCount" : ""
            }

            title = job.find_all("a", class_="job-card-list__title")
            if len(title) > 0:
                job_parsed = self.update_dict_object(job_parsed, "jobLink", title[0]['href'])
                job_parsed = self.update_dict_object(job_parsed, "jobTitle", title[0].string.strip())
            

            company_name = job.find_all("a", class_="job-card-container__company-name")
            if len(company_name) > 0:
                job_parsed = self.update_dict_object(job_parsed, "companyLink", company_name[0]['href'])
                job_parsed = self.update_dict_object(job_parsed, "companyName", company_name[0].string.strip())

            easy_apply = job.find_all("li-icon", "mr1")
            if len(easy_apply) > 0:
                job_parsed = self.update_dict_object(job_parsed, "applyMethod", "Easy Apply")
            else:
                job_parsed = self.update_dict_object(job_parsed, "applyMethod", "External")

            job_internal_id = job.find_all("div", class_="job-card-list")
            if len(job_internal_id) > 0:
                job_parsed = self.update_dict_object(job_parsed, "jobId", job_internal_id[0]['data-job-id'])

            metadata = job.find_all("li")
            for m in metadata:
                class_list = m['class']
                if len(class_list) > 1:
                    for _class in class_list:
                        # In case there is no content, dont search
                        if m.string is None:
                            break

                        if _class.find("workplace") != -1:
                            job_parsed = self.update_dict_object(job_parsed, "workType", m.string.strip())
                        elif _class.find("applicant-count") != -1:
                            job_parsed = self.update_dict_object(job_parsed, "applicantCount", m.string.strip())

                elif len(class_list) == 1 and class_list[0].find(""):
                    job_parsed = self.update_dict_object(job_parsed, "location", m.string.strip())
            
            job_parsed = self.update_dict_object(job_parsed, "id", self.job_id)
            self.job_id += 1
            jobs_parsed.append(job_parsed) 


        print(f"Page parsed with {len(jobs_parsed)} jobs")
        logging.info(f"Page parsed with {len(jobs_parsed)} jobs")

        return jobs_parsed


    def save_to_JSON(jobs: list, filename: str, new: bool=False, backup: bool = False):
        print(f"Saving new jobs to {filename}")
        logging.info(f"Saving new jobs to {filename}")

        if new:
            print(f"Creating new file")
            logging.info(f"Creating a mexi stablix")
            f = open(filename, "w")
            f.close()

        jobsFile = ""
        try:
            with open(filename, "r") as f:
                jobsFile = json.load(f)
        except FileNotFoundError:
            print(f"File doesn't exist, creating a new file with the name {filename}")
            logging.info(f"File doesn't exist, creating a new file with the name {filename}")
            f = open(filename, "w")
            f.close()
        except json.JSONDecodeError:
            print(f"Existing file does not contain a valid JSON object, overwriting file")
            logging.warning(f"Existing file does not contain a valid JSON object, overwriting file")
        

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