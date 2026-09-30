#!/usr/bin/env python3
"""Test d'acceptació de la cadena d'astrometria: llegeix els productes del WORK
i de l'OUT (segons comu.py i les variables d'entorn ESTRELLES_WORK /
ESTRELLES_OUT / APOD_OUT) i afirma la taula comu.ACCEPTACIO amb les seves
toleràncies. Només lectura.

Per cada línia imprimeix ✓ (dins tolerància), ✗ (fora) o «– no trobat» (falta el
producte que la sosté; no peta). Surt 0 si cap línia és ✗ i 2 si n'hi ha alguna.
Amb --estricte, un «no trobat» també fa sortir 2.

Productes que llegeix (WORK primer, després OUT):
    work(sony)/catalog_sony.txt                fonts Sony (38)
    work(vixen)/catalog_vixen_fonts.csv        fonts R6 (classe A + B = 24)
    work(xmatch)/final_match_{sony,r6}.csv     identificades (38 / 22), residu mediana, V límit
    work(xmatch)/final_solution.json           escala i PA nord (solució *_radial)
    work(xmatch)/zp2.json                      ZP☉
    work(xmatch)/corona2.csv                   B/B☉ (fac amb color) i quocient R6/Sony 1,15–3 R☉
    work(xmatch)/wings_{sony,r6}.npz | wings.json   fins on són fiables les ales
    WORK/_registres/deflexio.log (el deixa pipeline_estrelles.sh) o, si falta, l'stdout
        de deflexio.py executat aquí mateix (~2 s, només lectura)   σ(ε)
    apod()/retalls_estrelles.json | WORK/_registres/animacio.log   deflexió de HIP 46345
"""
from __future__ import annotations

import csv
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
import comu  # noqa: E402

AQUI = Path(__file__).resolve().parent
WORK = comu.ESTRELLES_WORK
OUT = comu.ESTRELLES_OUT
APOD = comu.APOD_OUT
REG = WORK / "_registres"
ACC = comu.ACCEPTACIO
ESTRICTE = "--estricte" in sys.argv[1:]

BINS_ALES = [0, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 13, 17, 22, 30, 40, 55, 75, 100, 130, 150]

linies: list[tuple[str, str]] = []   # (estat, text)


def troba(*cands: Path) -> Path | None:
    for p in cands:
        if p is not None and p.exists():
            return p
    return None


def ok(nom: str, text: str) -> None:
    linies.append(("✓", f"{nom}: {text}"))


def ko(nom: str, text: str) -> None:
    linies.append(("✗", f"{nom}: {text}"))


def falta(nom: str, que: str) -> None:
    linies.append(("–", f"{nom}: no trobat ({que})"))


def afirma_exacte(nom: str, obtingut, esperat, font: str) -> None:
    (ok if obtingut == esperat else ko)(nom, f"{obtingut} (esperat {esperat}) [{font}]")


def afirma_tol(nom: str, obtingut: float, esperat: float, tol: float, font: str,
               fmt: str = "{:.4f}", relatiu: bool = False) -> None:
    d = abs(obtingut - esperat)
    lim = tol * abs(esperat) if relatiu else tol
    detall = (f"{fmt.format(obtingut)} (esperat {fmt.format(esperat)} ± {100*tol:.0f} %"
              if relatiu else f"{fmt.format(obtingut)} (esperat {fmt.format(esperat)} ± {tol:g}")
    (ok if d <= lim else ko)(nom, f"{detall}; diferència {d:.2e}) [{font}]")


def llegeix_csv(p: Path) -> list[dict]:
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def curt(p: Path) -> str:
    try:
        return str(p.relative_to(WORK.parent))
    except ValueError:
        return str(p)


# ------------------------------------------------------------------ 1. fonts cegues
p = troba(WORK / "sony/catalog_sony.txt", OUT / "catalog_sony.txt")
if p:
    n = sum(1 for l in p.read_text().splitlines() if l.strip() and not l.startswith("#"))
    afirma_exacte("fonts Sony", n, ACC["fonts_sony"], curt(p))
else:
    falta("fonts Sony", "catalog_sony.txt")

