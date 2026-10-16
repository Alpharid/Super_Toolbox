<div align="center">

# 🧰 Super_Toolbox

**Une boîte à outils open-source, vivante et auto-entretenue — pour modder et créer des jeux, bâtir des agents IA, auditer son réseau, et tout le reste.**

Au cœur : **Heimdall**, un veilleur technologique qui se tient à jour sur ce qui sort d'utile et garde la boîte à jour.

![licence](https://img.shields.io/badge/code%20%C3%A0%20nous-MIT-green) ![outils](https://img.shields.io/badge/outils%20tiers-licence%20d'origine-blue) ![plateforme](https://img.shields.io/badge/Windows%20%7C%20Godot%204-informational) ![veille](https://img.shields.io/badge/Heimdall-veille%20active-orange)

</div>

---

## Pourquoi cette boîte ?

Les bons outils open-source sont éparpillés sur GitHub, GitLab, des listes « awesome », des forums… et on les oublie
au moment où on en a besoin. Super_Toolbox résout ça en trois temps :

1. **Elle rassemble** les meilleurs outils open-source utiles à des projets concrets, copiés dans le dépôt (git subtree)
   ou référencés, et **rangés par domaine** dans un index token-léger.
2. **Elle se consulte en réflexe** : quand on démarre ou reprend un projet, un coup d'œil à l'index dit quels outils
   s'appliquent — et ce qui manque.
3. **Elle se met à jour toute seule** grâce à **Heimdall**, le veilleur qui surveille les sorties/MAJ de la tech et
   enrichit la boîte au fil de l'eau.

> Presque tout ici appartient à la communauté open source. Chaque outil **garde sa licence d'origine** (voir `upstreams.json`).
> Le code qui est à nous (scripts, docs) est sous MIT.

## 🗺️ Par où commencer

| Vous voulez… | Allez voir |
|---|---|
| **Tout voir d'un coup** (par domaine, 1 ligne par outil) | **[INDEX.md](INDEX.md)** ← le pilier, à lire en premier |
| Faire une tâche précise (« modder un jeu », « physique Godot », « trouver une ressource ») | [guides/](guides/README.md) |
| Le détail complet d'un outil | [CATALOGUE.md](CATALOGUE.md) |
| Comprendre le veilleur | [heimdall/README.md](heimdall/README.md) |
| Reprendre le projet sans contexte (pour une IA) | [HANDOVER.md](HANDOVER.md) |

## 🛰️ Heimdall — le cœur vivant

Heimdall (le gardien qui voit tout, dans la mythologie nordique) est le **pilier intelligent** de la boîte. Il veille
sur **6 domaines** :

`godot` · `physique-netcode` · `modding-re` · `ia-agents` · `secu-reseau` · `devtools`

- **Réflexe projet** — à l'ouverture d'un projet :
  ```
  powershell -ExecutionPolicy Bypass -File heimdall\heimdall.ps1 project -Name <Projet>
  ```
  → les outils de la boîte qui s'appliquent, et les manques à combler.
- **Digest de veille** — une passe (manuelle ou planifiée 1×/semaine) produit un rapport daté dans
  `heimdall/reports/` et met à jour l'index. Dernier en date : [`heimdall/reports/`](heimdall/reports/).

L'intelligence (lire le web, juger ce qui est pertinent) est faite par l'IA ; les scripts ne font que la mécanique.

## 📦 Ce qu'il y a dedans (aperçu)

| Domaine | Quelques outils copiés |
|---|---|
| 🎮 **godot** | [limboai](upstream/limboai), [beehave](upstream/beehave) (behavior trees / FSM) |
| 🧱 **physique-netcode** | [JoltPhysics](upstream/JoltPhysics) (+ ~150 démos), [GodotIK](upstream/GodotIK), [godot-destruction-plugin](upstream/godot-destruction-plugin), [netfox](upstream/netfox) (rollback) |
| 🔧 **modding-re** | [universal-modder](upstream/universal-modder) (la méthode complète), [rea](upstream/rea) (RE), [GhidraMCP](upstream/GhidraMCP), [Il2CppDumper](upstream/Il2CppDumper), [minhook](upstream/minhook) |
| 🤖 **ia-agents** | [awesome-mcp-servers](upstream/awesome-mcp-servers), [awesome-claude-code](upstream/awesome-claude-code) |
| 🧰 **ressources** | [public-apis](upstream/public-apis), [awesome-godot](upstream/awesome-godot), [magictools](upstream/magictools), [awesome-gamedev](upstream/awesome-gamedev), [awesome](upstream/awesome) |

→ La liste **complète et à jour** est dans **[INDEX.md](INDEX.md)**.

## 🔄 Maintenir / contribuer

```powershell
# santé de la boîte
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 verify
# nouveautés des outils déjà copiés (ne modifie rien)
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 check
# intégrer la dernière version d'un outil
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 update -Name <outil>
# ajouter un nouvel outil (copie en git subtree)
powershell -ExecutionPolicy Bypass -File scripts\kit.ps1 add -Name <nom> -Url <url> -Category <domaine> -Role "<rôle>"
```

Les gros outils (ou licences non permissives) ne sont pas copiés : ils sont **référencés** (liens dans `CATALOGUE.md`
et dans les digests Heimdall) et s'installent depuis leur release officielle.

## ⚖️ Licences & usage

- Chaque dépôt dans `upstream/` conserve **sa propre licence** (listée dans `upstreams.json`). Respectez-la pour tout réemploi.
- Modding : outils destinés à des **jeux possédés**, en solo / hors ligne. Pas de contournement d'anti-cheat ni de DRM.
- Sécurité / réseau : outils d'**audit défensif**, à n'utiliser que sur des réseaux et équipements **possédés ou dont le test est autorisé**.

---

<div align="center">
<sub>Boîte à outils maintenue avec l'aide de Claude. Les outils tiers appartiennent à leurs auteurs respectifs. 💚 l'open source.</sub>
</div>
