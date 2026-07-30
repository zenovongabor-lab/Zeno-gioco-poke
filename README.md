# Zeno gioco Poké — Poké Draft Duel

A two-player Pokémon **draft duel** game, playable right in the browser.
Crack open mystery Poké Balls, draft a team of six, then either compare team
power or **fight it out** in a HeartGold/SoulSilver-style battle.

The whole game is a single self-contained file: [`index.html`](./index.html).

## How to play

1. **Setup screen** — choose:
   - **Player 2**: AI Rival or a second human (pass-and-play).
   - **AI difficulty** (when Player 2 is the AI): *Easy* (settles for whatever
     it opens), *Normal* (holds out for decent picks), or *Hard* (ruthless
     drafting and always-optimal battle moves).
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
   different ball. Every Pokémon is **unique** — once a species is drafted by
   either player, it can't appear again for the rest of the game.
3. **Finish** — depending on your Ending choice you get a VS power scoreboard
   or a full turn-based battle with the real type chart, STAB, damage rolls,
   critical hits, HP bars, and faint-and-switch.

Pokémon data and artwork are pulled live from [PokéAPI](https://pokeapi.co/)
(including Megas, Gigantamax forms, and shinies). If the network is blocked the
game quietly falls back to a small built-in roster so it always runs.

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
