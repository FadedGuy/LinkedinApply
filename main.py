import webbrowser
import pyautogui as pygui
from time import sleep
import numpy as np
import cv2 as cv
import os
from bs4 import BeautifulSoup

# f_AL=true means it's only showing easy apply jobs
LINKEDIN_URL = "https://www.linkedin.com/jobs/search/?"
LINKEDIN_EASY_APPLY = "f_AL=true"
# As small as I could get it
IMAGES_FOLDER = "imgs/"
FIRST_LOAD_MATCH = "contextMenu.png"
SEARCH_ICON = "searchIcon.png"
# Podria ser la flecha y los 3 puntos o solicitar y guardar, sin embargo esos cambian de tama;o
LOADED_SEARCH = "loadedSearch.png"
HTML_PARSE_FILENAME = "parse"
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

# We check if the file is being downloaded by renaming the file, in case it is being used (i.e downloading), rename raises OSError
def waitDownload(file):
    times = 0
    filename = file + ".html"
    while times < 10:
        try:
            os.rename(filename, filename)
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
    pygui.hotkey('shift', 'tab')

    # Shortcut to save file, so we can parse and fill logs without neededing complicated image to text AI
    pygui.hotkey('ctrl', 's')
    pygui.hotkey('alt', 'tab')
    pygui.hotkey('alt', 'tab')

    # Save file with name, check if we need to replace previous since this is done once per page load
    # Open file directly with name so we don't need to check if it exists since we just created it, or truncated it
    file = open(HTML_PARSE_FILENAME+".html", 'w')
    file.close()
    pygui.typewrite(HTML_PARSE_FILENAME)
    pygui.press('enter', 2, interval=0.5)

    waitDownload(HTML_PARSE_FILENAME)
    # Sum screen blue pixels to know when button is ready?
    print(f"Page loaded and saved as {HTML_PARSE_FILENAME} for parsing")

def parseHTML():
    with open(HTML_PARSE_FILENAME+".html") as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Search for ul with class="scaffold-layout__list-container" to get job list
    # within it get all li and traverse them 
    jobsSet = soup.find_all("div", class_="job-card-list__entity-lockup")
    jobsParsed = []
    for job in jobsSet:
        i = 0
        jobParsed = []
        for child in job.stripped_strings:
            # Format followed is as follows:
            # Title, Business, Location, [Type]
            if i >= 0 and i < 3:
                if i == 0:
                    jobParsed.append({'Title' : child})
                elif i == 1:
                    jobParsed.append({'Business Name': child})
                else:
                    jobParsed.append({'Location': child})
                    
            elif child != "Ocultar empleo":
                jobParsed.append({'Type': child})
            i+=1
        jobsParsed.append(jobParsed)            

    return jobsParsed

def jobLoop():
    loadNSavePage()
    sleep(1)
    jobs = parseHTML()
    
    for job in jobs:
        for property in job:
            print(f"{property}")
        print("\n")

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
