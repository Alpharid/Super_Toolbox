"""Client maison des crédits de l'API Claude (Super_Toolbox), porté de Guardians of the Seal.

Ce qu'il garantit :
- **liste blanche des projets** (`projets_autorises.json`) : un projet absent est refusé (ProjetNonAutorise), sans exception.
  Avant d'ajouter un projet : **demander au propriétaire, au moins une fois par projet** ; noter la date de son accord ;
- **la clé lue explicitement** dans un fichier hors git (celui que nomme `source_cle`), jamais dans l'environnement :
  `ANTHROPIC_API_KEY` ferait payer Claude Code par le crédit de l'API au lieu de l'abonnement. La clé n'est jamais affichée
  ni journalisée ;
- **un journal par projet** (une ligne JSON par appel : date, modèle, usage, jetons, coût estimé, projet) ;
- **un plafond d'arrêt commun** à tous les projets, compté sur le cycle de facturation en cours (le crédit se renouvelle le
  même jour chaque mois, sans report) : au-delà, plus aucun appel ne part (PlafondAtteint) ;
- **la Batch API** (moitié prix) pour tout ce qui n'est pas pressé, **le cache des consignes** (`cache_systeme=True`), la sortie
  imposée par **schéma JSON**, et un **cache des réponses** sur disque (facultatif, `memoriser=True`) : la même demande ne se paie
  qu'une fois.

Usage :
    import sys; sys.path.insert(0, r"D:/Super_Toolbox/scripts/claude_api")
    from claude_api import Client, HAIKU
    api = Client("Mon_Projet")                       # refusé si le projet n'est pas dans la liste blanche
    rep = api.appeler(HAIKU, "Bonjour", usage="essai", max_tokens=200, effort="low")
    rep.texte, rep.cout

En ligne de commande :
    python claude_api.py projets                     # la liste blanche et la source de la clé (jamais la clé)
    python claude_api.py depenses [--projet X] [--depuis AAAA-MM-JJ]
    python claude_api.py verifier <Projet>           # autorisé ou refusé, sans appel
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# La console Windows est en cp1252 : un « → » imprimé par un script la faisait planter.
for _flux in (sys.stdout, sys.stderr):
    if hasattr(_flux, "reconfigure"):
        _flux.reconfigure(encoding="utf-8", errors="replace")

ICI = Path(__file__).resolve().parent
LISTE_BLANCHE = ICI / "projets_autorises.json"

HAIKU = "claude-haiku-5-5"
SONNET = "claude-sonnet-5-5"
OPUS = "claude-opus-5-5"

# Prix en dollars par million de jetons (entrée, sortie), tarif de la Console au 2026-11-07.
# Haiku 5.5 : ce prix vaut jusqu'à 100 000 jetons d'entrée (au-delà 0,50 / 2,50).
PRIX = {
    HAIKU: (0.10, 0.50),
    SONNET: (2.00, 10.00),
    OPUS: (4.00, 20.00),
}
LECTURE_CACHE = 0.10   # une lecture du cache coûte 10 % de l'entrée
ECRITURE_CACHE = 1.25  # une écriture, 125 %
REMISE_LOT = 0.50      # Batch API : moitié prix


class CleAbsente(RuntimeError):
    pass


class PlafondAtteint(RuntimeError):
    pass


class ProjetNonAutorise(PermissionError):
    pass


def charger_liste() -> dict:
    return json.loads(LISTE_BLANCHE.read_text(encoding="utf-8"))


def debut_cycle(jour: int, aujourd_hui: _dt.date | None = None) -> str:
    """Date ISO du début du cycle de facturation en cours (le crédit se renouvelle le `jour` de chaque mois)."""
    d = aujourd_hui or _dt.date.today()
    if d.day >= jour:
        return d.replace(day=jour).isoformat()
    mois, annee = (d.month - 1, d.year) if d.month > 1 else (12, d.year - 1)
    return _dt.date(annee, mois, jour).isoformat()


def cout(modele: str, entree: int, sortie: int, cache_lu: int = 0, cache_ecrit: int = 0, lot: bool = False) -> float:
    pe, ps = PRIX.get(modele, PRIX[OPUS])  # modèle inconnu : on compte au prix le plus haut
    if modele == HAIKU and entree + cache_lu + cache_ecrit > 100_000:
        pe, ps = 0.50, 2.50
    total = (entree * pe + cache_lu * pe * LECTURE_CACHE + cache_ecrit * pe * ECRITURE_CACHE + sortie * ps) / 1e6
    return total * (REMISE_LOT if lot else 1.0)


def _lignes(journal: Path):
    if not journal.exists():
        return
    for ligne in journal.read_text(encoding="utf-8").splitlines():
        if ligne.strip():
            try:
                yield json.loads(ligne)
            except json.JSONDecodeError:
                continue  # une ligne à moitié écrite par un autre processus


def journaux(liste: dict | None = None) -> dict[str, Path]:
    liste = liste or charger_liste()
    return {nom: Path(p["racine"]) / p["journal"] for nom, p in liste["projets"].items()}


def total_cycle(liste: dict | None = None, depuis: str | None = None) -> float:
    """Dépense de tous les projets autorisés depuis le début du cycle (le plafond est commun)."""
    liste = liste or charger_liste()
    depuis = depuis or debut_cycle(liste["jour_du_cycle"])
    return sum(d.get("cout", 0.0) for j in journaux(liste).values() for d in _lignes(j) if d.get("quand", "") >= depuis)


@dataclass
class Reponse:
    texte: str
    arret: str
    cout: float
    brut: object
    du_cache: bool = False


def _texte(msg) -> str:
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _parametres(modele, contenu, systeme, max_tokens, effort, cache_systeme, format_json):
    p = {
        "model": modele,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": contenu}],
    }
    if systeme:
        if cache_systeme:
            p["system"] = [{"type": "text", "text": systeme, "cache_control": {"type": "ephemeral"}}]
        else:
            p["system"] = systeme
    oc = {}
    if effort:
        oc["effort"] = effort
    if format_json:
        oc["format"] = {"type": "json_schema", "schema": format_json}
    if oc:
        p["output_config"] = oc
    return p


class Client:
    """Le client d'un projet de la liste blanche. Refuse tout autre projet dès la construction."""

    def __init__(self, projet: str):
        self.liste = charger_liste()
        p = self.liste["projets"].get(projet)
        if p is None:
            raise ProjetNonAutorise(
                f"« {projet} » n'est pas dans la liste blanche de l'API ({LISTE_BLANCHE}). "
                "Demander d'abord au propriétaire s'il accepte d'y mettre du crédit, puis l'ajouter avec la date de son accord.")
        self.projet = projet
        self.racine = Path(p["racine"])
        self.journal = self.racine / p["journal"]
        self.journal_lots = self.racine / p.get("lots", str(Path(p["journal"]).with_name("lots.jsonl")))
        self.dossier_cache = self.racine / p["cache"] if p.get("cache") else self.journal.parent / "cache_reponses"
        self.plafond = float(self.liste["plafond_arret"])
        self._api = None

    # --- la clé et le client Anthropic --------------------------------------------------------------------------------
    def lire_cle(self) -> str:
        s = self.liste["source_cle"]
        fichier = Path(s["fichier"])
        if not fichier.exists():
            raise CleAbsente(f"{fichier} n'existe pas")
        for ligne in fichier.read_text(encoding="utf-8-sig").splitlines():
            ligne = ligne.strip()
            if ligne.startswith(s["variable"] + "="):
                cle = ligne.split("=", 1)[1].strip().strip('"').strip("'")
                if cle:
                    return cle
        raise CleAbsente(f"clé attendue : {s['variable']}= est vide dans {fichier}")

    def api(self):
        if self._api is None:
            import anthropic
            self._api = anthropic.Anthropic(api_key=self.lire_cle(), max_retries=3)
        return self._api

    # --- journal et plafond ------------------------------------------------------------------------------------------
    def noter(self, modele: str, usage: str, u, lot: bool = False) -> float:
        entree = getattr(u, "input_tokens", 0) or 0
        sortie = getattr(u, "output_tokens", 0) or 0
        lu = getattr(u, "cache_read_input_tokens", 0) or 0
        ecrit = getattr(u, "cache_creation_input_tokens", 0) or 0
        c = cout(modele, entree, sortie, lu, ecrit, lot)
        ligne = {
            "quand": _dt.datetime.now().isoformat(timespec="seconds"),
            "modele": modele, "usage": usage, "lot": lot,
            "entree": entree, "sortie": sortie, "cache_lu": lu, "cache_ecrit": ecrit,
            "cout": round(c, 6), "projet": self.projet,
        }
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        with self.journal.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
        return c

    def total_depense(self, depuis: str | None = None) -> float:
        """Dépense commune du cycle en cours (tous projets) ; `depuis` pour une autre date."""
        return total_cycle(self.liste, depuis)

    def verifier_plafond(self):
        t = self.total_depense()
        if t >= self.plafond:
            raise PlafondAtteint(f"{t:.2f} $ dépensés sur le cycle : plafond de {self.plafond:.0f} $ atteint, plus d'appel")

    # --- cache des réponses ------------------------------------------------------------------------------------------
    def _cle_cache(self, p: dict) -> Path:
        h = hashlib.sha256(json.dumps(p, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()
        return self.dossier_cache / f"{h[:32]}.json"

    # --- appels ------------------------------------------------------------------------------------------------------
    def appeler(self, modele: str, contenu, systeme: str | None = None, *, usage: str, max_tokens: int = 4000,
                effort: str | None = None, cache_systeme: bool = False, format_json: dict | None = None,
                memoriser: bool = False) -> Reponse:
        """Un appel. `contenu` : texte, ou liste de blocs (images…). `format_json` : schéma imposé.
        `memoriser` : la même demande déjà payée est rendue depuis le disque, pour rien."""
        p = _parametres(modele, contenu, systeme, max_tokens, effort, cache_systeme, format_json)
        fichier_cache = self._cle_cache(p) if memoriser else None
        if fichier_cache and fichier_cache.exists():
            d = json.loads(fichier_cache.read_text(encoding="utf-8"))
            return Reponse(d["texte"], d["arret"], 0.0, None, du_cache=True)
        self.verifier_plafond()
        if max_tokens > 16000:
            with self.api().messages.stream(**p) as s:
                msg = s.get_final_message()
        else:
            msg = self.api().messages.create(**p)
        c = self.noter(modele, usage, msg.usage)
        rep = Reponse(_texte(msg), msg.stop_reason, c, msg)
        if fichier_cache and rep.arret != "max_tokens":
            fichier_cache.parent.mkdir(parents=True, exist_ok=True)
            fichier_cache.write_text(json.dumps({"texte": rep.texte, "arret": rep.arret, "usage": usage,
                                                 "quand": _dt.datetime.now().isoformat(timespec="seconds")},
                                                ensure_ascii=False), encoding="utf-8")
        return rep

    def lancer_lot(self, demandes: list[dict], *, usage: str) -> str:
        """demandes : [{"id": "…", "modele": …, "contenu": …, "systeme": …, "max_tokens": …, "effort": …,
        "cache_systeme": bool, "format_json": dict}] → identifiant du lot (Batch API, moitié prix)."""
        self.verifier_plafond()
        reqs = []
        for d in demandes:
            p = _parametres(d["modele"], d["contenu"], d.get("systeme"), d.get("max_tokens", 4000), d.get("effort"),
                            d.get("cache_systeme", False), d.get("format_json"))
            reqs.append({"custom_id": d["id"], "params": p})
        lot = self.api().messages.batches.create(requests=reqs)
        self.journal_lots.parent.mkdir(parents=True, exist_ok=True)
        with self.journal_lots.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"quand": _dt.datetime.now().isoformat(timespec="seconds"), "lot": lot.id,
                                "usage": usage, "n": len(reqs), "projet": self.projet}, ensure_ascii=False) + "\n")
        return lot.id

    def attendre_lot(self, lot_id: str, *, usage: str, pause: int = 30) -> dict[str, Reponse]:
        """Attend la fin du lot ; rend {id: Reponse} (les erreurs ont arret="erreur:…")."""
        c = self.api()
        while c.messages.batches.retrieve(lot_id).processing_status != "ended":
            time.sleep(pause)
        sortie = {}
        for r in c.messages.batches.results(lot_id):
            if r.result.type == "succeeded":
                msg = r.result.message
                cc = self.noter(msg.model, usage, msg.usage, lot=True)
                sortie[r.custom_id] = Reponse(_texte(msg), msg.stop_reason, cc, msg)
            else:
                sortie[r.custom_id] = Reponse("", "erreur:" + r.result.type, 0.0, r.result)
        return sortie


