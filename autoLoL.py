import pyautogui
import win32gui
import win32ui
import keyboard
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

    def CheckPixel(self, pos):
        rgb_image = self.screenshot.convert('RGB')
        r, g, b = rgb_image.getpixel(pos)
        rgb = (r, g, b)
        return rgb


def main():
    autolol = AutoLoL()

    role = input("Enter role: ")
    champion = input("Enter champion: ")
    print("")

    # x, y positions of places in 1600x900 client
    acceptButtonBorder = (800, 669)
    acceptButton = (800, 700)
    inQueue = (1425, 70)
    runeButton = (545, 855)
    chatBox = (55, 855)
    championSearch = (960, 130)
    selectChampion = (485, 210)
    lockIn = (805, 765)
    waitingForLobby = True

    Thread(target=autolol.Screenshot).start()
    sleep(0.25)

    # Wait for Accept to appear
    while autolol.CheckPixel(acceptButtonBorder) != (10, 195, 182):
        print("Waiting for matchmaking to find a game")
    autolol.ClickInClient(acceptButton)

    # Wait for Chatbox to appear
    while waitingForLobby:
        chatBoxRGB = autolol.CheckPixel(chatBox)
        inQueueRGB = autolol.CheckPixel(inQueue)
        runeButtonRGB = autolol.CheckPixel(runeButton)
        if chatBoxRGB == (1, 10, 19) and runeButtonRGB == (205, 190, 145):
            print("No longer in queue.")
            while not autolol.ChatLoaded():
                print("Waiting for chat to load.")
            for _ in range(0, 5):
                autolol.ClickInClient(chatBox)
                keyboard.write(role)
                keyboard.press_and_release('Enter')
            waitingForLobby = False
        # If someone cancels queue
        elif inQueueRGB == (0, 31, 45) or inQueueRGB == (9, 166, 70):
            if autolol.CheckPixel(acceptButtonBorder) != (10, 195, 182):
                print("Waiting for matchmaking to find a game")
            else:
                autolol.ClickInClient(acceptButton)
        else:
            pass

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
