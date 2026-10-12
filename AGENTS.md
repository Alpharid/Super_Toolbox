# Modding_Tools_Kit — consignes pour les agents IA

Kit privé de l'utilisateur (Alpharid) pour modder et créer des jeux PC sous Windows. Dépôts tiers copiés en git subtree
dans `upstream/` (universal-modder, rea…), registre `upstreams.json`, outil `scripts/kit.ps1`.
**Documentation complète : [HANDOVER.md](HANDOVER.md)** — par besoin : [guides/](guides/README.md) — par dépôt : [CATALOGUE.md](CATALOGUE.md).

- Ne pas modifier `upstream/` ; mettre à jour avec `scripts/kit.ps1 check` puis `update -Name <dépôt>` (un à la fois, après résumé à l'utilisateur).
- Ne jamais déplacer/renommer un dossier de `upstream/` (git subtree) ; vérifier la santé du kit : `scripts/kit.ps1 verify`.
- Ajouter un dépôt : `scripts/kit.ps1 add -Name <nom> -Url <url> -Role "<rôle>"`, puis le documenter dans HANDOVER.md et CATALOGUE.md.
- Légalité : jeux possédés, solo/hors ligne ; pas de contournement d'anti-cheat/DRM ; rien du jeu ni de décompilé dans git.
- Petit contexte : lire un seul SKILL.md à la fois, rediriger les grosses sorties vers des fichiers, pas de serveur MCP rea.
- Journaliser chaque changement dans HANDOVER.md § Historique.
