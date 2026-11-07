# Des joueurs IA dans un jeu en ligne (qui jouent vraiment)

> **L'outil existe : [Hyperbole](../hyperbole/README.md)** (2026-11-02). Ce guide en donne la méthode ; Hyperbole la met en
> œuvre pour n'importe quel jeu : profils de base (§6), journal commun (§7), orchestrateur, rapports, jumeaux, rejeu,
> Esprit LLM local borné. Un jeu en ligne y branche ses bots-clients par l'écrivain C# ou le pont TCP, en voie `reel` (x1).

Faire vivre un monde en ligne avec des personnages joués par des IA : ils farment, craftent, échangent, discutent,
se groupent et se fâchent, **sans tricher** et **sans comportement scripté**. Ils servent aussi de testeurs
(équilibre, bugs bloquants, exploits, quêtes, économie, charge). Méthode tirée de la conception des « Descellés »
d'un MMO maison, Guardians of the Seal (oct.-nov. 2026), écrite pour servir à n'importe quel jeu.

## 1. La règle d'or : un bot est un client

- Le bot se connecte par **le même protocole que le jeu** et reçoit la même vue que le joueur. Il ne peut pas tricher
  si le serveur est **autoritaire** (il décide de tout et refuse ce qui est illégal). Sans serveur autoritaire, commencer par là.
- Côté serveur, un drapeau sur le compte sert **uniquement** à compter (humains / bots) et à observer. Aucune règle du
  monde ne le lit (règle de revue + test d'architecture).
- Côté bot, la décision passe par une façade « ce qu'un joueur peut savoir ». Pas de tables de butin ni d'apparitions :
  il **apprend** en jouant et par la rumeur du chat.
- Le plus simple : réutiliser le **noyau du client** (réseau + état local, sans moteur graphique) s'il existe.

## 2. Trois couches, le LLM seulement en haut

| Couche | Rôle | Techno | Coût |
|---|---|---|---|
| Corps | se déplacer, combattre, ramasser, fuir | code classique (A*, réflexes) | ~nul, des milliers de bots |
| Tête | quoi faire maintenant : lieu, quête, craft, build, se déconnecter | utility AI / GOAP : chaque option reçoit un score selon envies, personnalité, expérience | très faible |
| Esprit | parler, se souvenir, aimer, détester, se fixer des buts | LLM, sortie JSON, **appelé sur événement** | c'est là que ça coûte |

L'Esprit ne pilote jamais un geste : il change des buts et des relations, la Tête en tient compte.
Déclencheurs : on lui parle, événement marquant (mort, niveau, butin rare, insulte, cadeau), début de session (plan),
fin de session (résumé), réflexion lente toutes les 10-20 min.

## 3. Ce qui les fait vivre (paramètres, pas scripts)

- **Personnalité chiffrée avec des défauts** (radin, vantard, rancunier, menteur…) : sans défauts, un LLM est trop
  gentil et il ne se passe rien.
- **Une vie hors jeu** → agenda bruité, sessions de durée variable, AFK, absences, départs et arrivées. Avec des
  horaires réalistes, environ un quart des bots sont en ligne au pic.
- **Apprendre au lieu de savoir** : estimation par lieu (XP/min, gain, risque) mise à jour par l'expérience
  (explorer un peu, exploiter beaucoup) → personne ne reste dans une zone trop facile ni ne meurt dans une zone trop dure,
  sans règle « niveau X = zone X ». Builds essayés, mesurés, gardés → une méta émerge. Rumeurs pondérées par la confiance.
- **Mémoire** : souvenirs datés avec importance, résumés de session, compactage des vieux souvenirs (contre la dérive),
  **graphe de relations** (affinité, confiance, rancune, dette) mis à jour par les événements. Outil possible : `mem0` (dans la boîte).
- **Chat crédible** : vitesse de frappe, fautes, silences, tout le monde ne répond pas à tout. RP : IC par défaut, OOC
  entre `(( ))` de temps en temps.
- **Filtre avant envoi** (liste + vérification) pour les interdits du jeu ; une ligne refusée est régénérée ou le bot se tait.
- **Brancher l'Esprit sans gêner le jeu** (fait sur Guardians, `bots/Gardiens.Descelles/Esprit/Parleur.cs`) : il écoute le chat
  et quelques événements (K.O., niveau, capture, connexion) ; **il décide d'abord s'il répond** (murmure 90 %, son prénom 85 %,
  groupe 50 %, proximité 35 %, zone 10 %, chance divisée par deux à chaque réplique des deux dernières minutes, une demande toutes
  les 20 s au plus, une même sorte d'événement au plus toutes les 10 min) ; la demande part **à côté de la boucle** (une tâche
  relue au pas suivant), puis chaque ligne est tapée à la vitesse du joueur. Caractère (RP ou non, défaut, vie, façon d'écrire)
  tiré de sa graine, toujours le même ; souvenirs et relations gardés d'une séance à l'autre. Essai : 4 bots, 12 min, 27 appels,
  ≈ 0,01 $ ; à corriger après lecture : un tic d'écriture tiré trop souvent, des annonces de niveau à la chaîne.

## 4. Être honnête avec les joueurs

Mélanger des bots à des joueurs sans le dire, c'est de la population truquée (des MMO l'ont payé cher). Les **assumer** :
une faction dans le lore, un compteur qui donne le détail humains / bots au survol, et à « t'es un bot ? » une
pirouette qui ne ment pas franchement.

Si l'Esprit passe par une API (Claude…), sa politique d'usage demande de dire aux utilisateurs qu'ils parlent à une IA, au
moins au début de chaque session ou dans l'interface. Sur Guardians : **une ligne du système dans le chat à chaque entrée dans le
monde** (« certains Gardiens de ce monde sont menés par une IA… »), le compteur, jamais **qui** ; et tant que cette ligne n'est
pas en ligne, l'Esprit ne parle que dans le monde d'essai.

## 5. Le modèle (local de préférence)

- Un modèle d'instruction moyen (8-14B), réflexion coupée, JSON, requêtes en parallèle (`OLLAMA_NUM_PARALLEL`, ou
  `llama-server -np N`). Voir [ia-locale-performante.md](ia-locale-performante.md).
