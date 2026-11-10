# INDEX — Super_Toolbox

> **Le fichier à lire en premier, et le seul à relire souvent.** Il liste tout ce que contient la toolbox, par
> domaine, en une ligne par outil. Pour le détail d'un outil → `CATALOGUE.md`. Pour « je veux faire X » → `guides/`.
> **Ne pas lire `CATALOGUE.md` ni fouiller `upstream/` tant que cet index suffit** (économie de tokens).

**9 domaines** : `godot` · `physique-netcode` · `modding-re` · `ia-agents` · `secu-reseau` · `devtools` · `creation-assets` · `qa-playtest` · `auto-diag`.
Deux cœurs vivants : **[Heimdall](heimdall/README.md)**, le veilleur (§ en bas), et **[Hyperbole](hyperbole/README.md)**, la salle
du temps (joueurs simulés qui testent les jeux sur le PC, §1 `qa-playtest`).
**La méthode Alpharium** (comment on travaille : propriétaire, chantiers, pages de décision, agents maison, local d'abord) :
[guides/notre-methode.md](guides/notre-methode.md), et sa vitrine [guides/vitrine/notre-methode.html](guides/vitrine/notre-methode.html).

---

## 1. Contenu copié (dans `upstream/`, git subtree)

### 🎮 godot — addons Godot 4
- **limboai** — `limbonaut/limboai` · MIT · behavior trees + machines à états hiérarchiques (éditeur visuel, GDExtension).
- **beehave** — `bitbrain/beehave` · MIT · behavior trees en **pur GDScript** (lisible, sans compilation).
- **godot-statecharts** — `derkork/godot-statecharts` · MIT · machines à états hiérarchiques/parallèles pilotables 100 % en code (idéal panels datapad).
- **limbo_console** — `limbonaut/limbo_console` · MIT · console de debug in-game (commandes) pour déboguer les builds exportés sans éditeur.
- **godot-gdscript-toolkit** — `Scony/godot-gdscript-toolkit` · MIT · linter + formateur GDScript en CLI (gdformat/gdlint), workflow tout-en-code.
- **godot_rl_agents_plugin** — `edbeeching/godot_rl_agents_plugin` · MIT · capteurs raycast/grille/caméra (« ce qu'un joueur voit ») = Sens prêts à l'emploi pour les Einherjar d'**Hyperbole** ; nœud Sync (headless accéléré ↔ Python).

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
- 📘 **Joueurs IA dans un jeu en ligne** (bots qui jouent vraiment sans tricher : Corps / Tête / Esprit LLM sur événement, mémoire et relations ; profils de joueurs sur mesure (tryhard, casual, chill, tricheur qui signale sans tricher, streamer…), rapports chiffrés + récit dans leur voix, séances d'un seul profil ou mélangées ; usages : peupler, économie, quêtes, charge, anti-triche, non-régression) → [guides/joueurs-ia-dans-un-jeu-en-ligne.md](guides/joueurs-ia-dans-un-jeu-en-ligne.md).
- 📘 **Le regard** (juge visuel par l'API avant l'œil du propriétaire : défauts connus, contexte « voulu » par entité, ~0,03 $ l'image, tri avant de soumettre) → [guides/le-regard.md](guides/le-regard.md) ; moteur générique **`scripts/regard/regard.py`** (le projet donne ses défauts, voulus et fiches dans un `regard.json`).
- **scripts/claude_api/** — maison · **le client de l'API Claude** pour tous les projets : `claude_api.py` (`Client(projet)` : journal par projet, plafond commun sur le cycle, Batch, cache des consignes et des réponses, schéma JSON) et **`projets_autorises.json`, la liste blanche** (Guardians seul ; un projet absent est refusé : demander au propriétaire d'abord) → [guides/economiser-tokens-et-gpu.md](guides/economiser-tokens-et-gpu.md) §3.
- 📘 **La gazette** (rapports des joueurs IA → une page par jour pour corriger et équilibrer, quelques centimes, « Pour juger, il manquait ») → [guides/la-gazette.md](guides/la-gazette.md).
- 📘 **Économiser tokens, crédits de l'API et GPU** (où tourne quoi, sessions courtes, client API avec journal, plafond, Batch, cache ; file du GPU) → [guides/economiser-tokens-et-gpu.md](guides/economiser-tokens-et-gpu.md).
- **awesome-claude-code** — `hesreallyhim/awesome-claude-code` · CC-BY-NC-ND · skills/hooks/commandes pour Claude Code (usage perso, lien-liste).

### 🧪 qa-playtest — playtest automatisé (outil maison : Hyperbole)
- **Hyperbole** — `hyperbole/` · maison (MIT comme le reste du code maison) · **la salle du temps** : Mr. Popo (orchestrateur Python
  stdlib) envoie des **Einherjar** (joueurs simulés à profils : moyen, tryhard, casual, chill, fouineur, streamer, saboteur, meneur,
  complétionniste, débutant) dans des **chambres** headless accélérées (ou x1 pour le réseau), cycle après cycle (**Valhalla**).
  **Sans triche** : entrées de joueur + Sens seulement (contrôle `lint`). Rapports : rétention, fun, défi, équilibre, apprentissage,
  bugs/blocages/failles/fuites, effet du saboteur (jumeau), A/B, non-régression, rejeu par graine ; Esprit LLM local optionnel.
  Addon **Godot 4.7**, écrivain **C#**, **pont TCP** pour tout autre moteur. Démarrer : `python hyperbole\hyperbole.py demo --ouvrir`
  · brancher un jeu : `hyperbole.py init <projet> --moteur godot` → [hyperbole/README.md](hyperbole/README.md).
- Liens (veille 2026-11-02, [rapport](heimdall/reports/2026-11-02-hyperbole.md)) : gdUnit4 6.2.3 (entrées simulées, Godot 4.7), godot-qa
  (scénarios JSON), godot-cli-control, playtest-agent, GBQA, PettingZoo, lifelines, Unreal Learning Agents → `CATALOGUE.md`.

### 🛡️ secu-reseau — sécurité, réseau & audit défensif
- _(rien de copié — licences surtout GPL/SSPL → référencées en lien : Nuclei, Cameradar, CrowdSec, RustScan, Lynis… voir `CATALOGUE.md` § Liens Heimdall et `heimdall/reports/`)._

### 🚗 auto-diag — diagnostic & codage automobile (OBD, CAN, UDS, GMLAN)
- _(rien de copié pour l'instant — liens, veille du 2026-11-10 : [rapport](heimdall/reports/2026-11-10-auto-diag.md))_ : **python-can** (LGPL), **can-isotp**, **udsoncan**, **cantools** (MIT) à réutiliser ; **OBDex** (codes défaut, données CC0) ; à étudier sans copier (GPL) : **scapy** `contrib/automotive/gm` (GMLAN), **ddt4all** (codage par fichiers de données), OpenVehicleDiag, CaringCaribou ; **SavvyCAN** (analyse de captures) ; **ELM327-emulator** (tests sans voiture). Adaptateurs : OBDLink MX+/EX (STN), CANable 2.0 candleLight (sonde).

### 🧰 devtools + listes transverses
- **scripts/chantiers/** — maison · **un terminal Claude par chantier** : `chantier.ps1` (ouvre la session sur sa fiche ; elle ne s'arrête jamais, surveille sa fiche et traite ce qui arrive sous « À TRAITER »), `chantiers_etat.sh` (état, alertes), `veille_chantiers.sh` (l'orchestrateur rend la main sur changement, calme ou point), `verrou_gpu.sh` (file du GPU partagée) → [guides/orchestrer-des-chantiers.md](guides/orchestrer-des-chantiers.md).
- **scripts/recompter_vitrine.py** — maison · recompte les chiffres de la méthode et de sa vitrine (tests listés par `dotnet`, dépôt, journaux de l'API) et les réécrit ; `--ach` recopie la vitrine dans ACH.
- **Pages de décisions** — maison · gabarit sombre à cocher + « Copier mes réponses », `scripts/verifier_page.sh` (node --check) → [guides/pages-de-decisions.md](guides/pages-de-decisions.md).
- **scripts/discord/** — maison · **un serveur Discord de jeu construit par script** : `construire.py` (le fichier → le serveur : rôles, salons par phases, droits, Communauté, accueil natif, AutoMod, textes fixes, un message par langue, guildes reconnues, salons vocaux des membres jamais élagués ; plan d'abord, ne supprime rien), `modele_serveur.yaml` (gabarit), faux Discord pour les tests → [guides/communaute-discord.md](guides/communaute-discord.md).
- **public-apis** — `public-apis/public-apis` · MIT · ~1 400 API gratuites classées.
- **awesome-godot** — `Calinou/awesome-godot` · CC-BY-4.0 · écosystème Godot.
- **magictools** — `ellisonleao/magictools` · MIT · création de jeux (moteurs, art, son, outils).
- **awesome-gamedev** — `Calinou/awesome-gamedev` · CC-BY-SA · logiciels & assets libres.
- **awesome** — `sindresorhus/awesome` · CC0 · méta-liste de toutes les listes « awesome ».

- 📘 **Vieux jeu PC en réseau par Internet** (IPX/DirectPlay → IPXWrapper + relais DOSBox-IPX, registre sans admin par DLL relais MinHook, pièges Windows 10/11, tests sans le jeu, distribution Windows/Mac) → [guides/jouer-en-reseau-a-un-vieux-jeu.md](guides/jouer-en-reseau-a-un-vieux-jeu.md).
- 📘 **Vieux jeu PC dans le navigateur** (source port → WebAssembly, pièges WebGL/ANGLE, hébergement Cloudflare Pages, cache IndexedDB, tests Chrome pilotés) → [guides/porter-un-jeu-pc-dans-le-navigateur.md](guides/porter-un-jeu-pc-dans-le-navigateur.md).

### 🎨 creation-assets — images, 3D, sprites, audio (installé en local, pas copié)
- **Atelier IA** — `C:\Atelier_IA` · ComfyUI portable + modèles partagés (`modeles/`) · lancer `lancer_comfyui.bat` → **guide [creer-des-assets.md](guides/creer-des-assets.md)**.
- **Modèles** (licences vérifiées UE + commercial) : Z-Image Turbo/base + Fun ControlNet (Apache) · Qwen-Image-2512 / Edit-2511 + LoRA angles + ControlNet Union (Apache) · **TRELLIS.2** image→3D natif (MIT) · BiRefNet (MIT).
- **Krita + krita-ai-diffusion** — repeindre par-dessus / inpainting branché sur l'atelier (casse le « look IA »).
- **scripts/comfy_client.py** — piloter ComfyUI depuis un script (txt2img et image→image Z-Image, LoRA, édition Qwen, **TRELLIS.2 image→GLB**, téléversement à empreinte).
- 📘 Chaînes éprouvées sur Guardians (entité → sprites 8 directions, icônes peintes, pièces d'interface, carte à l'encre, sons sans paroles par Whisper + AST, musique dans un mode imposé par squelette, personnage MPFB 2 + 100STYLE, vêtements simulés et tissu vivant par Dem Bones, logo et icône d'un jeu : relief en grand, pixel de 16 à 32 px, .ico de fenêtre par échelle) → [creer-des-assets.md](guides/creer-des-assets.md) § Chaînes éprouvées.
- 📘 **Musique et sons d'un jeu** (mode imposé par squelette, SFT + ScragVAE, peigne creusé, tri étalonné avant l'écoute, page d'écoute avec avis et notes libres, morceau en jeu refait de près en avant / après, vraies voix CC0 de Freesound par OAuth2, morceau généré rejoué par de vrais instruments (Demucs + Basic Pitch ONNX), désécrêtage, musique de combat qui reprend où elle était, bruitages MOSS) → [guides/musique-de-jeu.md](guides/musique-de-jeu.md).
- Audio/vidéo : ffmpeg, Audacity, **Surge XT** (microtonal, maqâms), 7-Zip, uv. Pistes : ai-toolkit (LoRA), ACE-Step (musique), Kimodo (mouvement), Wan VACE.

> Les listes se **grep**, jamais se lisent en entier. Gros outils non copiés (BepInEx, UE4SS, AssetRipper, ILSpy,
> Rapier, Terrain3D…) : liens en fin de `CATALOGUE.md`.

## 2. Carte projet → outils (le réflexe)

Quand on ouvre un projet : `heimdall.ps1 project -Name <Projet>` (détail dans `heimdall/projects.json`).

| Projet | Domaines | Outils du kit qui s'appliquent |
|---|---|---|
| **Stryder_Symbiosis** (jeu Godot+Jolt) | godot, physique-netcode, qa-playtest | JoltPhysics, GodotIK, godot-destruction-plugin, netfox, limboai, beehave, **Hyperbole** (1er adaptateur branché 2026-11-05, repo `hyperbole/`) → `guides/physique-et-godot.md` |
| **MixMaster_Regenesis** (serveur + panel) | modding-re, godot | rea, universal-modder, Il2CppDumper, GhidraMCP → `guides/reverse-engineering-avec-claude.md` (clean-room serveur) ; Hyperbole (bots-clients de charge, piste) |
| **Alphred_AI** (IA locale + panel + voix) | ia-agents, godot, devtools | context7, mem0, awesome-mcp-servers → `guides/ia-locale-performante.md` |
| **WifiSentinel** (audit réseau + panel) | secu-reseau, godot | public-apis _(manques : ONVIF/RTSP, scanners — Heimdall)_ |
| **Kali-Pi** (Pi Kali, datapad, stream-deck) | secu-reseau, devtools | _(manques — Heimdall)_ |
| **Waze_SA_Mod** (APK Waze re-packagé, sans root) | modding-re | android-reverse-engineering-skill → `guides/reverse-engineering-avec-claude.md` |
| **SteamDeck** (Deck OLED, émulation, multi local) | modding-re | coop-anything (PartyDeck écran partagé, netplay Dolphin/RetroArch, ports PC coop) |
| **GTA_SA_Chill_Trainer** (GTA SA moddé + trainer) | modding-re | coop-anything (annuaire : « Player 2 » CLEO drop-in/out, SA-MP/MTA), minhook |
| **Guardians_of_the_Seal** (MMORPG djinn, Godot) | creation-assets, godot, physique-netcode, qa-playtest | Atelier IA, comfy_client, universal-modder (asset-pipeline iso8), netfox, **Hyperbole** (journal des Descellés : `csharp/HyperboleJournal.cs`) → `guides/creer-des-assets.md`, `guides/joueurs-ia-dans-un-jeu-en-ligne.md` |
| **Tokyo_Hikitori** (jeu VR Unreal, Tokyo 1996) | creation-assets, physique-netcode, godot, devtools | Atelier IA (moodboard/repeints seulement), launcher d'Oddyseus _(manques : mains physiques VR, ragdoll actif, néons en VR — Heimdall)_ → `guides/creer-des-assets.md` |
| **Medusa_Record** (ex-Acapella, clip a cappella en mosaïque, Electron + ffmpeg) | creation-assets, devtools | ffmpeg _(manques : accordeur temps réel, alignement audio — Heimdall)_ |
| **MCM_Online** (Motocross Madness 1 & 2 à 8 par Internet : IPXWrapper + relais, lanceur, Mac via Wine) | modding-re, devtools | minhook (correctif registre sans admin) → `guides/jouer-en-reseau-a-un-vieux-jeu.md` |
| **MM2_Web** (Midtown Madness 2 dans le navigateur, OpenMM2 → WASM) | devtools, modding-re | coop-anything (annuaire, pour un futur multi) → `guides/porter-un-jeu-pc-dans-le-navigateur.md` |
| **Sanctuary** (rogue-lite : mini-jeu Electron + futur dungeon crawler 3D) | godot, creation-assets, qa-playtest | Hyperbole (runs : survie, causes de mort, contenu épuisé) |
| **TIDIM** (FPS coop, familiers d'un héros IA vantard) | godot, ia-agents, qa-playtest | Hyperbole (familiers simulés par profils, équilibre de la barre d'ego) |
| **Alpharium_KSC** (Kaddour Social Club : club social familial 3D, Godot 4.7 web ; reprend la Maquette Three.js et le Project ALL) | godot, creation-assets, qa-playtest, devtools | limbo_console, gdtoolkit, **Hyperbole** (charge à 32, économie), Atelier IA + TRELLIS.2 (décimé pour le web), musique de jeu → roadmap `C:\Alpharium_KSC\docs\fusion\ROADMAP.md` |
| **Project_ALL** (Alpharium Luxurious Lounge : le même club en Habbo 2D, TypeScript/Node, en service chez Annes) | devtools, qa-playtest | Hyperbole (pont TCP), pages de décisions |
| **Valisa** (« la valise » : diagnostic + codage auto, une voiture à la fois, .exe portable + Kali-Pi) | auto-diag, devtools, modding-re | Pages de décisions, python-can/can-isotp/udsoncan (pistes) _(manques : seed/key GMLAN et config BCM Corsa D (capture OP-COM), codes défaut constructeur libres, Subaru SSM — Heimdall)_ |
| **Ghul** (GHŪL : FPS d'horreur coop 1-8 sans interface, caméra de casque, Algérie réelle, Unreal 5.8) | creation-assets, physique-netcode, ia-agents, qa-playtest | **Hyperbole** (préparé, moteur commande), ffmpeg _(manques : post-process caméra UE, caméra de casque, IA de créatures (grimpeur, sprinteur), voix des ghuls, son spatial, coop 8 — Heimdall)_ → `guides/creer-des-assets.md` |

**Jeux** : tout projet de jeu passe par **Hyperbole** avant les vrais joueurs (`hyperbole.py init <projet>`), c'est là que
se testent l'équilibre, le fun et les bugs sans dépenser de tokens.

**Fil rouge** : presque tous ont un **panel/datapad Godot 4.7 construit 100 % en code** → toute ressource Godot
UI/thème/composants-en-code sert plusieurs projets : priorité de veille `godot`.

## 3. Heimdall — le veilleur (cœur de la toolbox)

Se tient au courant de ce qui sort d'utile, et garde cet index à jour. Tout : **[heimdall/README.md](heimdall/README.md)**.
- Déclic 1 — **réflexe projet** : `heimdall.ps1 project -Name <P>` → outils + manques ; un manque → veille ciblée.
- Déclic 2 — **digest hebdo** (agent planifié) : passe large, écrit `heimdall/reports/AAAA-MM-JJ.md`, met à jour cet index.
- Lancer une passe : `heimdall.ps1 brief` puis la recette du README (`report` → remplir → proposer → `kit.ps1 add`).

### Dernières nouveautés
<!-- HEIMDALL:LATEST -->
- **2026-11-10** — Nouveau domaine **`auto-diag`** (diagnostic & codage automobile), né avec **Valisa** : [heimdall/reports/2026-11-10-auto-diag.md](heimdall/reports/2026-11-10-auto-diag.md).
- **2026-11-09** — Retour de Guardians (chantier lancement) : **le serveur Discord construit par script** (`scripts/discord/`, gabarit par phases, tests sans Discord) et son guide ; le bot qui ne publie rien sans un clic.
- **2026-11-08** — Les pistes de la méthode faites : **client de l'API avec liste blanche des projets** (`scripts/claude_api/`), **regard générique** (`scripts/regard/`), chiffres de la vitrine recomptés par script ; le journal d'Hyperbole écrit par les joueurs IA de Guardians (rapport par profil, `comparer` entre versions, coût de la séance).
- **2026-11-07** (fin de nuit) — La gazette ne reprend plus ce qui est tranché et sépare « défaut prouvé » et « joueur IA perdu » ; l'Esprit des joueurs IA branché sans bloquer la boucle (quand répondre, mention « IA » à l'entrée) ; la traduction du wiki et du site (empreintes, segments).
- **2026-11-07** — **La méthode Alpharium** documentée (`guides/notre-methode.md` + vitrine) ; nouveaux guides : le regard, la gazette, la musique de jeu, l'économie de tokens et de GPU ; l'orchestrateur (« À TRAITER », veille, relance) dans `orchestrer-des-chantiers.md` ; `veille_chantiers.sh`.
- **2026-11-07** — Retour de Guardians of the Seal : orchestration en chantiers (`scripts/chantiers/`), pages de décisions (gabarit + vérificateur), chaînes d'art et de son dans `creer-des-assets.md`, `comfy_client.py` à niveau.
- **2026-11-02** — **Hyperbole** entre dans la boîte (playtest par joueurs simulés) + veille ciblée `qa-playtest` : [heimdall/reports/2026-11-02-hyperbole.md](heimdall/reports/2026-11-02-hyperbole.md).
- **2026-11-02** — 1 trouvaille (semaine calme) : voir [heimdall/reports/2026-11-02.md](heimdall/reports/2026-11-02.md).
<!-- /HEIMDALL:LATEST -->

## 4. Maintenir / étendre
- Mettre à jour les dépôts copiés : `scripts\kit.ps1 check` → `update -Name <outil>` ; santé : `kit.ps1 verify`.
- Ajouter un dépôt : `scripts\kit.ps1 add -Name <nom> -Url <url> -Category <domaine> -Role "<rôle>"`, puis 1 ligne ici + dans `CATALOGUE.md`.
- Détail par dépôt : [CATALOGUE.md](CATALOGUE.md) · par besoin : [guides/](guides/README.md) · passation/règles : [HANDOVER.md](HANDOVER.md).
