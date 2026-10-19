# Reverse engineering avec Claude — la méthode en 11 étapes

> Source : cours « How to Reverse Engineer Anything with Opus 5.5 » de @0xMovez (X, 2026-10-12), **adapté aux règles
> du kit** (rea en CLI, pas en MCP ; Windows = Ghidra lecture seule ; voir `HANDOVER.md` §5–§8). Le cours est bâti sur
> **rea** (`upstream/rea/`, déjà dans le kit). Ce guide garde la méthode et les prompts, corrige ce qui ne colle pas à notre
> installation, et ajoute les outils du kit pour chaque type de cible.
>
> Complète [modder-un-jeu.md](modder-un-jeu.md) : celui-là dit **quoi modder et comment**, celui-ci dit **comment lire
> l'intérieur d'un binaire avec un agent** et, si besoin, **le reconstruire proprement** (clean-room).

**Cadre (non négociable, `HANDOVER.md` §7)** : uniquement des cibles qu'on possède ou qu'on a le droit d'examiner
(jeux achetés, client MixMaster repris avec accord, nos propres builds). But = comprendre, interopérer, moder, reconstruire
**sans copier** — jamais contourner une protection anti-copie ou anti-triche en ligne.

---

## 0. Les règles de la maison (à poser avant de commencer)

