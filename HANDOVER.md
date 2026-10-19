# Super_Toolbox — HANDOVER

> Document de passation : permet à n'importe quelle IA (Claude, Alphred l'IA locale, une autre) de reprendre sans contexte.
> **Si tu es Alphred (modèle local) : lis d'abord le §6, il est écrit pour toi.** Mets à jour l'Historique (§11) après chaque changement.

## 1. Ce que c'est

La **boîte à outils open-source** de l'utilisateur (compte GitHub Alpharid, dépôt **public**
`Alpharid/Super_Toolbox`, local `D:\Super_Toolbox`). Elle rassemble les meilleurs outils open-source utiles à
**tous ses projets** (passés, présents, futurs) : modding/création de jeux, mais aussi IA/agents, réseau/sécurité
défensive, Godot UI, outils dev. Les dépôts tiers sont copiés dans `upstream/` avec **git subtree** (une vraie copie
+ un lien vers l'original pour récupérer ses nouveautés) ; notre documentation et nos scripts sont à la racine.

**Deux usages, en réflexe** (lire `INDEX.md` d'abord — c'est le pilier, token-léger) :
1. **À chaque projet touché** : consulter l'index + `heimdall.ps1 project -Name <P>` → proposer les outils pertinents déjà présents, et repérer les manques.
2. **Un manque, ou une veille planifiée** : **Heimdall** (le veilleur, `heimdall/`) cherche de nouveaux outils, propose les meilleurs, et tient l'index à jour. Voir §4 bis.

C'est public et open-source car presque tout vient de la communauté open source (chaque outil garde sa licence).

## 2. État (2026-10-16)

- **Renommé** `Modding_Tools_Kit` → **`Super_Toolbox`**, passé **public**. Pilier : `INDEX.md` (à lire en premier, token-léger).
- Cœur **Heimdall** ajouté (`heimdall/`) : veille techno sur 6 domaines + réflexe projet (§4 bis). 1er digest : `heimdall/reports/2026-10-16.md`.
- **26 dépôts** copiés (18 d'origine + 8 de la 1ère vague Heimdall), **4 guides par besoin** dans `guides/`, catalogue par dépôt dans `CATALOGUE.md`.
  `scripts\kit.ps1 verify` → « kit cohérent ».
- Digest hebdo : agent cloud planifié (routine `schedule`) qui lance une passe Heimdall et pousse un digest daté.
- **Rien n'est installé** sur le PC (ni `uv`, ffmpeg, Blender, Ghidra, JDK 21, `rea-agents`, ni les addons Godot) : on installe à
  la demande, pour un projet précis, en vérifiant d'abord ce qui existe déjà (règle de l'utilisateur : jamais de doublon).
- PC : Windows 11, RTX 3090 Ti, Python 3.13, Node, .NET, git, gh. `python3` = alias Microsoft Store qui ne lance rien.

### Mise à jour 2026-10-19
- Veille ciblée **Alphred** : guide `guides/ia-locale-performante.md` (moteur/modèle, agent, voix FR CPU, web local), rapport `heimdall/reports/2026-10-19-alphred.md`, pistes Alphred réécrites dans `projects.json`, sources ia-agents enrichies.
- Cours « Reverse Engineer Anything with Opus 5.5 » (@0xMovez) exploité : guide `guides/reverse-engineering-avec-claude.md` (méthode 11 étapes adaptée au kit : rea en CLI, Ghidra lecture seule sous Windows ; prompts triage/annotation/obfuscation/essaim/spec clean-room/parité), modèle `guides/modeles/CLAUDE.re-house-rules.md`, +1 subtree `android-reverse-engineering-skill` (**27 dépôts**), liens dans `CATALOGUE.md`, projet `Waze_SA_Mod` ajouté à Heimdall.

### À faire / idées
- Projet à venir : **Stryder_Symbiosis** (jeu Godot 4.7 + Jolt, physique avancée, coop ; dépôt `C-Chafik/Stryder-Symbiosis`, local
  `C:\Stryder-Symbiosis`, géré depuis une autre session Claude) → `guides/physique-et-godot.md` est écrit pour lui.
- Ajouter les dépôts pertinents au fil des demandes (critères ci-dessous) et maintenir à jour sur demande (§4).

### Mise à jour 2026-10-18
- **Atelier IA installé** (`C:\Atelier_IA`, ~110 Go de modèles) pour Guardians of the Seal et tous les projets à venir : 7ᵉ domaine `creation-assets`, guide `guides/creer-des-assets.md`, client `scripts/comfy_client.py`. Installés par winget : Krita (+ krita-ai-diffusion), ffmpeg, 7-Zip, Audacity, Surge XT, uv.

## 3. Contenu

Rangement : **un dossier par dépôt dans `upstream/`** (plat : git subtree retrouve chaque dépôt par son chemin, on ne déplace
jamais un dossier — cf. §8), la catégorie est un champ de `upstreams.json`. Pour s'orienter : `guides/` (par besoin) puis
`CATALOGUE.md` (par dépôt, avec chemins précis).

| Catégorie | Dépôts | Rôle |
|---|---|---|
| `modding` | `universal-modder`, `rea`, `GhidraMCP`, `Il2CppDumper`, `minhook`, `android-reverse-engineering-skill`, `coop-anything` | Méthode complète de modding + CLI `um` + base de connaissances ; reverse engineering (rea CLI/MCP, Ghidra piloté par Claude) ; Unity IL2CPP ; hooks natifs |
| `physique` | `JoltPhysics`, `GodotIK`, `godot-destruction-plugin` | Le moteur physique de Godot 4.4+ (sources, doc d'architecture, ~150 démos : cordes, poulies, flottaison, ragdolls, corps mous) ; IK 3D ; destruction |
| `godot` | `netfox`, `limboai`, `beehave` | Multijoueur (synchro, rollback) ; IA par behavior trees / machines à états |
| `listes` | `public-apis`, `awesome-godot`, `magictools`, `awesome-gamedev`, `awesome`, `awesome-mcp-servers`, `awesome-claude-code` | API gratuites ; ressources Godot / gamedev / assets libres ; méta-liste ; serveurs MCP ; outils Claude Code |

universal-modder dit **quoi faire** (méthode, route, vérification) ; rea et Ghidra **lisent l'intérieur des binaires**. Les gros
outils (BepInEx, UE4SS, AssetRipper, ILSpy, Rapier, Terrain3D…) ne sont **pas copiés** : liens à la fin de `CATALOGUE.md` et dans
les guides ; ils s'installent depuis leurs releases officielles.

**Critères pour ajouter un dépôt** : utile aux projets de l'utilisateur (modding, création de jeux — surtout Godot —, logiciels,
agents IA), maintenu, licence qui autorise la copie (sinon : simple lien), copie raisonnable (< ~50 Mo de fichiers ; au-delà :
lien). Mesurer avant : `gh api "repos/<owner>/<repo>/git/trees/HEAD?recursive=1" --jq '[.tree[]|select(.type=="blob")|.size]|add'`.

## 4. Garder le kit à jour (`scripts\kit.ps1`)

```
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 list                    # dépôts et commit synchronisé
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 check [-Name rea]       # nouveautés en amont (ne modifie rien)
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 update -Name rea [-Push] # intègre la dernière version (commit)
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 add -Name x -Url https://github.com/a/x -Category godot [-Role "..."] [-Push]
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 verify                  # santé : dossiers, synchro, patches locaux
```
- `upstreams.json` = registre (url, branche, dossier, licence, rôle, commit et date de synchro). Écrit par le script.
- Procédure quand l'utilisateur demande « mets à jour » : `check` → lire les commits (`git show --stat <hash>` sur ceux qui
  comptent) → résumer à l'utilisateur ce qui est **bénéfique** ou risqué → `update -Name …` (un dépôt à la fois) → noter dans
  l'Historique ce qui change pour nous → `git push`. rea publie plusieurs commits par jour : ne pas mettre à jour sans raison.
