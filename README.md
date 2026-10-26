# Super_Toolbox

**Une boîte à outils open source, tenue à jour, pour modder et créer des jeux, bâtir des agents IA, auditer son
réseau, et le reste.**

Au cœur : **Heimdall**, un veilleur technologique qui repère ce qui sort d'utile et garde la boîte à jour.

![licence](https://img.shields.io/badge/code%20%C3%A0%20nous-MIT-green) ![outils](https://img.shields.io/badge/outils%20tiers-licence%20d'origine-blue) ![plateforme](https://img.shields.io/badge/Windows%20%7C%20Godot%204-informational) ![veille](https://img.shields.io/badge/Heimdall-veille%20active-orange)

---

## Pourquoi cette boîte ?

Les bons outils open source sont éparpillés sur GitHub, GitLab, des listes « awesome », des forums… et on les oublie
au moment où on en a besoin. Super_Toolbox règle ça en trois temps :

1. **Elle rassemble** les outils open source utiles à des projets concrets, copiés dans le dépôt (git subtree) ou
   référencés, et **rangés par domaine** dans un index léger, une ligne par outil.
2. **Elle se consulte en réflexe** : quand on démarre ou reprend un projet, un coup d'œil à l'index dit quels outils
   s'appliquent, et ce qui manque.
3. **Elle se tient à jour** grâce à **Heimdall**, qui surveille les sorties et les mises à jour et enrichit la boîte
   au fil de l'eau.

> Presque tout ici appartient à la communauté open source. Chaque outil **garde sa licence d'origine** (voir
> `upstreams.json`). Le code qui est à nous (scripts, docs) est sous MIT.

## Par où commencer

| Vous voulez… | Allez voir |
|---|---|
| **Tout voir d'un coup** (par domaine, une ligne par outil) | **[INDEX.md](INDEX.md)**, le pilier, à lire en premier |
| Faire une tâche précise (« modder un jeu », « physique Godot », « créer des assets », « trouver une ressource ») | [guides/](guides/README.md) |
| Le détail complet d'un outil | [CATALOGUE.md](CATALOGUE.md) |
| Comprendre le veilleur | [heimdall/README.md](heimdall/README.md) |

Pour reprendre le projet (IA ou dev) : [HANDOVER.md](HANDOVER.md).

## Heimdall, le veilleur

Heimdall (le gardien qui voit tout, dans la mythologie nordique) est le cœur vivant de la boîte. Ce n'est pas un
service qui tourne en continu : c'est une méthode suivie par l'IA, outillée par `heimdall/heimdall.ps1` et deux
fichiers de données. Il veille sur ces domaines :

`godot` · `physique-netcode` · `modding-re` · `ia-agents` · `secu-reseau` · `devtools` · `creation-assets`

- **Réflexe projet** : à l'ouverture d'un projet,
  ```
  powershell -ExecutionPolicy Bypass -File heimdall\heimdall.ps1 project -Name <Projet>
  ```
  donne les outils de la boîte qui s'appliquent, les manques à combler et les pistes déjà notées
  (`heimdall/projects.json`, une entrée par projet).
- **Digest de veille** : une passe (manuelle, ou planifiée une fois par semaine) produit un rapport daté dans
  [`heimdall/reports/`](heimdall/reports/) et met à jour l'index.

L'intelligence (lire le web, juger ce qui est pertinent) est faite par l'IA ; les scripts ne font que la mécanique.

## Ce qu'il y a dedans (aperçu)

28 dépôts copiés dans `upstream/`, par exemple :

| Domaine | Quelques outils copiés |
|---|---|
| **godot** | [limboai](upstream/limboai), [beehave](upstream/beehave), [godot-statecharts](upstream/godot-statecharts), [limbo_console](upstream/limbo_console), [godot-gdscript-toolkit](upstream/godot-gdscript-toolkit) |
| **physique-netcode** | [JoltPhysics](upstream/JoltPhysics) (+ ~150 démos), [GodotIK](upstream/GodotIK), [godot-destruction-plugin](upstream/godot-destruction-plugin), [godot-softbody2d](upstream/godot-softbody2d), [netfox](upstream/netfox) (rollback) |
| **modding-re** | [universal-modder](upstream/universal-modder) (la méthode complète), [rea](upstream/rea), [GhidraMCP](upstream/GhidraMCP), [ida-pro-mcp](upstream/ida-pro-mcp), [Harmony](upstream/Harmony), [Il2CppDumper](upstream/Il2CppDumper), [minhook](upstream/minhook), [coop-anything](upstream/coop-anything) |
| **ia-agents** | [context7](upstream/context7), [mem0](upstream/mem0), [awesome-mcp-servers](upstream/awesome-mcp-servers), [awesome-claude-code](upstream/awesome-claude-code) |
| **listes** | [public-apis](upstream/public-apis), [awesome-godot](upstream/awesome-godot), [magictools](upstream/magictools), [awesome-gamedev](upstream/awesome-gamedev), [awesome](upstream/awesome) |

`secu-reseau` et `creation-assets` n'ont rien de copié (licences non permissives ou outils lourds) : ils sont
**référencés** dans `CATALOGUE.md`, les guides et les digests. La liste **complète et à jour** est dans
**[INDEX.md](INDEX.md)**.

## Maintenir / contribuer

```powershell
# santé de la boîte
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 verify
# dépôts copiés et commit synchronisé
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 list
# nouveautés des outils déjà copiés (ne modifie rien)
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 check
# intégrer la dernière version d'un outil
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 update -Name <outil>
# ajouter un nouvel outil (copie en git subtree)
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 add -Name <nom> -Url <url> -Category <domaine> -Role "<rôle>"
```

On ne modifie jamais un fichier dans `upstream/` (conflits à la prochaine mise à jour) : nos adaptations vont à la
racine. Les gros outils (ou à licence non permissive) ne sont pas copiés : ils sont **référencés** et s'installent
depuis leur release officielle.

## Licences et usage

- Chaque dépôt dans `upstream/` conserve **sa propre licence** (listée dans `upstreams.json`). Respectez-la pour tout
  réemploi.
- Modding : outils destinés à des **jeux possédés**, en solo / hors ligne. Pas de contournement d'anti-triche ni de DRM.
- Sécurité / réseau : outils d'**audit défensif**, à n'utiliser que sur des réseaux et équipements **possédés ou dont
  le test est autorisé**.
- Les outils tiers appartiennent à leurs auteurs respectifs.

Filiale d'[Alpharium](https://alpharid.github.io/ACH/#filiale/super-toolbox) — division γ Outils.