- GPU partagé : si le modèle n'est pas là, l'Esprit dort et les bots jouent en silence (Corps + Tête suffisent).
- Aucun bot en ligne → décharger le modèle (`keep_alive: 0`).
- Une API (Claude…) seulement pour les moments rares et importants : sinon le coût récurrent grimpe vite.

## 6. Des profils de joueurs, écrits pour chaque jeu

La personnalité (§3) dit comment un bot se tient avec les autres ; le **profil** dit comment il **joue**. Les deux se
combinent : un tryhard radin, un casual bavard, un chill rancunier. Les profils s'écrivent **sur mesure pour le jeu** :
ce qu'un tryhard optimise dans un MMO de capture (trio de créatures, ordre des quêtes) n'a rien à voir avec ce qu'il
optimise dans un jeu de course ou de survie. Une base de départ :

| Profil | Comment il joue | Ce qu'il fait remonter |
|---|---|---|
| **Tryhard** | longues séances, suit le chemin le plus rentable, copie et pousse la méta, compte tout | temps plancher du contenu, builds dominants, détours inutiles, ce qui est trop facile ou trop lent |
| **Joueur moyen** | rythme ordinaire, suit les quêtes, se trompe parfois | la référence : les temps « normaux » auxquels comparer les autres |
| **Casual** | séances courtes et espacées, lit en diagonale, se perd, abandonne quand ça coince | où l'on décroche, ce qui n'est pas compris, combien de séances avant d'arrêter |
| **Chill** | flâne, récolte, fabrique, discute, explore sans but | les coins vides, l'ennui, la vie du monde, l'artisanat et l'économie du quotidien |
| **Tricheur** | cherche l'abus **avec les seuls moyens d'un joueur** (ordre des gestes, déconnexion au pire moment, échange interrompu, rafales, cas limites des règles) | chaque faille, avec la marche à suivre pour la reproduire |
| **Streamer / vidéaste** | cherche ce qu'il montrerait à sa communauté : le spectaculaire, le drôle, le secret, le raté | les moments à montrer, les longs passages sans rien à montrer, les secrets trouvés trop tôt ou jamais |

Selon le jeu, en ajouter : le meneur de groupe, le marchand, le complétionniste qui veut tout le bestiaire, le
fouineur qui ouvre chaque porte, le gêneur social. Règles :

- **Un profil = des réglages de la Tête**, pas un script : poids des options, durée et fréquence des séances, patience,
  tolérance à l'échec, envie d'explorer, attention portée aux textes. Le casual n'est pas un tryhard ralenti : il fait
  d'autres choix.
- **Le tricheur ne triche jamais vraiment.** Pas de client modifié, pas de lecture de mémoire, pas de message hors du
  protocole du jeu. Quand il trouve une faille, il la reproduit une fois, la signale et passe à autre chose : il
  n'en profite pas et ne la répand pas. Ses essais agressifs (rafales, actions hors portée) restent sur un monde de test.
- **Un profil qui agit sur les autres** (gêneur, meneur, tricheur) fausse leurs mesures : le signaler dans le rapport de
  séance et comparer avec une séance sans lui.

## 7. Séances et rapports

**Séances d'un seul profil** : la mesure propre d'une manière de jouer. Dix casuals disent où l'on décroche, dix
tryhards donnent le temps plancher du contenu et la méta qui en sort.

