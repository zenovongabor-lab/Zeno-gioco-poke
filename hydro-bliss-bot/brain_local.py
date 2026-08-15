"""Free, LOCAL vision brain — runs on YOUR GPU via Ollama. No API key, no cost.

It sends game screenshots to a vision model running on your own machine and gets
back a decision. It can't truly *learn*, but it's given three things that make it
behave far less randomly:

  1. MEMORY  - each turn the model sees a short note of where it thinks it is and
     its goal, plus what it did the last several turns. Context carries forward.
  2. ORIENTATION - after a move, the bot checks whether the screen actually
     changed. If a direction produced no movement it's a WALL: the bot remembers
     it and stops ramming it, trying other directions instead.
  3. A PUSH TO MOVE - the model is told that pressing A alone gets nowhere; to
     progress it must walk with the arrows and follow paths/doors.

To stay fast it doesn't wake the model on every frame: a cheap frame-diff gates
the expensive call (new/settled screen, or stuck), and bridges other frames.
"""

import base64
import io
import json
import urllib.request

from PIL import ImageChops

TYPE_CHART = (
    "TYPE CHART (attacker -> super effective vs; prefer super-effective moves):\n"
    "Fire: Grass, Ice, Bug, Steel. Water: Fire, Ground, Rock. Grass: Water, Ground, Rock. "
    "Electric: Water, Flying (no effect on Ground). Ice: Grass, Ground, Flying, Dragon. "
    "Fighting: Normal, Ice, Rock, Dark, Steel (no effect on Ghost). Poison: Grass, Fairy (no effect on Steel). "
    "Ground: Fire, Electric, Poison, Rock, Steel (no effect on Flying). Flying: Grass, Fighting, Bug. "
    "Psychic: Fighting, Poison (no effect on Dark). Bug: Grass, Psychic, Dark. Rock: Fire, Ice, Flying, Bug. "
    "Ghost: Psychic, Ghost (no effect on Normal). Dragon: Dragon (no effect on Fairy). "
    "Dark: Psychic, Ghost. Steel: Ice, Rock, Fairy. Fairy: Fighting, Dragon, Dark. Normal: nothing."
)

SYSTEM = (
    "You are playing the game Pokemon Hydro Bliss. You see one screenshot and choose "
    "ONE controller input. Controls: a = confirm/advance text/select/attack, "
    "b = cancel/back, up/down/left/right = MOVE the character or navigate menus, start = menu.\n"
    "IMPORTANT: pressing 'a' alone does not get you anywhere. To go somewhere you MUST walk with "
    "up/down/left/right and follow paths, doors and stairs. In the overworld, keep moving and "
    "explore; do not stand still pressing a.\n"
    "In BATTLE: identify your Pokemon's type and the enemy's type, then choose the move that is "
    "SUPER EFFECTIVE (see chart). If you just lost (screen faded / sent to a Pokemon Center), "
    "you must heal and train before that fight again.\n"
    "GAME STRATEGY (Hydro Bliss):\n"
    "- FOLLOW THE STORY FIRST: read what characters say and advance dialogue with a. At the start, "
    "talk to the Professor and follow him -- he gives your first Pokemon. Do NOT look for a Pokemon "
    "Center yet; the starting town may not have one.\n"
    "- Then: reach and beat each city's Gym, in order.\n"
    "- Catch Pokemon: when a wild Pokemon appears and you have Poke Balls, weaken it, then throw a ball.\n"
    "- Heal only when Pokemon are LOW on HP: a Pokemon Center (red roof), a campfire, or a red rescue box.\n"
    "- Lost a Gym repeatedly -> get a Pokemon whose type is super-effective vs that Gym.\n\n"
    + TYPE_CHART +
    "\n\nReply with ONLY one JSON object describing the REAL screen (do not copy the example). "
    "'button' is exactly one of: a, b, up, down, left, right, start. Also give a short 'memory' "
    "noting where you are and your current goal.\n"
    'Example: {"screen":"a small room, an old man in a lab coat ahead","reason":"talk to the '
    'professor to get my starter","button":"up","presses":2,"memory":"start of game, going to the professor"}'
)


