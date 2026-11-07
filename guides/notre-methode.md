# La méthode Alpharium : un propriétaire, des sessions Claude, des outils faits maison

> Vue d'ensemble de la façon dont on travaille, écrite pour un humain qui découvre et pour une IA qui reprend le travail. Elle est
> née sur **Guardians of the Seal** (un MMORPG fait à deux, un propriétaire et Claude, depuis le 18 octobre 2026) et sert à tous les
> projets de la boîte. Ce document **relie** les guides détaillés, il ne les recopie pas. Vitrine visuelle :
> [vitrine/notre-methode.html](vitrine/notre-methode.html). Le nom vient du conglomérat qui réunit les projets du propriétaire,
> [Alpharium](https://alpharid.github.io/ACH/).

## 1. En une minute

Le propriétaire décide, Claude fabrique. Entre les deux, quatre choses tiennent le système :

1. **Les chantiers** : un sujet = une fiche écrite = un terminal Claude. Une session « orchestrateur » ouvre les terminaux, dépose
   les réponses du propriétaire dans les fiches, surveille et publie. → [orchestrer-des-chantiers.md](orchestrer-des-chantiers.md)
2. **Les pages de décision** : dès qu'un choix revient au propriétaire, une page HTML sombre s'ouvre sur son écran, une question par
   bloc, la préférence de Claude cochée d'avance, un bouton « Copier mes réponses ». → [pages-de-decisions.md](pages-de-decisions.md)
3. **Les agents maison** : des programmes qui font à notre place ce qu'un humain ferait mal ou trop lentement : jouer des heures
   (les joueurs IA), regarder des centaines d'images (le regard), lire des rapports (la gazette), trier de la musique, fabriquer des
   sprites. Ils tournent **sur le PC** quand c'est possible, par l'API Claude quand ça vaut le prix.
4. **La boîte à outils** (ce dépôt) : ce qui marche dans un projet y revient, avec son guide, pour servir au suivant. Heimdall la
   tient à jour. → [../INDEX.md](../INDEX.md)

```
 propriétaire ──(réponses recopiées)──► orchestrateur ──(fiche « À TRAITER »)──► chantier 1 … chantier 5
      ▲                                      │                                          │
      └──── page de décision (sombre, Copier) ◄───────────── question qui le concerne ──┘
                                             │
               agents maison : joueurs IA · regard · gazette · musique · art ── file du GPU ── PC local / API
```

## 2. Les principes

Chacun est né d'un vrai incident ou d'une demande du propriétaire ; la leçon d'origine est entre parenthèses.

| Principe | Ce que ça veut dire en pratique |
|---|---|
| **Le propriétaire décide** | Claude propose, avec sa préférence marquée ; les choix de jeu se valident **après essai en jeu**, pas sur papier. |
| **Un terminal par chantier** | Une session qui porte cinq sujets sature (contexte, images, journaux) et perd le fil. 4 ou 5 sessions à la fois au plus. |
| **Une décision = une page** | Rien ne reste en suspens seulement dans le terminal : le propriétaire y perd le fil. La page est sombre (une page claire ouverte la nuit l'a ébloui) et son bouton Copier est vérifié. |
| **Ne jamais s'arrêter pour attendre** | Une session qui attend une réponse fait sa page, continue tout ce qui n'en dépend pas, puis surveille sa fiche (trois chantiers sont restés figés une demi-journée sans que personne le voie). |
| **Rien de provisoire** | Pas de brouillon livré « en attendant » : le propriétaire refuse de faire deux fois le travail. Ce qui manque garde un repère neutre. |
| **Qualité avant vitesse** | On ne propose pas un raccourci technique qui dégrade le résultat. |
| **Essayer petit avant tout** | 2 ou 3 morceaux, montrés avant/après, puis le lot entier (une carte entière repeinte d'un coup a été jetée : la repeinte effaçait les petits objets). |
| **Trier avant de soumettre** | Une machine filtre avant l'oreille ou l'œil du propriétaire (des morceaux soumis sans tri l'ont fâché ; le tri existe depuis). |
| **Pas de « look IA »** | Partir de références d'artistes humains, écrire le style en mots de peintre, retoucher à la main. Pareil pour les textes : chaque phrase a un sens, pas de pseudo-poésie. |
| **Vérifier avant d'affirmer** | On ne dit pas « tout tourne » sans avoir regardé chaque session ; on ne dit pas « c'est un bug » sans l'avoir revu à vitesse normale. |
| **Tout dans le projet** | Copies, essais, worktrees restent dans le dossier du projet ; le jetable va dans le scratchpad de la session, jamais dans `%TEMP%`. On garde les archives. |
| **Rien ne tourne pour rien** | Serveur, client, ComfyUI : on ferme après usage. Les fenêtres d'essai s'ouvrent sur le second écran. |
| **Local d'abord, crédits comptés** | Le PC fait tout ce qu'il sait faire ; l'API sert quand elle est nettement meilleure, avec cache, lots et plafond. → [economiser-tokens-et-gpu.md](economiser-tokens-et-gpu.md) |
| **L'API, projet par projet** | Avant d'utiliser le crédit de l'API sur un projet, demander la permission au propriétaire, au moins une fois par projet : tous ne valent pas qu'on y mette des dollars. Le client refuse un projet qui n'est pas sur sa liste. |
| **Les pages ont la voix du projet** | Une page faite pour le propriétaire (décision, fiche, vitrine) prend les polices du projet (Guardians : Fondamento pour les titres, Amiri pour le texte), toujours en thème sombre. |
| **Libre d'abord** | Avant d'écrire un outil, chercher un dépôt libre ou un outil de studio (Heimdall, cette boîte). |
| **Prêt à reprendre** | À chaque push, le projet se reprend sans contexte : HANDOVER, CLAUDE.md, AGENTS.md, historique daté. |

## 3. Les outils, un par un

Chaque entrée : ce que c'est, quand l'appeler, ce que ça coûte, où est le détail. Les scripts cités sans chemin de la boîte sont
dans le dépôt de Guardians (privé) ; la méthode, elle, est réutilisable.

### Organisation

- **Les chantiers** (`scripts/chantiers/`) : `chantier.ps1` ouvre un terminal sur une fiche, `chantiers_etat.sh` dit l'état de chaque
  session et lève des alertes, `veille_chantiers.sh` rend la main à l'orchestrateur quand quelque chose bouge (ou quand tout est trop
  calme). Coût : rien, sinon des sessions en parallèle. → [orchestrer-des-chantiers.md](orchestrer-des-chantiers.md)
- **L'orchestrateur** : une session qui ne fabrique rien elle-même ; elle écrit les fiches, ouvre les terminaux, dépose les réponses
  du propriétaire sous « À TRAITER », relance les sessions figées, et seule publie. → [orchestrer-des-chantiers.md § L'orchestrateur](orchestrer-des-chantiers.md#lorchestrateur)
- **Les pages de décision** (`guides/modeles/page-de-decisions.html`, `scripts/verifier_page.sh`) : une centaine écrites sur
  Guardians en trois semaines, souvent en plusieurs versions (une boussole d'interface est passée par huit pages). → [pages-de-decisions.md](pages-de-decisions.md)
- **La file du GPU** (`scripts/chantiers/verrou_gpu.sh`) : un ticket par étape lourde, servi dans l'ordre d'arrivée, partagé entre
  projets (deux jeux se partagent une seule carte). → [economiser-tokens-et-gpu.md](economiser-tokens-et-gpu.md)
- **Les essais en jeu** : un serveur d'essai sur sa propre base, un client lancé avec un scénario scripté sur le second écran, des
  captures rangées, des commandes d'administration en ligne de commande. Le propriétaire n'est jamais dérangé par un essai.

### Agents qui jouent et lisent

- **Les joueurs IA (les Descellés de Guardians)** : des bots qui se connectent comme des joueurs, sans aucune triche (une seule porte
  vers le contenu du jeu, vérifiée par un test), réglés par sept profils (moyen, aguerri, casual, débutant, explorateur, chill,
  streamer). Ils jouent dans un monde d'essai accéléré jusqu'à ×20 et rendent un rapport chiffré. Ce qu'ils ont trouvé : une étape
  du tutoriel qui bloquait 5 joueurs sur 6, un marchand jamais approvisionné (739 achats refusés dans une séance), un souk plein qui
  bloquait une quête. Coût : le PC. → [joueurs-ia-dans-un-jeu-en-ligne.md](joueurs-ia-dans-un-jeu-en-ligne.md)
- **Hyperbole** (`hyperbole/`) : la généralisation des Descellés pour tout jeu, sur le PC, sans dépenser de tokens.
  → [../hyperbole/README.md](../hyperbole/README.md)
- **L'Esprit** : ce qui fait parler les joueurs IA dans le chat. Choisi par un essai à l'aveugle : 20 situations, la réponse d'un
  petit modèle de l'API contre celle d'un modèle local, sans savoir qui est qui ; le propriétaire a préféré l'API 17 fois sur 20.
  Plafond de 300 appels par séance (environ 0,10 $), seulement dans le monde d'essai. → [joueurs-ia-dans-un-jeu-en-ligne.md](joueurs-ia-dans-un-jeu-en-ligne.md) §5
- **La gazette** : un modèle de l'API lit les rapports d'une séance ou d'une journée de joueurs IA et en tire une page courte : ce qui
  bloque, l'équilibre, les anomalies, et ce qui manquait aux rapports pour juger. Quelques centimes. → [la-gazette.md](la-gazette.md)
- **Le regard** : un modèle de l'API regarde des images (sprites, interface, carte) et liste les défauts, avec leur gravité et s'ils
  étaient déjà connus. Il signale, il ne valide pas. Environ 0,03 $ l'image. → [le-regard.md](le-regard.md)
- **La traduction** : tout le texte du jeu extrait, traduit par lots avec un glossaire validé, puis relu par une seconde passe
  (1 477 entrées, environ 1,70 $ avec la relecture). Méthode dans [economiser-tokens-et-gpu.md](economiser-tokens-et-gpu.md) §3.

### Agents qui fabriquent (en local)

- **Les chaînes d'art** : entité → sprites en 8 directions (concept, fiche, modèle 3D, rendu, export), icônes peintes, pièces
  d'interface décorées, carte peinte et carte « relevé à la plume », animations par capture de mouvement, vêtements simulés.
  Sur Guardians : 32 entités en jeu, 50 tuiles de carte, 75 icônes validées. → [creer-des-assets.md § Chaînes éprouvées](creer-des-assets.md#chaînes-éprouvées-guardians-of-the-seal-octobre-novembre-2026)
- **La musique et les sons** : génération locale dans un mode imposé, nettoyage, tri automatique étalonné sur les verdicts du
  propriétaire, page d'écoute partagée ; bruitages et sons sans paroles. → [musique-de-jeu.md](musique-de-jeu.md)
- **L'IA locale (Alphred)** : un modèle local sur la carte de 24 Go, avec sa voix et son agent, pour ce qui n'a pas besoin de l'API.
  → [ia-locale-performante.md](ia-locale-performante.md)

### La boîte elle-même

- **Heimdall**, le veilleur : à chaque projet, quels outils de la boîte s'appliquent et ce qui manque ; une veille régulière.
  → [../heimdall/README.md](../heimdall/README.md)
- **Ce document et sa vitrine** : à tenir à jour (règle ci-dessous).

## 4. Ce que ça a donné (Guardians, 18 octobre → 7 novembre 2026)

Chiffres relevés le 2026-11-07 dans le dépôt et les journaux, pas estimés :

| | |
|---|---|
| Durée | 3 semaines, 407 commits, 20 versions publiées aux joueurs |
| Tests automatiques | 386 (règles 180, serveur 169, joueurs IA 24, noyau du client 13) |
| Chantiers | 16 fiches depuis le 5 novembre, 4 ou 5 en parallèle |
| Pages de décision | 95 |
| Leçons écrites | 31 règles tirées des retours du propriétaire, gardées en mémoire de projet |
| API Claude | 232 appels, **3,21 $** au total (sur 100 $ par mois) ; 19 lots à moitié prix |
| Joueurs IA | 38 séances rapportées, 7 profils |
| Art | 32 entités animées en 8 directions, 50 tuiles de carte, 75 icônes peintes, 844 références de paysages |
| Son | 44 bruitages ; tri musical étalonné sur 59 verdicts humains |

## 5. Faiblesses et pistes

Ce qui a raté, ce qu'on en a tiré, et ce qui reste faible.

| Ce qui a raté | Ce qu'on a appris | Où en est-on |
|---|---|---|
| Une session a attendu 4 h des réponses déposées dans sa fiche ; plus tard trois sessions sont restées figées une demi-journée. | Une session ne relit pas sa fiche toute seule. | `chantiers_etat.sh` (alertes), consigne « ne jamais s'arrêter, surveiller sa fiche », `veille_chantiers.sh`. Reste : relancer à la main une session figée. |
| Des morceaux soumis à l'écoute sans tri. | La machine trie avant l'oreille. | `tri.py` étalonné (17 rejets sur 21 recalés). Reste : les rejets « de goût » (voix, ambiance) passent. |
| Le regard signalait de faux défauts (un serpent « trop rond » qui l'est exprès, des « cheveux » qui sont une ombre). | Un juge sans contexte se trompe sur ce qui est voulu. | Fiche « voulus » par entité injectée à chaque appel. |
| 283 défauts d'un coup : le propriétaire en a jugé 58 puis a lâché. | Ne jamais lui soumettre une masse brute. | Claude trie d'abord, le propriétaire tranche le reste (47 points). |
| `git commit -- <chemin>` a embarqué le travail en cours d'une autre session dans le même fichier. | Le chemin commite le fichier tel qu'il est sur le disque. | Passer par l'index (`git add -p`), vérifier `git diff --cached`. |
| Un script jetable dans `%TEMP%` importé par une autre session ; un fichier à moitié écrit qui empêche tout le projet de compiler. | Les sessions partagent plus qu'on ne croit. | Scratchpad par session ; vérifications globales aux moments calmes. |
| Un style peint entraîné sur un modèle distillé : il ne peignait pas et inventait une signature. | Le modèle de base peignait déjà au simple prompt. | Entraîner sur le modèle de base (v2 prête, pas lancée). |
| Un chiffre « secondes de voix » donnait 74 s de chant à un morceau qui n'en a pas (le séparateur range les flûtes avec la voix). | Une mesure automatique se vérifie à l'oreille avant qu'on s'y fie. | Le chiffre n'est plus affiché. |
| À ×20, les joueurs IA voient des centaines de « cible introuvable ». | C'est l'accélération, pas le jeu (0 à ×1). | La gazette a pour consigne de ne pas les compter comme bugs. |
| Les documents de reprise dérivent (un compte de tests en retard d'un jour). | Un chiffre écrit à la main vieillit. | Piste : recompter les chiffres de la vitrine par un script. |

Pistes validées par le propriétaire le 2026-11-07, chacune dans son propre chantier (aussi dans `heimdall/projects.json`) :
- porter dans cette boîte le petit client de l'API de Guardians (cache, lots, plafond, journal des dépenses), pour tous les projets,
  **avec une liste blanche explicite des projets autorisés** (Guardians seul pour l'instant) : un projet absent est refusé ;
- faire du regard un outil générique (la liste des défauts et le contexte « voulu » fournis par chaque projet) ;
- brancher l'écrivain de journal d'Hyperbole dans les joueurs IA de Guardians (il existe, il n'est pas encore utilisé) ;
- noter le coût de chaque séance de joueurs IA dans son rapport ;
- un script qui recompte les chiffres de la vitrine (un compte de tests écrit à la main avait déjà un jour de retard) ;
- repasser en sombre les deux dernières pages de choix claires de Guardians.

## 6. La règle pour que ça reste vrai

**À chaque chantier qui crée ou change un outil maison** : mettre à jour son guide dans `guides/`, sa ligne dans ce document et
dans la vitrine (`guides/vitrine/notre-methode.html`), et `INDEX.md`. La vitrine est aussi servie par le site d'ACH
(<https://alpharid.github.io/ACH/methode/>, fichier `web/methode/index.html` du dépôt ACH) : la recopier telle quelle à chaque
changement et pousser ACH (ses liens sont absolus, la même page marche aux deux endroits). Une leçon tirée d'un incident va dans la section 5. Règle
reprise dans [orchestrer-des-chantiers.md](orchestrer-des-chantiers.md) et dans le HANDOVER de chaque projet qui suit la méthode.
