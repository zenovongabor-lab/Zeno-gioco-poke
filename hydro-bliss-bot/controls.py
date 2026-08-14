"""Turn abstract buttons ("a", "up", ...) into real keypresses in the game."""

import time
import pydirectinput

# Don't add pydirectinput's own delay on top of ours; we manage timing here.
pydirectinput.PAUSE = 0.0
# Keep pydirectinput's fail-safe (slam mouse to a corner to abort) available,
# but our own hotkey in main.py is the primary stop.
pydirectinput.FAILSAFE = False


class Controller:
    def __init__(self, keymap, press_duration, between_presses):
        self.keymap = keymap
        self.press_duration = press_duration
        self.between = between_presses

    def tap(self, button, presses=1):
        """Press an abstract button one or more times."""
        if button == "wait":
            time.sleep(self.press_duration + self.between)
            return
        key = self.keymap.get(button)
        if key is None:
            return  # unknown button -> ignore rather than crash
        for _ in range(max(1, presses)):
            pydirectinput.keyDown(key)
            time.sleep(self.press_duration)
            pydirectinput.keyUp(key)
            time.sleep(self.between)

    def run_actions(self, actions):
        """Execute a list of {"button": str, "presses": int} dicts in order."""
        for action in actions:
            button = action.get("button", "wait")
            presses = int(action.get("presses", 1) or 1)
            # Clamp so a single decision can't send the game 40 steps in one dir.
            presses = max(1, min(presses, 12))
            self.tap(button, presses)
