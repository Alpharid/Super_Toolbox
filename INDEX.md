# INDEX — Super_Toolbox

> **Le fichier à lire en premier, et le seul à relire souvent.** Il liste tout ce que contient la toolbox, par
> domaine, en une ligne par outil. Pour le détail d'un outil → `CATALOGUE.md`. Pour « je veux faire X » → `guides/`.
> **Ne pas lire `CATALOGUE.md` ni fouiller `upstream/` tant que cet index suffit** (économie de tokens).

**7 domaines** : `godot` · `physique-netcode` · `modding-re` · `ia-agents` · `secu-reseau` · `devtools` · `creation-assets`.
Le cœur vivant de la toolbox est **[Heimdall](heimdall/README.md)**, le veilleur (§ en bas).

---

## 1. Contenu copié (dans `upstream/`, git subtree)

### 🎮 godot — addons Godot 4
- **limboai** — `limbonaut/limboai` · MIT · behavior trees + machines à états hiérarchiques (éditeur visuel, GDExtension).
- **beehave** — `bitbrain/beehave` · MIT · behavior trees en **pur GDScript** (lisible, sans compilation).
- **godot-statecharts** — `derkork/godot-statecharts` · MIT · machines à états hiérarchiques/parallèles pilotables 100 % en code (idéal panels datapad).
- **limbo_console** — `limbonaut/limbo_console` · MIT · console de debug in-game (commandes) pour déboguer les builds exportés sans éditeur.
- **godot-gdscript-toolkit** — `Scony/godot-gdscript-toolkit` · MIT · linter + formateur GDScript en CLI (gdformat/gdlint), workflow tout-en-code.

### 🧱 physique-netcode — physique & multijoueur
- **JoltPhysics** — `jrouwe/JoltPhysics` · MIT · le moteur physique de Godot 4.4+ (sources + ~150 démos : cordes, flottaison, ragdolls, corps mous).
- **GodotIK** — `monxa/GodotIK` · MIT · IK 3D (FABRIK) pour Godot 4.3+.
- **godot-destruction-plugin** — `Jummit/godot-destruction-plugin` · MIT · fragments → corps rigides (destruction simple).
- **netfox** — `foxssake/netfox` · MIT · multijoueur Godot 4 : rollback, synchro d'état, prédiction d'entrées.
- **godot-softbody2d** — `appsinacup/godot-softbody2d` · MIT · soft bodies 2D (ressorts/points) : déformation, blobs, cordes (Stryder).

### 🔧 modding-re — modding & reverse engineering
- **universal-modder** — `rehan-remade/universal-modder` · MIT · **la méthode complète** pour modder presque n'importe quel jeu (CLI `um`, 11 skills, playbooks par moteur).
- **rea** — `morluto/rea` · MIT · reverse engineering avec preuves (CLI/MCP, Ghidra, .NET, Electron).
- **GhidraMCP** — `LaurieWired/GhidraMCP` · Apache-2.0 · piloter Ghidra depuis Claude (plugin + pont MCP).
- **ida-pro-mcp** — `mrexodia/ida-pro-mcp` · MIT · piloter IDA depuis Claude (décompilation, xrefs, renommage) — pendant de GhidraMCP.
- **Harmony** — `pardeike/Harmony` · MIT · patch runtime de méthodes .NET/C# (via BepInEx/MelonLoader) — standard du modding Unity.
- **Il2CppDumper** — `Perfare/Il2CppDumper` · MIT · jeux Unity IL2CPP (restaure noms de classes/méthodes).
- **minhook** — `TsudaKageyu/minhook` · BSD-2 · bibliothèque C de hooks x86/x64 (mods natifs).
- **android-reverse-engineering-skill** — `SimoneAvogadro/android-reverse-engineering-skill` · Apache-2.0 · skill Claude Code : APK → jadx, noms Kotlin malgré R8, API web extraites (Waze_SA_Mod).
- **coop-anything** — `cranebeaker/coop-anything` · MIT · playbook + serveur MCP pour rendre **coop n'importe quel jeu solo** (en ligne ou écran partagé) : reprise de mods abandonnés, RE, netcode Steam relay, QA par bots ; annuaire de 230+ mods coop, coop d'émulateurs, PartyDeck (écran partagé Steam Deck).
- 📘 **Méthode RE avec Claude** (11 étapes, prompts prêts, clean-room, parité) → [guides/reverse-engineering-avec-claude.md](guides/reverse-engineering-avec-claude.md).