- **Ne jamais modifier un fichier dans `upstream/`** : ça créerait des conflits à la prochaine mise à jour. Nos adaptations vont
  à la racine (docs, scripts). Si un patch local est inévitable, le décrire au §8 (Patches locaux).
- Les remotes `up-<nom>` sont recréés automatiquement par le script (un clone neuf du kit n'a que `origin`).

## 4 bis. Heimdall — le veilleur (cœur de la toolbox)

Doc complète : **`heimdall/README.md`**. En bref :
- `heimdall/sources.json` = 6 domaines (`godot`, `physique-netcode`, `modding-re`, `ia-agents`, `secu-reseau`, `devtools`) et leurs sources de veille.
- `heimdall/projects.json` = carte projet → domaines → outils du kit + manques + **pistes** (c'est la base du **réflexe**).
- `heimdall/reports/AAAA-MM-JJ.md` = digests datés. `heimdall/heimdall.ps1` = helper (`domains`, `sources`, `project`, `brief`, `report`, `log`).
- **Réflexe** quand on ouvre/relance un projet de l'utilisateur (consigne permanente) : `heimdall.ps1 project -Name <P>` → outils applicables + manques + **pistes** déjà notées ; proposer/utiliser ce qui est pertinent ; un manque non couvert → passe de veille ciblée.
- **Pistes** (`pistes` dans `projects.json`) : quand on trouve un outil qui irait bien à un projet précis (en veille ou en bossant), l'y **noter**. Au prochain passage sur ce projet, le proposer à l'utilisateur — ou l'utiliser directement si c'est évident et sans risque. Retirer la piste une fois adoptée (passe dans `outils_kit`) ou écartée.
- **Passe de veille** (recette dans `heimdall/README.md`) : `brief` → recherche web par domaine → `report` → remplir → décider lien vs subtree (`kit.ps1 add`) → MAJ `INDEX.md` → commit/push.
- L'intelligence (lire le web, juger) est faite par Claude ; le `.ps1` ne fait que la mécanique (données, squelettes).

## 5. Utilisation avec Claude (gros modèle)

- **universal-modder** :
  - en plugin : `/plugin marketplace add D:\Super_Toolbox\upstream\universal-modder` puis `/plugin install universal-modder@universal-modder` (non testé en local ; sinon le marketplace GitHub `rehan-remade/universal-modder`) ;
  - ou en lançant Claude Code **dans** `upstream\universal-modder` (ses `.claude\skills` et `.claude\settings.json` s'appliquent).
  - Point d'entrée : skill `mod-any-game` (`skills/mod-any-game/SKILL.md`). Le MCP `fal` exige `FAL_KEY` (payant, fal.ai) : sans
    clé, le désactiver via `/mcp` ; tout le reste marche (images locales possibles via ComfyUI : `um comfy`).
- **rea** : `npm install --global rea-agents@<version>` (PAS une compilation du dépôt : l'addon Windows n'existe que dans le
  paquet npm), Ghidra 12.1.x + JDK 21 complet pour le natif, puis `rea doctor --provider ghidra --json`.
  Brancher le MCP : `rea setup --client claude_code --dry-run --json` puis `--yes` — **modifie `~/.claude.json` de
  l'utilisateur : demander d'abord.** Mettre `REA_MCP_INPUT_SCHEMA_PROFILE=compact`.

## 5 bis. Utiliser le kit depuis un autre projet (ex. Stryder_Symbiosis, autre session Claude)

- Le kit est **une bibliothèque de référence**, pas une dépendance : on le lit depuis `D:\Super_Toolbox` (ou on le clone :
  `gh repo clone Alpharid/Super_Toolbox`, dépôt **public**). Ne pas le copier dans le projet du jeu.
- Commencer par `guides/README.md`, puis le guide du besoin (`guides/physique-et-godot.md` pour Stryder).
- Un addon (netfox, LimboAI, GodotIK…) s'installe dans le projet du jeu depuis **sa release officielle** (`addons/…`), pas depuis
  `upstream/` (qui contient les sources de développement, parfois sans les binaires GDExtension compilés).
- **Licences** pour un jeu vendu (Steam) : MIT / Apache-2.0 / BSD → OK, garder leur licence dans les crédits ; **interdit** d'embarquer
  du code sans licence, du CC BY-NC-ND, et méfiance avec le GPL. Détail : `guides/physique-et-godot.md` §4.
- Le kit ne contient rien de propre au jeu : les décisions du jeu restent dans le dépôt du jeu (ses ADR).

## 6. Utilisation par Alphred (agent local Qwen 27B, `D:\Alphred_AI\scripts\agent.ps1`)

Alphred tourne dans Claude Code avec **6 outils seulement** (Bash, Read, Edit, Write, Glob, Grep), **sans skills ni MCP** et un
contexte de ~128k tokens (compaction vers ~110k). Donc :

0. **Commence par `guides/README.md`** (une ligne par besoin → le bon guide), pas par les dépôts.
1. **Les skills se lisent comme des modes d'emploi.** Pour « modder le jeu X » : lire `upstream/universal-modder/skills/mod-any-game/SKILL.md`
   (par morceaux de 300 lignes max), puis seulement le skill de l'étape en cours (`game-recon`, `reverse-engineering`…) et le
   playbook du moteur (`upstream/universal-modder/skills/mod-any-game/references/engines/<moteur>.md`). Jamais tout d'un coup.
2. **CLI `um`** (universal-modder), depuis Bash :
   `PYTHONPATH=/d/Super_Toolbox/upstream/universal-modder python -m um <commande>` (le lanceur `bin/um` peut tomber sur
   l'alias `python3` cassé). Dépendances une fois : `python -m pip install pillow numpy pyyaml`.
   Le plus utile et sans risque : `um scan --list`, `um scan "<jeu>" --json > scan.json`, `um kb search "<jeu>"`, `um kb show <note>`,
   `um backup create …`. **Interdit ici : `um kb pr`** (il commite et pousse dans CE dépôt, cf. §8).
3. **rea : uniquement le CLI**, jamais le MCP (ses 172 définitions d'outils pèsent 68k à 120k tokens → contexte saturé).
   Toujours écrire la sortie dans un fichier puis lire un extrait : `rea search "<exe>" "Health" --kind strings --provider ghidra --json > s.json`
   puis Grep/Read. `--token-count` pour mesurer, `--token-limit N --token-offset M` pour paginer (format par défaut TOON, pas avec --json).
   Jamais `list_strings`/`list_procedures` sur un gros exe : `search` avec un motif précis, puis `decompile` sur UNE adresse.
   Doc à lire : `upstream/rea/.agents/skills/reverse-engineer-anything/SKILL.md` + `references/native-and-artifacts.md`.
4. **Pas d'outil WebSearch/WebFetch** : pour une recherche, `curl -s <url>` ou `gh api …` dans Bash (et demander à l'utilisateur
   pour les pages derrière une connexion). **Pas de vision fiable** : vérifier un mod par les journaux du jeu et des fichiers texte
   plutôt que par captures d'écran.
5. **Périmètre réaliste** : recon (`um scan`, `um kb`), mods de données/assets et via loader officiel (tModLoader, BepInEx,
   SMAPI, UE4SS Lua, Fabric…), lecture ciblée de code .NET (`rea inspect-managed-members --type …`). Le reverse engineering natif
   long (hooks C++, trampolines) et les mashups : proposer à l'utilisateur de le faire avec Claude.
6. **Listes (`upstream/public-apis`, `awesome-*`, `magictools`) : jamais en entier** (certaines font des milliers de lignes).
   `grep -n "^### " <README>` pour voir les catégories, puis Read autour de la ligne, ou `grep -in "<mot>"` directement.
7. Tenir un `MODLOG.md` dans le dossier du mod (méthode de universal-modder) : c'est ta mémoire si la conversation est compactée.
   Coupe-circuit : 3 échecs identiques → arrêter et expliquer.

## 7. Règles (légalité / sécurité) — non négociables

Jeux **possédés** par l'utilisateur, en solo/hors ligne ou sur ses propres serveurs. Jamais de contournement d'anti-cheat
(EAC, BattlEye, Vanguard, VAC…), de DRM ou de vérification de propriété ; jamais d'injection dans un client protégé ; jamais
publier/committer des fichiers du jeu ou du code décompilé (les dossiers `work/`, `decomp/`, `dumps/` sont ignorés par git).
Demander avant : piloter souris/clavier, installer un loader, toucher au registre, publier. Tuer des processus par PID exact.
(Sources : `upstream/universal-modder/skills/mod-any-game/references/safety.md`, `upstream/rea/DISCLAIMER.md`.)

## 8. Pièges connus

1. **`um kb pr --yes`** fait `git checkout -b` + commit + push dans le dossier parent du subtree, donc dans CE dépôt, et tente un
   `gh repo fork` → ne pas l'utiliser ici (`kb search/show/new/check` sont sans risque).
2. `upstream/universal-modder/bin/um` est un script **bash** ; depuis PowerShell : `python -m um` avec `PYTHONPATH`.
3. **rea sous Windows** : mode « Windows P0 » **lecture seule** (pas d'annotation/renommage), PE natifs x86/x64 seulement via
   Ghidra (Ghidra refuse les PE .NET → `inspect-managed-*`), **IL2CPP non décodé** (`GameAssembly.dll` = DLL native).
   Chemins refusés : liens symboliques/jonctions (bibliothèques Steam déplacées), SUBST, UNC, non-NTFS, caractères `& ^ % ! | < >`
   → copier le binaire dans `C:\rea-work\`. 1er import Ghidra très long (minutes) : augmenter `REA_GHIDRA_STARTUP_TIMEOUT_MS`,
   `GHIDRA_HEADLESS_MAXMEM=8G`. Chaque appel CLI réanalyse le binaire (`--snapshot FICHIER` met en cache les requêtes identiques).
4. rea ne **patche jamais** : il donne adresse, offset fichier (`address-to-file-offset`) et octets (`read-bytes`) ; le patch se fait ailleurs.
5. `FAL_KEY` (fal.ai) est la seule clé de universal-modder ; elle va dans l'environnement ou un `.env` (ignoré par git), jamais dans un fichier suivi.
6. Gros fichiers tiers (GIF 6 Mo, modèles .glb 4-5 Mo) : OK pour GitHub (< 50 Mo). Ne jamais ajouter de binaires de jeux ou d'outils (Ghidra…) au dépôt : `.local/` est ignoré.

7. **Ne jamais déplacer ni renommer un dossier de `upstream/`** : `git subtree` retrouve chaque dépôt par le chemin noté dans ses
   commits (`git-subtree-dir:`) ; un dossier déplacé ne peut plus être mis à jour. Pour réorganiser : changer la catégorie dans
   `upstreams.json`, les guides et le catalogue — pas les dossiers.
8. Les dépôts d'addons Godot (`netfox`, `limboai`, `GodotIK`) sont des **sources de développement** : `GodotIK/godot-cpp` est un
   sous-module vide, LimboAI se compile avec SCons. Pour les utiliser : releases officielles.

**Patches locaux dans `upstream/`** : aucun (`kit.ps1 verify` les signale).

## 9. Carte des fichiers

```
D:\Super_Toolbox\
├─ INDEX.md                  ★ à lire en premier : tout le contenu par domaine + carte projet→outils + Heimdall (token-léger)
├─ HANDOVER.md / CLAUDE.md / AGENTS.md / README.md / CATALOGUE.md
├─ heimdall\                 README (le veilleur), sources.json (domaines+sources), projects.json (projet→outils), heimdall.ps1, reports\AAAA-MM-JJ.md
├─ upstreams.json            registre des dépôts tiers : catégorie, licence, rôle, commit synchronisé (écrit par kit.ps1)
├─ scripts\kit.ps1           list / check / update / add / verify (PowerShell 5.1, UTF-8 avec BOM)
├─ upstream\universal-modder skills\ (11 SKILL.md), um\ (CLI Python), knowledge\ (INDEX.md, games\, techniques\), examples\ (4 mods)
├─ upstream\rea              scripts\rea.mjs (CLI/MCP), src\, bridge\ (Ghidra/Hopper), docs\ (installation, windows-ghidra-p0…), .agents\skills\
├─ upstream\GhidraMCP, Il2CppDumper, minhook          outils de modding (sources) — voir CATALOGUE.md
├─ upstream\JoltPhysics, GodotIK, godot-destruction-plugin   physique
├─ upstream\netfox, limboai, beehave                  addons Godot
├─ upstream\public-apis, awesome*, magictools          listes de ressources (README.md / readme.md)
├─ guides\                  README (index par besoin), modder-un-jeu, physique-et-godot, trouver-une-ressource, creer-des-assets,
│                           reverse-engineering-avec-claude (+ modeles\CLAUDE.re-house-rules.md), ia-locale-performante
└─ (ignorés par git) work\ decomp\ dumps\ captures\ .local\ .env .venv node_modules
```

## 10. Conventions

- Docs, commentaires, journaux en **français** ; scripts PowerShell en UTF-8 **avec BOM**, sortie `OK: …` / `ERREUR: …`.
- Commits : `Alpharid <67369311+Alpharid@users.noreply.github.com>` (configuré dans le dépôt local). Dépôt **public**.
- Pas de binaires dans git (Releases GitHub si besoin). Pas de secrets (dépôt public). Avant chaque push : `INDEX.md` et HANDOVER à jour + scan des secrets.
- Chaque mod = son propre dossier de travail (`work\<jeu>-<mod>\`, ignoré) ou son propre dépôt ; le kit contient des outils, pas des mods.

## 11. Historique

- **2026-10-19** — +1 subtree `coop-anything` (MIT, **28 dépôts**) à la demande de l'utilisateur : playbook + MCP pour rendre coop un jeu solo ; projets SteamDeck et GTA_SA_Chill_Trainer ajoutés à `heimdall/projects.json` avec leurs pistes.
- **2026-10-19** — Veille Alphred → guide `ia-locale-performante.md` + rapport `2026-10-19-alphred.md` + pistes Alphred (Qwen3.8 MTP, Pi, Pocket TTS, Smart Turn, SearXNG…).
- **2026-10-19** — Cours RE @0xMovez → guide `reverse-engineering-avec-claude.md` + modèle de règles RE ; subtree `android-reverse-engineering-skill` ; liens Caveman, bethington/ghidra-mcp, IDA MCP officiel, ImHex, mitmproxy, ArtCraft ; projet Waze_SA_Mod dans Heimdall ; digest `reports/2026-10-19-cours-re.md`.
- **2026-10-19** — Digest Heimdall hebdo : semaine calme (Godot 4.7.1, Jolt 5.6 à synchroniser, Ghidra 12.1.4, Suricata/Zeek en lien).
- **2026-10-18** — Domaine `creation-assets` + Atelier IA local (ComfyUI, Z-Image, Qwen-Image/Edit, TRELLIS.2, Krita AI) ; projet Guardians_of_the_Seal ajouté à Heimdall.

- **2026-10-12** — Création du kit par Claude (Claude Code) : `universal-modder` (2c220143) et `rea` (c22111ec) intégrés en
  subtree --squash, `scripts\kit.ps1` (testé : check / add / update sur copies jetables), docs de passation, dépôt privé GitHub.
  Alphred (agent local) informé du kit (`D:\Alphred_AI\HANDOVER.md` + prompt de `agent.ps1`).
- **2026-10-12** — +10 dépôts : listes `public-apis`, `awesome-godot`, `magictools`, `awesome-gamedev`, `awesome`, `awesome-mcp-servers`,
  `awesome-claude-code` ; outils `GhidraMCP`, `Il2CppDumper`, `minhook`. `kit.ps1` : catégories (`-Category`), licence via l'API GitHub.
- **2026-10-12** — Audit + restructuration : `guides/` (entrées par besoin), catégories `modding / physique / godot / listes`,
  `kit.ps1 verify`. +6 dépôts pour la physique et Godot (Stryder_Symbiosis) : `JoltPhysics`, `GodotIK`, `godot-destruction-plugin`,
  `netfox`, `limboai`, `beehave` ; liens vers Rapier, Ten Minute Physics, corde verlet, Terrain3D, godot_voxel, GodotSteam (Codeberg), GUT, gdUnit4.
- **2026-10-16** — **Super_Toolbox** : renommage `Modding_Tools_Kit` → `Super_Toolbox`, dépôt passé **public/open-source**. Portée
  élargie à tous les projets de l'utilisateur. Ajout du pilier `INDEX.md` (token-léger) et du cœur **Heimdall** (`heimdall/` :
  `sources.json` 6 domaines, `projects.json` 6 projets, `heimdall.ps1`, `reports/`). 1er digest de veille (`reports/2026-10-16.md`,
  ~36 outils repérés, vérifiés) + propositions d'ajout. Agent cloud hebdo planifié pour le digest.
- **2026-10-16** — **1ère vague Heimdall** : +8 dépôts en subtree (`godot-statecharts`, `limbo_console`, `godot-gdscript-toolkit`,
  `godot-softbody2d`, `context7`, `mem0`, `Harmony`, `ida-pro-mcp`) → **26 dépôts**. Serena et ~10 autres gardés en **lien**
  (licence non permissive, binaire ou pip) dans `CATALOGUE.md` § Ajouts Heimdall. Mécanisme **pistes** ajouté (`projects.json`
  + `heimdall.ps1 project` les affiche) : notes par projet à proposer/utiliser au prochain passage. Réflexe inscrit dans CLAUDE.md/AGENTS.md.
