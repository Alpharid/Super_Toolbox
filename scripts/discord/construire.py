#!/usr/bin/env python3
"""Construit un serveur Discord à partir d'un fichier (serveur.yaml) : rôles, catégories, salons, droits, mode Communauté,
accueil natif (Onboarding), AutoMod, messages fixes. Reproductible : il crée ce qui manque, corrige ce qui a changé, ne
supprime rien (il liste ce qui est en trop ; --elaguer supprime).

    python construire.py --verifier                              # relit le fichier, sans Discord
    python construire.py --env ../../server/discord_essai.env    # le plan, sans rien changer
    python construire.py --env … --appliquer --phase 1           # applique (essayer sur le serveur d'essai d'abord)

Le fichier .env contient DISCORD_JETON=… et DISCORD_SERVEUR=<identifiant du serveur>. Bibliothèque standard + PyYAML.
Générique (Super_Toolbox, scripts/discord/) : rien n'y est propre à un jeu.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML manque : pip install pyyaml")

API = "https://discord.com/api/v10"

# Les bits des permissions de Discord (https://discord.com/developers/docs/topics/permissions), par nom lisible.
PERMISSIONS = {
    "create_instant_invite": 0, "kick_members": 1, "ban_members": 2, "administrator": 3, "manage_channels": 4,
    "manage_guild": 5, "add_reactions": 6, "view_audit_log": 7, "priority_speaker": 8, "stream": 9, "view_channel": 10,
    "send_messages": 11, "send_tts_messages": 12, "manage_messages": 13, "embed_links": 14, "attach_files": 15,
    "read_message_history": 16, "mention_everyone": 17, "use_external_emojis": 18, "view_guild_insights": 19,
    "connect": 20, "speak": 21, "mute_members": 22, "deafen_members": 23, "move_members": 24,
    "use_voice_activation": 25, "change_nickname": 26, "manage_nicknames": 27, "manage_roles": 28,
    "manage_webhooks": 29, "manage_guild_expressions": 30, "use_application_commands": 31, "request_to_speak": 32,
    "manage_events": 33, "manage_threads": 34, "create_public_threads": 35, "create_private_threads": 36,
    "use_external_stickers": 37, "send_messages_in_threads": 38, "use_embedded_activities": 39,
    "moderate_members": 40, "view_creator_monetization_analytics": 41, "use_soundboard": 42,
    "create_guild_expressions": 43, "create_events": 44, "use_external_sounds": 45, "send_voice_messages": 46,
    "send_polls": 49, "use_external_apps": 50, "pin_messages": 51,
}
TYPES = {"texte": 0, "vocal": 2, "categorie": 4, "annonces": 5, "scene": 13, "forum": 15}
# Ces types exigent le mode Communauté : ils sont créés après son activation.
TYPES_COMMUNAUTE = {"annonces", "scene", "forum"}
PRESETS = {"injures": 1, "sexuel": 2, "insultes_haineuses": 3}
ACTIONS_AUTOMOD = {"bloquer": 1, "alerter": 2}


def bits(noms: list[str]) -> int:
    v = 0
    for n in noms:
        v |= 1 << PERMISSIONS[n]
    return v


def nom_salon(nom: str, type_: str) -> str:
    """Le nom tel que Discord le range : les salons écrits sont en minuscules, sans espaces."""
    if type_ in ("vocal", "scene", "categorie"):
        return nom
    return re.sub(r"\s+", "-", nom.strip().lower())


def couleur(c) -> int:
    return int(c.lstrip("#"), 16) if c else 0


# ---------------------------------------------------------------------------------------------------- le fichier

class Erreurs(Exception):
    pass


def charger(chemin: str) -> dict:
    with open(chemin, encoding="utf-8") as f:
        return deplier_guildes(yaml.safe_load(f))


def deplier_guildes(cfg: dict) -> dict:
    """Les guildes reconnues (section guildes:) : chacune a un rôle, une vitrine et un salon privé dans leur catégorie.

    guildes:
      categorie: "Les Guildes"         # elle doit exister dans categories:
      liste:
        - nom: "La Compagnie du Nord"
          couleur: "#7a5a3a"
          sujet: "Mercenaires · Mercenaries"
          chef: "123456789012345678"    # identifiant Discord du chef : il gère les messages de ses deux salons
    La vitrine : tout le monde lit, la guilde écrit. Le salon privé (« <nom>-entre-nous ») : la guilde seule ; le chef peut
    l'ouvrir aux autres ou le refermer (/guilde ouvrir, /guilde fermer : le bot), et le constructeur ne le referme pas
    (ouverture_libre). Ajouter une guilde = une entrée ici, puis construire.py --appliquer ; la retirer = l'enlever (--elaguer)."""
    g = cfg.get("guildes") or {}
    if not g.get("liste"):
        return cfg
    cat = next((c for c in cfg.get("categories", []) if c["nom"] == g.get("categorie")), None)
    if cat is None:
        raise ValueError(f"guildes : la catégorie « {g.get('categorie')} » n'existe pas")
    deja = {r["nom"] for r in cfg.get("roles", [])}
    for guilde in g["liste"]:
        role = f"Guilde · {guilde['nom']}"
        if role not in deja:
            cfg.setdefault("roles", []).append({"nom": role, "phase": cat.get("phase", 1), "couleur": guilde.get("couleur"),
                                                "separe": False, "mentionnable": False, "permissions": [],
                                                "note": "Guilde reconnue : donné par la modération ou à la demande de son chef."})
            deja.add(role)
        ecrire = ["view_channel", "send_messages", "create_public_threads", "attach_files", "embed_links", "read_message_history"]
        commun = {role: {"autoriser": ecrire}, "@bot": {"autoriser": ["view_channel", "send_messages", "manage_roles"]}}
        if "Modération" in deja:
            commun["Modération"] = {"autoriser": ["view_channel", "send_messages"]}
        if guilde.get("chef"):
            commun[f"membre:{guilde['chef']}"] = {"autoriser": ecrire + ["manage_messages", "pin_messages", "manage_threads"]}
        base = nom_salon(guilde["nom"], "texte")
        cat.setdefault("salons", []).append({
            "nom": base, "type": "texte", "sujet": guilde.get("sujet", ""),
            "droits": dict(commun, **{"@everyone": {"refuser": ["send_messages", "create_public_threads"]}})})
        cat["salons"].append({
            "nom": f"{base}-entre-nous", "type": "texte", "ouverture_libre": True,
            "sujet": "Le salon de la guilde : fermé aux autres, sauf si son chef l'ouvre · The guild's own channel",
            "droits": dict(commun, **{"@everyone": {"refuser": ["view_channel"]}})})
    return cfg


