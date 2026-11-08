# La gazette : les rapports des joueurs IA en une page par jour

> Née sur Guardians of the Seal (novembre 2026). Les joueurs IA (voir [joueurs-ia-dans-un-jeu-en-ligne.md](joueurs-ia-dans-un-jeu-en-ligne.md)
> et [Hyperbole](../hyperbole/README.md)) produisent des rapports chiffrés par séance : des dizaines de milliers de lignes que
> personne ne lit. La gazette les fait lire par un modèle de l'API et rend **une page courte, utile aux corrections et à
> l'équilibrage**. Code de référence : `tools/claude_api/gazette/gazette.py` du dépôt de Guardians (privé).

## Ce que le propriétaire en attend (ses consignes)

- **Une gazette par jour suffit** (toutes les séances du jour), pas une par séance.
- Orientée **corrections et équilibre** : chiffres, anomalies, ce qui bloque. Pas de texte d'ambiance.
- **Pas trop chère** : on estime le coût d'une journée avant de l'automatiser.
- C'est un outil qui s'ajuste à l'usage : chaque gazette finit par **« Pour juger, il manquait »**, ce qu'il faudrait ajouter aux
  rapports (ou en retirer s'il ne sert pas).

## Sa forme

Un titre de une (le fait marquant), 4 à 6 brèves chiffrées et nommées (« tel joueur, 24 K.O., toujours bloqué à la source »), puis
**« À regarder »** (3 à 5 constats, avec le chiffre qui les montre, sans solution inventée), **« Équilibre »**, **« Anomalies et
refus »**, **« Parole »** (ce qu'ils se sont dit), et « Pour juger, il manquait ». 350 à 550 mots.

Les consignes interdisent d'**inventer un chiffre**, un événement ou une réplique, et rappellent les règles du projet (aucun lieu réel,
rien de religieux). Elles disent aussi ce qui n'est pas un défaut : dans un monde accéléré ×10 ou ×20, les « cible introuvable » viennent
de l'accélération ; la gazette ne les présente pas comme des bugs.

**Les rapports en voix** (en option) : un par profil et par séance, à la première personne, comme l'écrirait un vrai testeur de ce
profil (le casual qui se perd, l'aguerri qui optimise, le streamer qui cherche le spectaculaire). Ils partent en lot (moitié prix).

```
python tools/claude_api/gazette/gazette.py estimer 2026-11-03         # coût d'une journée, sans appel
python tools/claude_api/gazette/gazette.py jour 2026-11-03 [--voix]   # la gazette du jour (+ rapports en voix, en lot)
python tools/claude_api/gazette/gazette.py page_jour 2026-11-03       # la page sombre à ouvrir au propriétaire
```

## Ce qu'elle ne doit plus faire (retours du propriétaire après la première semaine)

- **Reproposer ce qui est déjà tranché.** Une liste des points décidés (`deja_tranche.md` à côté du script : « où vendre » ne sera
  pas dit, une phrase de confort quand il n'y a plus d'étape, le marqueur de quête existe déjà…) est lue par toutes les consignes ;
  un fait qui s'y rattache sort marqué **« (connu) »**, avec le chiffre du jour s'il en apporte un. À compléter à chaque retour.
- **Prendre un joueur IA perdu pour un défaut du jeu.** Les profils simulent exprès des erreurs (partir du mauvais côté, comprendre
  un geste tard) ; avant d'accuser le jeu, vérifier que les bots ont **la même information que le joueur** (ici : l'objectif de
  chaque étape, celui du marqueur de la mini-carte). La gazette sépare « défaut prouvé » (un refus qui revient, une valeur
  impossible, un blocage chez plusieurs profils dont un aguerri) et « joueur IA perdu (peut-être une limite du bot) » ; le
  créateur ne change pas le tutoriel sur la seule foi des bots. Les rapports en voix ne réclament plus d'aide d'interface et
  disent « rien de neuf à proposer » plutôt que de radoter.
- **Mélanger le vérifié et le deviné.** La gazette ne lit que les rapports chiffrés ; ce que la session a **vérifié dans le code**
  (la cause d'un blocage, un défaut prouvé, une mesure faite à part) va dans `notes.md` du jour (`art/rendus/gazette/jour_<date>/`),
  écrit à la main : il s'affiche **en tête** de la page avec l'avis de la session, et la gazette le reçoit pour ne jamais le contredire
  (2026-11-08 : un bot bloqué toute une séance, cause lue dans le code, corrigée, vérifiée à la séance suivante). La page ne repose
  plus les questions déjà tranchées (rythme, nombre de rapports en voix) : des remarques libres seulement.
- Rythme retenu : **à la reprise** (la gazette de la veille quand le propriétaire revient), pas de tâche planifiée ; un point par
  séance seulement si le travail en cours en a besoin.

Effet mesuré sur la même journée, avant / après : tout ce qui était connu est sorti marqué, et un fait neuf est remonté au lieu
d'être noyé (le fennec qui répète le même conseil quatre fois dans une séance).

## Coût et rendement

- Modèle moyen (Sonnet), réflexion moyenne ; les rapports d'une journée tronqués à 60 000 caractères.
- **2 à 6 centimes la gazette** ; environ 0,15 $ la journée avec les rapports en voix (23 rapports : 0,15 $).
- Ce qu'elle a fait voir en une page, sur une séance de 40 joueurs IA : 85 % des refus venaient de stocks pleins chez les marchands,
  6 joueurs bloqués au même endroit, des gains d'expérience négatifs (une anomalie de calcul). Ses idées de jeu sont versées dans le
  carnet d'idées du projet, pas appliquées d'office.

## Pour un autre projet

Il faut des rapports de séance qui contiennent déjà les chiffres (progrès, refus et leur motif, blocages, anomalies) : la gazette ne
fait que les lire. Le journal commun d'Hyperbole en donne la forme. Puis : un client de l'API avec cache et lots
([economiser-tokens-et-gpu.md](economiser-tokens-et-gpu.md) §3), des consignes qui listent ce qui **n'est pas** un défaut dans ce
jeu, et la règle « n'invente aucun chiffre ».
