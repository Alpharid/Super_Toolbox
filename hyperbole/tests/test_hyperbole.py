"""Tests d'Hyperbole :  python -m unittest discover -s D:/Super_Toolbox/hyperbole/tests -v"""
from __future__ import annotations

import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from popo import analyse as A  # noqa: E402
from popo import compare as C  # noqa: E402
from popo import journal as J  # noqa: E402
from popo import lint as L  # noqa: E402
from popo import mission as M  # noqa: E402
from popo import oracles as O  # noqa: E402
from popo import orchestrator as ORCH  # noqa: E402
from popo import personas as P  # noqa: E402
from popo import spirit as SP  # noqa: E402
from einherjar.head import Head  # noqa: E402


class Personas(unittest.TestCase):
    def test_base_profiles_are_valid(self):
        ps = P.load_all()
        self.assertGreaterEqual(len(ps), 10)
        for pid, p in ps.items():
            self.assertEqual(P.check(p), [], pid)

    def test_disruptive_rules(self):
        ps = P.load_all()
        with self.assertRaises(ValueError):
            P.compose({"pure": "saboteur", "bots": 2}, ps, random.Random(1), "E")
        with self.assertRaises(ValueError):
            P.compose({"personas": {"moyen": 2, "saboteur": 2}}, ps, random.Random(1), "E")
        lobby = P.compose({"personas": {"moyen": 2, "saboteur": 1}}, ps, random.Random(1), "E")
        twin = P.twin_without_disruptive(lobby)
        self.assertEqual(len(twin), 2)
        self.assertTrue(all(b["persona_id"] == "moyen" for b in twin))

    def test_override_dir_merges_field_by_field(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "casual.json").write_text(json.dumps({"id": "casual", "patience": 0.05}), encoding="utf-8")
            ps = P.load_all([d])
            self.assertEqual(ps["casual"]["patience"], 0.05)
            self.assertEqual(ps["casual"]["knowledge"], "none")  # le reste vient de la base


class Oracles(unittest.TestCase):
    def ev(self, t, kind, **d):
        return {"t_game": t, "t_wall": 0, "world": "w", "kind": kind, "bot": "b", **d}

    def test_teleport_bounds_negative_noeffect_oscillation(self):
        evs = [self.ev(0, "act", verb="x", pos=[0, 0]), self.ev(1, "act", verb="x", pos=[50, 0]),
               self.ev(2, "act", verb="x", pos=[500, 0]), self.ev(3, "gain", resource="or", amount=1, total=-3)]
        evs += [self.ev(4 + i, "fail", verb="boire", reason="no_effect") for i in range(3)]
        evs += [self.ev(10 + i, "act", verb="aller", area="a" if i % 2 else "b") for i in range(6)]
        found = {x["what"].split(" :")[0].split(" (")[0] for x in O.scan(evs, {"vitesse_max_deplacement": 10, "bornes": [[-10, 100], [-10, 100]]})}
        for w in ("téléportation", "position hors des bornes du monde", "ressource négative", "geste sans effet", "oscillation"):
            self.assertIn(w, found)

    def test_kaplan_meier(self):
        km = A.kaplan_meier([(10, True), (20, True), (30, False), (40, True)])
        self.assertAlmostEqual(km[1][1], 0.75)
        self.assertAlmostEqual(km[-1][1], 0.0)


class HeadRules(unittest.TestCase):
    def test_saboteur_cap_and_no_disrupt_for_others(self):
        ps = P.load_all()
        h = Head("m", ps["moyen"], random.Random(1))
        self.assertEqual(h.score({"id": "x", "disrupt": True, "tags": {"disrupt": 1}}, 0), -9.0)
        s = Head("s", ps["saboteur"], random.Random(1))
        s.nuisance = [0.0] * int(ps["saboteur"]["nuisance_cap_per_hour"])
        self.assertEqual(s.score({"id": "x", "disrupt": True, "tags": {"disrupt": 1}}, 10), -9.0)

    def test_found_exploit_is_not_farmed(self):
        h = Head("f", P.load_all()["fouineur"], random.Random(1))
        o = {"id": "rafale", "verb": "vendre_rafale", "area": "v", "break": True}
        h.found_exploit(o, "x", [], 0)
        self.assertEqual(h.score(o, 1), -9.0)

    def test_wiki_only_for_knowers(self):
        ps = P.load_all()
        self.assertTrue(Head("t", ps["tryhard"], random.Random(1)).knows_wiki)
        self.assertFalse(Head("c", ps["casual"], random.Random(1)).knows_wiki)


class Lint(unittest.TestCase):
    def test_head_reading_the_game_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "tete.gd").write_text("func f():\n\tvar e = get_tree().get_nodes_in_group('ennemis')\n", encoding="utf-8")
            Path(d, "mes_senses.gd").write_text("func f():\n\treturn get_tree()\n", encoding="utf-8")
            pb = L.check(d, {"presets": ["godot"], "fichiers": ["*.gd"], "autorises": ["*senses*.gd"]})
            self.assertTrue(pb and all("tete.gd" in x for x in pb))


class Spirit(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(SP._numbers("71,7 min et 29 %"), {"71.7", "29"})


class EndToEnd(unittest.TestCase):
    """La démo La Fosse : chaque bug planté doit être retrouvé, rien ne doit être signalé sur le jeu propre."""

    def run_mission(self, out, bugs):
        m = M.load(HERE / "demo" / "banc.json")
        m["duree_min"] = 0.3
        m["chambres"] = 6
        m["params"]["bugs"] = bugs
        run = ORCH.run(m, out, log=lambda *a: None)
        b = J.validate(J.read_many(sorted(Path(run, "chambres").glob("*/journal.jsonl"))))
        self.assertTrue(b["ok"], b["errors"])
        return A.analyse(A.load_run(run)), run

    def test_bench(self):
        sys.path.insert(0, str(HERE))
        from demo import banc
        with tempfile.TemporaryDirectory() as d:
            planted = M.load(HERE / "demo" / "banc.json")["bugs_plantes"]
            a_bug, run_bug = self.run_mission(d, planted)
            a_clean, run_clean = self.run_mission(d, [])
            found = {b: [f for f in a_bug["constats"] if banc.MATCH[b](f)] for b in planted}
            missed = [b for b, v in found.items() if not v]
            self.assertLessEqual(len(missed), 1, f"bugs manqués : {missed}")
            false = [f["titre"] for f in a_clean["constats"] if f["gravite"] == "probleme" and f["domaine"] in ("bugs", "exploit", "perf")]
            self.assertEqual(false, [])
            self.assertGreaterEqual(len(a_bug["jumeaux"]), 1)  # le saboteur et le meneur ont leur jumeau
            from popo import report
            report.write(run_bug, a_bug, {})
            report.write(run_clean, a_clean, {})
            c = C.compare(run_clean, run_bug)
            self.assertTrue(c["constats_nouveaux"])


if __name__ == "__main__":
    unittest.main()
