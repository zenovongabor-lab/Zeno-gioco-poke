"""Entry point: the look -> think -> act loop for playing Hydro Bliss.

Usage (from a terminal, with Hydro Bliss already running):

    python main.py --test-capture     # just save one screenshot, press nothing
    python main.py                     # play until you stop it
    python main.py --steps 50          # play at most 50 turns

Stop at any time with the emergency hotkey (default Ctrl+Alt+Q) or Ctrl+C.
"""

import argparse
import glob
import os
import sys
import time
from datetime import datetime

import config
import capture


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def save_review_snapshot(img, decision):
    """Drop a screenshot + a one-line note into the review folder, and prune old ones.

    This is what you send to Claude at your twice-a-day check-ins: open the
    review folder, grab the newest .png and the last few lines of log.txt.
    """
    os.makedirs(config.REVIEW_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    img.save(os.path.join(config.REVIEW_DIR, f"snap-{stamp}.png"))

    acts = " ".join(f"{a['button']}x{a.get('presses', 1)}" for a in decision.get("actions", []))
    note = (f"[{datetime.now():%Y-%m-%d %H:%M:%S}] saw: {decision.get('screen', '?')[:90]} "
            f"| plan: {decision.get('plan', '')[:70]} | did: {acts} "
            f"| notes: {(decision.get('memory') or '')[:80]}\n")
    with open(os.path.join(config.REVIEW_DIR, "log.txt"), "a", encoding="utf-8") as fh:
        fh.write(note)

    # Keep only the newest REVIEW_KEEP snapshots so months of play don't fill the disk.
    snaps = sorted(glob.glob(os.path.join(config.REVIEW_DIR, "snap-*.png")))
    for old in snaps[:-config.REVIEW_KEEP]:
        try:
            os.remove(old)
        except OSError:
            pass


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
    if config.BRAIN == "local":
        from brain_local import LocalBrain
        log(f"Brain: local vision model '{config.OLLAMA_MODEL}' via Ollama ({config.OLLAMA_URL}). "
            f"No API cost.")
        return LocalBrain(config.OLLAMA_URL, config.OLLAMA_MODEL, config.VALID_BUTTONS)
    from brain_rule import RuleBrain
    log("Brain: free rule-based (no model, no cost).")
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

    log(f"Review snapshots -> ./{config.REVIEW_DIR}/ every {int(config.SNAPSHOT_EVERY)}s "
        f"(send the newest ones to Claude at your check-ins).")

    step = 0
    last_snapshot = 0.0
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

            now = time.monotonic()
            if now - last_snapshot >= config.SNAPSHOT_EVERY:
                save_review_snapshot(img, decision)
                last_snapshot = now

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
