"""The 'brain': shows each screenshot to Claude and gets back the next moves."""

import base64
import io
import json

from anthropic import Anthropic

# One tool the model is forced to call, so we always get clean structured output
# instead of having to parse free-form text.
PLAY_TOOL = {
    "name": "play",
    "description": "Decide the next input(s) to send to the game.",
    "input_schema": {
        "type": "object",
        "properties": {
            "screen": {
                "type": "string",
                "description": "What is on screen right now (menu, overworld, battle, dialogue, etc.) and any text you can read.",
            },
            "plan": {
                "type": "string",
                "description": "Your short-term goal and why these actions move toward it.",
            },
            "actions": {
                "type": "array",
                "description": "The button presses to perform now, in order. Usually 1-3.",
                "items": {
                    "type": "object",
                    "properties": {
                        "button": {"type": "string"},
                        "presses": {"type": "integer", "minimum": 1, "maximum": 12},
                    },
                    "required": ["button"],
                },
            },
            "notebook": {
                "type": "string",
                "description": "Updated long-term memory to carry forward: goals, where you are, what you've tried, party status. Overwrites the previous notebook, so restate what still matters.",
            },
        },
        "required": ["screen", "actions"],
    },
}


def _system_prompt(valid_buttons):
    return f"""You are an autonomous agent playing the fan-made game Pokemon Hydro Bliss \
(built on Pokemon Essentials). You see one screenshot per turn and choose button presses.

Your goal: play the game well, starting from the very beginning. Advance through \
intro dialogue, pick a starter, explore, win battles, and progress the story. Play \
like a thoughtful human would.

Controls you may use (the "button" field): {", ".join(valid_buttons)}.
  - a = confirm / interact / advance dialogue
  - b = cancel / back / run
  - start = open the pause menu
  - up/down/left/right = move or navigate menus
  - wait = do nothing this turn (use during animations or cutscenes)

Guidance:
  - Advancing text? Press "a" a few times, then look again.
  - In battle, read the situation: type matchups, HP, which move to use, whether to switch.
    You are strong at this reasoning — take it seriously.
  - Walking: send a modest number of presses (e.g. up x3), then re-check. You cannot
    see where you'll end up mid-walk, so don't send huge movements blindly.
  - If the screen looks identical to last turn, whatever you tried didn't work — try
    something different (a different direction, or "a"/"b").
  - Use the notebook to remember goals and progress across turns; you only see the
    current frame, so past context lives there.

Always call the `play` tool. Keep `actions` short (1-3 presses) so you can react to results."""


class ClaudeBrain:
    def __init__(self, api_key, model, valid_buttons):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.valid_buttons = valid_buttons
        self.system = _system_prompt(valid_buttons)
        self.notebook = "(empty)"
        self.recent = []  # short rolling log of the last few turns

    @staticmethod
    def _encode(image):
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return base64.standard_b64encode(buf.getvalue()).decode("ascii")

    def _recent_summary(self):
        if not self.recent:
            return "(this is the first turn)"
        return "\n".join(self.recent[-6:])

    def decide(self, image):
        """Return a dict: {screen, plan, actions, notebook}."""
        user_text = (
            f"Long-term notebook (your memory):\n{self.notebook}\n\n"
            f"Recent turns:\n{self._recent_summary()}\n\n"
            "Here is the current screen. Decide the next input(s)."
        )
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self.system,
            tools=[PLAY_TOOL],
            tool_choice={"type": "tool", "name": "play"},
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image", "source": {
                        "type": "base64", "media_type": "image/png",
                        "data": self._encode(image),
                    }},
                ],
            }],
        )

        decision = None
        for block in message.content:
            if block.type == "tool_use" and block.name == "play":
                decision = block.input
                break
        if decision is None:
            decision = {"screen": "(no tool call returned)", "actions": [{"button": "wait"}]}

        # Keep only valid buttons.
        decision["actions"] = [
            a for a in decision.get("actions", [])
            if a.get("button") in self.valid_buttons
        ] or [{"button": "wait"}]

        # Persist memory for next turn.
        if decision.get("notebook"):
            self.notebook = decision["notebook"]
        acts = " ".join(f"{a['button']}x{a.get('presses', 1)}" for a in decision["actions"])
        self.recent.append(f"- saw: {decision.get('screen', '?')[:120]} | did: {acts}")

        return decision
