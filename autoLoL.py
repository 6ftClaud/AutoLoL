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

    hwnd = None
    screenshot = None
    screenshot_stopped = False
    hwnd = None
    rect = None
    x = None
    y = None
    w = None
    h = None

    def __init__(self):
        self.hwnd = win32gui.FindWindow(None, "League of Legends")

    def WindowInfo(self):
        rect = win32gui.GetWindowRect(self.hwnd)
        self.x = rect[0]
        self.y = rect[1]
        self.w = rect[2] - self.x
        self.h = rect[3] - self.y

    def Screenshot(self, ):
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
            sleep(0.2)

    def FindAndClick(self, path):
        # w, h = template.shape[::-1]
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
            print(f"FindAndClick: found {path} with confidence of {max_val}")
            if max_val > 0.75:
                win32gui.SetForegroundWindow(self.hwnd)
                self.ClickInClient(
                    (max_loc[0] + width / 2, max_loc[1] + height / 2))
                foundImage = True

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
                print(f"FindImage: found {path} with confidence of {max_val}")
                return True
            else:
                return False

    def ClickInClient(self, clickpos, time=0):
        sleep(time)
        pyautogui.click(clickpos[0] + self.x, clickpos[1] + self.y)


def main():
    autolol = AutoLoL()

    champion = input("Enter champion: ")
    print("")

    # On 1600x900 client
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
        if pixelcolor == (1, 10, 19) and not inqueue:
            print("No longer in queue. Waiting for chat to load.")
            sleep(2)
            for _ in range(0, 5):
                autolol.ClickInClient(chatBox)
                keyboard.write("Mid")
                keyboard.press_and_release('Enter')
            waitingForChatbox = False

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
    sleep(3)


if __name__ == '__main__':
    main()
