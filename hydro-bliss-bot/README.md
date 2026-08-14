# Hydro Bliss Bot 🤖

A small AI agent that plays **Pokémon Hydro Bliss** on your own Windows PC.

It does what a person would do: it looks at the game window (screenshot), sends
that picture to Claude and asks "what should I press next?", then presses those
keys in the game. Look → think → act, on a loop.

> **Honest expectations.** Playing a whole Pokémon game *well* is genuinely
> hard for an AI — Anthropic's own *Claude Plays Pokémon* project shows even a
> top model gets stuck, wanders, and needs help. This bot will happily boot the
> game, mash through intro dialogue, make sensible **battle** choices, and make
> progress — but it is **not** a flawless speedrunner. Expect to babysit it,
> especially for tricky navigation and puzzles. It's a strong, imperfect player.

---

## What you need

- **Windows** with **Pokémon Hydro Bliss** installed and runnable.
- **Python 3.10+** — get it from [python.org](https://www.python.org/downloads/)
  and tick *"Add Python to PATH"* during install.
- An **Anthropic API key** — from [console.anthropic.com](https://console.anthropic.com/)
  (Settings → API Keys). This calls the paid API, so it costs a little money per
  run (see *Cost* below).

## Setup (once)

Open a terminal (PowerShell) **in this folder** and run:

```powershell
pip install -r requirements.txt
copy .env.example .env
```

Then open `.env` in a text editor and:

1. Paste your API key after `ANTHROPIC_API_KEY=`.
2. Leave `GAME_WINDOW_TITLE=Hydro Bliss` unless the game's window is titled
   something else.

## Run it

1. **Launch Hydro Bliss** and get to the title screen (or wherever you want the
   bot to take over). Play it in a **window**, not exclusive fullscreen, so the
   bot can capture and focus it.

2. **Test capture first** (this presses NO keys — it just proves the bot can see
   the game):

   ```powershell
   python main.py --test-capture
   ```

   It saves a screenshot into `logs/`. Open it. Does it show the game? 
   - ✅ Yes → continue.
   - ❌ "window not found" → the script prints every open window title; copy a
     word from the game's actual title into `GAME_WINDOW_TITLE` in `.env`.

3. **Let it play:**

   ```powershell
   python main.py
   ```

   You get a 3-second countdown — **click the game window** so it has keyboard
   focus. The bot then starts. Watch the terminal: each turn it prints what it
   sees, its plan, and the buttons it pressed.

   Play a limited number of turns with `python main.py --steps 30`.

4. **Stop it any time:** press **Ctrl+Alt+Q** (global) or **Ctrl+C** in the
   terminal.

---

## If the bot presses keys but nothing happens in-game

This is the single most common issue, and it's a one-line fix. The bot's keys
must match the keys **Hydro Bliss actually listens to**.

1. In the game, open **Options → Controls** and note which keys do Confirm,
   Cancel, and Menu.
2. Open `config.py` and edit the `KEYMAP` right-hand values to match. Defaults:

   | Button | Default key | Meaning              |
   |--------|-------------|----------------------|
   | `a`    | `z`         | Confirm / interact   |
   | `b`    | `x`         | Cancel / run         |
   | `start`| `enter`     | Open menu            |
   | arrows | arrow keys  | Move / navigate      |

Also: some games only accept input when their window is focused **and** not in
exclusive fullscreen. If keys still don't land, run the game windowed.

## Cost & tuning

Every turn is one Claude API call with one screenshot. To spend less:

- Raise `STEP_DELAY` in `.env` (fewer turns per minute).
- Use a cheaper/faster model: set `BOT_MODEL=claude-haiku-4-5-20251001` in
  `.env` (dumber but much cheaper). `claude-sonnet-5` is the default balance;
  `claude-opus-5` is smartest and priciest.

## How it's built

```
main.py       the look -> think -> act loop, CLI, emergency stop
capture.py    find the game window + screenshot it   (mss, pygetwindow)
controls.py   send keypresses into the game          (pydirectinput)
brain.py      ask Claude what to press, keep a memory notebook (anthropic)
config.py     all the knobs: model, keymap, timing
```

## Safety notes

- The bot only sends the specific game keys in `KEYMAP`. It doesn't move your
  mouse or type anywhere else — but it **does** send keystrokes to whatever
  window is focused, so keep the game focused and don't alt-tab into something
  important while it runs.
- Keep the emergency stop (**Ctrl+Alt+Q**) in mind before you start.
- Your API key lives only in your local `.env` (which is git-ignored). Never
  share it.

---

*Fan project. Not affiliated with Nintendo, Game Freak, or The Pokémon Company.*
