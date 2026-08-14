"""Entry point: the look -> think -> act loop for playing Hydro Bliss.

Usage (from a terminal, with Hydro Bliss already running):

    python main.py --test-capture     # just save one screenshot, press nothing
    python main.py                     # play until you stop it
    python main.py --steps 50          # play at most 50 turns

Stop at any time with the emergency hotkey (default Ctrl+Alt+Q) or Ctrl+C.
"""

import argparse
import sys
import time
from datetime import datetime

import config
import capture
from controls import Controller


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def acquire_window():
    win = capture.find_window(config.GAME_WINDOW_TITLE)
    if win is None:
        log(f'Could not find a window matching "{config.GAME_WINDOW_TITLE}".')
        log("Open windows I can see:")
        for t in capture.list_window_titles():
            log(f"    - {t}")
        log('Fix: set GAME_WINDOW_TITLE in your .env to a word from the game window\'s title.')
        sys.exit(1)
    log(f'Found game window: "{win.title}"  ({win.width}x{win.height})')
    return win


def test_capture():
    win = acquire_window()
    capture.focus_window(win)
    time.sleep(0.3)
    img = capture.capture(win)
    path = f"logs/test-capture-{datetime.now():%Y%m%d-%H%M%S}.png"
    img.save(path)
    log(f"Saved a screenshot to {path} -- open it and confirm it shows the game.")
    log("If it looks right, run:  python main.py")


def build_controller():
    """Pick the input method based on config.INPUT_METHOD."""
    if config.INPUT_METHOD == "gamepad":
        try:
            from controls_gamepad import GamepadController
        except Exception as exc:
            log(f"Could not start the virtual controller: {exc}")
            log("Make sure you ran:  pip install vgamepad   and installed the ViGEmBus driver.")
            sys.exit(1)
        log("Input: virtual Xbox controller.")
        return GamepadController(config.PRESS_DURATION, config.BETWEEN_PRESSES)
    from controls import Controller
    log("Input: keyboard.")
    return Controller(config.KEYMAP, config.PRESS_DURATION, config.BETWEEN_PRESSES)


def build_brain():
    """Pick the brain based on config.BRAIN."""
    if config.BRAIN == "claude":
        if not config.ANTHROPIC_API_KEY:
            log("BOT_BRAIN=claude but no ANTHROPIC_API_KEY set. Add your key to .env,")
            log("or set BOT_BRAIN=rule for the free version.")
            sys.exit(1)
        from brain import ClaudeBrain
        log(f"Brain: Claude ({config.MODEL}).")
        return ClaudeBrain(config.ANTHROPIC_API_KEY, config.MODEL, config.VALID_BUTTONS)
    from brain_rule import RuleBrain
    log("Brain: free rule-based (no API key, no cost).")
    return RuleBrain(config.VALID_BUTTONS)


def play(max_steps):
    import keyboard

    state = {"stop": False, "paused": False}

    def do_stop():
        state["stop"] = True

    def toggle_pause():
        state["paused"] = not state["paused"]
        if state["paused"]:
            log(f">>> PAUSED. Your mouse/keyboard are yours again. "
                f"Press {config.PAUSE_HOTKEY} to resume, {config.EMERGENCY_STOP_HOTKEY} to quit.")
        else:
            log(">>> RESUMED.")

    keyboard.add_hotkey(config.EMERGENCY_STOP_HOTKEY, do_stop)
    keyboard.add_hotkey(config.PAUSE_HOTKEY, toggle_pause)

    acquire_window()  # verify the game is there before we start
    controller = build_controller()
    brain = build_brain()

    log("=" * 60)
    log("HOW TO STOP / PAUSE (these work even while the game is on top):")
    log(f"   STOP  : {config.EMERGENCY_STOP_HOTKEY}   (or just close the game window)")
    log(f"   PAUSE : {config.PAUSE_HOTKEY}   (frees your mouse; press again to resume)")
    log("=" * 60)
    log("Starting in 3 seconds -- click the game window now so it has focus.")
    time.sleep(3)

    step = 0
    while not state["stop"]:
        if state["paused"]:
            time.sleep(0.2)          # idle without touching focus, keys, or the game
            continue
        if max_steps is not None and step >= max_steps:
            log(f"Reached step limit ({max_steps}). Stopping.")
            break

        # Re-find the game each turn: this tracks the window if it moves, and if
        # the game has been closed we stop cleanly instead of flailing.
        win = capture.find_window(config.GAME_WINDOW_TITLE)
        if win is None:
            log("Game window is gone (closed?). Stopping.")
            break

        step += 1
        try:
            if config.FOCUS_EACH_TURN:
                capture.focus_window(win)
            img = capture.capture(win)
            img.save("logs/last-frame.png")

            decision = brain.decide(img)
            acts = ", ".join(f"{a['button']} x{a.get('presses', 1)}" for a in decision["actions"])
            log(f"#{step}  {decision.get('screen', '?')[:80]}")
            if decision.get("plan"):
                log(f"      plan: {decision['plan'][:100]}")
            log(f"      -> {acts}")

            controller.run_actions(decision["actions"])
            time.sleep(config.STEP_DELAY)
        except KeyboardInterrupt:
            log("Ctrl+C -- stopping.")
            break
        except Exception as exc:  # one bad frame/API hiccup shouldn't kill the run
            log(f"Step error (continuing): {exc}")
            time.sleep(2.0)

    log("Bot stopped.")


def main():
    parser = argparse.ArgumentParser(description="Play Pokemon Hydro Bliss with Claude.")
    parser.add_argument("--test-capture", action="store_true",
                        help="Save one screenshot and exit. Press no keys. Do this first.")
    parser.add_argument("--steps", type=int, default=config.MAX_STEPS,
                        help="Maximum number of turns before stopping.")
    args = parser.parse_args()

    if args.test_capture:
        test_capture()
    else:
        play(args.steps)


if __name__ == "__main__":
    main()
