# Zeno gioco Poké — Poké Draft Duel

A two-player Pokémon **draft duel** game, playable right in the browser.
Crack open mystery Poké Balls, draft a team of six, then either compare team
power or **fight it out** in a retro Game-Boy-style battle.

The whole game is a single self-contained file: [`index.html`](./index.html).

## How to play

1. **Setup screen** — choose:
   - **Player 2**: AI Rival, a second human (pass-and-play), 🌐 Online, or
     🏆 **Campaign** (see below).
   - **No Go reroll**: once per round each player may reject a ball and open a
     different one (Off / 1 / 2 per round).
   - **Ending**: **Battle** (the two teams fight) or **Power total** (highest
     combined base stats wins).
   - **Draw style**: *Fair* (≈2 strong + 2 weaker per set), *Classic* (natural
     odds), or *Chaos* (anything — a shiny Gigantamax legendary is as likely as
     a plain Pikachu).
   - **Region**: All (National Dex) or any single generation, Kanto → Paldea.
   - **Legendaries**: Include or Exclude.
   - Optional trainer names.
2. **Draft** — six rounds. Each turn, four mystery balls appear. Tap one to
   reveal the Pokémon inside, then **Keep** it or spend a **No Go** to try a
   different ball.
3. **Finish** — depending on your Ending choice you get a VS power scoreboard
   or a full turn-based battle with the real type chart, STAB, damage rolls,
   critical hits, HP bars, and faint-and-switch.

## 🏆 Campaign mode — the 4 Rulers of the Draft

Pick **Campaign** on the setup screen and you draft your team of six exactly
like a normal duel — same draw style, region, and No-Go rules — then gear them
up in the item bag. Instead of one rival, you then run a **gauntlet against the
four Rulers of the Draft**, each a hand-built legendary team with its own
signature battle style:

| # | Ruler | Style | Ace |
|---|-------|-------|-----|
| 1 | The Absolute Champion | Mega Evolution | Mega Rayquaza |
| 2 | The Dimensional Emperor | Terastallization | Tera Arceus (Primal Groudon + Kyogre) |
| 3 | The Perfect Weapon | Z-Move | Ultra Necrozma |
| 4 | The Unbeatable Strategist | Dynamax / Gigantamax | Gigantamax Charizard |

Each Ruler has a real six-Pokémon roster with faithful movesets and abilities.
Your team is **fully healed between Rulers** (its held items carry over). Lose,
and you can retry the same Ruler with a fresh, healed team or redraft from
scratch. Beat all four and you're crowned **champion of the Draft**.

Pokémon data and artwork are pulled live from [PokéAPI](https://pokeapi.co/)
(including Megas, Gigantamax forms, and shinies). If the network is blocked the
game quietly falls back to a small built-in roster so it always runs.

## 🌊 Bonus game: Plunge — the daily dive

[`plunge/index.html`](./plunge/index.html) is a separate single-file trivia game
modelled on the Krillion format: **the rarer your answer, the deeper you dive.**

- **Daily dive**: the same 7 prompts for everyone each day (new set at 00:00 UTC),
  20 seconds per prompt, one attempt per day, with streak and best-depth stats.
- **Scoring**: Plankton 10 · Schooler 30 · Rare 60 · Deep Cut 85 · Abyssal 100
  (one hidden answer per prompt). Every point = 10 m; a perfect dive hits 7,000 m.
- **Thousands of prompts**: 134 open prompts (from "Name a fruit" to "Name
  something you can hear but not see", "Name a word borrowed from Italian" and
  "Name a philosophical idea") with about 14,000 accepted answers, plus about
  2,250 variations built from those lists ("Name a fruit, starting with P",
  "…with a Z in it", "…10 or more letters long"), for roughly 2,400 prompts.
  Matching is typo-tolerant. When the page runs as a Claude artifact, answers
  outside the bank are judged by Claude (the clock pauses while it decides).
- **A scene after every answer**: each tier has its own full-screen moment:
  swirling plankton, a bait ball of fish with a passing shark, an octopus in a
  cloud of ink, a glowing squid, and a golden leviathan for the hidden answer.
  The particles gather into your score, the tier is named, then everything
  streaks upward as you dive. Tap to skip.
- **Themed packs** (Food & Drink, Nature & Science, Art & Thought, Screen & Story,
  Games & Sport, World & Words) and an **Endless dive** with 3 lives.
- **Animated ocean**: a canvas sea that darkens through the Sunlight → Twilight →
  Midnight → Abyssal → Hadal zones, a submarine with a headlight, marine snow that
  streaks past as you descend, fish schools, glowing jellyfish and anglerfish lures,
  zone banners, celebration bursts and sound effects (with a mute button).

Once Pages is enabled it is live at `https://<your-username>.github.io/<repository-name>/plunge/`.

## Play it online (GitHub Pages)

This repo is set up to publish itself to the web. One-time setup:

1. Go to the repository's **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.

That's it. Every push to the `main` branch then redeploys automatically via
[`.github/workflows/pages.yml`](./.github/workflows/pages.yml), and the game
is live at:

```
https://<your-username>.github.io/<repository-name>/
```

Updating the game later is just a normal commit + push to `main` — no
file-renaming, no re-uploading. The live link stays the same forever.

> Prefer "deploy from a branch" instead of Actions? That also works: set
> **Settings → Pages → Source → Deploy from a branch → `main` / `root`**.

## Run it locally

Download `index.html` and open it in any browser (double-click it, or drag it
onto a browser window). It needs an internet connection the first time so it
can load the Pokémon artwork and stats.

---

*Fan project — not affiliated with Nintendo, Game Freak, or The Pokémon
Company. Pokémon data and sprites come from the community
[PokéAPI](https://pokeapi.co/) project.*
