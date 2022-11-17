import webbrowser
import pyautogui as pygui
from time import sleep
import numpy as np
import cv2 as cv
import os
from bs4 import BeautifulSoup
import json

# f_AL=true means it's only showing easy apply jobs
LINKEDIN_URL = "https://www.linkedin.com/jobs/search/?"
LINKEDIN_EASY_APPLY = "f_AL=true"
# As small as I could get it
IMAGES_FOLDER = "imgs/"
FIRST_LOAD_MATCH = "contextMenu.png"
SEARCH_ICON = "searchIcon.png"
JOB_LOAD_BRIEFCASE = "jobLoadBrief.png"
JOB_LOAD_EASY_APPLY = "jobLoadEasy.png"
JOB_LOAD_EXTERNAL = "jobLoadExternal.png"
# Podria ser la flecha y los 3 puntos o solicitar y guardar, sin embargo esos cambian de tama;o
LOADED_SEARCH = "loadedSearch.png"
HTML_PARSE_FILENAME = "parse"
JSON_PARSED_FILENAME = "out"
SUCESS_EXIT = 0
ERROR_EXIT = 1

# Min confidence value for it not have false-positives and still detect even when there are notifications
# would not recommend to go above 0.7 if there are notification globes
def waitToLoad(template, _confidence=0.45):
    times = 0
    while times < 10:
        screenCoords = pygui.locateOnScreen(template, confidence=_confidence)
        times += 1
        if(screenCoords is not None):
            print("Loaded sucessfully!")
            return True, screenCoords
        else:
            print(f"Loading...")
            sleep(1)

    print("Unable to load")
    return False, screenCoords

# We check if the file is being downloaded by size, treat possible error
def waitDownload(file):
    times = 0
    filename = file + ".html"
    size = 0
    sizeThresh = 700000
    while times < 10 and size < sizeThresh:
        try:
            if size != os.stat(filename).st_size:
                print("File downloading...")
                size = os.stat(filename).st_size
            else:
                print("File downloaded!")
                return True
        except OSError as e:
            print("File downloading...")
        sleep(1)
        times += 1

    print("Unable to download file")
    return False 

# Erase?
def closeCurrentWindow():
    pygui.hotkey('alt', 'f4')

def searchJob(title, location=""):
    print(f"Searching jobs for \"{title}\" at \"{location}\"")
    searchIcon = pygui.locateOnScreen(IMAGES_FOLDER+SEARCH_ICON, confidence=0.8)
    if searchIcon is not None:
        pygui.click(searchIcon[0], searchIcon[1])
        pygui.typewrite(title)
        pygui.press('tab')
        pygui.typewrite(location)
        pygui.press('enter')
        sleep(0.5)
        ssBefore = pygui.screenshot(region=(0,0,1920,1080))
        waitToLoad(ssBefore, 0.90)
        
# Helper in case we need openCV
def convertPIL2CV(_img):
    img = np.array(_img)
    return img[:,:,::-1].copy()

def loadNSavePage():
    print("Loading page for parsing")
    # Always require three tab's because it gets us to the first element highlighted
    # Positioned on first job title
    pygui.press('tab', presses=3, interval=0.5)

    # Load all jobs on page so we can save and use the file
    pygui.press('space', presses=5, interval=0.2)
    # Get back up to the first job in selection
    pygui.press('tab')
    sleep(0.2)
    pygui.hotkey('shift', 'tab')
    sleep(0.2)

    # Shortcut to save file, so we can parse and fill logs without neededing complicated image to text AI
    pygui.hotkey('ctrl', 's')
    sleep(0.2)
    pygui.hotkey('alt', 'tab')
    sleep(0.5)
    pygui.hotkey('alt', 'tab')
    sleep(0.5)

    # Save file with name, check if we need to replace previous since this is done once per page load
    # Open file directly with name so we don't need to check if it exists since we just created it, or truncated it
    file = open(HTML_PARSE_FILENAME+".html", 'w')
    file.close()
    pygui.typewrite(HTML_PARSE_FILENAME)
    pygui.press('enter', 2, interval=0.8)

    waitDownload(HTML_PARSE_FILENAME)
    # Sum screen blue pixels to know when button is ready?
    print(f"Page loaded and saved as {HTML_PARSE_FILENAME} for parsing")

