"""construire.py contre un faux Discord en mémoire : le plan, l'application, puis un second passage qui ne change rien.

    python -m unittest discover -s tests   (depuis communaute/discord)
"""
import copy
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
import construire as C  # noqa: E402

FICHIER = os.path.join(os.path.dirname(ICI), "modele_serveur.yaml")


class FauxDiscord:
    """Imite les appels REST dont construire.py se sert, avec les contraintes qui comptent (types de Communauté)."""

    def __init__(self):
        self.n = 1000
        self.g = {"id": "1", "name": "Essai", "features": [], "verification_level": 0,
                  "default_message_notifications": 0, "explicit_content_filter": 0, "preferred_locale": "en-US"}
        self.liste_roles = [{"id": "1", "name": "@everyone", "permissions": "0", "position": 0},
                            {"id": "900", "name": "Bot d'essai", "permissions": "8", "position": 20, "managed": True,
                             "tags": {"bot_id": "77"}}]
        self.liste_salons = []
        self.regles = []
        self.msgs = {}
        self.appels = 0
        self.accueil_recu = None

    def nid(self):
        self.n += 1
        return str(self.n)

    def ecrit(self):
        self.appels += 1

    def serveur_info(self): return copy.deepcopy(self.g)
    def moi(self): return {"id": "77"}
    def membre(self, uid): return {"roles": ["900"]}
    def roles(self): return copy.deepcopy(self.liste_roles)
    def salons(self): return copy.deepcopy(self.liste_salons)

    def creer_role(self, c):
        self.ecrit()
        r = dict(c, id=self.nid(), position=1, color=c.get("color", 0))
        self.liste_roles.append(r)
        return r

    def modifier_role(self, rid, c):
        self.ecrit()
        next(r for r in self.liste_roles if r["id"] == rid).update(c)

    def ordonner_roles(self, l):
        for o in l:
            next(r for r in self.liste_roles if r["id"] == o["id"])["position"] = o["position"]

    def creer_salon(self, c):
        self.ecrit()
        if c["type"] in (5, 13, 15) and "COMMUNITY" not in self.g["features"]:
            raise RuntimeError("type réservé aux serveurs Communauté")
        s = dict(c, id=self.nid())
        if "available_tags" in s:
            s["available_tags"] = [dict(t, id=self.nid()) for t in s["available_tags"]]
        self.liste_salons.append(s)
        return s

    def modifier_salon(self, sid, c):
        self.ecrit()
        next(s for s in self.liste_salons if s["id"] == sid).update(c)

    def ordonner_salons(self, l): pass
    def supprimer_salon(self, sid): self.liste_salons = [s for s in self.liste_salons if s["id"] != sid]
    def supprimer_role(self, rid): self.liste_roles = [r for r in self.liste_roles if r["id"] != rid]

    def modifier_serveur(self, c):
        self.ecrit()
        if "features" in c:
            assert self.g.get("rules_channel_id") or c.get("rules_channel_id"), "Communauté sans salon de règles"
        self.g.update(c)

    def accueil(self, c): self.accueil_recu = c
    def regles_automod(self): return copy.deepcopy(self.regles)

    def creer_automod(self, c):
        self.ecrit()
        self.regles.append(dict(c, id=self.nid()))

    def modifier_automod(self, rid, c):
        self.ecrit()
        next(r for r in self.regles if r["id"] == rid).update(c)

    def poster(self, sid, c):
        self.ecrit()
        m = dict(c, id=self.nid())
        self.msgs[(sid, m["id"])] = m
        return m

    def message(self, sid, mid): return copy.deepcopy(self.msgs.get((sid, mid)))

    def modifier_message(self, sid, mid, c):
        self.ecrit()
        self.msgs[(sid, mid)].update(c)


def construire(faux, cfg, phase, appliquer, etat):
    with redirect_stdout(io.StringIO()):
        c = C.Construction(faux, cfg, phase, appliquer, etat)
        return c.tout(), c


