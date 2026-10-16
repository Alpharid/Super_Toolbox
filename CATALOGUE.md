# Catalogue des outils du kit

Référence **par dépôt** (pour une entrée **par besoin** : [guides/](guides/README.md)). Chemins relatifs à `D:\Super_Toolbox\`. Méthode et règles : [HANDOVER.md](HANDOVER.md).

## universal-modder — `upstream/universal-modder/` (MIT, v0.2.0)

**Skills** (`skills/<nom>/SKILL.md`, Markdown ; à lire comme des modes d'emploi) :

| Skill | Sert à |
|---|---|
| `mod-any-game` | **Point d'entrée** : la boucle complète (intake → recon → route → lab → RE → tranche verticale → assets → vérif en jeu → vidéo → publication → note) |
| `game-recon` | « Peut-on modder X ? », moteur, version, anti-cheat, loaders → `MODDING_PLAN.md` |
| `game-research-websearch` | Recherche communauté (Wayback, GitHub, Nexus, Workshop, Thunderstore, Reddit, YouTube) |
| `reverse-engineering` | Internes du jeu : fonctions, formats `.pak/.dat`, mémoire (ILSpy, Cpp2IL, Ghidra/IDA MCP, Cheat Engine, Frida, x64dbg, RenderDoc) |
| `fal-assets` | Génération d'images/3D/audio/vidéo via fal.ai (clé `FAL_KEY`, payant) |
| `asset-pipeline` | Détourage, pixel art, palettes, planches de sprites, 3D → sprites 8/16 directions |
| `game-automation` | Lancer le jeu, captures, clavier/souris limités à la fenêtre du jeu, pont JSON en jeu |
| `showcase-video` | Enregistrer (vidéo + son du seul jeu) et monter une démo |
| `mashup-mods` | Un jeu dans un autre, portage de contenu |
| `publish-mod` | Empaqueter/publier (Nexus, Workshop, Thunderstore, mod.io, Modrinth) avec contrôle des fichiers interdits |
| `share-field-notes` | Consulter/écrire les notes de la base de connaissances |

**Playbooks par moteur** (`skills/mod-any-game/references/engines/`) : `unity` (Mono/IL2CPP, BepInEx, MelonLoader) · `unreal`
(UE4SS, paks, FModel) · `dotnet-xna` (Terraria/tModLoader, Stardew/SMAPI, Celeste) · `godot` · `source` · `bethesda`
(Skyrim, Fallout, Oblivion, Starfield) · `big-frameworks` (RE Engine, FromSoft, GTA V, Cyberpunk, BG3) · `minecraft` ·
`genie-aoe2` · `native` (proxy DLL, MinHook, ReShade) · `misc-engines` (GameMaker, RPG Maker, Ren'Py, Paradox, Electron…) ·
`zengin` (Gothic) · `retro-decomp`.

**CLI `um`** (`PYTHONPATH=upstream/universal-modder python -m um <groupe> --help`) : `scan` (détection jeu/moteur/routes, lecture
seule) · `kb` (base de connaissances : search/show/new/check — **pas `pr` ici**) · `backup` (sauvegardes zip) · `sprite` ·
`render3d` (Blender) · `fal` (FAL_KEY) · `comfy` (ComfyUI local) · `win` (launch/shot/drive/record/kill par PID) · `video` ·
`publish check`.

**Base de connaissances** : `knowledge/INDEX.md` (à parcourir avec Grep), `knowledge/games/<jeu>/`, `knowledge/techniques/`.
Ne jamais lire `knowledge/index.json` (180 Ko) en entier : `um kb search`.

**Exemples complets** (`examples/`) : `terraria-tmodloader` (C#), `aoe2-de-civ` (Python), `minecraft-gta5-passthrough`
(Java + C++), `outer-wilds-portal-gun` (C#).

**Dépendances** : Python ≥ 3.10 + pillow, numpy, pyyaml ; ffmpeg (`um win setup`), Blender (render3d), outils de RE selon le jeu.

## rea — `upstream/rea/` (MIT, v6.4.0, npm `rea-agents`)

Reverse engineering avec preuves (SHA-256, observations, inconnues). Un exécutable `rea` = CLI **et** serveur MCP (`rea mcp`).
Installer via npm (pas depuis les sources sous Windows). Aucune clé API, tout est local.

| Besoin | Commande CLI (ajouter `--json > fichier.json`) |
|---|---|
| Natif ou .NET ? | `rea inspect-managed-artifact <exe>` |
| Classes/membres .NET (Unity Mono : `Assembly-CSharp.dll`) | `rea inspect-managed-members <dll> --type Nom.Complet` |
| Chercher une chaîne / une fonction (natif, Ghidra) | `rea search <exe> "<motif>" --kind strings|procedures --provider ghidra` |
| Qui utilise cette adresse ? | `rea xrefs <exe> 0x… --provider ghidra` |
| Pseudo-code d'une fonction | `rea decompile <exe> <adresse|nom> --provider ghidra` (plus court que `function`) |
| Préparer un patch | `rea address-to-file-offset <exe> 0x…` · `rea read-bytes <exe> 0x… --length 16` |
| Ressources/version/icônes d'un exe | `rea inspect-pe-resources <exe>` |
| Électron / JS / archives | `rea analyze-javascript-application`, `rea inspect-artifact`, `rea extract-artifact` |
| Vérifier l'installation | `rea doctor --provider ghidra --json` · `rea providers --json` |

Moteurs : **Ghidra 12.1.x + JDK 21** (Windows : lecture seule, PE natifs x86/x64), IDA Pro via ida-pro-mcp. Hopper : macOS/Linux
seulement. Non pris en charge : IL2CPP (décodage), x64dbg, Frida, radare2. Skill utilisateur :
`.agents/skills/reverse-engineer-anything/SKILL.md` (+ `references/native-and-artifacts.md`). Doc Windows : `docs/windows-ghidra-p0.md`.

## Physique — catégorie `physique`

| Dossier | Licence | Contenu | Entrées utiles |
|---|---|---|---|
| `upstream/JoltPhysics/` | MIT | Le moteur physique de **Godot 4.4+** (C++) : sources, `Docs/Architecture.md` (contraintes, casse, personnages, grands mondes, déterminisme, rollback, corps mous), ~150 démos dans `Samples/Tests/` | Guide : `guides/physique-et-godot.md` §1. Démos : `Constraints/` (cordes, poulies, engrenages, charnières motorisées), `Water/` (flottaison), `Rig/` (ragdolls, corps qui suivent une animation), `SoftBody/`, `Character/CharacterSpaceShipTest` (marcher sur un vaisseau en mouvement) |
| `upstream/GodotIK/` | MIT | IK 3D (FABRIK) pour Godot 4.3+, GDExtension, contraintes scriptables | `GodotIK/README.md`, démo `GodotIK/godot_project` ; utiliser la release |
| `upstream/godot-destruction-plugin/` | MIT | Remplace un objet par ses fragments en corps rigides (fragments faits dans Blender) | `README.md` ; Godot 4 : addon des releases |

## Godot — catégorie `godot`

| Dossier | Licence | Contenu | Entrées utiles |
|---|---|---|---|
| `upstream/netfox/` | MIT | Multijoueur Godot 4 : temps réseau, synchro d'état, rollback, prédiction d'entrées, lag compensation, NAT (noray) | `docs/` (concepts, guides, `faq.md`), `docs/netfox.extras/guides/physics.md` (**rollback des RigidBody = stepping manuel, absent de Godot officiel**), `examples/` (multiplayer-simple, rollback-fps, rollback-npc…) |
| `upstream/limboai/` | MIT | Behavior trees + machines à états hiérarchiques, éditeur visuel, blackboard (GDExtension C++) | `README.md`, `doc/`, projet `demo/` ; utiliser la release |
| `upstream/beehave/` | MIT | Behavior trees en **pur GDScript** (lisible, modifiable, sans compilation) | `docs/`, `examples/`, `addons/beehave/` |

## Outils de modding complémentaires

| Dossier | Licence | Sert à | Comment |
|---|---|---|---|
| `upstream/GhidraMCP/` | Apache-2.0 | Piloter **Ghidra depuis Claude** (plugin Ghidra + pont MCP Python `bridge_mcp_ghidra.py`) : décompiler, renommer, lister fonctions/xrefs. Recommandé par le skill `reverse-engineering` de universal-modder | Installer l'extension (release GitHub du projet) dans Ghidra, lancer le pont, `claude mcp add` — pour Claude seulement (trop d'outils pour Alphred) |
| `upstream/Il2CppDumper/` | MIT | **Jeux Unity IL2CPP** : à partir de `GameAssembly.dll` + `global-metadata.dat`, restaure les noms de classes/méthodes/champs, génère des DLL factices (lisibles avec ILSpy/rea) et des scripts Ghidra/IDA pour nommer les fonctions. Comble le trou de rea (qui ne décode pas IL2CPP) | Prendre l'exe dans les releases du projet (C# .NET) ; sortie → `work\<jeu>\il2cpp\` |
| `upstream/minhook/` | BSD-2-Clause | Bibliothèque C de **hooks x86/x64** : intercepter une fonction du jeu dans un mod natif (proxy DLL `version.dll`/`dinput8.dll`, ASI). Voir le playbook `engines/native.md` | Se compile avec CMake/MSVC dans le projet du mod |

## Listes de ressources (à fouiller avec Grep, jamais à lire en entier)

| Dossier | Licence | Contenu | Astuce de recherche |
|---|---|---|---|
| `upstream/public-apis/` | MIT | ~1 400 **API publiques gratuites**, 52 catégories (Games & Comics, Machine Learning, Weather, Music, Anime, Finance, Open Data, Authentication…), avec colonnes Auth / HTTPS / CORS | Catégories : `grep -n "^### " upstream/public-apis/README.md` ; une catégorie : lire autour du numéro de ligne ; une API : `grep -in "steam\|twitch" upstream/public-apis/README.md` |
| `upstream/awesome-godot/` | CC-BY-4.0 | Écosystème **Godot** : plugins, modules, scripts, shaders, démos, jeux open source | `grep -in "<mot-clé>" upstream/awesome-godot/README.md` (vérifier la version Godot 4 de chaque plugin) |
| `upstream/magictools/` | MIT | **Création de jeux** : moteurs, graphismes, pixel art, 3D, audio, animation, level design, IA de jeu, publication, cours | `grep -n "^## \|^### " upstream/magictools/README.md` |
| `upstream/awesome-gamedev/` | CC-BY-SA-4.0 | Logiciels et **assets libres** pour faire des jeux (graphismes, sons, musiques, polices, moteurs) | idem |
| `upstream/awesome/` | CC0-1.0 | **Méta-liste** de toutes les listes « awesome » (tous sujets logiciels) : point de départ quand rien d'autre ne couvre le sujet | `grep -in "<sujet>" upstream/awesome/readme.md` puis ouvrir le lien de la liste trouvée |
| `upstream/awesome-mcp-servers/` | MIT | **Serveurs MCP** (outils pour agents) : RE, navigateurs, bases de données, fichiers, jeux… | `grep -in "ghidra\|ida\|game\|godot" upstream/awesome-mcp-servers/README.md` |
| `upstream/awesome-claude-code/` | CC-BY-NC-ND-4.0 | Skills, hooks, commandes slash, outils et workflows pour **Claude Code** | Tableau complet : `THE_RESOURCES_TABLE_NEW.csv` (Grep). Usage perso uniquement, ne pas modifier |

## Ajouts Heimdall — 1ère vague (2026-10-16)

Copiés en subtree (détail du digest : `heimdall/reports/2026-10-16.md`) :

| Dossier | Licence | Sert à |
|---|---|---|
| `upstream/godot-statecharts/` | MIT | Machines à états hiérarchiques/parallèles (IA, UI, flux) pilotables 100 % en code — panels datapad. |
| `upstream/limbo_console/` | MIT | Console de debug in-game (commandes, autocomplétion) — déboguer les builds exportés sans éditeur. |
| `upstream/godot-gdscript-toolkit/` | MIT | Linter + formateur GDScript en CLI (`gdformat`/`gdlint`) — workflow tout-en-code et CI. |
| `upstream/godot-softbody2d/` | MIT | Soft bodies 2D (ressorts/points) Godot 4 — déformation, blobs, cordes (Stryder). |
| `upstream/context7/` | MIT | Serveur MCP : injecte la doc à jour des bibliothèques dans le contexte (anti-hallucination d'API). |
| `upstream/mem0/` | Apache-2.0 | Mémoire longue durée pour agents/LLM (extraction + vectoriel) — mémoire persistante (Alphred). |
| `upstream/Harmony/` | MIT | Patch runtime de méthodes .NET/C# (via BepInEx/MelonLoader) — standard du modding Unity. |
| `upstream/ida-pro-mcp/` | MIT | Serveur MCP exposant IDA à un agent/Claude (décompilation, xrefs, renommage) — pendant de GhidraMCP. |

Référencés en **lien** (licence non permissive, binaire, ou à installer depuis la release/pip) :

- **ia-agents** : [Serena](https://github.com/oraios/serena) (MCP « IDE pour agents », licence mixte par composant → lien), [Kokoro](https://github.com/hexgrad/kokoro) (TTS local, Apache-2.0, poids lourds), [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (STT, MIT, pip). Alt RAG : [LightRAG](https://github.com/HKUDS/LightRAG).
- **physique-netcode** : [godot-rollback-netcode](https://gitlab.com/snopek-games/godot-rollback-netcode) (MIT, GitLab) — netcode rollback de référence (Stryder).
- **modding-re** : [UABEA](https://github.com/nesrak1/UABEA) (assets Unity, MIT, binaire), [MelonLoader](https://github.com/LavaGang/MelonLoader), [Frida](https://github.com/frida/frida).
- **secu-reseau** (audit **défensif** uniquement) : [Nuclei](https://github.com/projectdiscovery/nuclei) (MIT), [Cameradar](https://github.com/Ullaakut/cameradar) (RTSP, MIT), [CrowdSec](https://github.com/crowdsecurity/crowdsec) (MIT), [RustScan](https://github.com/RustScan/RustScan) (GPL), [Lynis](https://github.com/CISOfy/lynis) (hardening, GPL).
- **devtools** : [uv](https://github.com/astral-sh/uv) (Python tout-en-un), [Textual](https://github.com/Textualize/textual) (TUI Python), [Nuitka](https://github.com/Nuitka/Nuitka) (Python → .exe), [lazygit](https://github.com/jesseduffield/lazygit), [yazi](https://github.com/sxyazi/yazi), [Gum](https://github.com/charmbracelet/gum).

## Références non copiées (à récupérer depuis leurs releases quand un projet en a besoin)

- Loaders / frameworks de mod : [BepInEx](https://github.com/BepInEx/BepInEx) (Unity, LGPL), [MelonLoader](https://github.com/LavaGang/MelonLoader),
  [RE-UE4SS](https://github.com/UE4SS-RE/RE-UE4SS) (Unreal), [Ultimate ASI Loader](https://github.com/ThirteenAG/Ultimate-ASI-Loader) (natif),
  [UnityExplorer](https://github.com/yukieiji/UnityExplorer).
- Extraction / décompilation : [AssetRipper](https://github.com/AssetRipper/AssetRipper) (Unity, GPL, 440 Mo), [ILSpy](https://github.com/icsharpcode/ILSpy)
  (`dotnet tool install -g ilspycmd`), [dnSpyEx](https://github.com/dnSpyEx/dnSpy), [Cpp2IL](https://github.com/SamboyCoding/Cpp2IL), [FModel](https://github.com/4sval/FModel) (Unreal).
- Bibliothèques : [Dear ImGui](https://github.com/ocornut/imgui) (menus en jeu), [Godot demo projects](https://github.com/godotengine/godot-demo-projects) (exemples officiels Godot 4, 550 Mo).
- Physique / Godot (détails dans `guides/physique-et-godot.md` §3) : [Godot Rapier Physics](https://github.com/appsinacup/godot-rapier-physics) (stepping + fluides),
  [Ten Minute Physics](https://matthias-research.github.io/pages/) (XPBD, sans licence), [corde verlet 3D](https://github.com/2nafish117/godot-verlet-rope),
  [Phantom Camera](https://github.com/ramokz/phantom-camera), [Terrain3D](https://github.com/TokisanGames/Terrain3D), [godot_voxel](https://github.com/Zylann/godot_voxel),
  [GodotSteam](https://codeberg.org/godotsteam/godotsteam) (déménagé sur Codeberg), [GUT](https://github.com/bitwes/Gut), [gdUnit4](https://github.com/godot-gdunit-labs/gdUnit4), [godot-debug-menu](https://github.com/godot-extended-libraries/godot-debug-menu).
- Services gratuits pour développeurs (hébergement, BDD, e-mail…) : [free-for-dev](https://github.com/ripienaar/free-for-dev) — **pas de licence**, donc non copié.