p = troba(WORK / "vixen/catalog_vixen_fonts.csv", OUT / "catalog_vixen_fonts.csv")
if p:
    files = llegeix_csv(p)
    na = sum(1 for r in files if r.get("classe") == "A")
    nb = sum(1 for r in files if r.get("classe") == "B")
    afirma_exacte(f"fonts R6 (classe A {na} + B {nb})", na + nb, ACC["fonts_r6"], curt(p))
else:
    falta("fonts R6", "catalog_vixen_fonts.csv")

# ------------------------------------------------------------------ 2. identificades, residu, V límit
fm = {}
for tag, clau in (("sony", "identificades_sony"), ("r6", "identificades_r6")):
    p = troba(WORK / f"xmatch/final_match_{tag}.csv", OUT / f"final_match_{tag}.csv")
    if not p:
        falta(f"identificades {tag}", f"final_match_{tag}.csv")
        falta(f"residu mediana {tag}", f"final_match_{tag}.csv")
        continue
    fm[tag] = llegeix_csv(p)
    afirma_exacte(f"identificades {tag}", len(fm[tag]), ACC[clau], curt(p))
    try:
        res = [float(r["resid"]) for r in fm[tag] if r.get("resid") not in (None, "")]
        e, tol = ACC[f"residu_med_px_{tag}"]
        afirma_tol(f"residu mediana {tag} (px)", median(res), e, tol, curt(p), "{:.3f}")
    except (KeyError, ValueError) as exc:
        falta(f"residu mediana {tag}", f"columna resid: {exc}")

if "sony" in fm:
    try:
        vmax = max(float(r["V"]) for r in fm["sony"] if r.get("V") not in (None, ""))
        afirma_tol("V límit Sony (màx V identificada)", vmax, ACC["mag_limit"], 0.005,
                   "final_match_sony.csv", "{:.2f}")
    except (KeyError, ValueError) as exc:
        falta("V límit Sony", f"columna V: {exc}")
else:
    falta("V límit Sony", "final_match_sony.csv")

# ------------------------------------------------------------------ 3. placa
p = troba(WORK / "xmatch/final_solution.json", OUT / "final_solution.json")
if p:
    sol = json.load(open(p))
    for tag in ("sony", "r6"):
        s = sol.get(f"{tag}_radial") or sol.get(tag)
        if not s:
            falta(f"escala {tag}", f"clau {tag}_radial a {curt(p)}")
            continue
        quina = "radial" if f"{tag}_radial" in sol else "lineal"
        e, tol = ACC[f"escala_{tag}"]
        afirma_tol(f"escala {tag} (″/px, {quina})", float(s["scale"]), e, tol, curt(p))
        e, tol = ACC[f"pa_nord_{tag}"]
        afirma_tol(f"PA nord {tag} (°)", float(s["pa_north"]), e, tol, curt(p), "{:.3f}")
else:
    for tag in ("sony", "r6"):
        falta(f"escala {tag}", "final_solution.json")
        falta(f"PA nord {tag}", "final_solution.json")

# ------------------------------------------------------------------ 4. ZP
p = troba(WORK / "xmatch/zp2.json", OUT / "zp2.json")
if p:
    zp2 = json.load(open(p))
    for tag in ("sony", "r6"):
        if tag in zp2 and "ZPsun" in zp2[tag]:
            e, tol = ACC[f"zp_{tag}"]
            afirma_tol(f"ZP☉ {tag}", float(zp2[tag]["ZPsun"]), e, tol,
                       f"{curt(p)}, ±{zp2[tag].get('eZPsun', float('nan')):.3f}", "{:.3f}")
        else:
            falta(f"ZP☉ {tag}", f"clau {tag}.ZPsun a {curt(p)}")
else:
    for tag in ("sony", "r6"):
        falta(f"ZP☉ {tag}", "zp2.json")