def verifier(cfg: dict) -> list[str]:
    """Tout ce qui cloche dans le fichier, d'un coup (liste vide = bon)."""
    err: list[str] = []
    roles = [r["nom"] for r in cfg.get("roles", [])]
    if len(set(roles)) != len(roles):
        err.append("rôles en double")
    connus = set(roles) | {"@everyone", "@bot"}
    gabarits = cfg.get("gabarits", {})

    def droits(d: dict, ou: str):
        for cible, regle in (d or {}).items():
            if cible not in connus and not re.fullmatch(r"membre:\d{15,21}", cible):
                err.append(f"{ou} : rôle inconnu « {cible} »")
            for sens in ("autoriser", "refuser"):
                for p in regle.get(sens, []):
                    if p not in PERMISSIONS:
                        err.append(f"{ou} : permission inconnue « {p} »")

    for r in cfg.get("roles", []):
        for p in r.get("permissions", []):
            if p not in PERMISSIONS:
                err.append(f"rôle {r['nom']} : permission inconnue « {p} »")
    for p in cfg.get("permissions_de_base", []):
        if p not in PERMISSIONS:
            err.append(f"permissions de base : « {p} » inconnue")
    for g, d in gabarits.items():
        droits(d, f"gabarit {g}")
    salons: dict[str, str] = {}
    for cat in cfg.get("categories", []):
        if cat.get("gabarit") and cat["gabarit"] not in gabarits:
            err.append(f"catégorie {cat['nom']} : gabarit inconnu")
        for s in cat.get("salons", []):
            ou = f"salon {s['nom']}"
            if s["type"] not in TYPES or s["type"] == "categorie":
                err.append(f"{ou} : type « {s['type']} » inconnu")
                continue
            n = nom_salon(s["nom"], s["type"])
            if n != s["nom"]:
                err.append(f"{ou} : Discord l'écrira « {n} » (l'écrire ainsi)")
            if n in salons:
                err.append(f"{ou} : nom en double")
            salons[n] = s["type"]
            if s.get("gabarit") and s["gabarit"] not in gabarits:
                err.append(f"{ou} : gabarit inconnu")
            droits(s.get("droits"), ou)
            for cle in cles_messages(s):
                if cle not in cfg.get("messages", {}):
                    err.append(f"{ou} : message « {cle} » absent de messages:")
            if len(s.get("sujet", "")) > 1024:
                err.append(f"{ou} : sujet trop long (1024 au plus)")
            if s["type"] == "forum" and len(s.get("etiquettes", [])) > 20:
                err.append(f"{ou} : 20 étiquettes au plus")
    for k, texte in cfg.get("messages", {}).items():
        if len(texte) > 2000:
            err.append(f"message {k} : {len(texte)} caractères (2000 au plus)")
    sv = cfg.get("serveur", {})
    for cle in ("salon_regles", "salon_mises_a_jour", "salon_systeme"):
        if sv.get(cle) and sv[cle] not in salons:
            err.append(f"serveur.{cle} : salon « {sv[cle]} » inconnu")
    acc = cfg.get("accueil")
    if acc and acc.get("actif"):
        defaut = acc.get("salons_par_defaut", [])
        for s in defaut:
            if s not in salons:
                err.append(f"accueil : salon par défaut « {s} » inconnu")
        if len(defaut) < 7:
            err.append("accueil : Discord veut au moins 7 salons par défaut")
        for q in acc.get("questions", []):
            for o in q.get("options", []):
                for r in o.get("roles", []):
                    if r not in roles:
                        err.append(f"accueil : rôle « {r} » inconnu")
                for s in o.get("salons", []):
                    if s not in salons:
                        err.append(f"accueil : salon « {s} » inconnu")
    am = cfg.get("automod")
    if am:
        if am.get("alerte_dans") and am["alerte_dans"] not in salons:
            err.append("automod : salon d'alerte inconnu")
        for r in am.get("regles", []):
            for l in r.get("listes", []):
                if l not in PRESETS:
                    err.append(f"automod {r['nom']} : liste « {l} » inconnue")
            for m in r.get("motifs", []):
                try:
                    re.compile(m)
                except re.error as e:
                    err.append(f"automod {r['nom']} : motif invalide ({e})")
    return err