class LocalBrain:
    CALL_THRESHOLD = 0.02      # fraction of pixels changed that counts as "a new situation"
    CHANGE_PX = 40             # per-pixel delta that counts as changed
    IDENTICAL_FRAC = 0.002     # below this, the frame effectively did not change
    FORCE_ANALYZE_AFTER = 4    # static turns before we wake the model to navigate
    A_LOOP_LIMIT = 5           # A-presses in a row -> break the menu/loop
    DIRS = ["up", "right", "down", "left"]

    def __init__(self, url, model, valid_buttons):
        self.endpoint = url.rstrip("/") + "/api/chat"
        self.model = model
        self.valid_buttons = valid_buttons
        self.prev_thumb = None       # previous frame (for wall/blocked detection)
        self.last_analyzed = None    # frame the model last looked at
        self.static_count = 0
        self.a_streak = 0
        self.break_i = 0
        self.last_move = None        # last movement direction issued
        self.blocked = []            # directions that produced no movement (walls)
        self.recent = []             # rolling memory of recent turns
        self.notebook = "start of the game"

    @staticmethod
    def _thumb(image):
        return image.convert("L").resize((96, 72))

    @classmethod
    def _changed_fraction(cls, a, b):
        hist = ImageChops.difference(a, b).histogram()
        return sum(hist[cls.CHANGE_PX:]) / float(a.width * a.height)

    @staticmethod
    def _b64(image):
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return base64.standard_b64encode(buf.getvalue()).decode("ascii")

    def _act(self, note, plan, button, presses, memory=None):
        button = button if button in self.valid_buttons else "a"
        presses = max(1, min(int(presses or 1), 6))
        return {"screen": note, "plan": plan,
                "actions": [{"button": button, "presses": presses}],
                "memory": memory}

    def _memory_block(self):
        blocked = ", ".join(self.blocked) if self.blocked else "none"
        recent = " | ".join(self.recent[-6:]) if self.recent else "none yet"
        return (f"YOUR NOTES: {self.notebook}\n"
                f"RECENT TURNS: {recent}\n"
                f"WALLS (directions that did NOT move you last time -- do not keep going these ways): {blocked}\n"
                "You must MOVE with the arrows to make progress; pressing a alone will not get you anywhere.\n"
                "Here is the current screen. Choose one input.")

    def _ask_model(self, image):
        payload = json.dumps({
            "model": self.model,
            "format": "json",
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": self._memory_block(), "images": [self._b64(image)]},
            ],
        }).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        data = json.loads(body.get("message", {}).get("content", "{}"))
        return self._act(
            note=str(data.get("screen", "?"))[:80],
            plan=str(data.get("reason", "local model"))[:100],
            button=str(data.get("button", "a")).lower().strip(),
            presses=data.get("presses", 1),
            memory=str(data.get("memory", "")).strip()[:200] or None,
        )

    def _anti_loop(self, decision):
        """A/menu keeps not progressing -> try Down, B, then a couple of directions."""
        first = (decision.get("actions") or [{"button": "a"}])[0].get("button", "a")
        if first == "a":
            self.a_streak += 1
        else:
            self.a_streak = 0
        if self.a_streak >= self.A_LOOP_LIMIT:
            self.a_streak = 0
            breaker = ["down", "b", "right", "up"][self.break_i % 4]
            self.break_i += 1
            return self._act("A wasn't progressing -> break out", f"try {breaker}", breaker, 1)
        return decision

    def _navigate(self, decision):
        """Avoid walls: if the chosen direction just failed, try another. Record moves."""
        actions = decision.get("actions") or []
        if actions:
            btn = actions[0].get("button")
            if btn in self.DIRS and btn in self.blocked:
                for d in self.DIRS:
                    if d not in self.blocked:
                        actions[0]["button"] = d
                        decision["plan"] = f"{btn} is a wall, going {d} instead"
                        break
            self.last_move = actions[0].get("button") if actions[0].get("button") in self.DIRS else None
        return decision

    def _remember(self, decision):
        if decision.get("memory"):
            self.notebook = decision["memory"]
        acts = " ".join(f"{a['button']}x{a.get('presses', 1)}" for a in decision.get("actions", []))
        self.recent.append(f"{decision.get('screen', '?')[:45]} -> {acts}")
        self.recent = self.recent[-8:]

    def decide(self, image):
        thumb = self._thumb(image)

        # Did the LAST action change anything? A move that changed nothing hit a wall.
        if self.prev_thumb is not None and self.last_move is not None:
            if self._changed_fraction(self.prev_thumb, thumb) < self.IDENTICAL_FRAC:
                if self.last_move not in self.blocked:
                    self.blocked.append(self.last_move)
            else:
                self.blocked = []   # we actually moved -> forget old walls
        self.prev_thumb = thumb
        self.last_move = None

        # Wake the model on a genuinely new/settled screen, or when stuck.
        change = self._changed_fraction(self.last_analyzed, thumb) if self.last_analyzed is not None else 1.0
        wake = (self.last_analyzed is None
                or change > self.CALL_THRESHOLD
                or self.static_count >= self.FORCE_ANALYZE_AFTER)

        if wake:
            self.last_analyzed = thumb
            self.static_count = 0
            try:
                decision = self._ask_model(image)
            except Exception as exc:
                decision = self._act(f"model unavailable ({type(exc).__name__})", "tap A", "a", 2)
        else:
            self.static_count += 1
            decision = self._act(f"unchanged (d{change*100:.1f}%) -> tap A", "bridge", "a", 2)

        decision = self._anti_loop(decision)
        decision = self._navigate(decision)
        self._remember(decision)
        return decision
