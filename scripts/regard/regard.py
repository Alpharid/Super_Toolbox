"""Le regard (Super_Toolbox) : un modèle de l'API Claude regarde des rendus et liste ce qui cloche. Il signale, il ne valide pas.

Moteur générique : tout ce qui est propre à un projet est **en données**, dans un fichier de configuration JSON du projet
(modèle : `regard.exemple.json` à côté de ce script) :
- `projet` : son nom dans la liste blanche du client de l'API (`scripts/claude_api/projets_autorises.json`) ; un projet absent
  est refusé ;
- `presentation` : deux ou trois phrases sur le projet et son style (ce que le regard doit savoir avant de juger) ;
- `defauts` : le fichier Markdown des défauts déjà relevés (cherchés d'abord, « connu » = vrai) ;
- `voulus` : le fichier Markdown de ce que le propriétaire a dit voulu, une ligne `- **<nom>** : …` par entité ou pièce ;
- `fiches` : les documents où trouver la fiche d'une entité (sections `### <nom…>`), avec un titre et une longueur maximale ;
- `alias` : les noms de fichier qui ne sont pas ceux des fiches ; `entites` : comment reconnaître une entité dans un chemin ;
- `etalon` : des images aux défauts connus (et un témoin propre), pour mesurer le regard avant de s'y fier ;
- `sorties` : le dossier des rapports.

    python regard.py --config <projet>/regard.json <images…> [--contexte "…"] [--sortie rapport.md]
    python regard.py --config <projet>/regard.json --etalon

Environ 3 à 5 centimes par image (Opus, réflexion moyenne). Images réduites à 1 568 px au plus avant l'envoi.
Rien de ce que produit l'API ne sert à entraîner un modèle (politique d'usage d'Anthropic).
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "claude_api"))

SCHEMA = {
    "type": "object",
    "properties": {
        "defauts": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "quoi": {"type": "string"},
                "ou": {"type": "string"},
                "gravite": {"type": "string", "enum": ["à corriger", "à regarder", "détail"]},
                "connu": {"type": "boolean"},
            },
            "required": ["quoi", "ou", "gravite", "connu"], "additionalProperties": False}},
        "resume": {"type": "string"},
    },
    "required": ["defauts", "resume"], "additionalProperties": False,
}

CONSIGNES_COMMUNES = (
    "Tu es un œil de plus avant le propriétaire : tu **signales** ce qui cloche, tu ne valides rien et tu ne complimentes pas. "
    "Cherche d'abord les défauts déjà relevés (liste ci-dessous, « connu » = vrai), puis tout autre défaut net (« connu » = faux). "
    "Sois précis sur l'endroit (« main gauche, 3e silhouette depuis la gauche »). Pas de défaut inventé : si l'image est propre "
    "pour ce que tu sais voir, rends une liste vide et dis-le en une phrase. Le résumé tient en une ou deux phrases. Quand le "
    "contexte donne la fiche d'une entité (son sens, son inspiration, ce qui a été voulu), juge-la d'après elle : une créature "
    "n'a pas à avoir un corps d'humain.")


@dataclass
class Config:
    racine: Path
    projet: str
    presentation: str
    defauts: Path
    voulus: Path | None = None
    fiches: list[dict] = field(default_factory=list)
    alias: dict[str, str] = field(default_factory=dict)
    prefixe_entite: str = "entite_"
    dossier_entites: str = "entites"
    etalon: Path | None = None
    sorties: Path | None = None
    modele: str = "claude-opus-5-5"
    effort: str = "medium"
    usage: str = "regard"

    @classmethod
    def lire(cls, chemin: str | Path) -> "Config":
        chemin = Path(chemin).resolve()
        d = json.loads(chemin.read_text(encoding="utf-8"))
        racine = (chemin.parent / d.get("racine", ".")).resolve()
        p = lambda k: (racine / d[k]) if d.get(k) else None  # noqa: E731
        e = d.get("entites", {})
        return cls(racine=racine, projet=d["projet"], presentation=d["presentation"], defauts=p("defauts"),
                   voulus=p("voulus"), fiches=d.get("fiches", []), alias=d.get("alias", {}),
                   prefixe_entite=e.get("prefixe", "entite_"), dossier_entites=e.get("dossier", "entites"),
                   etalon=p("etalon"), sorties=p("sorties"), modele=d.get("modele", "claude-opus-5-5"),
                   effort=d.get("effort", "medium"), usage=d.get("usage", "regard"))

    def client(self):
        from claude_api import Client
        return Client(self.projet)


def consignes(conf: Config) -> str:
    return conf.presentation.rstrip() + " " + CONSIGNES_COMMUNES + "\n\n" + conf.defauts.read_text(encoding="utf-8")


def _sections(texte: str, titre_commence: str) -> list[str]:
    """Les sections « ### <titre…> » d'un Markdown dont le titre commence par ce mot (sans casse)."""
    out, cur = [], None
    for l in texte.splitlines():
        if l.startswith("### ") or l.startswith("## "):
            if cur is not None:
                out.append("\n".join(cur))
                cur = None
            if l.startswith("### ") and l[4:].lower().startswith(titre_commence):
                cur = [l]
            continue
        if cur is not None:
            cur.append(l)
    if cur is not None:
        out.append("\n".join(cur))
    return out


