"""Send input to games that only accept a controller, via a virtual Xbox pad.

Some games (Hydro Bliss included) ignore the keyboard and only read a gamepad.
This uses `vgamepad`, which creates a virtual Xbox 360 controller through the
ViGEmBus driver. The game sees a real Xbox controller; we press its buttons.

Requires:
  1. The ViGEmBus driver installed on Windows (pip installing vgamepad prompts
     to install it), and
  2. `pip install vgamepad`.

Button mapping (abstract button -> Xbox button), matching how Pokemon Essentials
reads a gamepad:
  a -> A (confirm), b -> B (cancel/run), dpad = movement,
  start -> Start (menu), select -> Back.
"""

import time
import vgamepad as vg

BUTTON_MAP = {
    "a": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "b": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    "start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "select": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
}


class GamepadController:
    def __init__(self, press_duration, between_presses):
        self.gp = vg.VX360Gamepad()
        self.press_duration = max(press_duration, 0.08)  # hold long enough to be polled
        self.between = between_presses
        # Give the game/driver a moment to register the new controller.
        time.sleep(0.5)

    def tap(self, button, presses=1):
        if button == "wait":
            time.sleep(self.press_duration + self.between)
            return
        btn = BUTTON_MAP.get(button)
        if btn is None:
            return
        for _ in range(max(1, presses)):
            self.gp.press_button(button=btn)
            self.gp.update()
            time.sleep(self.press_duration)
            self.gp.release_button(button=btn)
            self.gp.update()
            time.sleep(self.between)

    def run_actions(self, actions):
        for action in actions:
            button = action.get("button", "wait")
            presses = int(action.get("presses", 1) or 1)
            presses = max(1, min(presses, 12))
            self.tap(button, presses)