class TestsConstruire(unittest.TestCase):
    def setUp(self):
        self.cfg = C.charger(FICHIER)

    def test_le_fichier_est_bon(self):
        self.assertEqual(C.verifier(self.cfg), [])

    def test_le_verificateur_trouve_les_fautes(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["categories"][0]["salons"][0]["nom"] = "Bienvenue Ici"
        cfg["roles"][0]["permissions"] = ["voler_des_dinars"]
        cfg["accueil"]["salons_par_defaut"] = ["bienvenue"]
        err = C.verifier(cfg)
        self.assertTrue(any("Discord l'écrira" in e for e in err))
        self.assertTrue(any("voler_des_dinars" in e for e in err))
        self.assertTrue(any("au moins 7" in e for e in err))

    def test_le_plan_ne_touche_a_rien(self):
        faux = FauxDiscord()
        journal, _ = construire(faux, self.cfg, 1, False, {})
        self.assertGreater(len(journal), 20)
        self.assertEqual(faux.appels, 0)
        self.assertEqual(faux.liste_salons, [])

    def test_phase_1_puis_rien_a_changer(self):
        faux, etat = FauxDiscord(), {}
        construire(faux, self.cfg, 1, True, etat)
        noms = {s["name"] for s in faux.liste_salons}
        self.assertIn("bienvenue", noms)
        self.assertIn("journal-de-développement", noms)
        self.assertNotIn("état-du-serveur", noms)      # phase 2
        self.assertNotIn("alpha-bugs", noms)           # phase 3
        self.assertNotIn("Testeur de l'Alpha", {r["name"] for r in faux.liste_roles})
        self.assertIn("COMMUNITY", faux.g["features"])
        self.assertEqual(faux.g["default_message_notifications"], 1)
        annonces = next(s for s in faux.liste_salons if s["name"] == "annonces")
        self.assertEqual(annonces["type"], 5)
        self.assertIn("bienvenue", etat)
        # Les boutons des rôles au choix sur le message de bienvenue
        m = faux.message(next(s["id"] for s in faux.liste_salons if s["name"] == "bienvenue"), etat["bienvenue"])
        self.assertIn("role:Alerte Alpha", [b["custom_id"] for b in m["components"][0]["components"]])
        self.assertEqual(len(faux.regles), 4)
        self.assertGreaterEqual(len(faux.accueil_recu["default_channel_ids"]), 7)
        faux.appels = 0
        journal, _ = construire(faux, self.cfg, 1, True, etat)
        self.assertEqual(faux.appels, 0, journal)

    def test_passer_en_phase_3_ajoute_sans_rien_casser(self):
        faux, etat = FauxDiscord(), {}
        construire(faux, self.cfg, 1, True, etat)
        avant = {s["id"] for s in faux.liste_salons}
        construire(faux, self.cfg, 3, True, etat)
        apres = {s["id"] for s in faux.liste_salons}
        self.assertTrue(avant <= apres)
        alpha = next(s for s in faux.liste_salons if s["name"] == "alpha-discussion")
        testeur = next(r["id"] for r in faux.liste_roles if r["name"] == "Testeur de l'Alpha")
        cibles = {o["id"]: o for o in alpha["permission_overwrites"]}
        self.assertEqual(int(cibles["1"]["deny"]) & (1 << C.PERMISSIONS["view_channel"]), 1 << C.PERMISSIONS["view_channel"])
        self.assertTrue(int(cibles[testeur]["allow"]) & (1 << C.PERMISSIONS["view_channel"]))

    def test_un_texte_change_est_modifie_pas_reposte(self):
        faux, etat = FauxDiscord(), {}
        construire(faux, self.cfg, 1, True, etat)
        n_msgs = len(faux.msgs)
        cfg = copy.deepcopy(self.cfg)
        cfg["messages"]["regles"] += "\n8. Une règle de plus."
        journal, _ = construire(faux, cfg, 1, True, etat)
        self.assertEqual(len(faux.msgs), n_msgs)
        self.assertTrue(any("mis à jour" in j for j in journal))

    def test_ce_qui_est_en_trop_est_laisse(self):
        faux, etat = FauxDiscord(), {}
        construire(faux, self.cfg, 1, True, etat)
        faux.liste_salons.append({"id": "5", "name": "vieux-salon", "type": 0})
        journal, _ = construire(faux, self.cfg, 1, True, etat)
        self.assertTrue(any("vieux-salon" in j and "laissé" in j for j in journal))
        self.assertIn("5", {s["id"] for s in faux.liste_salons})

    def test_le_bot_trop_bas_est_signale(self):
        faux, etat = FauxDiscord(), {}
        construire(faux, self.cfg, 1, True, etat)
        next(r for r in faux.liste_roles if r["id"] == "900")["position"] = 0
        journal, _ = construire(faux, self.cfg, 1, False, etat)
        self.assertTrue(any("glisser le rôle du bot" in j for j in journal))

    def test_lecture_seule(self):
        faux, etat = FauxDiscord(), {}
        construire(faux, self.cfg, 1, True, etat)
        regles = next(s for s in faux.liste_salons if s["name"] == "règles")
        tous = next(o for o in regles["permission_overwrites"] if o["id"] == "1")
        self.assertTrue(int(tous["deny"]) & (1 << C.PERMISSIONS["send_messages"]))
        bot = next(o for o in regles["permission_overwrites"] if o["id"] == "900")
        self.assertTrue(int(bot["allow"]) & (1 << C.PERMISSIONS["send_messages"]))


if __name__ == "__main__":
    unittest.main()