# --- ligne de commande ------------------------------------------------------------------------------------------------
def _cli():
    ap = argparse.ArgumentParser(description="Client maison de l'API Claude : liste blanche, dépenses.")
    sous = ap.add_subparsers(dest="cmd", required=True)
    sous.add_parser("projets")
    d = sous.add_parser("depenses")
    d.add_argument("--projet")
    d.add_argument("--depuis")
    v = sous.add_parser("verifier")
    v.add_argument("projet")
    a = ap.parse_args()
    liste = charger_liste()

    if a.cmd == "projets":
        s = liste["source_cle"]
        print(f"Clé lue dans {s['fichier']} (variable {s['variable']}), jamais dans l'environnement.")
        print(f"Plafond commun : {liste['plafond_arret']} $ par cycle (renouvelé le {liste['jour_du_cycle']} du mois).")
        for nom, p in liste["projets"].items():
            print(f"  {nom:<28} autorisé le {p.get('autorise_le', '?')}  journal {p['journal']}")
    elif a.cmd == "verifier":
        try:
            Client(a.projet)
            print(f"« {a.projet} » est autorisé.")
        except ProjetNonAutorise as e:
            print(e)
            sys.exit(3)
    elif a.cmd == "depenses":
        depuis = a.depuis or debut_cycle(liste["jour_du_cycle"])
        par_usage, par_modele, par_projet, n = defaultdict(float), defaultdict(float), defaultdict(float), 0
        for nom, j in journaux(liste).items():
            if a.projet and nom != a.projet:
                continue
            for e in _lignes(j):
                if e.get("quand", "") < depuis:
                    continue
                n += 1
                par_usage[e.get("usage", "?")] += e["cout"]
                par_modele[e.get("modele", "?")] += e["cout"]
                par_projet[nom] += e["cout"]
        total = sum(par_projet.values())
        print(f"Depuis le {depuis} : {n} appels, {total:.4f} $ (arrêt commun à {liste['plafond_arret']} $ ; "
              "la page Cost de la Console fait foi)")
        for titre, table in (("projet", par_projet), ("usage", par_usage), ("modèle", par_modele)):
            print(f"Par {titre} :")
            for k, val in sorted(table.items(), key=lambda x: -x[1]):
                print(f"  {k:<30} {val:9.4f} $")


if __name__ == "__main__":
    _cli()
