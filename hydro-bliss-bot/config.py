"""Central configuration for the Hydro Bliss bot.

Nearly everything you might want to tweak lives here. The most important thing
to get right is KEYMAP: it must match the keys the game actually listens to.
Open Hydro Bliss, go to its Options -> Controls screen, and make these match.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Brain -----------------------------------------------------------------
# "rule"   = free, no model. A "smart masher": advances dialogue, wins many
#            early battles by spamming the first move, wanders to explore.
# "local"  = free, runs a vision model on YOUR GPU via Ollama. Actually looks
#            at the screen and decides. No API key, no per-call cost.
# "claude" = uses the Claude API. Smartest, but needs an API key and costs money.
BRAIN = os.getenv("BOT_BRAIN", "rule")

# --- Local model (only used when BRAIN = "local") --------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "minicpm-v")  # a small, screen-savvy vision model

# --- API / model (only used when BRAIN = "claude") -------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = os.getenv("BOT_MODEL", "claude-sonnet-5")

# --- Input method ----------------------------------------------------------
# "gamepad"  = send a virtual Xbox controller (needs vgamepad + ViGEmBus driver).
#              Required for games that ignore the keyboard, like Hydro Bliss.
# "keyboard" = send keypresses (uses KEYMAP below).
INPUT_METHOD = os.getenv("BOT_INPUT", "keyboard")

# Force the game to the foreground each turn so it receives input. Keyboard
# input needs this; the virtual controller usually does NOT (and skipping it
# leaves your mouse free while the bot plays). Auto-chosen from INPUT_METHOD;
# override by setting BOT_FOCUS=1 (always focus) or BOT_FOCUS=0 (never).
_focus_env = os.getenv("BOT_FOCUS")
FOCUS_EACH_TURN = (INPUT_METHOD == "keyboard") if _focus_env is None else (_focus_env == "1")

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
    "a": "space",   # Confirm / interact / advance dialogue  (Hydro Bliss uses Space)
    "b": "x",       # Cancel / back / run
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

# --- Review folder ---------------------------------------------------------
# The bot periodically drops a screenshot + a one-line note into this folder so
# you can check on it: open the folder, grab the newest picture and the log,
# and paste them into Claude for a course-correction.
REVIEW_DIR = "review"
SNAPSHOT_EVERY = float(os.getenv("SNAPSHOT_EVERY", "180"))  # seconds between review snapshots
REVIEW_KEEP = 300  # keep at most this many snapshots (older ones are deleted)