# ---------------------------------------------------------------------------------------------------- Discord

class Api:
    """REST de Discord, avec les limites de débit respectées (429 → attente de retry_after)."""

    def __init__(self, jeton: str, serveur: str):
        self.jeton, self.serveur = jeton, serveur

    def requete(self, methode: str, chemin: str, corps=None, raison: str = "serveur.yaml"):
        donnees = None if corps is None else json.dumps(corps).encode()
        for _ in range(6):
            req = urllib.request.Request(API + chemin, data=donnees, method=methode)
            req.add_header("Authorization", f"Bot {self.jeton}")
            req.add_header("User-Agent", "DiscordBot (https://github.com/Alpharid, 1.0) construire.py")
            req.add_header("X-Audit-Log-Reason", urllib.request.quote(raison))
            if donnees is not None:
                req.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(req, timeout=30) as rep:
                    texte = rep.read()
                    if rep.headers.get("X-RateLimit-Remaining") == "0":
                        time.sleep(float(rep.headers.get("X-RateLimit-Reset-After", "1")))
                    return json.loads(texte) if texte else None
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    attente = json.loads(e.read() or b"{}").get("retry_after", 2)
                    time.sleep(float(attente) + 0.25)
                    continue
                raise RuntimeError(f"{methode} {chemin} → {e.code} {e.read().decode(errors='replace')[:600]}") from None
        raise RuntimeError(f"{methode} {chemin} : trop de refus de débit")

    # Ce dont construire() a besoin (le faux de tests/ imite exactement ces méthodes)
    def serveur_info(self): return self.requete("GET", f"/guilds/{self.serveur}")
    def moi(self): return self.requete("GET", "/users/@me")
    def membre(self, uid): return self.requete("GET", f"/guilds/{self.serveur}/members/{uid}")
    def roles(self): return self.requete("GET", f"/guilds/{self.serveur}/roles")
    def salons(self): return self.requete("GET", f"/guilds/{self.serveur}/channels")
    def creer_role(self, c): return self.requete("POST", f"/guilds/{self.serveur}/roles", c)
    def modifier_role(self, rid, c): return self.requete("PATCH", f"/guilds/{self.serveur}/roles/{rid}", c)
    def ordonner_roles(self, l): return self.requete("PATCH", f"/guilds/{self.serveur}/roles", l)
    def creer_salon(self, c): return self.requete("POST", f"/guilds/{self.serveur}/channels", c)
    def modifier_salon(self, sid, c): return self.requete("PATCH", f"/channels/{sid}", c)
    def ordonner_salons(self, l): return self.requete("PATCH", f"/guilds/{self.serveur}/channels", l)
    def supprimer_salon(self, sid): return self.requete("DELETE", f"/channels/{sid}")
    def supprimer_role(self, rid): return self.requete("DELETE", f"/guilds/{self.serveur}/roles/{rid}")
    def modifier_serveur(self, c): return self.requete("PATCH", f"/guilds/{self.serveur}", c)
    def accueil(self, c): return self.requete("PUT", f"/guilds/{self.serveur}/onboarding", c)
    def accueil_actuel(self):
        try:
            return self.requete("GET", f"/guilds/{self.serveur}/onboarding")
        except RuntimeError:
            return None
    def regles_automod(self): return self.requete("GET", f"/guilds/{self.serveur}/auto-moderation/rules")
    def creer_automod(self, c): return self.requete("POST", f"/guilds/{self.serveur}/auto-moderation/rules", c)
    def modifier_automod(self, rid, c): return self.requete("PATCH", f"/guilds/{self.serveur}/auto-moderation/rules/{rid}", c)
    def poster(self, sid, c): return self.requete("POST", f"/channels/{sid}/messages", c)
    def message(self, sid, mid):
        try:
            return self.requete("GET", f"/channels/{sid}/messages/{mid}")
        except RuntimeError:
            return None
    def modifier_message(self, sid, mid, c): return self.requete("PATCH", f"/channels/{sid}/messages/{mid}", c)


