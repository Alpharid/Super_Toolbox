# Modding_Tools_Kit

Boîte à outils privée pour **modder des jeux PC et créer des jeux**, utilisable avec Claude et avec Alphred (l'IA locale).

| Outil | Pour quoi |
|---|---|
| [universal-modder](upstream/universal-modder) | La méthode complète pour modder presque n'importe quel jeu : reconnaissance, choix de la technique, sauvegardes, assets, tests en jeu, vidéo, publication |
| [rea](upstream/rea) | Reverse engineering : lire l'intérieur des .exe/.dll (Ghidra), du code .NET/Unity, des applis Electron |
| [GhidraMCP](upstream/GhidraMCP) · [Il2CppDumper](upstream/Il2CppDumper) · [minhook](upstream/minhook) | Ghidra piloté par l'IA · jeux Unity IL2CPP · hooks pour mods natifs |
| [JoltPhysics](upstream/JoltPhysics) · [GodotIK](upstream/GodotIK) · [godot-destruction-plugin](upstream/godot-destruction-plugin) | Le moteur physique de Godot (sources + ~150 démos) · IK 3D · destruction |
| [netfox](upstream/netfox) · [limboai](upstream/limboai) · [beehave](upstream/beehave) | Multijoueur Godot (rollback) · IA par behavior trees |
| [public-apis](upstream/public-apis) | ~1 400 API gratuites classées par thème |
| [awesome-godot](upstream/awesome-godot) · [magictools](upstream/magictools) · [awesome-gamedev](upstream/awesome-gamedev) | Ressources pour créer des jeux (Godot, art, son, outils, assets libres) |
| [awesome](upstream/awesome) · [awesome-mcp-servers](upstream/awesome-mcp-servers) · [awesome-claude-code](upstream/awesome-claude-code) | Méta-liste tous sujets · outils pour agents IA · outils pour Claude Code |

- **Par où commencer : [guides/](guides/README.md)** (modder un jeu · physique et Godot · trouver une ressource)
- Catalogue détaillé par dépôt : [CATALOGUE.md](CATALOGUE.md)
- Mise à jour depuis les dépôts d'origine : `powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 check` puis `update -Name <outil>` ; santé du kit : `kit.ps1 verify`
- Documentation technique et de passation (pour les IA) : **[HANDOVER.md](HANDOVER.md)**

Les outils tiers gardent leur licence d'origine (voir `upstreams.json`). Usage : jeux possédés, en solo / hors ligne.
