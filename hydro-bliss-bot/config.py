"""Central configuration for the Hydro Bliss bot.

Nearly everything you might want to tweak lives here. The most important thing
to get right is KEYMAP: it must match the keys the game actually listens to.
Open Hydro Bliss, go to its Options -> Controls screen, and make these match.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Brain -----------------------------------------------------------------
# "rule"   = free, no API key. A "smart masher": advances dialogue, wins many
#            early battles by spamming the first move, wanders to explore.
# "claude" = uses the Claude API to actually look at the screen and decide.
#            Smarter, but needs an API key and costs money per turn.
BRAIN = os.getenv("BOT_BRAIN", "rule")

# --- API / model (only used when BRAIN = "claude") -------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = os.getenv("BOT_MODEL", "claude-sonnet-5")

# --- Window / timing -------------------------------------------------------
GAME_WINDOW_TITLE = os.getenv("GAME_WINDOW_TITLE", "Hydro Bliss")
STEP_DELAY = float(os.getenv("STEP_DELAY", "0.35"))  # seconds between "look and act" cycles

# How long each key is physically held down, and the gap between taps.
# Pokemon Essentials games need a key held long enough to register (~one frame+).
PRESS_DURATION = 0.06
BETWEEN_PRESSES = 0.07

# --- Key mapping -----------------------------------------------------------
# Left side = the abstract button the AI thinks in.
# Right side = the physical keyboard key sent to the game (pydirectinput names).
#
# These are common Pokemon Essentials defaults. If the bot presses keys and
# nothing happens in-game, THIS is almost always what needs fixing. Check the
# game's own control-options screen and edit the right-hand values.
KEYMAP = {
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "a": "z",       # Confirm / interact / advance dialogue  (Essentials "C")
    "b": "x",       # Cancel / back / run                     (Essentials "B")
    "start": "enter",  # Open the pause menu
    "select": "backslash",
}

# The abstract buttons the AI is allowed to choose. "wait" does nothing for one
# cycle (useful during animations / cutscenes).
VALID_BUTTONS = ["up", "down", "left", "right", "a", "b", "start", "select", "wait"]

# --- Safety ----------------------------------------------------------------
# Global hotkey that instantly stops the bot no matter what. (Closing the game
# window also stops the bot.)
EMERGENCY_STOP_HOTKEY = "ctrl+alt+q"

# Global hotkey to pause/resume. While paused the bot stops grabbing focus and
# stops pressing keys, so your mouse and keyboard are yours again.
PAUSE_HOTKEY = "ctrl+alt+p"

# Max number of look-and-act cycles before the bot stops on its own (a safety
# cap so it can't run forever unattended). None = no limit.
MAX_STEPS = None
