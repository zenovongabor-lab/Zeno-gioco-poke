"""Free, no-API 'brain': a fast A-masher with an unstuck reflex.

Pressing A is the single most useful button in a Pokemon game: it advances
dialogue, confirms menus, and in battle attacks with the first move. So this
brain presses A on almost every turn. Only when the screen has been genuinely
frozen for several turns in a row -- nothing it does changes anything -- does it
assume it's standing still in the overworld and take a few exploratory steps to
get unstuck.

How it detects change matters. The game window is often mostly black (intros,
transitions) with only a small text box moving. Averaging the whole frame would
drown that out, so instead we count the FRACTION of pixels that changed
noticeably. A scrolling line of text lights up plenty of pixels even if it's a
small part of a big black screen.

It has no understanding of the game. It gets through intros, menus, and easy
battles; it gets stuck on anything needing real navigation or decisions.
"""

from PIL import ImageChops


class RuleBrain:
    CHANGE_PX = 40          # per-pixel brightness delta (0-255) that counts as "changed"
    IDENTICAL_FRAC = 0.002  # fewer than this fraction of pixels changed -> frozen frame
    STUCK_TURNS = 6         # this many frozen turns in a row -> try to move

    def __init__(self, valid_buttons):
        self.valid_buttons = valid_buttons
        self.prev = None
        self.frozen = 0
        self.walk_dirs = ["up", "right", "down", "left"]
        self.walk_idx = 0

    @staticmethod
    def _thumb(image):
        return image.convert("L").resize((96, 72))

    @classmethod
    def _changed_fraction(cls, a, b):
        diff = ImageChops.difference(a, b)
        hist = diff.histogram()                 # 256 bins for an "L" image
        changed = sum(hist[cls.CHANGE_PX:])     # pixels that changed >= CHANGE_PX
        return changed / float(a.width * a.height)

    def _act(self, note, actions):
        return {"screen": note, "plan": "free masher", "actions": actions, "notebook": ""}

    def decide(self, image):
        thumb = self._thumb(image)
        if self.prev is None:
            self.prev = thumb
            return self._act("start -> A", [{"button": "a", "presses": 2}])

        frac = self._changed_fraction(self.prev, thumb)
        self.prev = thumb

        if frac < self.IDENTICAL_FRAC:
            self.frozen += 1
        else:
            self.frozen = 0

        # Genuinely frozen for a while -> probably free to walk. Explore a bit.
        if self.frozen >= self.STUCK_TURNS:
            self.frozen = 0
            direction = self.walk_dirs[self.walk_idx % len(self.walk_dirs)]
            self.walk_idx += 1
            return self._act(f"stuck -> explore {direction}",
                             [{"button": direction, "presses": 2}, {"button": "a", "presses": 1}])

        # Default: keep advancing / confirming / attacking.
        return self._act(f"advance ({frac*100:.1f}% moved) -> A", [{"button": "a", "presses": 2}])