def contient(reel, voulu) -> bool:
    """Discord renvoie plus de champs qu'on n'en écrit : on ne compare que ce que le fichier fixe."""
    if isinstance(voulu, dict):
        return isinstance(reel, dict) and all(contient(reel.get(k), v) for k, v in voulu.items())
    if isinstance(voulu, list):
        return isinstance(reel, list) and len(reel) == len(voulu) and all(contient(a, b) for a, b in zip(reel, voulu))
    return str(reel) == str(voulu) if voulu is not None else reel in (None, "", [])


def cles_messages(salon: dict) -> list:
    """Les messages d'un salon : une clé, ou une liste (un message par langue, dans l'ordre où ils paraissent)."""
    m = salon.get("message")
    return [] if not m else [m] if isinstance(m, str) else list(m)


def lier_salons(texte: str, ids: dict) -> str:
    """« #règles » devient un lien cliquable (<#id>) quand le salon existe déjà ; sinon le texte reste tel quel."""
    def lien(m):
        sid = ids.get(m.group(1))
        return f"<#{sid}>" if sid and not str(sid).startswith("(") else m.group(0)
    return re.sub(r"#([\w-]+)", lien, texte)


def boutons_de(message: dict) -> list:
    return [(b.get("label"), b.get("custom_id")) for rang in message.get("components") or [] for b in rang.get("components", [])]


def flocon() -> str:
    """Un identifiant neuf au format de Discord (pour les questions et options d'accueil nouvelles)."""
    flocon.n = getattr(flocon, "n", 0) + 1
    return str(((int(time.time() * 1000) - 1420070400000) << 22) | (flocon.n & 0xFFF))


# ---------------------------------------------------------------------------------------------------- le plan

