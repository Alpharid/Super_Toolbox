# Hyperbole — la salle du temps des Einherjar

> Des joueurs simulés qui jouent **vraiment**, **sans tricher**, pendant des heures ou des jours de jeu pour chaque
> heure de PC, et qui rapportent ce qu'un studio voudrait savoir avant les vrais joueurs : **le jeu tient-il des
> heures ? Est-il amusant ? Est-il équilibré ? Où sont les bugs, les blocages, les failles ?**
> Tout tourne **sur le PC** (CPU + GPU local) : pas de tokens dépensés pour des tests qu'une machine peut faire.

Le vocabulaire :

| Nom | Ce que c'est |
|---|---|
| **Hyperbole** | l'outil : la « salle du temps » où le temps du jeu file bien plus vite que le nôtre |
| **Mr. Popo** | l'orchestrateur (`popo/`) : prépare les lobbies, ouvre K chambres en parallèle, surveille, rassemble, analyse |
| **Einherjar** | les bots-joueurs : une **Tête** (utility AI réglée par un profil), des **Sens** (ce qu'un joueur perçoit), un **Corps** (des entrées de joueur) |
| **Chambre** | un processus du jeu (headless) où joue un lobby d'Einherjar ; accélérée ou à x1 |
| **Valhalla** | la boucle : les Einherjar y retournent cycle après cycle (nouvelles graines) pour accumuler de la donnée |
| **Esprit** | un LLM local (Ollama), optionnel : il réécrit les récits dans la voix des profils et trie les constats |
| **Heimdall** | le veilleur de la Super_Toolbox : il suit ce qui sort (bots de test, métriques, papiers) et fait évoluer Hyperbole |

Il réunit les deux pistes précédentes : les **Descellés** de Guardians of the Seal (bots-clients sans triche, Corps / Tête /
Esprit, profils de joueurs, rapports chiffrés + récit) et le plan **Hyperbole** de Stryder Symbiosis (chambres headless
accélérées, Sens/Corps au niveau des entrées, journal commun, saboteur et meneur avec jumeau). Plus les idées de la veille
Heimdall du 2026-11-02 : oracles génériques, repro rejouable, banc de bugs injectés, courbes de survie, couverture.

## Démarrer en 1 minute

```powershell
cd D:\Super_Toolbox\hyperbole
python hyperbole.py demo --ouvrir          # La Fosse (jeu jouet) : 12 chambres, ~50 Einherjar, rapport dans le navigateur
python hyperbole.py demo --banc            # banc : 7 bugs plantés, combien en retrouvent-ils ? (100 %, 0 fausse alerte)
python -m unittest discover -s tests -v    # tests
```

Python 3.10+, **bibliothèque standard seule** (rien à installer). Godot 4.7 pour l'addon. Ollama pour l'Esprit (optionnel).

## Brancher un jeu

1. `python hyperbole.py init C:\MonJeu --moteur godot` → `C:\MonJeu\hyperbole\{mission.json, personas\, README.md}`
   et l'addon dans `C:\MonJeu\addons\hyperbole`. Moteurs : `godot`, `python`, `commande` (n'importe quel moteur via le pont).
2. Écrire l'adaptateur du jeu : ses **Sens** (les options qu'un joueur a, ce qu'il perçoit) et son **Corps** (option →
   entrées sur la manette virtuelle). Godot : [godot/README.md](godot/README.md) (exemple complet dans `godot/exemple/`).
   Autres moteurs : [docs/PROTOCOLE.md](docs/PROTOCOLE.md) (journal JSONL + contrat de chambre + pont TCP).
