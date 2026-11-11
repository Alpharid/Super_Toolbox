# Le code sobre : écrire le moins de code qui fait tout le travail

> Méthode tirée de **Ponytail** (`DietrichGebert/ponytail`, MIT, lu le 2026-11-11), **sans installer le plugin** : on garde ses
> règles utiles, on écarte ce qui abîmerait nos projets, et on dit **quand** appliquer. Ce n'est pas une consigne à suivre bêtement :
> c'est un réflexe à doser selon le projet (§4).
> Voir aussi : [economiser-tokens-et-gpu.md](economiser-tokens-et-gpu.md), [notre-methode.md](notre-methode.md).

## 1. Ce que ça vaut vraiment

- Ponytail annonce −54 % de code et −22 % de tokens. **JetBrains a mesuré (80 tâches appariées) : −15 % de code, −10 % de coût,
  −11 % de temps.** Le gain en tokens est modeste ; nos vraies économies restent côté lecture (index, Grep, sessions courtes).
- Le vrai gain est ailleurs : **moins de code à relire, à tester et à réparer plus tard**, surtout dans les repos repris par une
  autre IA (handover).
- Risque d'une application aveugle : des versions trop maigres, des fonctionnalités rognées, un jeu sans saveur. D'où le §4.

## 2. Les règles qu'on garde

**L'échelle avant d'écrire** : prendre le premier barreau qui fait **tout** le travail.

1. Est-ce que ça doit exister ? Une option, un réglage, une souplesse que personne n'a demandés : on ne les fait pas, et on les nomme
   en une ligne (le propriétaire tranche).
2. Ça existe déjà dans le projet (une fonction, un composant, un motif) ? On le réutilise comme le fait le code voisin.
3. La bibliothèque standard ou le moteur le font (Godot, .NET, Python stdlib) ? On s'en sert, sauf si le projet a son propre outil.
4. Une dépendance déjà installée, ou un outil de la Super_Toolbox ? On s'en sert. **Jamais une dépendance nouvelle pour trois lignes.**
5. Une ligne qu'un lecteur comprend d'un coup d'œil ? Une ligne. (Une ligne qu'il faut décoder n'est pas courte.)
6. Sinon : le minimum de code qui marche.

**Paresseux sur la solution, jamais sur le changement.**
- Avant de toucher : lister tout ce que le changement doit atteindre (appelants, tests, données de test, config, exports) et ce qu'il
  pourrait casser (données détruites ou exposées, appelants qui ne marchent plus). C'est ça, le périmètre ; le reste est du hors-sujet.
- **Correction de bug** : grep de **tous** les appelants de la fonction touchée, puis corriger la cause **une fois**, dans le code
  partagé (pas un pansement dans un seul appelant).
- Du code déplacé ou fusionné **garde** sa gestion d'erreurs et ses validations.
- À taille égale, prendre la solution juste sur les cas limites (vide, zéro, dernier élément, arrondis, fuseaux horaires).
- Garder la structure du projet (ses couches, ses conventions). Supprimer vaut mieux qu'ajouter.

**Un petit test, pas une couverture.** Une logique nouvelle et non triviale (une branche, une boucle, un analyseur, de l'argent, de la
sécurité, un script neuf) laisse **un** petit test ou une auto-vérification par assert. Un changement trivial n'en demande pas.

**Les raccourcis se signent.** Un raccourci volontaire porte un commentaire :
`# shortcut: <sa limite>, <quand le reprendre>` (ou `//`). Sans déclencheur de reprise, il pourrit en silence.
Relevé de la dette :
`git grep -nE '(#|//|/[*]) ?shortcut:'`. Une ligne par marqueur dans le `HANDOVER.md` (§ backlog) avant un push, si le projet en a.

**Les commentaires** : seulement le *pourquoi* que le code ne peut pas montrer, en une ligne. Le reste va au HANDOVER.

**Fin de réponse** : une ou deux lignes sur ce qui n'a pas été vérifié et le risque à connaître (c'est déjà notre règle : dire ce qui
n'a pas été testé).

## 3. Ce qu'on ne coupe jamais