Copier [modeles/CLAUDE.re-house-rules.md](modeles/CLAUDE.re-house-rules.md) en `CLAUDE.md` du dossier de travail
(ex. `C:\rea-work\<cible>\CLAUDE.md`). Résumé : chaque affirmation est étiquetée **observation / inférence / inconnu**
et cite sa preuve (adresse, octets, pseudo-code, site d'appel) ; on commence par le plus petit aperçu ; on ne relance
jamais une analyse identique ; on reconstruit depuis le **comportement** et les specs publiques, jamais depuis du code copié.

**Sécurité** : un binaire peut contenir du texte piégé qui détourne l'agent quand il lit les chaînes ou le pseudo-code
(injection de prompt). Cible inconnue → l'analyser dans une **VM**, sortie de rea écrite dans un fichier puis lue par
extraits, et pas d'outils d'exécution de scripts ouverts à l'agent pendant la lecture.

## 1. Le moteur — comment un agent lit un binaire

Le modèle ne désassemble rien lui-même : un outil charge le fichier dans un vrai moteur (Ghidra, IDA, Hopper) et expose
les résultats comme des fonctions. Boucle : *l'agent demande → rea renvoie des faits avec preuves → l'agent pose la
question suivante ou écrit/teste une réimplémentation*. Tout tourne en local.

## 2. L'installation (chez nous)

- **rea** : `npm install --global rea-agents@<version>` (Node 22+). Vérifier : `rea doctor --provider ghidra --json`.
- **Moteur** : Ghidra 12.1.x + JDK 21 (gratuit ; sous Windows = mode « P0 » **lecture seule**, PE x86/x64).
  IDA si licence → `upstream/ida-pro-mcp/` ou le serveur officiel [HexRaysSA/ida-mcp](https://github.com/HexRaysSA/ida-mcp).
  Hopper = macOS/Linux seulement.
- ⚠️ Le cours fait `npx rea-agents setup` pour brancher le **MCP**. **Pas chez nous** : ses ~170 outils pèsent 68k–120k
  tokens → contexte saturé. On utilise le **CLI** avec `--json > fichier` puis lecture d'extraits (`HANDOVER.md` §6).
  Si on veut un MCP Ghidra quand même : [bethington/ghidra-mcp](https://github.com/bethington/ghidra-mcp) (Apache-2.0,
  200+ outils mais **chargement paresseux**, headless + Docker) ou `upstream/GhidraMCP/` (plus petit).
- Rien n'est installé par défaut sur le PC : vérifier l'existant avant (règle globale « installer un logiciel »).

**Niveau d'effort de Claude** (le plus gros levier de qualité du cours) :

| Tâche | Effort |
|---|---|
| Inspecter, naviguer, trier | `medium` |
| Annoter une fonction ordinaire | `high` (`xhigh` pour les fonctions-cœur) |
| Code obfusqué, arithmétique de pointeurs lourde | `max` |

## 3. Le routage — le bon outil selon la cible

Première erreur des débutants : ouvrir un désassembleur sur une appli Electron dont le JavaScript est en clair.

| Cible | Outil d'entrée |
|---|---|
| Electron / JS (`resources/app.asar`) | `rea analyze-javascript-application` — pas de désassembleur |
| .NET (C#, Unity **Mono** `Assembly-CSharp.dll`) | `rea inspect-managed-artifact` / `inspect-managed-members`, [ILSpy](https://github.com/icsharpcode/ILSpy) |
| Unity **IL2CPP** | `upstream/Il2CppDumper/` (ou [Cpp2IL](https://github.com/SamboyCoding/Cpp2IL)) puis rea/Ghidra sur `GameAssembly.dll` |
| Natif PE (Windows x86/x64) | `rea … --provider ghidra` (lecture seule) ; IDA via `upstream/ida-pro-mcp/` |
| **APK / XAPK / AAR Android** | **`upstream/android-reverse-engineering-skill/`** (jadx, noms Kotlin récupérés malgré R8, extraction des API web) |
| Archive / format inconnu | `rea inspect-artifact` / `extract-artifact` ; à la main : [ImHex](https://github.com/WerWolv/ImHex) (GPL, MCP intégré désactivé par défaut) |
| Protocole réseau d'une appli | [mitmproxy](https://github.com/mitmproxy/mitmproxy) (MIT) : enregistre les requêtes, l'agent cartographie l'API |
| Comportement à l'exécution | [Frida](https://github.com/frida/frida) (hooks dynamiques — PC ; téléphone = root, **exclu** pour le OnePlus 12) |

Prompt d'entrée (ne lance **pas** encore d'analyse profonde) :

```text
Je veux comprendre comment fonctionne [FONCTIONNALITÉ] dans [APPLI], qui se trouve à [CHEMIN ABSOLU].

D'abord, dis-moi quel type de cible c'est (natif, Electron/JS, .NET, Unity IL2CPP, Go, APK, WASM) et choisis
le bon outil pour l'ouvrir (voir guides/reverse-engineering-avec-claude.md §3). Pas d'analyse profonde pour l'instant.

Ensuite, donne-moi une carte en un paragraphe : avec quoi l'appli est construite, sa taille, et où tu chercherais
[FONCTIONNALITÉ] en premier. Sépare observations, inférences et inconnues, et cite la preuve de chaque affirmation.
```

## 4. Reconnaissance — aperçu, chaînes, graphe d'appels

Ne pas ouvrir de code tout de suite. D'abord la carte : architecture, nombre de fonctions, point d'entrée, **chaînes**
(URL, messages d'erreur, noms de fonctionnalités = l'indice le plus rapide). Puis classer les fonctions par nombre de
**références croisées (xrefs)** : une fonction appelée 147 fois est le cœur de l'appli ; une appelée 2 fois peut attendre.

```powershell
rea search  "C:\rea-work\cible\app.exe" "http" --kind strings --provider ghidra --json > work\strings_http.json
rea xrefs   "C:\rea-work\cible\app.exe" 0x401ab0 --provider ghidra --json > work\xrefs_401ab0.json
```

## 5. Décompiler — une fonction à la fois

```powershell
rea decompile "C:\rea-work\cible\app.exe" 0x401ab0 --provider ghidra --json > work\fn_401ab0.json
rea trace     "C:\rea-work\cible\app.exe" "sync" --provider ghidra --json > work\trace_sync.json
```

Le pseudo-code est moche (`var_28`, casts partout) mais lisible — c'est tout ce qu'il faut à Claude.
Vitrine de rea : un son du vieux jeu DX-Ball suivi jusqu'à la fonction de balance gauche/droite, réécrite en C qui passe
les 3 205 cas de test d'origine et reproduit les 63 octets compilés → https://rea.tools/showcase/

## 6. Annoter — faire nommer chaque variable par Claude (effort `high`/`xhigh`)

```text
Voici le pseudo-code décompilé d'une fonction qui a [N] références croisées.

Pour cette fonction :
1. Renomme chaque variable d'après son usage réel.
2. Donne son rôle en une phrase.
3. Liste les structures de données qu'elle lit et écrit.
4. Nomme le motif (singleton, fabrique, machine à états, observateur…).
5. Réécris-la en [LANGAGE CIBLE : C#, GDScript, Rust, C…] propre et idiomatique, avec commentaires de doc.
6. Signale toute gestion d'erreur, validation d'entrée ou contrôle de sécurité manquant.

Raisonne sur ce qu'est chaque valeur avant de choisir un nom. Marque tout ce dont tu n'es pas sûr.

[coller le pseudo-code]
```

La décompilation dit **ce que** fait le code ; Claude dit **pourquoi**, et donne les noms pour le reconstruire.

## 7. Obfuscation — savoir quand s'arrêter (effort `max`)

Référence : Elastic Security Labs, *« The Cost of Understanding: LLM-Driven Reverse Engineering vs Iterative LLM
Obfuscation »* (avril 2026) — Claude Opus 4.6 en contrôleur/workers via IDA MCP contre l'obfuscateur **Tigress** :
https://www.elastic.co/security-labs/llm-reversing-vs-llm-obfuscation. Chiffres relayés (~40 % de 20 cibles résolues,
**0 %** sur les combinaisons multi-couches ; JIT et virtualisation imbriquée = les pires) : à recouper sur la page d'Elastic.

Leçons :
- **Un échec coûte ~2× une réussite** (le modèle insiste avant d'abandonner) → **budget par fonction**, arrêt tôt.
- **Réduire le bruit avant d'envoyer** : sorties rea en JSON filtrées, ou [Caveman](https://github.com/JuliusBrussee/caveman)
  (`caveman shrink -- <commande>` compresse les sorties JSON/logs ; Apache-2.0). Le cours annonce « −75 % » ; le banc
  de Caveman mesure −33 % de tokens d'entrée sur des sessions entières (bien plus sur un JSON isolé).
- Les 5 techniques qu'on rencontre : aplatissement du flot de contrôle, prédicats opaques, code mort, chaînes chiffrées,
  découpage de fonctions.

```text
Cette fonction semble obfusquée. Travaille en effort max.

1. Identifie les techniques présentes (aplatissement du flot de contrôle, prédicats opaques, code mort,
   chaînes chiffrées, découpage de fonctions) et montre où chacune apparaît dans CE code.
2. Résous-les : retire les branches mortes, évalue les prédicats opaques, désaplatis le dispatcher,
   déchiffre les chaînes en ligne si la clé est récupérable.
3. Montre la fonction propre qui reste.
4. Note ta confiance de 1 à 10. En dessous de 6, dis exactement quelles parties sont incertaines et quel
   contexte voisin les résoudrait. Ne devine pas en silence.

[coller le pseudo-code obfusqué]
```

## 8. L'essaim — un contrôleur, des workers

Une seule conversation ne lit pas bien 500 fonctions (elle oublie, nomme la même chose de trois façons, se contredit).
Solution : un **contrôleur** distribue, des **workers** prennent une grappe de fonctions chacun. Chez nous : sous-agents
Claude Code (`Agent`) ou un Workflow si l'utilisateur l'a demandé ; workers en **Sonnet/Haiku** pour tenir le budget.

Contrôleur :
```text
Tu es le contrôleur d'une rétro-ingénierie. La carte des fonctions est dans functions.json
(adresse, nom, taille, xref_count).

1. Regroupe les fonctions par proximité dans le graphe d'appels ; ordonne les grappes par xrefs.
2. Confie chaque grappe à un worker. N'analyse jamais une fonction toi-même.
3. Injecte les structures déjà résolues dans la consigne de chaque worker pour que les noms restent cohérents.
4. Si un worker rend une confiance < 6, mets une 2e passe en file avec le contexte de ses voisins résolus.
5. Suis la dépense cumulée de tokens et rapporte-la après chaque grappe.
```

Worker :
```text
Tu es un worker. Tu reçois une fonction décompilée et les structures résolues jusqu'ici.
Rends exactement : adresse, rôle, confiance (1-10), structs_utilisées, structs_nouvelles, source_propre, alertes.
Réutilise les noms de structures existants ; n'invente jamais un 2e nom pour une structure déjà nommée
par le contrôleur. Une seule fonction. Arrête-toi quand c'est fait.
```

## 9. Clean-room — les 4 règles qui gardent la reconstruction propre

Reconstruire = copier **ce que fait** l'appli, jamais le code dedans. (Méthode de l'équipe ArtCraft, voir §10.)

1. **Observer, jamais copier.** Faire tourner la cible en boîte noire, regarder ce qu'elle fait. Ne pas coller son code,
   ni reprendre son texte au-delà des simples noms de fonctionnalités.
2. **Des specs, pas des sources.** Les formats de fichiers viennent des normes publiques (ex. OOXML = ECMA-376), jamais
   du parseur d'un concurrent ni de code GPL/LGPL.
3. **Assets originaux uniquement.** Chaque icône, police, son : dessiné, domaine public ou licence ouverte, avec une
   ligne dans un fichier d'attribution (cf. `ATTRIBUTION.md` de WordCraft).
4. **Séparer les deux métiers.** Un agent retrouve le comportement et écrit une **spec** ; un **autre contexte**
   implémente depuis la spec seule, sans jamais voir l'analyse. Cette séparation EST la frontière clean-room.

Prompt de spec (contexte n°1) :
```text
À partir de l'analyse terminée, écris une spécification clean-room pour une réimplémentation.

Décris UNIQUEMENT le COMPORTEMENT. Inclus : chaque interface publique, le modèle de données, chaque fonctionnalité
visible comme une exigence testable, les formats de fichiers lus et écrits (d'après le comportement observé et les
specs publiques), et le comportement en cas d'erreur.

N'inclus PAS : adresses ou offsets, noms de variables issus de la décompilation, assembleur, ni rien de copié de
l'original. Un développeur qui n'a jamais vu le binaire doit pouvoir implémenter une version compatible avec ce
seul document.

Sortie markdown, sections : Architecture, Modèle de données, API publique, Formats de fichiers, Cas de test.
```

**Cas concret chez nous** : `MixMaster_Regenesis` — un serveur privé = une réimplémentation du serveur à partir du
**comportement du client** (paquets observés) : exactement ce schéma spec → implémentation séparées.

## 10. Le modèle ArtCraft — « chaque action est une commande nommée »

[ArtCraft / Crafting Apps](https://github.com/storytold) : suite d'applis libres en Rust pur (Apache-2.0/MIT),
reconstructions clean-room d'outils payants — [PhotoCraft](https://github.com/storytold/photocraft) (retouche),
[VectorCraft](https://github.com/storytold/vectorcraft), [FilmCraft](https://github.com/storytold/filmcraft),
[PdfCraft](https://github.com/storytold/pdfcraft), [SoundCraft](https://github.com/storytold/soundcraft),
[WordCraft](https://github.com/storytold/wordcraft), [DeckCraft](https://github.com/storytold/deckcraft)… État : alpha
/ en développement.

Deux idées à **réutiliser dans nos projets** :
- **Couches** : chaque couche n'utilise que celle du dessous (mesures de base → modèle → commandes → rendu → fenêtre).
- **Registre de commandes** : chaque action est une commande nommée (`format.bold`, `export.pdf`…) ; un clic, un raccourci
  et un agent IA déclenchent **exactement la même chose** → l'appli est pilotable par un agent dès le départ (MCP :
  `list_commands`, `execute`, `batch`…). À appliquer aux panels Godot (datapad Alphred, Control Panel MixMaster,
  Omnicommande).

## 11. Vérifier et livrer — prouver la parité, exposer en MCP

Sans le source d'origine, on compare le **comportement** : mêmes entrées → mêmes sorties.

```text
Construis un banc de test comportemental qui compare le binaire d'origine et ma reconstruction.

Génère 50 entrées : 30 normales, 10 limites (vide, taille max, unicode, caractères spéciaux), 10 erreurs
(malformées, champs manquants, corrompues). Passe chacune dans les deux. Compare la sortie octet par octet
quand c'est possible, sémantiquement sinon. Donne le taux de correspondance, la liste des divergences et une
gravité pour chacune (cosmétique / comportementale / critique). Enregistre dans report.md.
```

Puis livrer comme rea l'a fait : fonctions bien nommées et décrites, un CLI, installation en une ligne, et un serveur MCP
si un agent doit le piloter. **Tester au fil de l'eau**, pas à la fin.

---

## Les 6 erreurs qui font perdre un week-end

1. **Désassembleur sur une appli Electron** → `rea analyze-javascript-application`, pas de natif.
2. **Tout extraire avant de lire** → aperçu d'abord ; extraire tout noie la logique et fait exploser la facture.
3. **Lire les fonctions dans l'ordre du fichier** → trier par xrefs.
4. **S'acharner sur l'obfuscation multi-couches** → 0 % de réussite au banc ; budget, contexte des voisins, revenir plus tard.
5. **Laisser le modèle copier du code dans la reconstruction** → casse la clean-room : spec dans un contexte, implémentation dans un autre.
6. **Livrer sans rapport de parité** → « je crois que ça colle » n'est pas une preuve ; 50 tests et un taux, si.

Résumé : *router la cible → cartographier → décompiler les fonctions chaudes → faire tout nommer par Claude → casser
l'obfuscation qui en vaut la peine → passer à l'échelle avec un essaim → spec clean-room → reconstruire → prouver la parité.*