**Séances mélangées** : une composition proche d'une vraie population (par exemple moitié de joueurs moyens, un quart
de casuals, des chill, quelques tryhards, un tricheur, un streamer). On y voit ce qui ne naît qu'à plusieurs : la
concurrence sur une ressource rare, la cible volée, l'entraide, la file devant un personnage de quête, les prix qui bougent.

Chaque séance note sa **graine**, la **version** du jeu, la **composition** et l'**accélération** du monde, pour la
rejouer à l'identique après un correctif. Un monde accéléré crée ses propres artefacts (une cible disparaît entre la vue
et l'ordre) : revoir à vitesse réelle avant de conclure à un défaut du jeu.

**Chaque bot rend un rapport en deux parties :**

1. **Les mesures**, au même format pour tous (JSONL) : temps par étape et par quête, XP et gains par heure, K.O.,
   abandons, refus, chemin suivi. C'est ce qui permet de comparer les profils entre eux et d'une version à l'autre.
2. **Un récit dans sa voix** : le tryhard râle que l'étape 4 est un détour de six minutes ; le casual écrit qu'il n'a
   pas trouvé où aller et qu'il a quitté ; le streamer liste trois moments à montrer et dit qu'entre la 20e et la 45e
   minute il n'avait rien à filmer ; le tricheur décrit sa faille pas à pas. Sans LLM, des gabarits par profil remplis
   par les mesures suffisent ; avec un LLM, le récit s'écrit **à partir des mesures seulement** (chaque phrase
   renvoie à une ligne mesurée, rien d'inventé).

Un orchestrateur agrège tout (JSONL + résumé Markdown lisible par une IA, qui peut proposer les corrections). Les
**écarts entre profils** parlent plus qu'un chiffre seul : si le casual met trois fois plus que le joueur moyen sur
une quête, elle est mal expliquée ; si le tryhard la finit en deux minutes, elle est peut-être contournable.

Genres de signalements :

| Genre | Ce qui le déclenche |
|---|---|
| `blocage` | position figée malgré l'intention, chemin introuvable, étape de quête qui ne se valide pas |
| `anomalie` | résultat hors des bornes des règles partagées, objet ou monnaie apparus sans cause |
| `refus` | refus du serveur que le bot n'attendait pas (désaccord client / serveur) |
| `exploit` | gains aberrants par rapport à la distribution, ou faille trouvée par le tricheur |
| `equilibre` | XP/h par lieu et par niveau, temps pour vaincre, K.O. par adversaire, builds gagnants, quêtes abandonnées |
| `ressenti` | ce que le profil a vécu : ennui, confusion, frustration, envie de montrer (le récit, en résumé) |

## 8. À quoi ils servent

- **Peupler le monde** au début, quand il y a peu de joueurs (et l'assumer, §4).
- **Tester l'économie des joueurs** : sources et fuites de monnaie, prix, inflation, ce qu'un profil accumule en
  quelques heures (dans Guardians, les gains du butin montaient trop vite : vu dans les rapports).
- **Valider le design des quêtes** : où chaque profil bloque, combien de temps il y passe, où il abandonne.
- **Charge du serveur** : monter le nombre de bots par palier et mesurer la boucle, la mémoire, la bande passante.
- **Ligne de base pour l'anti-triche** : les gains et rythmes de joueurs honnêtes, par profil ; un humain très au-dessus
  de la distribution des tryhards mérite un regard.
- **Non-régression** après chaque publication : une séance courte, toujours la même (graine et composition fixes),
  comparée au rapport précédent.
- **Plus tard, des personas LLM** (IC/OOC, §3 et §5) : le profil donne la manière de jouer, la persona donne la voix.

## 9. Démarrer petit

1. Serveur : drapeau + compteur + création des comptes bots par l'admin.
2. 5-10 bots Corps + Tête, sans LLM : ils doivent finir le tutoriel et farmer au bon endroit. Dès ce stade, deux ou
   trois profils (moyen, casual, tryhard) : leurs écarts sont la première mesure utile.
3. Rapports par profil (mesures + récit à gabarits), séances seules puis mélangées ; le tricheur sur un monde de test.
4. Esprit : chat, mémoire, relations, récits écrits par le LLM.
5. Horaires, observatoire (graphe social + « gazette » quotidienne), puis on monte en nombre en mesurant.

## Références

- *Generative Agents* (Park et al., 2023) — `joonspk-research/generative_agents` : mémoire, réflexion, plans (25 agents).
- *Project Sid* (Altera, 2024, arXiv 2411.00114) : 1000+ agents dans Minecraft, rôles, règles, cultures.
- *Voyager* (2023) — `MineDojo/Voyager` : agent qui apprend Minecraft seul (bibliothèque de compétences).
- *Mineflayer* — `PrismarineJS/mineflayer` : bots Minecraft en JS, si on veut expérimenter sur Minecraft d'abord.
