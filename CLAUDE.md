# Super_Toolbox

Boîte à outils **open-source** pour tous les projets de l'utilisateur (modding/jeux, IA/agents, réseau/sécurité
défensive, Godot UI, outils dev). Dépôts tiers en git subtree dans `upstream/`. **À lire en premier : `INDEX.md`**
(pilier token-léger). Tout le détail : @HANDOVER.md

**Réflexe (important)** : dès qu'on touche un projet de l'utilisateur, consulter `INDEX.md` puis
`heimdall.ps1 project -Name <Projet>` → proposer les outils pertinents déjà présents et repérer les manques. Un
manque non couvert → lancer une passe de veille **Heimdall** (`heimdall/README.md`) pour trouver/proposer/ajouter.

Règles :
- S'orienter via `INDEX.md` (par domaine), puis `guides/` (par besoin), puis `CATALOGUE.md` (par dépôt). Ne pas fouiller `upstream/` si l'index suffit (tokens).
- Ne jamais modifier `upstream/` : mises à jour uniquement via `scripts\kit.ps1` (check → résumé à l'utilisateur → update, un dépôt à la fois).
- Ne jamais déplacer/renommer un dossier de `upstream/` (git subtree le retrouve par son chemin).
- Modding : jeux possédés, solo/hors ligne ; jamais d'anti-cheat/DRM contourné ; jamais de fichiers de jeu ni de code décompilé dans git. Sécurité/réseau : audit **défensif** de réseaux possédés/autorisés uniquement (voir les lignes rouges dans `heimdall/projects.json`).
- Ne pas lancer `um kb pr` dans ce dépôt. Grosses sorties (rea, Ghidra…) → dans un fichier, puis lecture ciblée.
- Agent local (Alphred) : lis le §6 de HANDOVER.md ; skills = fichiers SKILL.md à lire par morceaux, rea en CLI seulement.
- Dépôt **public** : pas de secrets, scan avant push. Après chaque changement : MAJ `INDEX.md` si le contenu change + une ligne datée dans HANDOVER.md § Historique ; commits en Alpharid.