3. Écrire les étapes du jeu (`milestones`), et si besoin des profils propres au jeu dans `personas/` (ils surchargent ceux d'ici).
4. `python D:\Super_Toolbox\hyperbole\hyperbole.py lancer hyperbole\mission.json --ouvrir`

## Ce qu'on règle (la mission)

Un fichier JSON (modèles dans `missions/`). Tout a une valeur par défaut :

| Clé | Rôle |
|---|---|
| `objectif` | `equilibre`, `fun`, `bugs`, `apprentissage`, `social`, `economie`, `charge`, `non-regression` → choisit les lobbies par défaut |
| `lobbies` | ou à la main : `{"pure": "casual", "bots": 4}` (mesure propre d'un profil) ou `{"personas": {"moyen": 2, "saboteur": 1}}` (lobby d'amis) |
| `mode` | `chambre` (accélérée) · `reel` (x1, réseau) · `mixte` (les deux, et le rapport signale ce qui n'apparaît qu'en accéléré) |
| `vitesse` | `"max"` (le CPU décide, pas de temps fixe) ou un multiple |
| `duree_min` / `duree_jeu_h` | durée réelle par chambre / plafond en heures de jeu |
| `chambres` | en parallèle (`auto` = cœurs / 2) |
| `valhalla.cycles` | passages successifs (nouvelles graines) ; `graines` fixes pour la non-régression |
| `variantes` | A/B : chaque lobby joué pour chaque variante de `params`, **même graine** (équilibrage honnête) |
| `jumeaux` | chaque lobby avec saboteur ou meneur a son jumeau sans lui (leur effet sur les autres, mesuré) |
| `seuils` | ce qui déclenche un constat (bande de victoires visée, ennui max, fuite %/h, vitesse max de déplacement, bornes…) |
| `lint` | le contrôle « sans triche » des fichiers de la tête (refuse de lancer s'il échoue) |
| `esprit` | `{"actif": true, "modele": "mistral-nemo:12b"}` : récits et tri par le LLM local, GPU partagé respecté |

## Les profils (personas)

10 de base dans `personas/` : **moyen** (la référence), **tryhard**, **casual**, **chill**, **fouineur** (failles par les
seuls moyens d'un joueur, mondes de test), **streamer**, **saboteur** (plafond de nuisance, lobbies mélangés, un au plus),
**meneur**, **complétionniste**, **débutant**. Un profil = des **réglages**, pas un script : envies (`drives`), adresse
(visée, réaction, erreurs, apprentissage), savoir (`none` / `partial` / `wiki`), patience, tolérance à l'échec et à
l'ennui, goût du risque, curiosité, lecture des textes, durée des séances, rôle social, et en option :

- `instructions` : consignes libres (lues par l'Esprit ; ex. « tu joues comme un enfant de 10 ans ») ;
- `goals` : envies propres au jeu (`{"craft": 0.6}`) ;
- `tools` : outils permis (`["wiki", "carte"]`, `[]` = aucun, absent = selon `knowledge`).

`python hyperbole.py profils` les liste et les contrôle. Héritage : `"extends": "casual"`.

## Ce qu'on obtient (dans `runs/<run>/rapport/`)

- **`brief_ia.md`** : 40 lignes pour une IA (Claude) : constats triés, preuves, comment rejouer. **Le lire d'abord** (tokens).
- **`rapport.html`** : la page (rétention par profil, causes de mort, victoires par menace, carte de couverture et de
  blocages, étapes, économie, jumeaux, A/B, récits).
- `rapport.md`, `summary.json` (toutes les mesures, pour `comparer`).

Les questions et ce qui y répond :

| Question | Mesures |
|---|---|
| Ça tient des heures ? | rétention (Kaplan-Meier) par profil, abandons précoces et leurs raisons, crashs, gels, fuites (%/h de jeu) |
| C'est amusant ? | moments/h, part d'ennui, frustration/h, variété des gestes (entropie), contenu épuisé après N min |
| Le défi est bon ? | victoires par profil (bande visée), par menace, morts/h, causes dominantes |
| C'est équilibré ? | étapes : temps par profil (le casual 3× le moyen = mal expliqué ; le tryhard 4× plus vite = contournable), économie (sources, puits, net/h), gains aberrants |
| Ça s'apprend sans UI ? | signaux compris (et en combien de temps) par profil ; mécaniques : 1er succès, ratés début → fin |
| Des bugs ? | blocages (carte), erreurs moteur groupées, anomalies, oracles (téléportation, hors bornes, ressource négative, geste sans effet, progression figée, oscillation), failles du fouineur |
| Et à plusieurs ? | effet du saboteur / meneur sur les autres (jumeau), entraide, vols (`blame`) |

**Honnêteté** : ce sont des bots. Leurs chiffres se lisent **en comparaison** (entre profils, entre versions, entre
variantes), pas comme l'avis de vrais joueurs. Une chambre accélérée crée ses propres artefacts : revoir à x1 avant de
conclure (mode `mixte`).

## Les commandes

```
python hyperbole.py lancer   <mission.json> [--minutes N] [--chambres K] [--esprit] [--ouvrir] [--dry]
python hyperbole.py valhalla <mission.json> --cycles 5          # plusieurs passages, nouvelles graines
python hyperbole.py rapport  <run> [--esprit] [--forcer]         # refaire l'analyse
python hyperbole.py comparer <run_avant> <run_apres> [--strict]  # non-régression (code 1 si régression, pour la CI)
python hyperbole.py rejouer  <run> <chambre>                     # même graine, même lobby : vérifier un correctif
python hyperbole.py repro    <run> <chambre> <bot> --jusqua 812  # les entrées d'un Einherjar jusqu'à t : scénario rejouable
python hyperbole.py lint     <mission.json>                      # contrôle sans triche
python hyperbole.py valider  <journal.jsonl>                     # contrat du journal
python hyperbole.py profils  [--dossier D]
python hyperbole.py init     <projet> --moteur godot|python|commande
python hyperbole.py pont     <chamber.json> -- <jeu> ... {port}  # têtes Python pour un autre moteur
python hyperbole.py demo     [--banc] [--ouvrir]
```

Kill switch : Ctrl+C, ou créer le fichier `KILL` dans le dossier du run.

## Fichiers

```
hyperbole/
  hyperbole.py            point d'entrée (CLI)
  popo/                   Mr. Popo : journal, personas, mission, chamber, orchestrator, oracles, analyse, narrate, spirit, report, compare, lint, cli
  einherjar/              la Tête en Python (head.py) + le pont TCP pour les autres moteurs (bridge.py)
  personas/               les 10 profils de base
  missions/               modèles (godot, python, commande) + exemple A/B
  godot/addons/hyperbole/ l'addon Godot 4.7 : chambre, journal, manette virtuelle, Sens, Corps, Tête, Einherjar
  godot/exemple/          « Les Plaines » : intégration complète, avec un mur planté que les Einherjar trouvent
  csharp/                 écrivain de journal + lecture du contrat pour .NET (Guardians)
  demo/                   « La Fosse » (jeu jouet) + le banc de bugs injectés
  docs/PROTOCOLE.md       le contrat (chambre, journal, sans triche, pont, options)
  tests/                  python -m unittest discover -s tests
```

## Maintenu par Heimdall

Heimdall (`../heimdall/`) suit le domaine `qa-playtest` (bots de test, playtest automatisé, métriques de fun et de
churn, agents LLM joueurs) et propose ce qui améliore Hyperbole ; chaque projet de jeu a Hyperbole dans ses outils
(`heimdall.ps1 project -Name <P>`). Premier digest : [../heimdall/reports/2026-11-02-hyperbole.md](../heimdall/reports/2026-11-02-hyperbole.md).

**Pistes déjà notées** : Tête par **MCTS** à poids de profil (Holmgård 2019) quand l'utility AI ne suffit plus ;
**population simulée** (compétence, persistance, seuil d'ennui tirés par bot, Roohi 2020) ; **Cox** (lifelines, optionnel)
pour l'effet des covariables sur l'abandon ; export des repros en scénarios **godot-qa** / tests **gdUnit4** ; capteurs
**godot_rl_agents** (raycasts, grille) comme Sens prêts à l'emploi ; Esprit **appelé quand un bot est bloqué** (budget plafonné).
