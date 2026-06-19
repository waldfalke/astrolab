# -*- coding: utf-8 -*-
"""Deterministic grand-report assembler — the back half of run_solar_gift.

Fills the EMPTY scaffold (artifacts/report-templates/grand-report.html) from:
  - prose.md       — the model's prose, in the [[SECTION]] contract below (the ONLY model input)
  - computed data  — techblocks built HERE from recipe outputs (numbers never come from the model)
  - real wheel SVGs— cleaned and embedded verbatim (the model never hand-draws a wheel)

TWIN SYMMETRY: both year axes expand as repeats — one WINDOW chapter per carrier_windows row
(time axis) and one SPHERE section per CHARGED sphere from sphere_summary (domain axis).

PROVENANCE: this is invoked by run_assemble_report.ps1, which stamps a run-dir + manifest with
source hashes. This file is pure transform: inputs in, HTML out, no hidden state.

prose.md CONTRACT (the model writes this; one marker per line starts a block, body until next marker):
  [[TITLE]]            one line
  [[COVER_KICKER]]     one line
  [[BIRTH_LINE]]       one line
  [[FORECAST_LINE]]    one line
  [[TLDR]]             paragraph(s)
  [[HOW_TO_READ]]      paragraph(s)
  [[PORTRAIT_H]]       one line (heading)
  [[PORTRAIT_BODY]]    paragraph(s)
  [[YEAR_H]]           one line
  [[YEAR_LEAD]]        one line
  [[YEAR_THEME]]       paragraph(s)
  [[WINDOW open=YYYY-MM-DD title=...]]   body — one per carrier window, keyed by window_open
  [[SPHERE key=work title=... kicker=...]] body — one per charged sphere, keyed by sphere key
  [[PHASE_NOTE]]       paragraph(s)  (optional — omit block to drop the phase section)
  [[SUPPORTS_BODY]]    paragraph(s)
  [[NOTE_METHOD]]      paragraph(s)
"""
import re, sys, csv, json, html, pathlib, argparse

GLYPH = {"sun":"☉","moon":"☽","mercury":"☿","venus":"♀","mars":"♂","jupiter":"♃","saturn":"♄",
         "uranus":"♅","neptune":"♆","pluto":"♇","north node":"☊","south node":"☋","chiron":"⚷",
         "ascendant":"ASC","midheaven":"MC","ic":"IC","descendant":"DSC"}
ASP = {"conjunction":"☌","opposition":"☍","trine":"△","square":"□","sextile":"⚹",
       "parallel":"∥","contraparallel":"⚯"}
RU_SIGN = {"Aries":"Овен","Taurus":"Телец","Gemini":"Близнецы","Cancer":"Рак","Leo":"Лев",
           "Virgo":"Дева","Libra":"Весы","Scorpio":"Скорпион","Sagittarius":"Стрелец",
           "Capricorn":"Козерог","Aquarius":"Водолей","Pisces":"Рыбы"}


def g(name):
    n = (name or "").lower().replace("natal:", "").replace("return:", "").strip()
    return GLYPH.get(n, name)


def read_csv(p):
    p = pathlib.Path(p)
    if not p.exists():
        return []
    with p.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def as_paras(text):
    """plain prose -> <p>…</p> blocks (blank-line separated). Leaves existing <p> alone."""
    t = (text or "").strip()
    if not t:
        return ""
    if t.lstrip().startswith("<"):
        return t
    blocks = re.split(r"\n\s*\n", t)
    return "\n".join("<p>" + html.escape(b.strip()).replace("\n", "<br>") + "</p>" for b in blocks if b.strip())


