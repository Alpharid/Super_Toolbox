# Modding_Tools_Kit — HANDOVER

> Document de passation : permet à n'importe quelle IA (Claude, Alphred l'IA locale, une autre) de reprendre sans contexte.
> **Si tu es Alphred (modèle local) : lis d'abord le §6, il est écrit pour toi.** Mets à jour l'Historique (§11) après chaque changement.

## 1. Ce que c'est

Le **kit d'outils de modding et de création de jeux** de l'utilisateur (compte GitHub Alpharid, dépôt **privé**
`Alpharid/Modding_Tools_Kit`, local `D:\Modding_Tools_Kit`). Il rassemble des dépôts tiers utiles, copiés dans `upstream/`
avec **git subtree** (une vraie copie dans ce dépôt + un lien vers l'original pour récupérer ses nouveautés), plus notre
documentation et nos scripts à la racine. Objectif de l'utilisateur : y ajouter au fil du temps tous les dépôts pertinents
pour modder des jeux et en créer, et s'en servir avec Claude et avec Alphred.

## 2. État (2026-10-12)

- 2 dépôts intégrés : `universal-modder` et `rea` (voir §3 et `CATALOGUE.md`). Lus et documentés, **rien n'est encore installé**
  sur le PC (pas de `uv`, ffmpeg, Blender, Ghidra, JDK 21, ni du paquet npm `rea-agents`). On installe à la demande, pour un
  projet de mod précis (règle de l'utilisateur : vérifier d'abord si l'outil existe déjà sur le PC, ne jamais installer de doublon).
- PC : Windows 11, RTX 3090 Ti, Python 3.13, Node, .NET, git, gh présents. `python3` = alias Microsoft Store qui ne lance rien.

### À faire / idées
- L'utilisateur a « quelques idées derrière la tête » : attendre ses demandes, puis installer seulement ce qu'il faut.
- Ajouter les dépôts pertinents qu'il demandera (`scripts\kit.ps1 add …`), et les documenter ici + dans `CATALOGUE.md`.

## 3. Contenu

| Dossier | Origine (licence) | Quoi | Quand s'en servir |
|---|---|---|---|
| `upstream/universal-modder` | rehan-remade/universal-modder (MIT) | 11 skills Markdown + CLI Python `um` + base de connaissances (`knowledge/`, ~180 notes sur des jeux et techniques) + playbooks par moteur | Toute demande « modder le jeu X » : recon du jeu, choix de la route, sauvegardes, assets, tests en jeu, vidéo, publication |
| `upstream/rea` | morluto/rea (MIT) | CLI + serveur MCP `rea` (npm `rea-agents`) : reverse engineering avec preuves (Ghidra/IDA pour le natif, parseur .NET intégré, ressources PE, JS/Electron, archives) | Comprendre le code d'un jeu : trouver une fonction, une chaîne, décompiler, obtenir l'offset fichier d'une adresse |

Détail des skills, commandes et moteurs : `CATALOGUE.md`. Les deux se complètent : universal-modder dit **quoi faire** (méthode,
route, vérification) ; rea **lit l'intérieur des binaires** (étape « reverse-engineering » de universal-modder).

## 4. Garder le kit à jour (`scripts\kit.ps1`)

```
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 list                    # dépôts et commit synchronisé
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 check [-Name rea]       # nouveautés en amont (ne modifie rien)
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 update -Name rea [-Push] # intègre la dernière version (commit)
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 add -Name x -Url https://github.com/a/x [-Role "..."] [-Push]
```
- `upstreams.json` = registre (url, branche, dossier, licence, rôle, commit et date de synchro). Écrit par le script.
- Procédure quand l'utilisateur demande « mets à jour » : `check` → lire les commits (`git show --stat <hash>` sur ceux qui
  comptent) → résumer à l'utilisateur ce qui est **bénéfique** ou risqué → `update -Name …` (un dépôt à la fois) → noter dans
  l'Historique ce qui change pour nous → `git push`. rea publie plusieurs commits par jour : ne pas mettre à jour sans raison.
- **Ne jamais modifier un fichier dans `upstream/`** : ça créerait des conflits à la prochaine mise à jour. Nos adaptations vont
  à la racine (docs, scripts). Si un patch local est inévitable, le décrire au §8 (Patches locaux).
- Les remotes `up-<nom>` sont recréés automatiquement par le script (un clone neuf du kit n'a que `origin`).

## 5. Utilisation avec Claude (gros modèle)

- **universal-modder** :
  - en plugin : `/plugin marketplace add D:\Modding_Tools_Kit\upstream\universal-modder` puis `/plugin install universal-modder@universal-modder` (non testé en local ; sinon le marketplace GitHub `rehan-remade/universal-modder`) ;
  - ou en lançant Claude Code **dans** `upstream\universal-modder` (ses `.claude\skills` et `.claude\settings.json` s'appliquent).
  - Point d'entrée : skill `mod-any-game` (`skills/mod-any-game/SKILL.md`). Le MCP `fal` exige `FAL_KEY` (payant, fal.ai) : sans
    clé, le désactiver via `/mcp` ; tout le reste marche (images locales possibles via ComfyUI : `um comfy`).
- **rea** : `npm install --global rea-agents@<version>` (PAS une compilation du dépôt : l'addon Windows n'existe que dans le
  paquet npm), Ghidra 12.1.x + JDK 21 complet pour le natif, puis `rea doctor --provider ghidra --json`.
  Brancher le MCP : `rea setup --client claude_code --dry-run --json` puis `--yes` — **modifie `~/.claude.json` de
  l'utilisateur : demander d'abord.** Mettre `REA_MCP_INPUT_SCHEMA_PROFILE=compact`.

## 6. Utilisation par Alphred (agent local Qwen 27B, `D:\Alphred_AI\scripts\agent.ps1`)

Alphred tourne dans Claude Code avec **6 outils seulement** (Bash, Read, Edit, Write, Glob, Grep), **sans skills ni MCP** et un
contexte de ~128k tokens (compaction vers ~110k). Donc :

1. **Les skills se lisent comme des modes d'emploi.** Pour « modder le jeu X » : lire `upstream/universal-modder/skills/mod-any-game/SKILL.md`
   (par morceaux de 300 lignes max), puis seulement le skill de l'étape en cours (`game-recon`, `reverse-engineering`…) et le
   playbook du moteur (`upstream/universal-modder/skills/mod-any-game/references/engines/<moteur>.md`). Jamais tout d'un coup.
2. **CLI `um`** (universal-modder), depuis Bash :
   `PYTHONPATH=/d/Modding_Tools_Kit/upstream/universal-modder python -m um <commande>` (le lanceur `bin/um` peut tomber sur
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
6. Tenir un `MODLOG.md` dans le dossier du mod (méthode de universal-modder) : c'est ta mémoire si la conversation est compactée.
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

**Patches locaux dans `upstream/`** : aucun.

## 9. Carte des fichiers

```
D:\Modding_Tools_Kit\
├─ HANDOVER.md / CLAUDE.md / AGENTS.md / README.md / CATALOGUE.md
├─ upstreams.json            registre des dépôts tiers (écrit par kit.ps1)
├─ scripts\kit.ps1           list / check / update / add (PowerShell 5.1, UTF-8 avec BOM)
├─ upstream\universal-modder skills\ (11 SKILL.md), um\ (CLI Python), knowledge\ (INDEX.md, games\, techniques\), examples\ (4 mods)
├─ upstream\rea              scripts\rea.mjs (CLI/MCP), src\, bridge\ (Ghidra/Hopper), docs\ (installation, windows-ghidra-p0…), .agents\skills\
└─ (ignorés par git) work\ decomp\ dumps\ captures\ .local\ .env .venv node_modules
```

## 10. Conventions

- Docs, commentaires, journaux en **français** ; scripts PowerShell en UTF-8 **avec BOM**, sortie `OK: …` / `ERREUR: …`.
- Commits : `Alpharid <67369311+Alpharid@users.noreply.github.com>` (configuré dans le dépôt local). Dépôt **privé**.
- Pas de binaires dans git (Releases GitHub si besoin). Pas de secrets. Avant chaque push : HANDOVER à jour + scan des secrets.
- Chaque mod = son propre dossier de travail (`work\<jeu>-<mod>\`, ignoré) ou son propre dépôt ; le kit contient des outils, pas des mods.

## 11. Historique

- **2026-10-12** — Création du kit par Claude (Claude Code) : `universal-modder` (2c220143) et `rea` (c22111ec) intégrés en
  subtree --squash, `scripts\kit.ps1` (testé : check / add / update sur copies jetables), docs de passation, dépôt privé GitHub.
  Alphred (agent local) informé du kit (`D:\Alphred_AI\HANDOVER.md` + prompt de `agent.ps1`).
