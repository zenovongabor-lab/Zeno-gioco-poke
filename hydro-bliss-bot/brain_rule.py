"""A free, no-API 'brain' for the bot.

It can't truly understand the screen, but it isn't fully blind either: it
compares each frame to the previous one to guess what's happening, and reacts
with simple, effective heuristics:

  - Screen barely changing  -> probably waiting for input: tap A (advance
    dialogue / confirm menu / pick the first battle move). If tapping A stops
    producing any change, we're likely free to walk, so it explores.
  - Screen changing a little -> text is scrolling or a menu is moving: press A.
  - Screen changing a lot    -> an animation/transition is playing: ease off.

This "mash A, occasionally walk" strategy gets a Pokemon game through a
surprising amount of its early parts, and spamming A in battle keeps attacking
with the first move (which wins many early fights). It is not smart. It will get
stuck on anything requiring real navigation or decisions.

Thresholds (HIGH/LOW below) are the main thing to tune if it misbehaves.
"""

from PIL import ImageChops, ImageStat


class RuleBrain:
    # Change thresholds, measured as the mean per-pixel brightness difference
    # between two downscaled grayscale frames (0 = identical, ~255 = opposite).
    HIGH = 12.0   # above this: a big animation/transition is happening
    LOW = 2.0     # below this: the screen is essentially still

    def __init__(self, valid_buttons):
        self.valid_buttons = valid_buttons
        self.prev = None
        self.idle_streak = 0                      # turns of "nothing changed while tapping A"
        self.walk_dirs = ["up", "right", "down", "left"]
        self.walk_idx = 0
        self.turn = 0

    @staticmethod
    def _thumb(image):
        # Small + grayscale = fast, and ignores tiny cosmetic flicker.
        return image.convert("L").resize((80, 60))

    @staticmethod
    def _change(a, b):
        return ImageStat.Stat(ImageChops.difference(a, b)).mean[0]

    def _act(self, note, actions):
        return {"screen": note, "plan": "free rule-based heuristic",
                "actions": actions, "notebook": ""}

    def decide(self, image):
        self.turn += 1
        thumb = self._thumb(image)

        if self.prev is None:
            self.prev = thumb
            return self._act("first frame -> tap A", [{"button": "a", "presses": 2}])

        change = self._change(self.prev, thumb)
        self.prev = thumb

        if change > self.HIGH:
            # Something big is animating (battle intro, screen fade). Nudge once
            # and let it play out.
            self.idle_streak = 0
            return self._act(f"busy (d{change:.1f}) -> tap A",
                             [{"button": "a", "presses": 1}])

        if change > self.LOW:
            # Text scrolling or a menu moving -> keep confirming/advancing.
            self.idle_streak = 0
            return self._act(f"text/menu (d{change:.1f}) -> A",
                             [{"button": "a", "presses": 2}])

        # Essentially static: either dialogue waiting for a press, or we're just
        # standing in the overworld. Tap A a couple of times; if that changes
        # nothing across several turns, assume we're free to move and explore.
        self.idle_streak += 1
        if self.idle_streak <= 2:
            return self._act(f"idle (d{change:.1f}) -> tap A",
                             [{"button": "a", "presses": 2}])

        direction = self.walk_dirs[self.walk_idx % len(self.walk_dirs)]
        self.walk_idx += 1
        self.idle_streak = 0
        return self._act(f"idle -> explore {direction}",
                         [{"button": direction, "presses": 3}, {"button": "a", "presses": 1}])
