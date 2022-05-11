import pyautogui
import logging


class PerformAction:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def log_info(self, message: str):
        if self.verbose:
            logging.info(message)

    def press_down(self):
        self.log_info("Pressed Key: Down")
        pyautogui.press("down")

    def press_up(self):
        self.log_info("Pressed Key: Up")
        pyautogui.press("up")

    def press_left(self):
        self.log_info("Pressed Key: Left")
        pyautogui.press("left")

    def press_right(self):
        self.log_info("Pressed Key: Right")
        pyautogui.press("right")

    def scroll_down(self):
        self.log_info("Scrolled Down")
        pyautogui.scroll(100)

    def scroll_up(self):
        self.log_info("Scrolled Up")
        pyautogui.scroll(-100)