class Construction:
    """Compare le fichier au serveur, puis applique. self.journal garde chaque action (le plan, à relire)."""

    def __init__(self, api, cfg: dict, phase: int, appliquer: bool, etat_messages: dict | None = None):
        self.api, self.cfg, self.phase, self.appliquer = api, cfg, phase, appliquer
        self.journal: list[str] = []
        self.etat_messages = etat_messages if etat_messages is not None else {}
        self.g = api.serveur_info()
        self.ids_roles: dict[str, str] = {}
        self.ids_salons: dict[str, str] = {}
        self.fictifs = 0

    def note(self, s: str):
        self.journal.append(s)
        print(("  ✔ " if self.appliquer else "  · ") + s)

    def faire(self, fonction, *args):
        if self.appliquer:
            return fonction(*args)
        self.fictifs += 1
        return {"id": f"(nouveau-{self.fictifs})"}

    def visible(self, objet: dict, parent_phase: int = 1) -> bool:
        return max(objet.get("phase", 1), parent_phase) <= self.phase

    # -- rôles
    def roles(self):
        existants = {r["name"]: r for r in self.api.roles()}
        self.ids_roles["@everyone"] = self.g["id"]
        moi = self.api.moi()
        mon_role = None
        for rid in self.api.membre(moi["id"]).get("roles", []):
            r = next((x for x in existants.values() if x["id"] == rid), None)
            if r and (r.get("tags") or {}).get("bot_id") == moi["id"]:
                mon_role = r
        if mon_role:
            self.ids_roles["@bot"] = mon_role["id"]
        else:
            self.note("ATTENTION : rôle du bot introuvable (droits « @bot » ignorés)")
        base = bits(self.cfg.get("permissions_de_base", []))
        ev = existants.get("@everyone")
        if ev and int(ev["permissions"]) != base:
            self.note("@everyone : permissions de base remises au fichier")
            self.faire(self.api.modifier_role, self.g["id"], {"permissions": str(base)})
        voulus = [r for r in self.cfg.get("roles", []) if self.visible(r)]
        for r in voulus:
            corps = {"name": r["nom"], "permissions": str(bits(r.get("permissions", []))), "color": couleur(r.get("couleur")),
                     "hoist": bool(r.get("separe")), "mentionable": bool(r.get("mentionnable"))}
            ex = existants.get(r["nom"])
            if not ex:
                self.note(f"rôle « {r['nom']} » : créé")
                self.ids_roles[r["nom"]] = self.faire(self.api.creer_role, corps)["id"]
                continue
            self.ids_roles[r["nom"]] = ex["id"]
            diff = {k: v for k, v in corps.items() if k != "name" and str(ex.get(k)) != str(v)}
            if diff:
                self.note(f"rôle « {r['nom']} » : {', '.join(diff)} corrigés")
                self.faire(self.api.modifier_role, ex["id"], diff)
        # L'ordre : le rôle du bot en tête (il ne donne que des rôles plus bas que le sien), puis ceux du fichier, dans l'ordre.
        # Discord accepte de monter le rôle du bot quand il est dans la même requête (vu sur le serveur d'essai, 2026-11-09) ;
        # les rôles neufs naissent tous à la position 1, d'où cette remise en ordre.
        ids = ([mon_role["id"]] if mon_role else []) + [self.ids_roles[r["nom"]] for r in voulus]
        ids = [i for i in ids if not str(i).startswith("(")]
        if ids:
            actuels = {r["id"]: r["position"] for r in (self.api.roles() if self.appliquer else existants.values())}
            pos = [actuels.get(i, -1) for i in ids]
            en_ordre = all(a > b for a, b in zip(pos, pos[1:])) and len(ids) == len(pos)
            if not en_ordre:
                if self.appliquer:
                    try:
                        self.api.ordonner_roles([{"id": i, "position": len(ids) - k} for k, i in enumerate(ids)])
                        self.note("ordre des rôles remis (le bot en tête)")
                    except RuntimeError as e:
                        self.note(f"ATTENTION : ordre des rôles refusé ({e}) : glisser le rôle du bot tout en haut (Paramètres du "
                                  "serveur → Rôles) : il ne peut donner que des rôles plus bas que le sien")
                else:
                    self.note("ordre des rôles à remettre (le bot en tête)")
        en_trop = [n for n, r in existants.items() if n != "@everyone" and not r.get("managed")
                   and n not in {x["nom"] for x in self.cfg.get("roles", [])}]
        for n in en_trop:
            self.note(f"rôle « {n} » : absent du fichier" + (" → supprimé" if self.args_elaguer else " (laissé)"))
            if self.args_elaguer:
                self.faire(self.api.supprimer_role, existants[n]["id"])

    args_elaguer = False

    # -- droits d'un salon
    def droits(self, gabarit: str | None, extra: dict | None) -> list[dict]:
        regles: dict[str, dict] = {}
        for source in (self.cfg.get("gabarits", {}).get(gabarit, {}) if gabarit else {}, extra or {}):
            for cible, r in source.items():
                d = regles.setdefault(cible, {"autoriser": set(), "refuser": set()})
                d["autoriser"] |= set(r.get("autoriser", []))
                d["refuser"] |= set(r.get("refuser", []))
        sortie = []
        for cible, r in regles.items():
            membre = cible.startswith("membre:")
            rid = cible[7:] if membre else self.ids_roles.get(cible)
            if rid is None:
                continue  # rôle d'une phase pas encore construite
            sortie.append({"id": rid, "type": 1 if membre else 0, "allow": str(bits(sorted(r["autoriser"]))),
                           "deny": str(bits(sorted(r["refuser"] - r["autoriser"])))})
        return sorted(sortie, key=lambda o: o["id"])

    @staticmethod
    def memes_droits(a: list[dict], b: list[dict]) -> bool:
        cle = lambda l: sorted((str(o["id"]), int(o["type"]), int(o["allow"]), int(o["deny"])) for o in l)
        return cle(a) == cle(b)

    # -- catégories et salons
    def salons(self, seulement_communaute: bool | None):
        existants = self.api.salons()
        par_nom = {}
        for s in existants:
            par_nom.setdefault((s["name"], s["type"]), s)
        position = 0
        ordre = []
        for cat in self.cfg.get("categories", []):
            if not self.visible(cat):
                continue
            position += 1
            ex = par_nom.get((cat["nom"], 4))
            droits_cat = self.droits(cat.get("gabarit"), cat.get("droits"))
            if seulement_communaute is not True:
                if not ex:
                    self.note(f"catégorie « {cat['nom']} » : créée")
                    ex = self.faire(self.api.creer_salon, {"name": cat["nom"], "type": 4, "permission_overwrites": droits_cat})
                elif not self.memes_droits(ex.get("permission_overwrites", []), droits_cat):
                    self.note(f"catégorie « {cat['nom']} » : droits corrigés")
                    self.faire(self.api.modifier_salon, ex["id"], {"permission_overwrites": droits_cat})
            if not ex and cat["nom"] in self.ids_salons:
                ex = {"id": self.ids_salons[cat["nom"]]}  # créée au premier passage (ou prévue, en plan)
            if not ex:
                continue
            self.ids_salons[cat["nom"]] = ex["id"]
            ordre.append({"id": ex["id"], "position": position})
            for s in cat.get("salons", []):
                if not self.visible(s, cat.get("phase", 1)):
                    continue
                position += 1
                communaute = s["type"] in TYPES_COMMUNAUTE
                t = TYPES[s["type"]]
                ancien = par_nom.get((s["nom"], t)) or (par_nom.get((s["nom"], 0)) if t == 5 else None)
                if seulement_communaute is not None and communaute != seulement_communaute:
                    # pas de ce passage : on garde seulement sa place dans l'ordre
                    sid = self.ids_salons.get(s["nom"]) or (ancien or {}).get("id")
                    if sid:
                        ordre.append({"id": sid, "position": position})
                    continue
                gab = s.get("gabarit") or cat.get("gabarit")
                corps = {"name": s["nom"], "type": t, "parent_id": ex["id"],
                         "permission_overwrites": self.droits(gab, s.get("droits"))}
                if s.get("sujet") and s["type"] not in ("vocal", "scene"):
                    corps["topic"] = s["sujet"]
                if s["type"] == "forum":
                    corps["available_tags"] = [{"name": e} for e in s.get("etiquettes", [])]
                if not ancien:
                    self.note(f"salon #{s['nom']} ({s['type']}) : créé dans « {cat['nom']} »")
                    ancien = self.faire(self.api.creer_salon, corps)
                else:
                    diff = {}
                    if ancien["type"] != t:
                        diff["type"] = t  # texte → annonces, une fois la Communauté active
                    if str(ancien.get("parent_id")) != str(ex["id"]):
                        diff["parent_id"] = ex["id"]
                    if corps.get("topic") and (ancien.get("topic") or "") != corps["topic"]:
                        diff["topic"] = corps["topic"]
                    if s.get("ouverture_libre"):
                        # le salon s'ouvre et se ferme par le bot (/guilde) : garder le droit « @everyone » qu'il porte
                        tous = str(self.ids_roles.get("@everyone"))
                        actuel = [o for o in ancien.get("permission_overwrites", []) if str(o["id"]) == tous]
                        corps["permission_overwrites"] = sorted(
                            [o for o in corps["permission_overwrites"] if str(o["id"]) != tous] + actuel, key=lambda o: o["id"])
                    if not self.memes_droits(ancien.get("permission_overwrites", []), corps["permission_overwrites"]):
                        diff["permission_overwrites"] = corps["permission_overwrites"]
                    if s["type"] == "forum":
                        noms = [e["name"] for e in ancien.get("available_tags", [])]
                        manquent = [e for e in s.get("etiquettes", []) if e not in noms]
                        if manquent:
                            diff["available_tags"] = ancien.get("available_tags", []) + [{"name": e} for e in manquent]
                    if diff:
                        self.note(f"salon #{s['nom']} : {', '.join(diff)} corrigés")
                        self.faire(self.api.modifier_salon, ancien["id"], diff)
                self.ids_salons[s["nom"]] = ancien["id"]
                ordre.append({"id": ancien["id"], "position": position})
        # L'ordre seulement (le parent est posé à la création ou corrigé plus haut : Discord refuse d'en changer plusieurs à la
        # fois dans cette requête). Rien n'est envoyé si l'ordre actuel est déjà le bon.
        ordre = [o for o in ordre if not str(o["id"]).startswith("(")]
        if self.appliquer and ordre:
            actuels = {x["id"]: x.get("position", 0) for x in self.api.salons()}
            if [o["id"] for o in sorted(ordre, key=lambda o: (actuels.get(o["id"], -1), o["position"]))] == [o["id"] for o in ordre]:
                ordre = []
        if self.appliquer and ordre:
            try:
                self.api.ordonner_salons(ordre)
            except RuntimeError as e:
                self.note(f"ordre des salons non appliqué ({e})")
        if seulement_communaute is not False:
            voulus = {(nom_salon(s["nom"], s["type"]), TYPES[s["type"]]) for c in self.cfg.get("categories", [])
                      for s in c.get("salons", [])} | {(c["nom"], 4) for c in self.cfg.get("categories", [])}
            # Les salons vocaux que le bot ouvre aux joueurs (les « feux ») vivent dans une catégorie marquée
            # vocaux_libres : ils ne sont pas dans le fichier et ne doivent jamais être élagués.
            libres = {str(self.ids_salons.get(c["nom"])) for c in self.cfg.get("categories", []) if c.get("vocaux_libres")}
            for s in existants:
                if s["type"] == 2 and str(s.get("parent_id")) in libres:
                    continue
                if (s["name"], s["type"]) not in voulus and not (s["type"] == 0 and (s["name"], 5) in voulus):
                    self.note(f"salon « {s['name']} » : absent du fichier" + (" → supprimé" if self.args_elaguer else " (laissé)"))
                    if self.args_elaguer:
                        self.faire(self.api.supprimer_salon, s["id"])

    # -- le serveur, le mode Communauté
    def serveur(self):
        sv = self.cfg.get("serveur", {})
        corps = {"verification_level": sv.get("niveau_verification", 2),
                 "default_message_notifications": sv.get("notifications_par_defaut", 1),
                 "explicit_content_filter": sv.get("filtre_contenu_explicite", 2),
                 "preferred_locale": sv.get("langue", "fr")}
        for cle, champ in (("salon_regles", "rules_channel_id"), ("salon_mises_a_jour", "public_updates_channel_id"),
                           ("salon_systeme", "system_channel_id")):
            if sv.get(cle) in self.ids_salons:
                corps[champ] = self.ids_salons[sv[cle]]
        features = list(self.g.get("features", []))
        if "COMMUNITY" not in features:
            features.append("COMMUNITY")
            corps["features"] = features
            self.note("mode Communauté : activé (salons d'annonces, forums, scène, accueil)")
        diff = {k: v for k, v in corps.items() if str(self.g.get(k)) != str(v)}
        if diff:
            if "features" not in diff:
                self.note(f"serveur : {', '.join(diff)} corrigés")
            self.faire(self.api.modifier_serveur, diff)
            self.g.update(diff)

    # -- l'accueil natif
    @staticmethod
    def empreinte_accueil(a: dict | None):
        """Ce qui compte dans l'accueil, sans les identifiants des questions (Discord les garde, le fichier les refait)."""
        if not a:
            return None
        return (bool(a.get("enabled")), tuple(sorted(str(i) for i in a.get("default_channel_ids", []))),
                tuple((q.get("title"), bool(q.get("single_select")), bool(q.get("required")),
                       tuple((o.get("title"), o.get("description") or None, tuple(sorted(map(str, o.get("role_ids") or []))),
                              tuple(sorted(map(str, o.get("channel_ids") or [])))) for o in q.get("options", [])))
                      for q in a.get("prompts", [])))

    def accueil(self):
        acc = self.cfg.get("accueil")
        if not acc or not acc.get("actif"):
            return
        ids = lambda noms, table: [table[n] for n in noms if n in table and not str(table[n]).startswith("(")]
        questions = []
        for q in acc.get("questions", []):
            options = [{"id": flocon(), "title": o["titre"], "description": o.get("description") or None,
                        "role_ids": ids(o.get("roles", []), self.ids_roles), "channel_ids": ids(o.get("salons", []), self.ids_salons)}
                       for o in q.get("options", [])]
            questions.append({"id": flocon(), "type": 0, "title": q["titre"], "options": options,
                              "single_select": bool(q.get("unique")), "required": bool(q.get("obligatoire")), "in_onboarding": True})
        corps = {"prompts": questions, "default_channel_ids": ids(acc.get("salons_par_defaut", []), self.ids_salons),
                 "enabled": True, "mode": 0}
        if self.empreinte_accueil(self.api.accueil_actuel()) == self.empreinte_accueil(corps):
            return  # déjà tel que le fichier le veut
        self.note(f"accueil : {len(questions)} questions, {len(corps['default_channel_ids'])} salons par défaut")
        if self.appliquer:
            try:
                self.api.accueil(corps)
            except RuntimeError as e:
                self.note(f"accueil refusé par Discord ({e}) : à finir à la main (Paramètres → Accueil)")

    # -- AutoMod
    def automod(self):
        am = self.cfg.get("automod")
        if not am:
            return
        alerte = self.ids_salons.get(am.get("alerte_dans"))
        existants = {r["name"]: r for r in (self.api.regles_automod() or [])}
        for r in am.get("regles", []):
            actions = []
            for a in r.get("actions", []):
                if a == "bloquer":
                    m = {"custom_message": r["message_bloque"]} if r.get("message_bloque") else {}
                    actions.append({"type": 1, "metadata": m})
                elif a == "alerter" and alerte and not str(alerte).startswith("("):
                    actions.append({"type": 2, "metadata": {"channel_id": alerte}})
                elif a.startswith("exclure_") and r["type"] in ("mots", "mentions"):
                    minutes = int(re.findall(r"\d+", a)[0])
                    actions.append({"type": 3, "metadata": {"duration_seconds": minutes * 60}})
            meta: dict = {}
            trig = {"mots": 1, "spam": 3, "preset": 4, "mentions": 5}[r["type"]]
            if r["type"] == "mots":
                meta = {"keyword_filter": r.get("mots", []), "regex_patterns": r.get("motifs", [])}
            elif r["type"] == "preset":
                meta = {"presets": [PRESETS[l] for l in r.get("listes", [])]}
            elif r["type"] == "mentions":
                meta = {"mention_total_limit": r.get("limite", 5), "mention_raid_protection_enabled": bool(r.get("anti_raid"))}
            corps = {"name": r["nom"], "event_type": 1, "trigger_type": trig, "trigger_metadata": meta, "actions": actions,
                     "enabled": True, "exempt_roles": sorted(self.ids_roles[x] for x in r.get("exceptions_roles", []) if x in self.ids_roles
                                                       and not str(self.ids_roles[x]).startswith("("))}
            ex = existants.get(r["nom"])
            try:
                if not ex:
                    self.note(f"AutoMod « {r['nom']} » : créée")
                    self.faire(self.api.creer_automod, corps)
                else:
                    diff = {k: v for k, v in corps.items() if k not in ("event_type", "trigger_type") and not (sorted(map(str, ex.get(k) or [])) == sorted(map(str, v)) if k == "exempt_roles" else contient(ex.get(k), v))}
                    if diff:
                        self.note(f"AutoMod « {r['nom']} » : {', '.join(diff)} corrigés")
                        self.faire(self.api.modifier_automod, ex["id"], diff)
            except RuntimeError as e:
                self.note(f"AutoMod « {r['nom']} » refusée ({e})")

    # -- les messages fixes (et les boutons des rôles au choix)
    def messages(self):
        textes = self.cfg.get("messages", {})
        boutons = self.cfg.get("bot", {}).get("roles_au_choix", {})
        for cat in self.cfg.get("categories", []):
            for s in cat.get("salons", []):
                cles = cles_messages(s)
                sid = self.ids_salons.get(s["nom"])
                if not cles or not sid or str(sid).startswith("(") or not self.visible(s, cat.get("phase", 1)):
                    continue
                for rang, cle in enumerate(cles):
                    corps = {"content": lier_salons(textes[cle].strip(), self.ids_salons),
                             "allowed_mentions": {"parse": []}, "components": []}
                    # Les boutons des rôles au choix vont sous le dernier message du salon (le plus près du lecteur)
                    if boutons.get("salon") == s["nom"] and rang == len(cles) - 1:
                        roles = [r for r in boutons.get("roles", []) if r in self.ids_roles]
                        lignes = [roles[i:i + 5] for i in range(0, len(roles), 5)]
                        corps["components"] = [{"type": 1, "components": [
                            {"type": 2, "style": 2, "label": r, "custom_id": f"role:{r}"} for r in ligne]}
                            for ligne in lignes]
                    # Le premier message garde la clé du salon (états déjà écrits) ; les suivants « salon/clé »
                    etat = s["nom"] if rang == 0 else f"{s['nom']}/{cle}"
                    connu = self.etat_messages.get(etat)
                    ancien = self.api.message(sid, connu) if connu else None
                    if not ancien:
                        self.note(f"#{s['nom']} : message « {cle} » posté")
                        m = self.faire(self.api.poster, sid, corps)
                        if self.appliquer:
                            self.etat_messages[etat] = m["id"]
                    elif ancien.get("content") != corps["content"] or boutons_de(ancien) != boutons_de(corps):
                        self.note(f"#{s['nom']} : message « {cle} » mis à jour")
                        self.faire(self.api.modifier_message, sid, connu, corps)

    def tout(self, communaute=True, accueil=True, automod=True, messages=True):
        print(f"Serveur « {self.g.get('name')} », phase {self.phase}, {'APPLIQUÉ' if self.appliquer else 'plan seulement'}")
        self.roles()
        self.salons(seulement_communaute=False if communaute else None)
        if communaute:
            self.serveur()
            self.salons(seulement_communaute=True)
            if accueil:
                self.accueil()
        if automod:
            self.automod()
        if messages:
            self.messages()
        if not self.journal:
            print("  rien à changer : le serveur suit le fichier.")
        return self.journal


