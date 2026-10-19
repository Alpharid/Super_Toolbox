# Fallout: New Vegas (2010)

| | |
|---|---|
| Engine | Gamebryo (xNVSE plugins for native hooks) |
| Versions tested | Steam/GOG release 1.4.0.525 |
| Projects | NV:MP (multiplayer: players, NPC motion, combat; closed netcode); [fnv-coop](https://github.com/cranebeaker/fnv-coop) (story sync layer) |
| Release | [fnv-coop](https://github.com/cranebeaker/fnv-coop) (developer preview, no player release yet) |
| QA level | automated |
| Last updated | 2026-10-16 |

## Where things stand

NV:MP lets people play in the same world, but quests are client-side and quest actors
are deliberately not synced. fnv-coop is a host-authoritative quest and story sync layer
(an xNVSE plugin plus a game-free sync core) meant to run next to NV:MP. It is a
developer preview with no player release or installer yet.

## Existing work

- NV:MP: players, NPC motion and combat. Closed netcode, no quest sync. See its entry in
  the directory.
- fnv-coop: the story layer described here.

## How the game works (for co-op)

- Quest logic runs as stage result scripts in the ESM. Sync captures the effects of a
  stage on the host as one transaction and applies it on clients without re-running the
  scripts.
- NV:MP's story server has no quest sync; its client marks quest actors as local.

## What we changed

- Sync core: engine-agnostic protocol and merge rules (stage = max, flags = OR,
  kills = union), covered by a simulator and soak tests.
- Effect capture: hooks record every world change a quest script makes on the host and a
  guest applies the transaction without re-running the script.
- Host-to-client quest-stage sync over our own network channel in the real game.
- Per-quest co-op rules for every story quest.
- Two game copies on one PC for tests, with the single-instance checks neutralized inside
  our own process.

## QA

- Game-free suites: the sync core with its simulator (2 to 4 clients on a lossy,
  reordering link), seeded chaos fuzzing and a 4-player soak.
- A JSON-RPC bridge plugin inside the game (`exec`, `waitFor`, `state`) lets tests drive
  real game copies; world snapshots split into shared and per-player state are diffed.
- Host capture and guest apply of quest-script effects in the real game, with matching
  snapshots.
- Host-to-client quest-stage sync over our own network channel in the real game.
- Run them with `python -I tools/test_all.py` in the fnv-coop repo; suites that need your
  own game install skip with a message.

## How to play

There is no player release yet. Follow the fnv-coop repo for the installer.

## Known issues

- Developer preview only: no installer, no player documentation.
- Windows and New Vegas 1.4.0.525 only.

## Next steps

Package an installer and a player release, and pair it with NV:MP for avatars and combat.