# ---------------------------------------------------------------- prose.md parser
def parse_prose(path):
    raw = pathlib.Path(path).read_text(encoding="utf-8")
    blocks, cur, buf = [], None, []
    for line in raw.splitlines():
        m = re.match(r"^\[\[([A-Z_]+)(.*)\]\]\s*$", line.strip())
        if m:
            if cur is not None:
                blocks.append((cur[0], cur[1], "\n".join(buf).strip()))
            cur, buf = (m.group(1), m.group(2).strip()), []
        else:
            buf.append(line)
    if cur is not None:
        blocks.append((cur[0], cur[1], "\n".join(buf).strip()))

    simple, windows, spheres = {}, {}, {}
    for tag, attr, body in blocks:
        if tag == "WINDOW":
            a = dict(re.findall(r"(\w+)=([^\s]+(?:\s+(?![\w]+=)[^\s]+)*)", attr))
            key = a.get("open", "")
            windows[key] = {"title": a.get("title", ""), "body": body}
        elif tag == "SPHERE":
            a = dict(re.findall(r"(\w+)=([^\s]+(?:\s+(?![\w]+=)[^\s]+)*)", attr))
            spheres[a.get("key", "")] = {"title": a.get("title", ""), "kicker": a.get("kicker", ""), "body": body}
        else:
            simple[tag] = body
    return simple, windows, spheres


# ---------------------------------------------------------------- deterministic techblocks
def clean_svg(path):
    p = pathlib.Path(path)
    if not p.exists():
        return '<div class="wheel-missing">[колесо не отрисовано]</div>'
    s = p.read_text(encoding="utf-8")
    s = re.sub(r'<svg([^>]*?)\swidth="[^"]*"', r'<svg\1', s, count=1)
    s = re.sub(r'<svg([^>]*?)\sheight="[^"]*"', r'<svg\1', s, count=1)
    if "preserveAspectRatio" not in s.split(">", 1)[0]:
        s = s.replace("<svg", '<svg preserveAspectRatio="xMidYMid meet"', 1)
    s = re.sub(r'<text[^>]*>[^<]*CATMEastrolab Renderer MVP[^<]*</text>', '', s)
    return s


def sr_techblock(sr_dir, profection):
    """SR angles + year-ruler + profection — all from compute, no model numbers."""
    pts = read_csv(pathlib.Path(sr_dir) / "04_return_chart_points.csv")
    ang = {p["point"].lower(): p for p in pts}
    bits = []
    for k, lab in (("ascendant", "ASC"), ("midheaven", "MC")):
        if k in ang:
            a = ang[k]
            bits.append(f"{lab} соляра — {RU_SIGN.get(a['sign'], a['sign'])} {float(a['degree']):.0f}°")
    if profection:
        pr = profection[0]
        lord = pr.get("lord_of_year", "")
        bits.append(f"хозяин года — {g(lord)} {RU_SIGN.get(pr.get('lord_natal_sign',''), pr.get('lord_natal_sign',''))} "
                    f"(профекция д.{pr.get('profected_house','')}, {RU_SIGN.get(pr.get('profected_sign',''), pr.get('profected_sign',''))})")
    return "; ".join(bits) + "." if bits else ""


def win_techblock(row, natal_house, natal_dign):
    """One carrier window -> a compute-traceable technique line."""
    tb = (row.get("transit_body") or "").lower()
    tgt = (row.get("natal_target") or "").lower()
    asp = (row.get("aspect") or "").lower()
    orb = row.get("tightest_orb_deg", "")
    try:
        orb_min = f"{float(orb) * 60:.0f}′"
    except ValueError:
        orb_min = orb
    peaks = (row.get("exact_dates") or "").split(";")
    peak = peaks[0].strip() if peaks else ""
    seg = f"{g(tb)} {ASP.get(asp, asp)} натал {g(tgt)}, орб {orb_min}"
    if peak:
        seg += f", точно {peak}"
    seg += f" (окно {row.get('window_open','')}–{row.get('window_close','')}"
    h = natal_house.get(tgt)
    if h:
        seg += f"; цель в д.{h}"
    d = natal_dign.get(tgt)
    if d and d not in ("перегрин", "peregrine"):
        seg += f", {d}"
    seg += ")."
    return seg


