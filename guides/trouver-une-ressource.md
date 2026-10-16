# Trouver une ressource (API, outil, asset, plugin, serveur MCP)

Toutes les listes sont dans `upstream/` ; elles font de quelques centaines à plusieurs milliers de lignes : **Grep, jamais lecture complète**.

| Je cherche… | Où | Commande type (Bash, depuis `D:\Super_Toolbox`) |
|---|---|---|
| Une **API** gratuite (jeux, IA, météo, musique, anime, finance, données ouvertes…) | `upstream/public-apis/README.md` | `grep -n "^### " upstream/public-apis/README.md` (les 52 catégories) puis Read autour de la ligne ; ou `grep -in "twitch\|steam" upstream/public-apis/README.md`. Colonnes : Auth (clé ?), HTTPS, CORS |
| Un **plugin / addon Godot** | `upstream/awesome-godot/README.md` | `grep -in "rope\|water\|network" upstream/awesome-godot/README.md` — vérifier la compatibilité Godot 4 |
| De quoi **créer un jeu** (moteur, pixel art, 3D, son, level design, publication) | `upstream/magictools/README.md`, `upstream/awesome-gamedev/README.md` (libres) | `grep -n "^## \|^### " upstream/magictools/README.md` |
| Des **assets libres** (graphismes, sons, musiques, polices) | `upstream/awesome-gamedev/README.md` | idem |
| Un **serveur MCP** (donner un outil à un agent) | `upstream/awesome-mcp-servers/README.md` | `grep -in "ghidra\|blender\|godot\|database" upstream/awesome-mcp-servers/README.md` |
| Un skill / hook / outil pour **Claude Code** | `upstream/awesome-claude-code/THE_RESOURCES_TABLE_NEW.csv` | `grep -i "<mot>" upstream/awesome-claude-code/THE_RESOURCES_TABLE_NEW.csv` |
| **N'importe quel autre sujet logiciel** | `upstream/awesome/readme.md` (méta-liste) | `grep -in "<sujet>" upstream/awesome/readme.md` → ouvrir la liste trouvée sur GitHub |
| Un service **gratuit** pour développeurs (hébergement, BDD, e-mail, CI) | https://github.com/ripienaar/free-for-dev (non copié : pas de licence) | `curl -s https://raw.githubusercontent.com/ripienaar/free-for-dev/master/README.md \| grep -i "<mot>"` |

Une ressource trouvée devient souvent utile pour de bon → l'ajouter au kit : `scripts\kit.ps1 add …` (critères : `HANDOVER.md` §3).
