import time
from typing import Callable, Dict


class ActionMatcher:
    def __init__(self) -> None:
        self.actions: Dict[str, Callable[[], None]] = {}
        self.last_trigger_time = time.time()

    def add_action(self, action_name: str, action: Callable[[], None]) -> None:
        self.actions[action_name] = action

    def throttle(self, func: Callable[[], None], timeout: int) -> bool:
        if time.time() - self.last_trigger_time > timeout:
            func()
            self.last_trigger_time = time.time()
            return True

        return False

    def match(self, instruction: str) -> str:
        for action_name, action in self.actions.items():
            if action_name.replace(" ", "").lower() in instruction.replace(" ", "").lower():
                executed = self.throttle(action, 1)
                if executed:
                    return f"HIT: {action_name}"

                return f"TOO FREQUENT: {action_name}"

        return "NOT HIT"
