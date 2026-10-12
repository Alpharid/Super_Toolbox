# Modding_Tools_Kit

Boîte à outils privée pour **modder des jeux PC et créer des jeux**, utilisable avec Claude et avec Alphred (l'IA locale).

| Outil | Pour quoi |
|---|---|
| [universal-modder](upstream/universal-modder) | La méthode complète pour modder presque n'importe quel jeu : reconnaissance, choix de la technique, sauvegardes, assets, tests en jeu, vidéo, publication |
| [rea](upstream/rea) | Reverse engineering : lire l'intérieur des .exe/.dll (Ghidra), du code .NET/Unity, des applis Electron |

- Catalogue détaillé : [CATALOGUE.md](CATALOGUE.md)
- Mise à jour depuis les dépôts d'origine : `powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 check` puis `update -Name <outil>`
- Documentation technique et de passation (pour les IA) : **[HANDOVER.md](HANDOVER.md)**

Les outils tiers gardent leur licence d'origine (MIT pour les deux). Usage : jeux possédés, en solo / hors ligne.
