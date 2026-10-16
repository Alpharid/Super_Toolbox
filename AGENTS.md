# Super_Toolbox — consignes pour les agents IA

Boîte à outils **open-source** de l'utilisateur (Alpharid), sous Windows, pour tous ses projets (modding/jeux,
IA/agents, réseau/sécurité défensive, Godot UI, outils dev). Dépôts tiers copiés en git subtree dans `upstream/`,
registre `upstreams.json`, outils `scripts/kit.ps1` et `heimdall/heimdall.ps1`.
**À lire en premier : [INDEX.md](INDEX.md)** — complet : [HANDOVER.md](HANDOVER.md) — par besoin : [guides/](guides/README.md) — par dépôt : [CATALOGUE.md](CATALOGUE.md).

- **Réflexe** : en ouvrant un projet, lire `INDEX.md` + `heimdall.ps1 project -Name <Projet>` (outils applicables + manques) ; un manque → passe de veille **Heimdall** (`heimdall/README.md`).
- Ne pas modifier `upstream/` ; mettre à jour avec `scripts/kit.ps1 check` puis `update -Name <dépôt>` (un à la fois, après résumé à l'utilisateur).
- Ne jamais déplacer/renommer un dossier de `upstream/` (git subtree) ; santé du kit : `scripts/kit.ps1 verify`.
- Ajouter un dépôt : `scripts/kit.ps1 add -Name <nom> -Url <url> -Category <domaine> -Role "<rôle>"`, puis 1 ligne dans `INDEX.md` et `CATALOGUE.md`.
- Légalité : modding = jeux possédés, solo/hors ligne, pas d'anti-cheat/DRM, rien du jeu ni de décompilé dans git ; sécurité = audit **défensif** de réseaux possédés/autorisés (lignes rouges dans `heimdall/projects.json`).
- Petit contexte (Alphred) : lire un seul SKILL.md à la fois, rediriger les grosses sorties vers des fichiers, pas de serveur MCP rea.
- Dépôt **public** : pas de secrets. Journaliser chaque changement dans HANDOVER.md § Historique.
