"""Free, LOCAL vision brain — runs on YOUR GPU via Ollama. No API key, no cost.

It sends game screenshots to a vision model running on your own machine
(Ollama at http://localhost:11434) and gets back a decision. Because it runs on
your RTX 4070, you can let it play for months with zero API charges.

The hybrid trick that keeps it fast: it does NOT wake the model on every frame.
A cheap frame-difference check decides *when* a real decision is needed —
- screen meaningfully changed and settled (new dialogue, a battle menu, a new
  area) -> wake the model and ask what to do,
- screen basically unchanged since the model last looked -> just advance with A,
- stuck too long with nothing changing -> wake the model to figure out where to go.
So the expensive model call happens only at genuine decision points; the cheap
A-presses bridge the gaps. That's what makes a local model practical in realtime.
"""

import base64
import io
import json
import urllib.request

from PIL import ImageChops

TYPE_CHART = (
    "TYPE CHART (attacking type -> super effective against; pick moves that are super effective):\n"
    "Fire: Grass, Ice, Bug, Steel. Water: Fire, Ground, Rock. Grass: Water, Ground, Rock. "
    "Electric: Water, Flying (no effect on Ground). Ice: Grass, Ground, Flying, Dragon. "
    "Fighting: Normal, Ice, Rock, Dark, Steel (no effect on Ghost). Poison: Grass, Fairy (no effect on Steel). "
    "Ground: Fire, Electric, Poison, Rock, Steel (no effect on Flying). Flying: Grass, Fighting, Bug. "
    "Psychic: Fighting, Poison (no effect on Dark). Bug: Grass, Psychic, Dark. Rock: Fire, Ice, Flying, Bug. "
    "Ghost: Psychic, Ghost (no effect on Normal). Dragon: Dragon (no effect on Fairy). "
    "Dark: Psychic, Ghost. Steel: Ice, Rock, Fairy. Fairy: Fighting, Dragon, Dark. Normal: nothing (no effect on Ghost)."
)

SYSTEM = (
    "You are playing the game Pokemon Hydro Bliss. You see one screenshot and choose "
    "ONE controller input. Controls: a = confirm/advance text/select/attack, "
    "b = cancel/back, up/down/left/right = move or navigate menus, start = open menu.\n"
    "In BATTLE: identify your Pokemon's type and the enemy's type, then choose the move that is "
    "SUPER EFFECTIVE using the type chart below. If you just lost (screen faded / you were sent to a "
    "Pokemon Center), you need to heal and train before trying that fight again.\n"
    "In the OVERWORLD: move toward unexplored areas, doors, stairs, and NPCs.\n"
    "GAME STRATEGY (Hydro Bliss):\n"
    "- Goal: beat each city's Gym, in order. In a new town, first find the Pokemon Center "
    "(building with a red roof) and heal there.\n"
    "- Catch lots of Pokemon early: when a wild Pokemon appears and you have Poke Balls, "
    "weaken it a little, then throw a ball. A varied team wins gyms.\n"
    "- Heal whenever HP is low: a Pokemon Center, a campfire on a route, or a red rescue box "
    "all fully heal your team.\n"
    "- Losing a Gym repeatedly means you need a Pokemon whose type is super-effective vs that Gym.\n\n"
    + TYPE_CHART +
    "\n\nReply ONLY with JSON: "
    '{"screen":"<what you see>","reason":"<why, mention types if in battle>",'
    '"button":"<one of a,b,up,down,left,right,start>","presses":<1-6>}'
)


class LocalBrain:
    CALL_THRESHOLD = 0.02      # fraction of pixels changed that counts as "a new situation"
    CHANGE_PX = 40             # per-pixel delta that counts as changed
    FORCE_ANALYZE_AFTER = 4    # static turns before we wake the model to navigate

    def __init__(self, url, model, valid_buttons):
        self.endpoint = url.rstrip("/") + "/api/chat"
        self.model = model
        self.valid_buttons = valid_buttons
        self.last_analyzed = None   # thumbnail of the frame the model last looked at
        self.static_count = 0
        self.notebook = "(empty)"

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

    def _act(self, note, plan, button, presses):
        button = button if button in self.valid_buttons else "a"
        presses = max(1, min(int(presses or 1), 6))
        return {"screen": note, "plan": plan,
                "actions": [{"button": button, "presses": presses}], "notebook": ""}

    def _ask_model(self, image):
        payload = json.dumps({
            "model": self.model,
            "format": "json",
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": "Here is the current screen. Choose one input.",
                 "images": [self._b64(image)]},
            ],
        }).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body.get("message", {}).get("content", "{}")
        data = json.loads(content)
        return self._act(
            note=str(data.get("screen", "?"))[:80],
            plan=str(data.get("reason", "local model"))[:100],
            button=str(data.get("button", "a")).lower().strip(),
            presses=data.get("presses", 1),
        )

    def decide(self, image):
        thumb = self._thumb(image)

        # Decide whether this frame warrants waking the model.
        if self.last_analyzed is None:
            change = 1.0
        else:
            change = self._changed_fraction(self.last_analyzed, thumb)

        wake = (self.last_analyzed is None
                or change > self.CALL_THRESHOLD
                or self.static_count >= self.FORCE_ANALYZE_AFTER)

        if wake:
            self.last_analyzed = thumb
            self.static_count = 0
            try:
                return self._ask_model(image)
            except Exception as exc:
                # Ollama not running / model reply unparseable -> keep moving cheaply.
                return self._act(f"local model unavailable ({type(exc).__name__})",
                                 "falling back to tap A", "a", 2)

        # Nothing new since the model last looked: bridge cheaply with A.
        self.static_count += 1
        return self._act(f"unchanged (d{change*100:.1f}%) -> tap A", "bridge", "a", 2)
