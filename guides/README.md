# Guides — « je veux faire X, je regarde quoi ? »

Points d'entrée **par besoin** (le `CATALOGUE.md` est rangé par dépôt). Chaque guide renvoie vers les fichiers précis du kit.

| Je veux… | Guide |
|---|---|
| Modder un jeu PC existant (Unity, Unreal, Bethesda, natif…) | [modder-un-jeu.md](modder-un-jeu.md) |
| Faire un jeu Godot 4 avec une physique avancée (cordes, structures qui cèdent, eau, créature qui marche, coop) — ex. **Stryder_Symbiosis** | [physique-et-godot.md](physique-et-godot.md) |
| Lire l'intérieur d'un binaire/APK avec Claude (rea, Ghidra, essaim d'agents) et le reconstruire proprement (clean-room, parité) — ex. **MixMaster_Regenesis**, **Waze_SA_Mod** | [reverse-engineering-avec-claude.md](reverse-engineering-avec-claude.md) (+ [modeles/CLAUDE.re-house-rules.md](modeles/CLAUDE.re-house-rules.md)) |
| Faire tourner un LLM / un agent / une voix en local, vite et fiable sur 24 Go — ex. **Alphred_AI** | [ia-locale-performante.md](ia-locale-performante.md) |
| Trouver une API, un outil, un asset libre, un plugin Godot, un serveur MCP | [trouver-une-ressource.md](trouver-une-ressource.md) |
| Créer des assets (concept, décors, personnages, sprites iso 8 directions, icônes peintes, pièces d'interface, carte à l'encre, sons sans paroles, musique) en local, licences UE vérifiées — ex. **Guardians_of_the_Seal** | [creer-des-assets.md](creer-des-assets.md) |
| Jouer à plusieurs par Internet à un vieux jeu « réseau local » (IPX/DirectPlay), sans VPN ni admin, et le distribuer à la famille — ex. **MCM_Online** | [jouer-en-reseau-a-un-vieux-jeu.md](jouer-en-reseau-a-un-vieux-jeu.md) |
| Faire tourner un vieux jeu PC dans un navigateur (le vrai jeu, pas un remake) et l'héberger — ex. **MM2_Web** | [porter-un-jeu-pc-dans-le-navigateur.md](porter-un-jeu-pc-dans-le-navigateur.md) |
| Faire tester un jeu par des joueurs simulés sans triche (équilibre, fun, défi, bugs, blocages, failles, non-régression), en chambres accélérées sur le PC — ex. **Stryder_Symbiosis**, **Guardians_of_the_Seal** | [../hyperbole/README.md](../hyperbole/README.md) (Hyperbole) + [joueurs-ia-dans-un-jeu-en-ligne.md](joueurs-ia-dans-un-jeu-en-ligne.md) |
| Mener plusieurs chantiers à la fois avec un terminal Claude par chantier (fiches, état, file du GPU, pièges de git) — ex. **Guardians_of_the_Seal** | [orchestrer-des-chantiers.md](orchestrer-des-chantiers.md) (+ `../scripts/chantiers/`) |
| Faire trancher le propriétaire : une page HTML de décisions à cocher, sombre, avec « Copier mes réponses » | [pages-de-decisions.md](pages-de-decisions.md) (+ [modeles/page-de-decisions.html](modeles/page-de-decisions.html), `../scripts/verifier_page.sh`) |
| Utiliser le kit depuis un autre projet / une autre session Claude | [../HANDOVER.md](../HANDOVER.md) §5 bis |

Règle commune : **lire par morceaux** (Grep d'abord, puis Read sur les lignes utiles). Le kit pèse ~140 Mo de texte : il ne se lit jamais en entier.