def parseHTML(jobId):
    with open(HTML_PARSE_FILENAME+".html") as file:
        soup = BeautifulSoup(file, 'html.parser')

    jobsSet = soup.find_all("li", class_="jobs-search-results__list-item")
    jobsParsed = list()
    for job in jobsSet:
        jobParsed = dict()
        title = job.find_all("a", class_="job-card-list__title")
        if(len(title) > 0):
            jobParsed.update({"linkJob": title[0]['href']})
            jobParsed.update({"jobTitle": title[0].string.strip()})
        
        bName = job.find_all("a", class_="job-card-container__company-name")
        if(len(bName) > 0):
            jobParsed.update({"companyName": bName[0].string.strip()})

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
            
    return jobsParsed

def saveToJSON(jobs, filename):
    jsonJobs = json.dumps(jobs, indent="\n")

    with open(filename+".json", "w") as f:
        f.write(jsonJobs)

def apply2Job(job, loadIndicator1):
    pygui.press('enter')
    sleep(1)
    waitToLoad(IMAGES_FOLDER + loadIndicator1, 0.9)

    easyApply = True
    coords = pygui.locateOnScreen(IMAGES_FOLDER + JOB_LOAD_EASY_APPLY, confidence=0.8)
    if coords is None:
        coords = pygui.locateOnScreen(IMAGES_FOLDER + JOB_LOAD_EXTERNAL, confidence=0.8)
        if coords is None:
            print("Unable to apply")
            return False, None
        else:
            easyApply = False
    
    # Ver la cantidad de tab que se requieren para llegar a solicitar, el color obscurece cuando esta en tab
    if(easyApply):
        # Es de 1 o varias paginas? 
        # Elegir cv correcto
        # Quitar checkbox de seguir a la empresa
        # Verificar que todas tengan respuestas
        # Enviar solicitud
        job.update({'applyMethod': 'easy Apply'})

    else:
        job.update({'applyMethod': 'external Page'})
        # pygui.moveTo(coords[0], coords[1])
        # pygui.keyDown('ctrl')
        # pygui.click()
        # pygui.keyUp('ctrl')

    # Go back to list and next job 
    pygui.hotkey('shift', 'tab')
    pygui.press('tab', presses=3)

    return True, job

def jobLoop():
    jobIdN = 0
    loadNSavePage()
    sleep(1)
    jobs = parseHTML(jobIdN)
    jobIdN += len(jobs)
    # Escape from download menu that pops-up
    pygui.press('esc', interval=0.2)

    i = 0
    for job in jobs:
        stat, job = apply2Job(job, JOB_LOAD_BRIEFCASE)
        if stat is False:
            break

        i = i + 1
        if(i > 4):
            break

    saveToJSON(jobs, JSON_PARSED_FILENAME)

def main():
    # Add Win+D or minimize all?

    webbrowser.open(LINKEDIN_URL, new=True, autoraise=True)

    sucess, res = waitToLoad(IMAGES_FOLDER + FIRST_LOAD_MATCH)
    if(not sucess):
        print("Error! Could not load page")
        exit(ERROR_EXIT)
    
    searchJob("qa", "Irlanda")

    sucess, res = waitToLoad(IMAGES_FOLDER + LOADED_SEARCH, 0.85)
    if(not sucess):
        print("Error! Could not find match!")
        exit(ERROR_EXIT)

    jobLoop()

    # closeCurrentWindow()
    exit(SUCESS_EXIT)


if __name__ == '__main__':
    main()
