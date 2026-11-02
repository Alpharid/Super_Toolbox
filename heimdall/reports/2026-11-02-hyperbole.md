# Digest Heimdall — 2026-11-02 — veille ciblée « Hyperbole » (playtest automatisé par joueurs simulés)

> Passe ciblée demandée pendant la construction d'**Hyperbole** (`hyperbole/`), sur les domaines `ia-agents`, `godot`, `devtools`
> et le nouveau domaine **`qa-playtest`** créé pour l'occasion. Licences et dates vérifiées sur l'API GitHub le 2026-11-02.
> Déjà dans le kit, non recomptés : GUT, gdUnit4 (liens), Ollama + Qwen (`guides/ia-locale-performante.md`), le guide
> joueurs-IA, coop-anything.

## À retenir (résumé)

- **Hyperbole comble un vrai vide** : aucun framework open source mûr ne pilote un jeu *uniquement par les entrées d'un
  joueur*, avec des profils de joueurs, en chambres accélérées, et des rapports fun / défi / équilibre / bugs. Les briques
  existantes sont petites et dispersées.
- **Ajouté en subtree** : `godot_rl_agents_plugin` (MIT, 174 Ko). Ses capteurs (RaycastSensor 2D/3D, GridSensor, caméra) sont des
  Sens honnêtes prêts à l'emploi pour les Einherjar Godot, et son nœud Sync montre le pattern « Godot headless accéléré ↔ Python ».
- **Repris dans Hyperbole dès sa v0.1** : oracles génériques (playtest-agent), repro rejouable par graine, banc de bugs
  injectés avec rappel / fausses alertes (playtest-agent, GBQA), survie Kaplan-Meier (Roohi 2020, Bonometti 2019), couverture,
  courbes d'apprentissage par mécanique, difficulté lue en *rang relatif* (Xiao & Yang 2024), Esprit LLM borné (budget, tri final).
- En **lien** : godot-cli-control, godot-qa, playtest-agent, GBQA, GamingAgent, PettingZoo, lifelines (dépendance optionnelle),
  Unreal Learning Agents (pour Tokyo_Hikitori plus tard). **Écartés** : NitroGen (licence non commerciale), Voyager/Cradle
  (inactifs, idées gardées), Unity ML-Agents (Unity pas une cible), AltTester/GameDriver/modl.ai (pas de Godot), PlayGodot (fork
  du moteur), godot-autosim (simule un modèle abstrait, pas le vrai jeu).

## Trouvailles

