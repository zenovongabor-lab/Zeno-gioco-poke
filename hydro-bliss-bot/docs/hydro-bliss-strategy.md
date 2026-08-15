# Pokémon Hydro Bliss — Bot Strategy Guide

Translated/condensed from the user's `pokemon_hydro_bliss_bot_guide.pdf`. This is
the **high-level strategy** used at the human-in-the-loop check-ins (a small
local model can't execute multi-step plans; a reviewer applies this). The
per-frame-actionable bits are also baked into `brain_local.py`'s prompt.

## 1. Main directive & gameplay loop
Goal: complete the game by beating every city's **Gym**, in order.

**New-city routine:**
1. Find and note the **Pokémon Center**.
2. Enter and **fully heal** the team (this sets the respawn point).
3. Find the **Gym** and challenge the leader.

**Defeat / adaptation loop** — if beaten at a Gym (you respawn at the last
Center), on repeated losses:
1. Identify the Gym's dominant **elemental type**.
2. Find Pokémon with **super-effective (2×/4×)** attacks/types against it.
3. Check whether such Pokémon are already in the **PC Box**.
4. If not, **catch suitable Pokémon on the surrounding routes** before retrying.

## 2. Early game — capture priority
Early on the priority is **NOT** grinding but **maximizing captures**. A large,
varied Box = the flexibility to build a counter-team for each Gym.
- Use Poké Balls on every new route to catch **at least one of each species**.
- Treat the PC Box as a **type reserve** (Fire, Water, Grass, Electric, Fighting, …).

## 3. Hydro-Bliss-specific mechanics
| Mechanic | What it does | Bot action |
|---|---|---|
| **Campfire** (rest points on routes) | Fully heals team, removes serious status (Freeze/Frostbite). Triggers Auto-Save. | Use before tough route trainers to avoid trips back to the Center. |
| **Field Rescue Packages** (red boxes on routes) | Free full heal, once per day. Triggers Auto-Save. | Quick heal while exploring/catching, without returning to town. |
| **Elevation system** | Pokémon are Grounded / Hovering / Airborne. Winged or Levitate = Airborne, **immune to Ground moves**. | Check the Advanced Pokédex in battle (key **V**) for enemy elevation before using Ground moves. |
| **Advanced battle info (key V)** | Shows stat modifiers, remaining Screen turns (Light Screen/Reflect), field effects. | Open it before choosing a move for accurate damage/status decisions. |
| **Coverage & status moves** | Trainers/wild use Sticky Web, Hidden Power, etc. to punish switches. | Mind speed; carry hazard removal (Rapid Spin/Defog) or Shed Shell for traps. |

## 4. Decision tree
```
IF new city reached      -> GO_TO_POKEMON_CENTER() -> HEAL()
IF team ready            -> GO_TO_GYM() -> FIGHT_LEADER()
IF defeated at Gym:
    ANALYZE_GYM_WEAKNESS()
    SEARCH_PC_BOX(super_effective_type)
    IF FOUND:     SWAP_INTO_TEAM() -> RETRY_GYM()
    IF NOT FOUND: CATCH_ON_ROUTE(super_effective_type) -> RETRY_GYM()
DURING EXPLORATION: use CAMPFIRE / FIELD_RESCUE_PACKAGE whenever available to keep HP full.
```

## 5. Game facts (from the v2 technical spec) — reference for check-ins
> The v2 spec proposed a hardcoded step-count FSM. Hardcoded movement is too
> brittle to rely on (one desync breaks the whole path), so we keep the *knowledge*
> here for the human-in-the-loop, not as a blind script.

**Controls (confirmed):** Confirm/interact = C / Space / Enter · Cancel/back/menu = X (Esc) ·
Move = arrows · Run = hold Z (per the in-game controls screen) · Key item = F ·
**Battle info = V** (opens detailed stats, elevation status, screen turns).

**Two regions, 36 badges total:** Haido and Kosei, ending in Regional Championship tournaments.

**Starters:** Rowlet (Grass), Litten (Fire), Popplio (Water).

**Intro flow (bedroom → Route 1):**
1. Pass intro logos / pick region (Haido or Kosei) with Confirm.
2. Wake in bed → go downstairs → out the front door to the town.
3. Enter the Professor's Lab → approach the starter table → pick Rowlet/Litten/Popplio →
   skip the nickname screen.
4. Win Rival Battle #1 (early on, spamming the first attack usually wins).
5. Leave town north to Route 1 → normal exploration begins.

**Battle tip — Elevation:** press **V** to check the target's elevation. If it's **Airborne**
(winged / Levitate), **Ground-type moves do nothing** — pick a different move.

**Loop after that:** OVERWORLD (explore + catch + rest at campfires/rescue boxes) →
new TOWN (heal at the Center = sets respawn) → GYM (fight leader) → on repeated DEFEAT,
identify the gym's type, pull a super-effective Pokémon from the PC Box or catch one on a
nearby route, then retry.