- Les validations aux **frontières de confiance** : tout ce qui vient d'un joueur, d'un client réseau, d'un fichier ou d'Internet.
  Sur un serveur de jeu, **le serveur vérifie toujours** (anti-triche).
- La gestion d'erreurs qui **évite une perte de données** (sauvegardes, comptes, bases, écritures dans le bon ordre).
- La **sécurité** et les secrets.
- Le **calibrage et les garde-fous du matériel réel** (calculateurs auto, Raspberry Pi, périphériques) : confirmations, sauvegarde
  avant écriture, mode lecture seule par défaut.
- L'**accessibilité** et **tout ce que le propriétaire a demandé**.

## 4. Quand l'appliquer, quand ne pas l'appliquer

| Situation | Dose | Pourquoi / comment |
|---|---|---|
| Correction de bug, n'importe quel projet | **Pleine** | Grep des appelants, cause corrigée une fois, un test qui aurait échoué. |
| Outils, scripts, panels, maintenance PC (Super_Toolbox, Omnicommande, WifiSentinel, lanceurs) | **Pleine** | Code qu'on relit et répare souvent : le moins possible, stdlib d'abord. |
| Mods et rétro-ingénierie | **Pleine sur l'échelle** | Barreaux 2-4 : réutiliser le cadre existant (Harmony, BepInEx, ImGui du trainer…) plutôt que réécrire. |
| Prototype, concept, essai jetable | **Pleine** + `shortcut:` partout | On va vite, mais chaque raccourci dit sa limite pour le jour où le proto devient le jeu. |
| Systèmes d'un jeu (logique, données, IA, netcode) | **Moyenne** | L'échelle oui ; mais une architecture prévue par la feuille de route ou le GDD **compte comme demandée** (ce n'est pas du « pour plus tard »). |
| Serveur multijoueur (Guardians, MixMaster, SA_COOP, MCM) | **Moyenne, charge réelle** | Juger à la charge visée (plusieurs joueurs, plusieurs processus), pas « un utilisateur ». Jamais couper les vérifications serveur. |
| Matériel réel, voiture, réseau familial (Valisa, Kali-Pi, Dasai) | **Faible** | Le code minimal ne doit jamais retirer une confirmation, une sauvegarde ou un mode sûr (§3). |
| Ressenti de jeu, UI, direction artistique, contenu, lore | **Non** | Le « juice », les finitions, les variantes d'animation, les textes : ce n'est pas du superflu, c'est le jeu. Le minimal donne le « look IA » qu'on refuse. |
| Demande vague (« fais-moi X ») | **Non : on demande** | Ponytail livre la plus petite version ; nous, on pose les choix sur une page de décisions ([pages-de-decisions.md](pages-de-decisions.md)) ou on suit le GDD. |
| Code qu'une autre IA reprendra (tous nos repos) | **Lisibilité d'abord** | Pas de one-liner astucieux : un code clair un peu plus long vaut mieux qu'un code court à décoder. |

**Ce qu'on n'importe pas** : la posture « développeur flemmard » en consigne permanente, la réduction automatique des demandes
vagues, et le plugin lui-même (il s'injecte dans chaque session, sans distinguer un jeu d'un script).

## 5. En relecture de code

L'ordre de Ponytail (repris tel quel, il est bon) : **juste → sûr → tient la charge → testé → rapide → sobre.**

- Chaque remarque a un **cas concret** : « cette entrée ou cette situation donne ce mauvais résultat ». Pas de cas, pas de remarque.
- Avant de dire « inutilisé » : grep de tout l'arbre (tests, config, références en chaîne ou dynamiques, signaux Godot, scènes `.tscn`).
- Dire **quelle charge** on a supposée (un joueur, une famille, un serveur public).
- Sobre en dernier : supprimer le code mort et les options jamais réglées, réutiliser l'existant (nommer le fichier), fusionner les
  quasi-copies qui doivent changer ensemble, découper une fonction **par tâche**, jamais par nombre de lignes.
- Un raccourci signé `shortcut:` qui nomme sa limite n'est pas un défaut : c'est une dette connue.
