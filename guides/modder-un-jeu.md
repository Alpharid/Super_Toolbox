# Modder un jeu PC — guide

Règles d'abord : jeu **possédé**, solo / hors ligne ou serveur à soi, aucun contournement d'anti-cheat ou de DRM, rien du jeu
ni de décompilé dans git (voir `HANDOVER.md` §7). Chemins relatifs à `D:\Modding_Tools_Kit\`.

## La méthode (universal-modder)
1. Lire `upstream/universal-modder/skills/mod-any-game/SKILL.md` (la boucle complète) — par morceaux.
2. Reconnaissance : `um scan "<jeu>" --json` (moteur, version, anti-cheat, loaders, routes classées) et `um kb search "<jeu>"`
   (le jeu a peut-être déjà une note). Lancer `um` : `PYTHONPATH=upstream/universal-modder python -m um …`.
3. Lire **un** playbook : `upstream/universal-modder/skills/mod-any-game/references/engines/<moteur>.md`.
4. Toujours la route la moins chère d'abord : fichiers de données → API d'un loader → patch managé → hook natif.
5. `MODLOG.md` dans le dossier du mod ; `um backup create` avant de toucher aux sauvegardes.

## Par type de jeu → outils

| Le jeu est… | Lire | Outils du kit | À installer (releases, liens dans `CATALOGUE.md`) |
|---|---|---|---|
| Unity **Mono** (`*_Data/Managed/Assembly-CSharp.dll`) | `engines/unity.md` | `rea inspect-managed-members` | BepInEx ou MelonLoader, ILSpy / dnSpyEx, UnityExplorer, AssetRipper |
| Unity **IL2CPP** (`GameAssembly.dll` + `global-metadata.dat`) | `engines/unity.md` | **`upstream/Il2CppDumper`** (noms des classes/méthodes) puis `rea`/Ghidra sur `GameAssembly.dll` | BepInEx 6 / MelonLoader, Cpp2IL |
| Unreal 4/5 (`*.pak`, `*-Win64-Shipping.exe`) | `engines/unreal.md` | — | RE-UE4SS (mods Lua), FModel, repak/retoc |
| .NET / XNA (Terraria, Stardew, Celeste) | `engines/dotnet-xna.md` | `rea inspect-managed-*`, exemple `upstream/universal-modder/examples/terraria-tmodloader` | tModLoader / SMAPI / Everest, ILSpy |
| Bethesda (Skyrim, Fallout, Oblivion, Starfield) | `engines/bethesda.md` | — | xEdit, Creation Kit, SKSE/F4SE, MO2 |
| Natif C/C++ sans moteur connu | `engines/native.md` | `rea search/xrefs/decompile` (CLI), **`upstream/GhidraMCP`** (Claude), **`upstream/minhook`** (hooks) | Ghidra 12.1 + JDK 21, Ultimate ASI Loader, x64dbg |
| Godot (`*.pck`) | `engines/godot.md` | — | GDRE Tools |
| Electron / HTML5 (`resources/app.asar`) | `engines/misc-engines.md` | `rea analyze-javascript-application`, `rea extract-artifact` | — |

Exemples complets de mods (code, scripts, vidéo) : `upstream/universal-modder/examples/`.
Notes de terrain sur ~70 jeux : `upstream/universal-modder/knowledge/` (`um kb search` plutôt que lire l'index).