### 🤖 ia-agents — agents IA, MCP & LLM local
- **context7** — `upstash/context7` · MIT · serveur MCP qui injecte la doc à jour des libs dans le contexte (anti-hallucination d'API).
- **mem0** — `mem0ai/mem0` · Apache-2.0 · mémoire longue durée pour agents/LLM (extraction + vectoriel) — mémoire persistante (Alphred).
- **awesome-mcp-servers** — `punkpeye/awesome-mcp-servers` · MIT · liste de serveurs MCP (outils pour agents).
- 📘 **IA locale rapide et fiable (24 Go)** : moteur/modèle (Qwen3.8 MTP), agent (Pi), voix FR sur CPU, web local → [guides/ia-locale-performante.md](guides/ia-locale-performante.md).
- **awesome-claude-code** — `hesreallyhim/awesome-claude-code` · CC-BY-NC-ND · skills/hooks/commandes pour Claude Code (usage perso, lien-liste).

### 🛡️ secu-reseau — sécurité, réseau & audit défensif
- _(rien de copié — licences surtout GPL/SSPL → référencées en lien : Nuclei, Cameradar, CrowdSec, RustScan, Lynis… voir `CATALOGUE.md` § Liens Heimdall et `heimdall/reports/`)._

### 🧰 devtools + listes transverses
- **public-apis** — `public-apis/public-apis` · MIT · ~1 400 API gratuites classées.
- **awesome-godot** — `Calinou/awesome-godot` · CC-BY-4.0 · écosystème Godot.
- **magictools** — `ellisonleao/magictools` · MIT · création de jeux (moteurs, art, son, outils).
- **awesome-gamedev** — `Calinou/awesome-gamedev` · CC-BY-SA · logiciels & assets libres.
- **awesome** — `sindresorhus/awesome` · CC0 · méta-liste de toutes les listes « awesome ».

### 🎨 creation-assets — images, 3D, sprites, audio (installé en local, pas copié)
- **Atelier IA** — `C:\Atelier_IA` · ComfyUI portable + modèles partagés (`modeles/`) · lancer `lancer_comfyui.bat` → **guide [creer-des-assets.md](guides/creer-des-assets.md)**.
- **Modèles** (licences vérifiées UE + commercial) : Z-Image Turbo/base + Fun ControlNet (Apache) · Qwen-Image-2512 / Edit-2511 + LoRA angles + ControlNet Union (Apache) · **TRELLIS.2** image→3D natif (MIT) · BiRefNet (MIT).
- **Krita + krita-ai-diffusion** — repeindre par-dessus / inpainting branché sur l'atelier (casse le « look IA »).
- **scripts/comfy_client.py** — piloter ComfyUI depuis un script (txt2img, édition, upload).
- Audio/vidéo : ffmpeg, Audacity, **Surge XT** (microtonal, maqâms), 7-Zip, uv. Pistes : ai-toolkit (LoRA), ACE-Step (musique), Kimodo (mouvement), Wan VACE.

> Les listes se **grep**, jamais se lisent en entier. Gros outils non copiés (BepInEx, UE4SS, AssetRipper, ILSpy,
> Rapier, Terrain3D…) : liens en fin de `CATALOGUE.md`.

## 2. Carte projet → outils (le réflexe)

Quand on ouvre un projet : `heimdall.ps1 project -Name <Projet>` (détail dans `heimdall/projects.json`).

| Projet | Domaines | Outils du kit qui s'appliquent |
|---|---|---|
| **Stryder_Symbiosis** (jeu Godot+Jolt) | godot, physique-netcode | JoltPhysics, GodotIK, godot-destruction-plugin, netfox, limboai, beehave → `guides/physique-et-godot.md` |
| **MixMaster_Regenesis** (serveur + panel) | modding-re, godot | rea, universal-modder, Il2CppDumper, GhidraMCP → `guides/reverse-engineering-avec-claude.md` (clean-room serveur) |
| **Alphred_AI** (IA locale + panel + voix) | ia-agents, godot, devtools | context7, mem0, awesome-mcp-servers → `guides/ia-locale-performante.md` |
| **WifiSentinel** (audit réseau + panel) | secu-reseau, godot | public-apis _(manques : ONVIF/RTSP, scanners — Heimdall)_ |
| **Kali-Pi** (Pi Kali, datapad, stream-deck) | secu-reseau, devtools | _(manques — Heimdall)_ |
| **Waze_SA_Mod** (APK Waze re-packagé, sans root) | modding-re | android-reverse-engineering-skill → `guides/reverse-engineering-avec-claude.md` |
| **SteamDeck** (Deck OLED, émulation, multi local) | modding-re | coop-anything (PartyDeck écran partagé, netplay Dolphin/RetroArch, ports PC coop) |
| **GTA_SA_Chill_Trainer** (GTA SA moddé + trainer) | modding-re | coop-anything (annuaire : « Player 2 » CLEO drop-in/out, SA-MP/MTA), minhook |
| **Guardians_of_the_Seal** (MMORPG djinn, Godot) | creation-assets, godot, physique-netcode | Atelier IA, comfy_client, universal-modder (asset-pipeline iso8), netfox → `guides/creer-des-assets.md` |
| **Tokyo_Hikitori** (jeu VR Unreal, Tokyo 1996) | creation-assets, physique-netcode, godot, devtools | Atelier IA (moodboard/repeints seulement), launcher d'Oddyseus _(manques : mains physiques VR, ragdoll actif, néons en VR — Heimdall)_ → `guides/creer-des-assets.md` |
| **Acapella_Record** (clip a cappella en mosaïque, Electron + ffmpeg) | creation-assets, devtools | ffmpeg _(manques : accordeur temps réel, alignement audio — Heimdall)_ |

**Fil rouge** : presque tous ont un **panel/datapad Godot 4.7 construit 100 % en code** → toute ressource Godot
UI/thème/composants-en-code sert plusieurs projets : priorité de veille `godot`.

## 3. Heimdall — le veilleur (cœur de la toolbox)

Se tient au courant de ce qui sort d'utile, et garde cet index à jour. Tout : **[heimdall/README.md](heimdall/README.md)**.
- Déclic 1 — **réflexe projet** : `heimdall.ps1 project -Name <P>` → outils + manques ; un manque → veille ciblée.
- Déclic 2 — **digest hebdo** (agent planifié) : passe large, écrit `heimdall/reports/AAAA-MM-JJ.md`, met à jour cet index.
- Lancer une passe : `heimdall.ps1 brief` puis la recette du README (`report` → remplir → proposer → `kit.ps1 add`).

### Dernières nouveautés
<!-- HEIMDALL:LATEST -->
- **2026-10-19** — +1 subtree **coop-anything** (MIT) : rendre coop n'importe quel jeu solo (playbook, MCP, annuaire 230+ mods) ; pistes ajoutées pour SteamDeck et GTA_SA_Chill_Trainer.
- **2026-10-19** — Veille **Alphred** : guide [ia-locale-performante.md](guides/ia-locale-performante.md) (Qwen3.8 MTP, Ollama 0.40.6, Pi, Pocket TTS, Smart Turn, SearXNG…) · [rapport](heimdall/reports/2026-10-19-alphred.md).
- **2026-10-19** — Cours RE de @0xMovez exploité : guide [reverse-engineering-avec-claude.md](guides/reverse-engineering-avec-claude.md) (11 étapes, prompts, clean-room, parité) + modèle de règles RE ; +1 subtree `android-reverse-engineering-skill` ; liens Caveman, ghidra-mcp (bethington), IDA MCP officiel, ImHex, mitmproxy, ArtCraft. Détail : [heimdall/reports/2026-10-19-cours-re.md](heimdall/reports/2026-10-19-cours-re.md).
- **2026-10-19** — 6 trouvailles : voir [heimdall/reports/2026-10-19.md](heimdall/reports/2026-10-19.md).
- **2026-10-18** — Nouveau domaine **`creation-assets`** : Atelier IA local (ComfyUI, Z-Image, Qwen-Image/Edit, TRELLIS.2, Krita AI) + guide [creer-des-assets.md](guides/creer-des-assets.md) + `scripts/comfy_client.py`.
- **2026-10-16** — Premier digest + **1ère vague** : +8 outils copiés, ~11 en lien. Détail : [heimdall/reports/2026-10-16.md](heimdall/reports/2026-10-16.md) · liens : [CATALOGUE.md](CATALOGUE.md) § Ajouts Heimdall.
<!-- /HEIMDALL:LATEST -->

## 4. Maintenir / étendre
- Mettre à jour les dépôts copiés : `scripts\kit.ps1 check` → `update -Name <outil>` ; santé : `kit.ps1 verify`.
- Ajouter un dépôt : `scripts\kit.ps1 add -Name <nom> -Url <url> -Category <domaine> -Role "<rôle>"`, puis 1 ligne ici + dans `CATALOGUE.md`.
- Détail par dépôt : [CATALOGUE.md](CATALOGUE.md) · par besoin : [guides/](guides/README.md) · passation/règles : [HANDOVER.md](HANDOVER.md).
