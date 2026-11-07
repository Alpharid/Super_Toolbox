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