def fiche_entite(conf: Config, nom: str) -> str:
    """Ce que le regard doit savoir d'une entité avant de la juger : ses fiches (sections `### <nom>` des documents listés) et ce
    que le propriétaire a dit voulu. Un juge sans contexte prend ce qui est voulu pour un défaut."""
    morceaux = []
    for f in conf.fiches:
        cle = conf.alias.get(nom, nom.replace("_", " ")).lower() if f.get("alias", False) else nom.lower()
        source = conf.racine / f["source"]
        if not source.exists():
            continue
        trouve = _sections(source.read_text(encoding="utf-8"), cle)
        if trouve:
            t = "\n\n".join(trouve)
            n = f.get("max")
            if n and len(t) > n:
                t = t[:n] + " […]"
            morceaux.append(f"{f['titre']} :\n" + t)
    if conf.voulus and conf.voulus.exists():
        voulus = [l for l in conf.voulus.read_text(encoding="utf-8").splitlines() if l.startswith(f"- **{nom}**")]
        if voulus:
            morceaux.append("Ce que le propriétaire a dit voulu (ce n'est pas un défaut) :\n" + "\n".join(voulus))
    return "\n\n".join(morceaux)


def nom_entite(conf: Config, chemin: Path) -> str | None:
    if chemin.stem.startswith(conf.prefixe_entite):
        return chemin.stem[len(conf.prefixe_entite):]
    if chemin.parent.parent.name == conf.dossier_entites:
        return chemin.parent.name
    return None


def contexte_complet(conf: Config, chemin: Path, contexte: str) -> str:
    """Le contexte d'une image, plus la fiche de l'entité si c'en est une (<prefixe><nom>.png, ou <dossier>/<nom>/…png)."""
    nom = nom_entite(conf, chemin)
    f = fiche_entite(conf, nom) if nom else ""
    return contexte + ("\n\n" + f if f else "")


def bloc_image(chemin: Path) -> dict:
    """L'image réduite à 1 568 px ; en JPEG de haute qualité au-delà de 1,2 Mo (les gros PNG ne passaient pas sur une connexion
    montante modeste)."""
    from PIL import Image
    im = Image.open(chemin)
    im.load()
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA")
    if max(im.size) > 1568:
        r = 1568 / max(im.size)
        im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    if buf.tell() > 1_200_000:
        buf = io.BytesIO()
        im.convert("RGB").save(buf, format="JPEG", quality=93)
        return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                            "data": base64.standard_b64encode(buf.getvalue()).decode()}}
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                        "data": base64.standard_b64encode(buf.getvalue()).decode()}}


def texte_demande(conf: Config, chemin: Path, contexte: str) -> str:
    c = contexte_complet(conf, chemin, contexte)
    return f"Image : {chemin.name}." + (f" Contexte : {c}." if c else "") + " Rends le rapport JSON."


