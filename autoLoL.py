import pyautogui
import win32gui
import win32ui
import keyboard
import cv2 as cv
import numpy as np
from time import sleep
from ctypes import windll
from PIL import Image
from threading import Thread

class AutoLoL:

    declined = False
    hwnd = None
    screenshot = None
    screenshot_stopped = False
    rect = None
    x = None
    y = None
    w = None
    h = None

    def __init__(self):
        self.hwnd = win32gui.FindWindow(None, "League of Legends")

    # Constantly update LoL client position in case it moves
    def WindowInfo(self):
        rect = win32gui.GetWindowRect(self.hwnd)
        self.x = rect[0]
        self.y = rect[1]
        self.w = rect[2] - self.x
        self.h = rect[3] - self.y

    def Screenshot(self, ):
        # Create Screenshot thread to constantly update LoL screenshot
        while not self.screenshot_stopped:
            self.WindowInfo()
            hwndDC = win32gui.GetWindowDC(self.hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, self.w, self.h)
            saveDC.SelectObject(saveBitMap)
            windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 0)
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            self.screenshot = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwndDC)

    def FindAndClick(self, path):
        foundImage = False
        while not foundImage:
            print(f"Searching for {path} on screen")
            PILimage = self.screenshot.convert('RGB')
            haystack_img = np.array(PILimage)
            haystack_img = haystack_img[:, :, ::-1].copy()
            needle_img = cv.imread(path, cv.IMREAD_UNCHANGED)
            _, width, height = needle_img.shape[::-1]
            needle_img = needle_img[..., :3]
            result = cv.matchTemplate(
                haystack_img, needle_img, cv.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv.minMaxLoc(result)
            if max_val > 0.75:
                print(f"FindAndClick: found {path}, confidence {max_val}")
                win32gui.SetForegroundWindow(self.hwnd)
                self.ClickInClient(
                    (max_loc[0] + width / 2, max_loc[1] + height / 2))
                foundImage = True
            # If cannot find Accept, goes back and checks if in champ select
            elif self.declined and not foundImage:
                break

    def FindImage(self, path):
        foundImage = False
        while not foundImage:
            print(f"Searching for {path} on screen")
            PILimage = self.screenshot.convert('RGB')
            haystack_img = np.array(PILimage)
            haystack_img = haystack_img[:, :, ::-1].copy()
            needle_img = cv.imread(path, cv.IMREAD_UNCHANGED)
            needle_img = needle_img[..., :3]
            result = cv.matchTemplate(
                haystack_img, needle_img, cv.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv.minMaxLoc(result)
            if max_val > 0.75:
                foundImage = True
                print(f"FindImage: found {path}, confidence {max_val}")
                return True
            else:
                return False

    def ClickInClient(self, clickpos, time=0):
        sleep(time)
        pyautogui.click(clickpos[0] + self.x, clickpos[1] + self.y)

    def ChatLoaded(self):
        # 35x740 to 285x800 in 1600x900 client
        rgb_image = self.screenshot.convert('RGB')
        for x in range(35, 65, 2):
            for y in range(740, 800, 2):
                r, _, _ = rgb_image.getpixel((x, y))
                if r > 30:
                    print("Chat loaded.")
                    return True
        return False


def main():
    autolol = AutoLoL()

    role = input("Enter role: ")
    champion = input("Enter champion: ")
    print("")

    # x, y positions of places in 1600x900 client
    chatBox = (55, 855)
    championSearch = (960, 130)
    selectChampion = (485, 210)
    lockIn = (805, 765)
    waitingForChatbox = True

    Thread(target=autolol.Screenshot).start()
    sleep(0.25)

    # Wait for Accept to appear
    autolol.FindAndClick('accept.png')

    # Wait for Chatbox to appear
    while waitingForChatbox:
        pixelcolor = autolol.screenshot.getpixel(chatBox)
        inqueue = autolol.FindImage('inqueue.png')
        inqueue2 = autolol.FindImage('inqueue2.png')
        if pixelcolor == (1, 10, 19) and not inqueue:
            print("No longer in queue. Waiting for chat to load.")
            while True:
                loaded = autolol.ChatLoaded()
                if loaded:
                    break
            for _ in range(0, 5):
                autolol.ClickInClient(chatBox)
                keyboard.write(role)
                keyboard.press_and_release('Enter')
            waitingForChatbox = False
        # If someone declines queue, check again
        elif inqueue and inqueue2:
            autolol.declined = True
            autolol.FindAndClick('accept.png')

    # Target champ search and write
    print(f"Searching for {champion}")
    autolol.ClickInClient(championSearch)
    keyboard.write(champion)

    # Select champion
    print(f"Selecting {champion}")
    autolol.ClickInClient(selectChampion, 0.15)

    # Lock in
    print("Locking in")
    autolol.ClickInClient(lockIn, 0.15)

    autolol.screenshot_stopped = True
    print("GL HF")
    sleep(2)


if __name__ == '__main__':
    main()
