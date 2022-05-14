import pyautogui
import logging


class Actor:
    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def _log_info(self, message: str) -> None:
        if self.verbose:
            logging.info(message)

    def press_down(self) -> None:
        self._log_info("Pressed Key: Down")
        pyautogui.press("down")

    def press_up(self) -> None:
        self._log_info("Pressed Key: Up")
        pyautogui.press("up")

    def press_left(self) -> None:
        self._log_info("Pressed Key: Left")
        pyautogui.press("left")

    def press_right(self) -> None:
        self._log_info("Pressed Key: Right")
        pyautogui.press("right")

    def scroll_down(self) -> None:
        self._log_info("Scrolled Down")
        pyautogui.scroll(100)

    def scroll_up(self) -> None:
        self._log_info("Scrolled Up")
        pyautogui.scroll(-100)
