# Modding_Tools_Kit

Kit d'outils de modding et de création de jeux (dépôts tiers en git subtree dans `upstream/`). Tout est décrit ici : @HANDOVER.md

Règles :
- Ne jamais modifier `upstream/` : mises à jour uniquement via `scripts\kit.ps1` (check → résumé à l'utilisateur → update).
- Jeux possédés, solo/hors ligne uniquement ; jamais d'anti-cheat/DRM contourné ; jamais de fichiers de jeu ni de code décompilé dans git.
- Ne pas lancer `um kb pr` dans ce dépôt. Grosses sorties (rea, ILSpy, Ghidra) → dans un fichier, puis lecture ciblée.
- Agent local (Alphred) : lis le §6 de HANDOVER.md ; skills = fichiers SKILL.md à lire par morceaux, rea en CLI seulement.
- Après chaque changement : une ligne datée dans HANDOVER.md § Historique ; commits en Alpharid, dépôt privé.