# ------------------------------------------------------------------ 5. B/B☉ i quocient de corona
p = troba(WORK / "xmatch/corona2.csv", OUT / "corona2.csv")
if p:
    cor = llegeix_csv(p)
    if cor and "fac" not in cor[0]:
        falta("B/B☉", f"columna fac a {curt(p)}")
    else:
        for tag in ("sony", "r6"):
            facs = sorted({float(r["fac"]) for r in cor if r["tren"] == tag})
            if not facs:
                falta(f"B/B☉ {tag}", f"cap fila {tag} a {curt(p)}")
                continue
            e, tol = ACC[f"b_bsol_{tag}"]
            nota = "fac amb color" if "fac_nocolor" in cor[0] else "fac (format vell, sense columna fac_nocolor)"
            afirma_tol(f"B/B☉ {tag} per (ADU/s, píxel verd)", facs[0], e, tol,
                       f"{curt(p)}, {nota}", "{:.4e}", relatiu=True)
        # quocient R6/Sony a 1,15–3 R☉: mateixa fórmula que corona2.py (tres exposicions, 7 radis, mediana)
        cols = [c for c in cor[0] if re.fullmatch(r"r\d+(\.\d+)?", c)]
        cols = sorted(cols, key=lambda c: float(c[1:]))[:7]
        rat = []
        for e_exp in (1 / 30., 1 / 8., 1 / 4.):
            a = [r for r in cor if r["tren"] == "sony" and math.isclose(float(r["exp"]), e_exp, rel_tol=1e-6)]
            b = [r for r in cor if r["tren"] == "r6" and math.isclose(float(r["exp"]), e_exp, rel_tol=1e-6)]
            if not a or not b:
                continue
            a, b = a[0], b[0]
            for c in cols:
                try:
                    va, vb = float(a[c]), float(b[c])
                except ValueError:
                    continue
                if math.isfinite(va) and math.isfinite(vb) and va != 0:
                    rat.append(vb * float(b["fac"]) / (va * float(a["fac"])))
        if rat and cols:
            e, tol = ACC["quocient_corona_r6_sony"]
            afirma_tol(f"quocient corona R6/Sony a {cols[0][1:]}–{cols[-1][1:]} R☉ (mediana de {len(rat)})",
                       median(rat), e, tol, curt(p), "{:.3f}")
        else:
            falta("quocient corona R6/Sony", f"files sony/r6 a 1/30, 1/8, 1/4 s a {curt(p)}")
else:
    for tag in ("sony", "r6"):
        falta(f"B/B☉ {tag}", "corona2.csv")
    falta("quocient corona R6/Sony", "corona2.csv")

# ------------------------------------------------------------------ 6. ales de la PSF
for tag in ("sony", "r6"):
    r = prof = bins = None
    pz = troba(WORK / f"xmatch/wings_{tag}.npz")
    pj = troba(WORK / "xmatch/wings.json", OUT / "wings.json")
    try:
        if pz:
            import numpy as np
            z = np.load(pz)
            prof = [float(v) for v in z["prof"]]
            bins = [float(v) for v in z["bins"]] if "bins" in z.files else BINS_ALES
            font = curt(pz)
        elif pj:
            w = json.load(open(pj))
            if tag in w:
                prof = [float(v) for v in w[tag]["prof"]]
                bins = BINS_ALES
                font = f"{curt(pj)} (BINS de wings.py)"
    except Exception as exc:  # noqa: BLE001
        prof = None
        falta(f"ales PSF {tag}", f"no es pot llegir: {exc}")
        continue
    if prof is None:
        falta(f"ales PSF {tag}", "wings_*.npz / wings.json")
        continue
    cum, s = [], 0.0
    for i, pr in enumerate(prof):
        s += pr * math.pi * (bins[i + 1] ** 2 - bins[i] ** 2)
        cum.append(s)
    # «fiable fins a»: l'últim radi on el flux acumulat encara no passa d'1,05 (Sony 1,045 a 13 px; R6 0,963 a 30 px)
    fiable = None
    for i, c in enumerate(cum):
        if c <= 1.05:
            fiable = bins[i + 1]
        else:
            break
    e = ACC[f"ales_psf_px_{tag}"]
    ci = cum[bins.index(e) - 1] if e in bins else float("nan")
    (ok if fiable == e else ko)(f"ales PSF {tag} fiables fins a (px)",
                                f"{fiable} (esperat {e}; flux acumulat a {e} px = {ci:.3f}) [{font}]")

