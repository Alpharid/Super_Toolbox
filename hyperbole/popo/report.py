"""Les sorties d'un run, dans <run>/rapport/ :

- brief_ia.md   : le résumé TRÈS court pour une IA (Claude) : constats + preuves + comment rejouer. Lire celui-là d'abord.
- rapport.md    : le rapport complet en Markdown.
- rapport.html  : la page autonome pour le propriétaire (graphiques SVG, clair/sombre, aucune dépendance).
- summary.json  : toutes les mesures (machine) ; sert à `popo compare`.
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

SEV = {"probleme": "Problème", "surveiller": "À surveiller", "info": "Info"}
PALETTE = ["#2f6f8f", "#b5562f", "#5b8a3c", "#8a4f9e", "#c08a1e", "#3f7f7a", "#9e3f5c", "#6b6b6b", "#1f4f9e", "#7a5a2f"]


def _fmt(x, unit=""):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{x}{unit}"


def _pct(x):
    return "–" if x is None else f"{int(round(x * 100))} %"


def _rejouer(r):
    if not r:
        return ""
    parts = []
    for k in ("world", "seed", "t_game"):
        if r.get(k) is not None:
            parts.append(f"{k}={r[k]}")
    return " · ".join(parts)


# ------------------------------------------------------------------ Markdown
def brief_md(a: dict, stories: dict, triage) -> str:
    v = a["volume"]
    L = [f"# Hyperbole — brief IA — {a['run']}", "",
         f"Jeu : {a['mission']} · version {a.get('version') or '?'} · objectifs {', '.join(a.get('objectifs') or [])}",
         f"Volume : {v['einherjar']} Einherjar, {v['chambres']} chambres, {v['heures_bot']} h-bot de jeu, vitesse médiane x{v['vitesse_mediane']}, "
         f"{v['heures_bot_par_heure_pc']} h-bot par heure de PC.", "",
         "Les chiffres sont MESURÉS par des bots (rang relatif entre profils et entre versions, pas une vérité humaine).",
         "Rejouer un constat : `hyperbole rejouer <run> <world>` (même graine, même lobby).", "", "## Constats (du plus grave)"]
    for f in a["constats"][:25]:
        L.append(f"- [{SEV[f['gravite']]}|{f['domaine']}] {f['titre']} — {f['preuve']}" + (f" ({_rejouer(f['rejouer'])})" if f.get("rejouer") else ""))
    if len(a["constats"]) > 25:
        L.append(f"- … {len(a['constats']) - 25} autres dans rapport.md")
    if triage:
        L += ["", "## Tri (Esprit, hypothèses à vérifier)"]
        for g in triage:
            L.append(f"- P{g.get('priorite', '?')} : {', '.join(g.get('titres', []))[:200]} → hypothèse : {g.get('hypothese')} ; test : {g.get('test')}")
    L += ["", "## Profils (médianes)", "", "| profil | bots | min joués | victoires | morts/h | ennui | frustr./h | variété | ratés | moments/h | abandon tôt |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for pid, p in sorted(a["personas"].items()):
        L.append(f"| {pid} | {p['bots']} | {_fmt(p['play_min'])} | {_pct(p['success'])} | {_fmt(p['deaths_h'])} | {_pct(p['downtime'])} | "
                 f"{_fmt(p['frustration_h'])} | {_fmt(p['variety'])} | {_pct(p['fail_rate'])} | {_fmt(p['moments_h'])} | {_pct(p['early_quit'])} |")
    return "\n".join(L) + "\n"


def full_md(a: dict, stories: dict, triage, spirit_log) -> str:
    L = [brief_md(a, stories, triage).replace("— brief IA —", "— rapport —", 1)]
    if a["etapes"]:
        L += ["## Étapes (minutes de jeu depuis l'arrivée, médiane ; part qui l'atteint)", ""]
        ps = sorted({p for m in a["etapes"].values() for p in m["par_profil"]})
        L += ["| étape | " + " | ".join(ps) + " |", "|---|" + "---|" * len(ps)]
        for m, info in a["etapes"].items():
            L.append(f"| {m} | " + " | ".join(f"{_fmt(info['par_profil'][p]['median_min'])} ({_pct(info['par_profil'][p]['atteint'])})"
                                             if p in info["par_profil"] else "–" for p in ps) + " |")
        L.append("")
    if a["menaces"]:
        L += ["## Défi par menace", "", "| menace | victoires | défaites | succès |", "|---|---|---|---|"]
        L += [f"| {t} | {x['victoires']} | {x['defaites']} | {_pct(x['succes'])} |" for t, x in a["menaces"].items()]
        L.append("")
    if a["morts"]:
        L += ["## Causes de mort", ""] + [f"- {c} : {n}" for c, n in a["morts"].items()] + [""]
    if a["apprentissage"]:
        L += ["## Apprentissage des signaux (minutes, part qui comprend)", ""]
        for cue, by in a["apprentissage"].items():
            L.append(f"- **{cue}** : " + " ; ".join(f"{p} {_fmt(v['median_min'])} min ({_pct(v['part'])})" for p, v in by.items()))
        L.append("")
    if a.get("mecaniques"):
        L += ["## Mécaniques (1er succès, ratés début → fin)", ""]
        for verb, by in a["mecaniques"].items():
            L.append(f"- **{verb}** : " + " ; ".join(f"{p} {_fmt(v['premier_succes_min'])} min, {_pct(v['rate_debut'])} → {_pct(v['rate_fin'])}" for p, v in by.items()))
        L.append("")
    if a["economie"]:
        L += ["## Économie (par heure-bot)", "", "| ressource | gagné/h | dépensé/h | net/h | sources |", "|---|---|---|---|---|"]
        L += [f"| {r} | {e['gain_h']} | {e['spend_h']} | {e['net_h']} | {e['sources']} |" for r, e in a["economie"].items()]
        L.append("")
    if a["jumeaux"]:
        L += ["## Effet du saboteur / meneur sur les autres (lobby jumeau, même graine)", "",
              "| rôle | frustr./h avec → sans | ennui | moments/h | morts/h |", "|---|---|---|---|---|"]
        for t in a["jumeaux"]:
            L.append(f"| {t['role']} | {t['frustration_h']['avec']} → {t['frustration_h']['sans']} | {t['downtime']['avec']} → {t['downtime']['sans']} | "
                     f"{t['moments_h']['avec']} → {t['moments_h']['sans']} | {t['deaths_h']['avec']} → {t['deaths_h']['sans']} |")
        L.append("")
    for title, key in (("Variantes (A/B)", "variantes"), ("Voies : chambre accélérée vs x1", "voies")):
        if a.get(key):
            L += [f"## {title}", "", "| groupe | bots | victoires | morts/h | frustr./h | ennui | moments/h | variété | ratés |", "|---|---|---|---|---|---|---|---|---|"]
            for k, g in a[key].items():
                L.append(f"| {k} | {g['bots']} | {_pct(g['success'])} | {g['deaths_h']} | {g['frustration_h']} | {_pct(g['downtime'])} | {g['moments_h']} | {g['variety']} | {_pct(g['fail_rate'])} |")
            L.append("")
    if a["erreurs"]:
        L += ["## Erreurs du moteur (groupées)", ""] + [f"- ×{e['n']} [{e['niveau']}] `{e['message']}` ({_rejouer(e['premier'])})" for e in a["erreurs"][:30]] + [""]
    if a["fuites"]:
        L += ["## Fuites probables", ""] + [f"- {l['world']} : {l['mesure']} {l['de']} → {l['a']} (+{l['pct_h']} %/h)" for l in a["fuites"]] + [""]
    L += ["## Récits des profils", ""]
    for pid, st in stories.items():
        L.append(f"**{pid}** — " + " ".join(s["texte"] for s in st))
        L.append("")
    v = a["volume"]
    L += ["## Chambres", "", "| chambre | voie | graine | variante | jumeau de | h de jeu | vitesse | fin |", "|---|---|---|---|---|---|---|---|"]
    for w, c in a["chambres"].items():
        L.append(f"| {w} | {c['lane']} | {c['seed']} | {c['variant'] or ''} | {c['twin_of'] or ''} | {round(c['t_game_s'] / 3600, 2)} | x{c['speed']} | {c['reason'] or ''}{' CRASH' if c['crashed'] else ''} |")
    if spirit_log:
        L += ["", "Esprit : " + " ; ".join(spirit_log)]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ SVG
def _svg_retention(personas: dict) -> str:
    W, H, P = 640, 260, 36
    tmax = max([t for p in personas.values() for t, _ in p["retention"]] + [1])
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Rétention par profil">']
    for i in range(0, 5):
        y = P + (H - 2 * P) * i / 4
        out.append(f'<line x1="{P}" x2="{W - 10}" y1="{y}" y2="{y}" class="grid"/><text x="4" y="{y + 4}" class="ax">{100 - 25 * i}%</text>')
    out.append(f'<text x="{W - 10}" y="{H - 8}" class="ax" text-anchor="end">{round(tmax)} min</text><text x="{P}" y="{H - 8}" class="ax">0</text>')
    legend = []
    for i, (pid, p) in enumerate(sorted(personas.items())):
        col = PALETTE[i % len(PALETTE)]
        pts, last = [], 1.0
        for t, s in p["retention"]:
            x = P + (W - P - 10) * t / tmax
            pts.append(f"{x:.1f},{P + (H - 2 * P) * (1 - last):.1f}")
            pts.append(f"{x:.1f},{P + (H - 2 * P) * (1 - s):.1f}")
            last = s
        pts.append(f"{W - 10},{P + (H - 2 * P) * (1 - last):.1f}")
        out.append(f'<polyline fill="none" stroke="{col}" stroke-width="2" points="{" ".join(pts)}"/>')
        legend.append(f'<span><i style="background:{col}"></i>{html.escape(pid)}</span>')
    out.append("</svg>")
    return "".join(out) + f'<div class="legend">{"".join(legend)}</div>'


def _svg_bars(items: dict, unit="") -> str:
    if not items:
        return "<p class='muted'>Rien de mesuré.</p>"
    mx = max(items.values()) or 1
    rows = []
    for k, v in list(items.items())[:12]:
        rows.append(f'<div class="bar"><span class="lbl">{html.escape(str(k))}</span><span class="track"><span class="fill" style="width:{100 * v / mx:.1f}%"></span></span><span class="num">{v}{unit}</span></div>')
    return "".join(rows)


def _svg_grid(carte: dict, stuck: list, size) -> str:
    if not carte:
        return "<p class='muted'>Aucune position dans les journaux (champ pos).</p>"
    cells = [tuple(map(int, k.split(","))) for k in carte]
    xs, ys = [c[0] for c in cells], [c[1] for c in cells]
    x0, y0, nx, ny = min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    s = max(4, min(18, int(560 / max(nx, ny))))
    mx = max(carte.values()) or 1
    stuck_cells = {tuple(b["cellule"]): b["bots"] for b in stuck if isinstance(b["cellule"], list)}
    out = [f'<svg viewBox="0 0 {nx * s} {ny * s}" style="max-width:{nx * s}px" role="img" aria-label="Carte de couverture">']
    for k, n in carte.items():
        x, y = map(int, k.split(","))
        out.append(f'<rect x="{(x - x0) * s}" y="{(y - y0) * s}" width="{s - 1}" height="{s - 1}" class="cov" style="opacity:{0.15 + 0.85 * n / mx:.2f}"><title>{k} : {n} Einherjar</title></rect>')
    for (x, y), n in stuck_cells.items():
        out.append(f'<rect x="{(x - x0) * s}" y="{(y - y0) * s}" width="{s - 1}" height="{s - 1}" class="stk"><title>blocage {x},{y} : {n} Einherjar</title></rect>')
    out.append("</svg>")
    return "".join(out) + f'<p class="muted">Cellules de {size} unités ; plus foncé = plus visité ; cadre rouge = blocages. Zone blanche = jamais vue.</p>'


CSS = """
:root{--bg:#f6f4ef;--panel:#fffdf8;--ink:#1d1d1b;--muted:#6a675f;--line:#ddd8cc;--accent:#2f6f8f;--bad:#b23a2a;--warn:#a8690f;--info:#4b6b8a;--cov:#2f6f8f}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15171a;--panel:#1d2024;--ink:#e8e5dd;--muted:#9a968c;--line:#33373d;--accent:#6fb1d1;--bad:#e2705e;--warn:#e0a548;--info:#8fb0cf;--cov:#6fb1d1}}
:root[data-theme="dark"]{--bg:#15171a;--panel:#1d2024;--ink:#e8e5dd;--muted:#9a968c;--line:#33373d;--accent:#6fb1d1;--bad:#e2705e;--warn:#e0a548;--info:#8fb0cf;--cov:#6fb1d1}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 64px}h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 10px;border-bottom:1px solid var(--line);padding-bottom:4px}
.muted{color:var(--muted)}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:16px 0}
.kpi{background:var(--panel);border:1px solid var(--line);padding:10px 12px}.kpi b{display:block;font:600 22px ui-monospace,Consolas,monospace}
.f{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--info);padding:8px 12px;margin:6px 0}
.f.probleme{border-left-color:var(--bad)}.f.surveiller{border-left-color:var(--warn)}.f small{color:var(--muted);display:block}
.chip{font:600 11px ui-monospace,Consolas,monospace;text-transform:uppercase;margin-right:6px;color:var(--muted)}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;background:var(--panel)}th,td{border:1px solid var(--line);padding:4px 7px;text-align:left}
td.n{font-family:ui-monospace,Consolas,monospace;text-align:right}svg{width:100%;height:auto}.grid{stroke:var(--line)}.ax{fill:var(--muted);font-size:11px}
.legend span{margin-right:12px;font-size:13px}.legend i{display:inline-block;width:10px;height:10px;margin-right:4px}
.bar{display:grid;grid-template-columns:180px 1fr 60px;gap:8px;align-items:center;font-size:13px;margin:3px 0}.track{background:var(--line);height:10px}
.fill{display:block;height:10px;background:var(--accent)}.num{font-family:ui-monospace,Consolas,monospace;text-align:right}
.cov{fill:var(--cov)}.stk{fill:none;stroke:var(--bad);stroke-width:2}.story{background:var(--panel);border:1px solid var(--line);padding:8px 12px;margin:6px 0}
@media (max-width:600px){.bar{grid-template-columns:110px 1fr 50px}}
"""


def page(a: dict, stories: dict, triage) -> str:
    e = html.escape
    v = a["volume"]
    counts = {k: sum(1 for f in a["constats"] if f["gravite"] == k) for k in SEV}
    kp = [("Einherjar", v["einherjar"]), ("Heures-bot de jeu", v["heures_bot"]), ("Vitesse médiane", f"x{v['vitesse_mediane']}"),
          ("h-bot / h de PC", v["heures_bot_par_heure_pc"]), ("Problèmes", counts["probleme"]), ("À surveiller", counts["surveiller"])]
    H = [f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
         f"<title>Hyperbole — {e(a['mission'])}</title><style>{CSS}</style></head><body><main>",
         f"<h1>Hyperbole · {e(a['mission'])}</h1><div class='muted'>Run {e(a['run'])} · version {e(str(a.get('version') or '?'))} · objectifs {e(', '.join(a.get('objectifs') or []))}</div>",
         "<div class='kpis'>" + "".join(f"<div class='kpi'><span class='muted'>{e(k)}</span><b>{e(str(x))}</b></div>" for k, x in kp) + "</div>",
         "<p class='muted'>Tout est mesuré par des bots qui jouent sans tricher. Les chiffres se lisent en comparaison (entre profils, entre versions), pas comme l'avis de vrais joueurs.</p>",
         "<h2>Constats</h2>"]
    for f in a["constats"][:60]:
        H.append(f"<div class='f {f['gravite']}'><span class='chip'>{SEV[f['gravite']]} · {e(f['domaine'])}</span>{e(f['titre'])}"
                 f"<small>{e(str(f['preuve']))}{(' · rejouer : ' + e(_rejouer(f['rejouer']))) if f.get('rejouer') else ''}</small></div>")
    if not a["constats"]:
        H.append("<p>Aucun constat : rien n'a dépassé les seuils.</p>")
    if triage:
        H.append("<h2>Tri de l'Esprit (hypothèses)</h2><ul>" + "".join(
            f"<li><b>P{e(str(g.get('priorite')))}</b> {e(', '.join(g.get('titres', [])))} — <i>hypothèse :</i> {e(str(g.get('hypothese')))} · <i>test :</i> {e(str(g.get('test')))}</li>" for g in triage) + "</ul>")
    H.append("<h2>Profils</h2><div class='scroll'><table><tr><th>profil</th><th>bots</th><th>min joués</th><th>victoires</th><th>morts/h</th><th>ennui</th><th>frustr./h</th><th>variété</th><th>ratés</th><th>moments/h</th><th>abandon tôt</th></tr>")
    for pid, p in sorted(a["personas"].items()):
        H.append(f"<tr><td>{e(pid)}</td><td class=n>{p['bots']}</td><td class=n>{_fmt(p['play_min'])}</td><td class=n>{_pct(p['success'])}</td><td class=n>{_fmt(p['deaths_h'])}</td>"
                 f"<td class=n>{_pct(p['downtime'])}</td><td class=n>{_fmt(p['frustration_h'])}</td><td class=n>{_fmt(p['variety'])}</td><td class=n>{_pct(p['fail_rate'])}</td>"
                 f"<td class=n>{_fmt(p['moments_h'])}</td><td class=n>{_pct(p['early_quit'])}</td></tr>")
    H.append("</table></div>")
    H.append("<h2>Rétention (part des Einherjar encore en jeu)</h2>" + _svg_retention(a["personas"]))
    H.append("<h2>Récits</h2>" + "".join(f"<div class='story'><b>{e(pid)}</b> — {e(' '.join(s['texte'] for s in st))}</div>" for pid, st in stories.items()))
    H.append("<h2>Causes de mort</h2>" + _svg_bars(a["morts"]))
    if a["menaces"]:
        H.append("<h2>Victoires par menace</h2>" + _svg_bars({k: int(round((x["succes"] or 0) * 100)) for k, x in a["menaces"].items() if x["succes"] is not None}, " %"))
    H.append("<h2>Couverture et blocages</h2>" + _svg_grid(a["couverture"]["carte"], a["blocages"], a["couverture"]["taille"]))
    if a["etapes"]:
        ps = sorted({p for m in a["etapes"].values() for p in m["par_profil"]})
        H.append("<h2>Étapes (min de jeu, part qui l'atteint)</h2><div class='scroll'><table><tr><th>étape</th>" + "".join(f"<th>{e(p)}</th>" for p in ps) + "</tr>")
        for m, info in a["etapes"].items():
            H.append(f"<tr><td>{e(m)}</td>" + "".join(f"<td class=n>{_fmt(info['par_profil'][p]['median_min'])} ({_pct(info['par_profil'][p]['atteint'])})</td>" if p in info["par_profil"] else "<td class=n>–</td>" for p in ps) + "</tr>")
        H.append("</table></div>")
    if a["economie"]:
        H.append("<h2>Économie (par heure-bot)</h2><div class='scroll'><table><tr><th>ressource</th><th>gagné/h</th><th>dépensé/h</th><th>net/h</th></tr>" +
                 "".join(f"<tr><td>{e(r)}</td><td class=n>{x['gain_h']}</td><td class=n>{x['spend_h']}</td><td class=n>{x['net_h']}</td></tr>" for r, x in a["economie"].items()) + "</table></div>")
    if a["jumeaux"]:
        H.append("<h2>Effet du saboteur / meneur (jumeau sans lui, même graine)</h2><div class='scroll'><table><tr><th>rôle</th><th>frustr./h</th><th>ennui</th><th>moments/h</th><th>morts/h</th></tr>" +
                 "".join(f"<tr><td>{e(t['role'])}</td>" + "".join(f"<td class=n>{t[k]['avec']} → {t[k]['sans']}</td>" for k in ("frustration_h", "downtime", "moments_h", "deaths_h")) + "</tr>" for t in a["jumeaux"]) + "</table></div>")
    for title, key in (("Variantes A/B", "variantes"), ("Chambre accélérée vs x1", "voies")):
        if a.get(key):
            H.append(f"<h2>{title}</h2><div class='scroll'><table><tr><th>groupe</th><th>bots</th><th>victoires</th><th>morts/h</th><th>frustr./h</th><th>ennui</th><th>moments/h</th></tr>" +
                     "".join(f"<tr><td>{e(k)}</td><td class=n>{g['bots']}</td><td class=n>{_pct(g['success'])}</td><td class=n>{g['deaths_h']}</td><td class=n>{g['frustration_h']}</td><td class=n>{_pct(g['downtime'])}</td><td class=n>{g['moments_h']}</td></tr>" for k, g in a[key].items()) + "</table></div>")
    H.append("<h2>Chambres</h2><div class='scroll'><table><tr><th>chambre</th><th>voie</th><th>graine</th><th>variante</th><th>h de jeu</th><th>vitesse</th><th>fin</th></tr>" +
             "".join(f"<tr><td>{e(w)}</td><td>{c['lane']}</td><td class=n>{c['seed']}</td><td>{e(str(c['variant'] or ''))}</td><td class=n>{round(c['t_game_s'] / 3600, 2)}</td><td class=n>x{c['speed']}</td><td>{e(str(c['reason'] or ''))}{' <b>CRASH</b>' if c['crashed'] else ''}</td></tr>" for w, c in a["chambres"].items()) + "</table></div>")
    H.append("<p class='muted'>Hyperbole — Super_Toolbox. Mesures complètes : summary.json · résumé pour IA : brief_ia.md.</p></main></body></html>")
    return "\n".join(H)


def write(run_dir: Path, a: dict, stories: dict, triage=None, spirit_log=None) -> Path:
    out = Path(run_dir) / "rapport"
    out.mkdir(exist_ok=True)
    (out / "summary.json").write_text(json.dumps({"analyse": a, "recits": stories, "tri": triage}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (out / "brief_ia.md").write_text(brief_md(a, stories, triage), encoding="utf-8")
    (out / "rapport.md").write_text(full_md(a, stories, triage, spirit_log or []), encoding="utf-8")
    (out / "rapport.html").write_text(page(a, stories, triage), encoding="utf-8")
    return out