# ---------------------------------------------------------------- assembly
def fill_block(block, mapping):
    out = block
    for k, v in mapping.items():
        out = out.replace("{{" + k + "}}", v if v is not None else "")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--prose", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sr-dir", required=True)
    ap.add_argument("--carrier", required=True)
    ap.add_argument("--outputs", required=True)      # chart outputs/ (natal longitudes + cusps)
    ap.add_argument("--natal-dir", required=True)    # natal_failover run-dir (07_natal_dignities.csv)
    ap.add_argument("--sphere-summary", required=True)
    ap.add_argument("--renders", required=True)      # dir holding natal/sr/window wheel svgs (named)
    args = ap.parse_args()

    tpl = pathlib.Path(args.template).read_text(encoding="utf-8")
    simple, windows, spheres = parse_prose(args.prose)
    profection = read_csv(pathlib.Path(args.sr_dir) / "13_annual_profection.csv")
    carriers = read_csv(args.carrier)
    summ = read_csv(args.sphere_summary)

    # natal house per body — derive from longitudes + Placidus cusps (no extra recipe)
    cusps = read_csv(pathlib.Path(args.outputs) / "houses_placidus.csv")
    cuspd = {int(c["house"]): float(str(c["longitude"]).replace(",", ".")) for c in cusps}

    def house_of(lon):
        for h in range(1, 13):
            c1, c2 = cuspd.get(h), cuspd.get(h % 12 + 1)
            if c1 is None or c2 is None:
                continue
            inb = (c1 <= lon < c2) if c1 < c2 else (lon >= c1 or lon < c2)
            if inb:
                return h
        return ""
    natal_house = {}
    for r in read_csv(pathlib.Path(args.outputs) / "natal_longitudes.csv"):
        natal_house[(r.get("body") or "").lower()] = house_of(float(str(r["longitude"]).replace(",", ".")))
    # dignity per body — from the natal_failover run-dir (traditional)
    natal_dign = {}
    for r in read_csv(pathlib.Path(args.natal_dir) / "07_natal_dignities.csv"):
        natal_dign[(r.get("body") or "").lower()] = r.get("dignity", "")

    rend = pathlib.Path(args.renders)

    # split template into head / window-template / sphere-template / tail by the repeat sections
    # capture ONLY the <section>…</section> — never the trailing <!-- /repeat … --> marker. Including a
    # comment (esp. a multi-line one the regex truncates) duplicates an UNCLOSED <!-- per block, which
    # later comment-stripping then eats across into the next block.
    win_re = re.compile(r'(<section>\s*<div class="kicker"><span>Окно года.*?</section>)', re.S)
    sph_re = re.compile(r'(<section>\s*<div class="kicker"><span>Сфера жизни.*?</section>)', re.S)
    win_tpl_m = win_re.search(tpl)
    sph_tpl_m = sph_re.search(tpl)
    if not win_tpl_m or not sph_tpl_m:
        print("ERROR: could not locate WINDOW/SPHERE repeat blocks in template", file=sys.stderr)
        sys.exit(3)
    win_tpl = win_tpl_m.group(1)
    sph_tpl = sph_tpl_m.group(1)

    # expand WINDOWS (time axis) — only the windows the MODEL selected (one [[WINDOW]] per chosen
    # carrier), NOT every carrier row. The model curates which passes carry the year; the assembler
    # renders the chosen ones, keyed by window_open. Chronological.
    carrier_by_open = {r.get("window_open", ""): r for r in carriers}
    win_html = []
    for key in sorted(windows.keys()):
        pr = windows[key]
        row = carrier_by_open.get(key)
        if not row:
            print(f"  WARN: prose [[WINDOW open={key}]] has no matching carrier row — techblock skipped", file=sys.stderr)
            row = {"window_open": key, "window_close": "", "transit_body": "", "aspect": "", "natal_target": "", "tightest_orb_deg": "", "exact_dates": ""}
        dates = f"{row.get('window_open','')} – {row.get('window_close','')}"
        win_html.append(fill_block(win_tpl, {
            "WIN_DATES": html.escape(dates), "WIN_TITLE": html.escape(pr["title"]),
            "WIN_BIWHEEL_SVG": clean_svg(rend / f"window_{key}.svg"),
            "WIN_TECHBLOCK": html.escape(win_techblock(row, natal_house, natal_dign)) if row.get("transit_body") else "",
            "WIN_PROSE": as_paras(pr["body"]),
        }))

    # expand SPHERES (domain axis) — one per CHARGED sphere
    sph_html = []
    for s in summ:
        if str(s.get("charged", "")).lower() not in ("true", "1", "yes"):
            continue
        key = s.get("sphere", "")
        pr = spheres.get(key)
        if not pr or not pr.get("body", "").strip():
            print(f"  WARN: charged sphere '{key}' has no prose [[SPHERE key={key}]] — section skipped", file=sys.stderr)
            continue
        sph_html.append(fill_block(sph_tpl, {
            "SPH_KICKER": html.escape(pr["kicker"] or s.get("title", "")),
            "SPH_TITLE": html.escape(pr["title"] or s.get("title", "")),
            "SPH_BODY": as_paras(pr["body"]),
        }))

    out = tpl.replace(win_tpl, "\n".join(win_html)).replace(sph_tpl, "\n".join(sph_html))

    # simple tokens
    smap = {
        "TOKENS": "", "COVER_KICKER": html.escape(simple.get("COVER_KICKER", "")),
        "TITLE": html.escape(simple.get("TITLE", "")), "BIRTH_LINE": html.escape(simple.get("BIRTH_LINE", "")),
        "FORECAST_LINE": html.escape(simple.get("FORECAST_LINE", "")),
        "NATAL_WHEEL_SVG": clean_svg(rend / "natal.svg"),
        "TLDR": as_paras(simple.get("TLDR", "")), "HOW_TO_READ": as_paras(simple.get("HOW_TO_READ", "")),
        "PORTRAIT_H": html.escape(simple.get("PORTRAIT_H", "Портрет")), "PORTRAIT_BODY": as_paras(simple.get("PORTRAIT_BODY", "")),
        "YEAR_H": html.escape(simple.get("YEAR_H", "Карта года")), "YEAR_LEAD": html.escape(simple.get("YEAR_LEAD", "")),
        "SR_WHEEL_SVG": clean_svg(rend / "sr.svg"), "SR_TECHBLOCK": html.escape(sr_techblock(args.sr_dir, profection)),
        "YEAR_THEME": as_paras(simple.get("YEAR_THEME", "")),
        "PHASE_NOTE": as_paras(simple.get("PHASE_NOTE", "")), "SUPPORTS_BODY": as_paras(simple.get("SUPPORTS_BODY", "")),
        "NOTE_METHOD": as_paras(simple.get("NOTE_METHOD", "")),
    }
    out = fill_block(out, smap)

    # phase section: drop if model gave no PHASE_NOTE
    if not simple.get("PHASE_NOTE", "").strip():
        out = re.sub(r'<section>\s*<div class="kicker"><span>Дополнительный слой.*?</section>', "", out, flags=re.S)

    # strip all author-facing HTML comments (instructions, the TOKENS legend, §-refs) — not for the client
    out = re.sub(r"<!--.*?-->", "", out, flags=re.S)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", out)
    pathlib.Path(args.out).write_text(out, encoding="utf-8")
    print(f"assembled -> {args.out}  (windows={len(win_html)} spheres={len(sph_html)} leftover_tokens={len(set(leftover))})")
    if leftover:
        print("  unfilled: " + ", ".join(sorted(set(leftover))), file=sys.stderr)


if __name__ == "__main__":
    main()