# ------------------------------------------------------------------ 7. deflexió: σ(ε)
def sortida_deflexio() -> tuple[str | None, str]:
    p = troba(REG / "deflexio.log")
    if p:
        return p.read_text(errors="replace"), curt(p)
    scr = AQUI / "deflexio/deflexio.py"
    csvs = [OUT / "estrelles_sony.csv", OUT / "estrelles_r6.csv"]
    if scr.exists() and all(c.exists() for c in csvs):
        try:
            r = subprocess.run([sys.executable, str(scr)], capture_output=True, text=True, timeout=180)
            if r.returncode == 0:
                return r.stdout, "stdout de deflexio.py executat ara"
            return None, f"deflexio.py ha fallat (rc={r.returncode}): {r.stderr.strip()[-160:]}"
        except Exception as exc:  # noqa: BLE001
            return None, f"deflexio.py no s'ha pogut executar: {exc}"
    return None, "_registres/deflexio.log ni estrelles_{sony,r6}.csv"


txt, font = sortida_deflexio()
if txt:
    m = re.search(r"σ\(eps\)\s*=\s*([\d.,]+)\s*→\s*GR a\s*([\d.,]+)σ\s*·\s*separar GR de Newton.*?a\s*([\d.,]+)σ", txt)
    if m:
        s_comb = float(m.group(1).replace(",", "."))
        e, tol = ACC["sigma_eps"]
        afirma_tol(f"forecast σ(ε) combinat (Fisher; GR a {m.group(2)}σ, GR–Newton a {m.group(3)}σ; no detecció)", s_comb, e, tol,
                   font, "{:.2f}")
    else:
        falta("σ(ε) combinat", f"la línia «σ(eps) = … → GR a …σ» no és a {font}")
    for m in re.finditer(r"^\s*(\S+)\s+.*?HIP 46345\s+([\d.]+)\s+([\d.]+)″\s+([\d.]+)", txt, re.M):
        e, tol = ACC["deflexio_hip46345_arcsec"]
        afirma_tol(f"predicció GR HIP 46345 (″, {m.group(1)}, r = {m.group(2)} R☉, {m.group(4)} px, catàleg)",
                   float(m.group(3)), e, tol, font, "{:.3f}")
else:
    falta("σ(ε) combinat", font)

# ------------------------------------------------------------------ 8. deflexió: HIP 46345
p = troba(APOD / "retalls_estrelles.json")
if p:
    try:
        ret = json.load(open(p))
        v = ret["HIP 46345"]
        tren = "vixen" if "vixen" in v else next(iter(v))
        gr = float(v[tren]["gr_arcsec"])
        e, tol = ACC["deflexio_hip46345_arcsec"]
        afirma_tol(f"predicció GR HIP 46345 (″, {tren}, r = {v[tren].get('r_sol', float('nan'))} R☉, {v[tren].get('gr_px', '?')} px)",
                   gr, e, tol, curt(p), "{:.4f}")
    except (KeyError, ValueError, TypeError) as exc:
        falta("deflexió HIP 46345 (retalls)", f"{curt(p)}: {exc}")
else:
    pl = troba(REG / "animacio.log")
    if pl:
        m = re.search(r"Einstein\s+([\d.,]+)\"\s*=\s*([\d.,]+) px", pl.read_text(errors="replace"))
        if m:
            e, tol = ACC["deflexio_hip46345_arcsec"]
            afirma_tol(f"predicció GR HIP 46345 (″, centroide refinat, {m.group(2)} px)",
                       float(m.group(1).replace(",", ".")), e, tol, curt(pl), "{:.3f}")
        else:
            falta("deflexió HIP 46345", f"línia «Einstein …» a {curt(pl)}")
    else:
        falta("deflexió HIP 46345", "APOD/retalls_estrelles.json ni _registres/animacio.log")

# ------------------------------------------------------------------ resum
print(f"Test d'acceptació de la cadena d'astrometria  (WORK={WORK}  OUT={OUT}  APOD={APOD})")
print()
for estat, text in linies:
    print(f" {estat} {text}")
n_ok = sum(1 for e, _ in linies if e == "✓")
n_ko = sum(1 for e, _ in linies if e == "✗")
n_na = sum(1 for e, _ in linies if e == "–")
print()
print(f"{n_ok} ✓ · {n_ko} ✗ · {n_na} no trobat  ({len(linies)} línies)")
if n_ko or (ESTRICTE and n_na):
    sys.exit(2)
sys.exit(0)
