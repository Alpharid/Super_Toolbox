# Catalogue des outils du kit

Référence rapide : quoi utiliser pour quoi. Chemins relatifs à `D:\Modding_Tools_Kit\`. Méthode et règles : [HANDOVER.md](HANDOVER.md).

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