def demande_lot(conf: Config, ident: str, chemin: Path, contexte: str) -> dict:
    """Une demande pour `Client.lancer_lot` (Batch API, moitié prix)."""
    return {"id": ident, "modele": conf.modele, "max_tokens": 8000, "effort": conf.effort, "cache_systeme": True,
            "systeme": consignes(conf), "format_json": SCHEMA,
            "contenu": [bloc_image(chemin), {"type": "text", "text": texte_demande(conf, chemin, contexte)}]}


def lire_rapport(texte: str) -> dict:
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        return {"defauts": [], "resume": "(réponse illisible) " + texte[:300]}


def regarder(conf: Config, chemin: Path, contexte: str = "", api=None) -> tuple[dict, float]:
    api = api or conf.client()
    r = api.appeler(conf.modele, [bloc_image(chemin), {"type": "text", "text": texte_demande(conf, chemin, contexte)}],
                    consignes(conf), usage=conf.usage, max_tokens=8000, effort=conf.effort, cache_systeme=True,
                    format_json=SCHEMA)
    return lire_rapport(r.texte), r.cout


def rapport_md(res: list[tuple[Path, dict]]) -> str:
    out = []
    for p, d in res:
        out.append(f"### {p.name}\n{d['resume']}")
        for x in d["defauts"]:
            out.append(f"- [{x['gravite']}]{' (connu)' if x['connu'] else ''} {x['quoi']} : {x['ou']}")
        out.append("")
    return "\n".join(out)


def etalon(conf: Config) -> str:
    """Le regard mesuré sur des défauts connus : chaque image de l'étalon liste ses défauts attendus et les mots qui doivent
    apparaître dans le rapport pour qu'on les compte trouvés ; une image sans défaut attendu sert de témoin propre."""
    api = conf.client()
    images = json.loads(conf.etalon.read_text(encoding="utf-8"))["images"]
    res, total, lignes = [], 0.0, []
    for e in images:
        p = conf.racine / e["chemin"]
        d, c = regarder(conf, p, e["contexte"], api)
        total += c
        res.append((p, d))
        vu = " ".join(x["quoi"].lower() + " " + x["ou"].lower() for x in d["defauts"])
        trouves = [m for m in e["attendus"] if any(k in vu for k in m["mots"])]
        lignes.append(f"- {p.name} : {len(trouves)}/{len(e['attendus'])} défauts attendus trouvés"
                      f" ({', '.join(m['nom'] for m in trouves) or 'aucun'}) ; {len(d['defauts'])} signalés ; "
                      f"témoin propre : {'oui' if not e['attendus'] else '-'}")
    nom = conf.etalon.stem
    sortie = (conf.sorties or conf.etalon.parent) / f"{nom}.md"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(f"# Le regard, mesuré sur l'étalon ({nom})\n\n" + "\n".join(lignes) + f"\n\nCoût : {total:.3f} $\n\n"
                      + rapport_md(res), encoding="utf-8")
    return "\n".join(lignes) + f"\nCoût : {total:.3f} $ → {sortie}"


def main(argv: list[str] | None = None, config: str | Path | None = None):
    ap = argparse.ArgumentParser(description="Le regard : défauts des rendus, par l'API Claude.")
    if config is None:
        ap.add_argument("--config", required=True, help="le fichier regard.json du projet")
    ap.add_argument("images", nargs="*")
    ap.add_argument("--contexte", default="")
    ap.add_argument("--sortie")
    ap.add_argument("--etalon", action="store_true")
    a = ap.parse_args(argv)
    conf = Config.lire(config or a.config)
    if a.etalon:
        print(etalon(conf))
        return
    api = conf.client()
    res, total = [], 0.0
    for i in a.images:
        d, c = regarder(conf, Path(i), a.contexte, api)
        total += c
        res.append((Path(i), d))
    md = rapport_md(res) + f"\nCoût : {total:.3f} $\n"
    if a.sortie:
        Path(a.sortie).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