| # | Nom · dépôt | Licence | Dernière activité | Apport | Décision |
|---|---|---|---|---|---|
| 1 | **godot_rl_agents_plugin** · `edbeeching/godot_rl_agents_plugin` (+ `godot_rl_agents`, Python) | MIT | plugin 18/07/2026 | Sync (headless, speedup, action repeat) ↔ Python par socket ; capteurs « ce qu'un joueur voit » | **subtree** du plugin ; le dépôt Python (~265 Mo) en lien |
| 2 | **gdUnit4** / **gdUnit4Net** · `godot-gdunit-labs/*` | MIT | v6.2.3 le 01/11/2026 (Godot 4.7) | scene runner : entrées simulées en headless (GDScript, C#) → tester les Corps, transformer un repro en test | lien (déjà au catalogue), note 4.7 |
| 3 | **godot-cli-control** · `ClaymanTwinkle/godot-cli-control` | MIT | 11/07/2026 | JSON-RPC WebSocket + client Python + pytest : entrées, captures, vidéos. **Lit/écrit aussi les propriétés** : à filtrer (sans triche) | lien, spike possible |
| 4 | **godot-qa** · `youichi-uda/godot-qa` | MIT | 06/07/2026 | scénarios JSON (input, wait, assert, screenshot) → JUnit XML ; format cible de `hyperbole.py repro` | lien |
| 5 | **playtest-agent** · `kevinnie2003/playtest-agent` | MIT | 18/09/2026 (projet d'un jour) | oracles génériques, personas, repro, banc de bugs injectés, LLM seulement quand bloqué | lien + idées (reprises) |
| 6 | **GBQA** · `camel-ai/GBQA` (arXiv 2604.02648) | Apache-2.0 | 25/06/2026 | benchmark QA par LLM : 30 jeux, 124 bugs ; taxonomie de bugs et schéma de rapport | lien |
| 7 | **GamingAgent / lmgame** · `lmgame-org/GamingAgent` | MIT | 16/11/2025 | harnais perception / mémoire / raisonnement pour agents LLM joueurs : référence pour l'Esprit | lien |
| 8 | **PettingZoo** (+ Gymnasium) · `Farama-Foundation/PettingZoo` | MIT | 30/10/2026 | API AEC / Parallel : forme reprise par le pont TCP d'Hyperbole (une observation, une action par agent) | lien |
| 9 | **lifelines** · `CamDavidsonPilon/lifelines` | MIT | 07/03/2026 | Kaplan-Meier (fait en stdlib dans Hyperbole) ; Cox pour l'effet profil / build sur l'abandon | dépendance optionnelle future |
| 10 | **Voyager** · `MineDojo/Voyager` · **Cradle** · `BAAI-Agents/Cradle` | MIT | 2024 | bibliothèque de compétences ; écran → clavier/souris | écartés (inactifs), idées gardées |
| 11 | **NitroGen** · `MineDojo/NitroGen` | NVIDIA non commerciale | 25/01/2026 | modèle pixels → manette | écarté (licence) |
| 12 | **Unity ML-Agents** | Apache-2.0 | 30/10/2026 | référence capteurs / side channels | écarté (Unity) |
| 13 | **AltTester**, GameDriver, modl.ai | GPL-3.0 / commercial | 2026 | automatisation d'entrées Unity/Unreal | écartés (pas de Godot) ; à revoir pour Unreal |
| 14 | **Unreal Learning Agents** (UE 5.x) | licence Epic | docs 5.7 | interactor, démos humaines, behavior cloning | lien pour Tokyo_Hikitori |

## Papiers (lecture)

- **Personas procédurales** (Holmgård et al., IEEE ToG 2019) : les profils ne diffèrent que par des poids d'utilité d'un MCTS → piste « Tête MCTS ».
- **Difficulté et churn sans joueurs** (Roohi et al., CHI PLAY 2020, arXiv 2008.12937) : population simulée (compétence, persistance, ennui) → piste.
- **Difficulté mesurée par agents LLM** (Xiao & Yang 2024, arXiv 2410.02829) : corrélation forte mais en *rang relatif* → règle d'honnêteté des rapports.
- **TITAN** (2025, arXiv 2509.22170) : agent LLM de test pour MMORPG (abstraction d'état, mémoire, oracle LLM) → référence pour Guardians.
- **Survie / churn sur télémétrie** (Bonometti 2019, arXiv 1905.10998 ; Hadiji 2014).
- **Synthèse 2026** « AI for Games in the Foundation Model Era » (arXiv 2609.16679) : valider un joueur simulé contre la population cible.

## Ce qui est entré dans Hyperbole

1. Profils = poids d'utilité, pas de code par profil (10 profils de base, héritage, surcharge par jeu).
2. Rétention Kaplan-Meier par profil, abandons précoces et leurs raisons.
3. Oracles génériques sur le journal : téléportation (même instantanée), hors bornes, ressource négative, valeur non finie,
   geste sans effet, progression figée, oscillation.
4. Repro : chaque constat porte chambre + graine + instant ; `rejouer` rejoue à l'identique (vérifié : 4 770 / 4 770
   événements identiques sur La Fosse) ; `repro` exporte les entrées d'un bot jusqu'à t.
5. Banc de bugs injectés (`demo --banc`) : **7/7 retrouvés, 0 fausse alerte** sur le jeu propre.
6. Esprit (LLM local) appelé seulement à la fin, budget plafonné, sorties vérifiées (un nombre absent des phrases mesurées = rejet).
7. Difficulté = rang relatif ; avertissement dans chaque rapport.
8. Mécaniques : 1er succès, ratés en début puis en fin de séance (jamais maîtrisé = constat).
9. Couverture : carte des cellules visitées par profil + blocages.
10. Perception honnête côté Godot (cône + rayon), interdiction d'écrire l'état du jeu (pad virtuel), contrôle `lint`.

## Pistes ouvertes (dans `projects.json` → Super_Toolbox)

- Tête **MCTS** à poids de profil si l'utility AI plafonne ; **population simulée** + **Cox** (lifelines) ; export des repros en
  **godot-qa** / **gdUnit4** ; Esprit appelé **quand un bot est bloqué** ; capteurs **godot_rl_agents** comme Sens par défaut.
