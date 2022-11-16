import webbrowser
import pyautogui as pygui
from time import sleep

# f_AL=true means it's only showing easy apply jobs
LINKEDIN_URL_EASY_APPLY = "https://www.linkedin.com/jobs/search/?&f_AL=true"
LINKEDIN_URL = "https://www.linkedin.com/jobs/search/"
# As small as I could get it
IMAGES_FOLDER = "imgs/"
FIRST_LOAD_MATCH = "contextMenu.png"
SEARCH_ICON = "searchIcon.png"
SUCESS_EXIT = 0
ERROR_EXIT = 1

# Min confidence value for it not have false-positives and still detect even when there are notifications
# would not recommend to go above 0.7 if there are notification globes
def waitToLoad(template, _confidence=0.45):
    times = 0
    while times < 10:
        contextMenu = pygui.locateOnScreen(template, confidence=_confidence)
        times += 1
        if(contextMenu is not None):
            return True, contextMenu
        else:
            print("Loading...")
            sleep(1)

    return False, contextMenu

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


def main():
    webbrowser.open(LINKEDIN_URL, new=True, autoraise=True)

    sucess, res = waitToLoad(IMAGES_FOLDER + FIRST_LOAD_MATCH)
    if(not sucess):
        print("Error! Could not load page")
        exit(ERROR_EXIT)
    
    searchJob("software", "mexico")

    # closeCurrentWindow()
    exit(SUCESS_EXIT)


if __name__ == '__main__':
    main()