def lire_env(chemin: str) -> dict:
    env = {}
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if ligne and not ligne.startswith("#") and "=" in ligne:
                k, v = ligne.split("=", 1)
                env[k.strip()] = v.strip().strip('"')
    return env


def main(argv=None):
    ici = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fichier", default=os.path.join(ici, "serveur.yaml"))
    p.add_argument("--env", help="fichier .env : DISCORD_JETON, DISCORD_SERVEUR")
    p.add_argument("--phase", type=int, default=1)
    p.add_argument("--verifier", action="store_true", help="relire le fichier seulement (pas de Discord)")
    p.add_argument("--appliquer", action="store_true", help="appliquer (sinon : le plan seulement)")
    p.add_argument("--elaguer", action="store_true", help="supprimer ce qui n'est pas dans le fichier")
    p.add_argument("--sans-communaute", action="store_true")
    p.add_argument("--sans-accueil", action="store_true")
    p.add_argument("--sans-automod", action="store_true")
    p.add_argument("--sans-messages", action="store_true")
    a = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cfg = charger(a.fichier)
    err = verifier(cfg)
    if err:
        print("Le fichier a des erreurs :\n  - " + "\n  - ".join(err))
        return 1
    if a.verifier:
        n_salons = sum(len(c.get("salons", [])) for c in cfg.get("categories", []))
        print(f"Fichier bon : {len(cfg.get('roles', []))} rôles, {len(cfg.get('categories', []))} catégories, {n_salons} salons.")
        return 0
    if not a.env:
        print("--env manque (le jeton et l'identifiant du serveur)")
        return 2
    env = lire_env(a.env)
    api = Api(env["DISCORD_JETON"], env["DISCORD_SERVEUR"])
    donnees = os.path.join(ici, "donnees")
    os.makedirs(donnees, exist_ok=True)
    chemin_etat = os.path.join(donnees, f"messages_{env['DISCORD_SERVEUR']}.json")
    etat = json.load(open(chemin_etat, encoding="utf-8")) if os.path.exists(chemin_etat) else {}
    c = Construction(api, cfg, a.phase, a.appliquer, etat)
    c.args_elaguer = a.elaguer
    c.tout(communaute=not a.sans_communaute, accueil=not a.sans_accueil, automod=not a.sans_automod, messages=not a.sans_messages)
    if a.appliquer:
        with open(chemin_etat, "w", encoding="utf-8") as f:
            json.dump(etat, f, indent=1)
    else:
        print("\n(rien n'a changé : relancer avec --appliquer)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
