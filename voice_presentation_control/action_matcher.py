from typing import Callable, Dict


class ActionMatcher:
    def __init__(self) -> None:
        self.actions: Dict[str, Callable[[], None]] = {}

    def add_action(self, action_name, action: Callable[[], None]) -> None:
        self.actions[action_name] = action

    def match(self, action) -> bool:
        for action_name, action_function in self.actions.items():
            if action_name in action:
                action_function()
                return True

        return False
