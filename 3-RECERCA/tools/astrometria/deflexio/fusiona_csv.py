#!/usr/bin/env python3
"""Fusió catàleg cec + identificacions → estrelles_sony.csv i estrelles_r6.csv.

Reconstrueix, per programa, els dos CSV que fins ara només existien fets a mà
(~/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/estrelles_*.csv,
del 16-08-2026) i que són
l'entrada de deflexio.py, mascara_estrelles.py i requisits.py. Mateixa
capçalera: id,x,y,nom,senyal,fwhm,nota.

Entrades (tot a comu.work):
    work("sony")/catalog_sony.txt            38 fonts cegues (final3.py)
    work("vixen")/catalog_vixen_fonts.csv    32 candidates: 21 A + 3 B publicades, 8 REBUTJADA
    work("xmatch")/IDENTIFICACIONS_sony.csv  38 identificacions amb HIP/TYC/Sp/V
    work("xmatch")/IDENTIFICACIONS_r6.csv    21 identificacions
    work("xmatch")/final_match_r6.csv        complement: hi ha V10 = HIP 46464 (22/24 publicades),
                                             que la llista fotomètrica va deixar fora per ser a la vora
Sortides:
    out()/estrelles_sony.csv   38 files, x/y arrodonides a 0,1 px com l'original
    out()/estrelles_r6.csv     24 files (A-00…A-21, B-11, B-24, B-26), x/y a 0,01 px

Diferències conegudes amb la versió feta a mà (cap consumidor no les llegeix):
  - «nom» surt per a TOTES les identificades (38/38 i 22/24); la versió a mà
    només en tenia 12 i 9, perquè es va escriure abans del creuament complet.
  - «nom» no porta el nom de Flamsteed («8 Leonis»): no és a cap entrada.
  - «senyal», «fwhm» i «nota» es construeixen del catàleg amb el mateix patró,
    però sense les observacions en prosa («La més brillant del camp…»).
Els números que en depenen (σ(ε) de deflexio.py) només usen id, x, y.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu  # noqa: E402

ESC_SONY = comu.SONY["escala_vella"]      # 3,234: la que duu la capçalera de catalog_sony.txt


def dec(v, n=2):
    """Número en text català (coma decimal), n decimals."""
    return f"{float(v):.{n}f}".replace(".", ",")


def llegeix_ident(tren):
    """{det: dict} de IDENTIFICACIONS_<tren>.csv, complementat amb final_match_<tren>.csv."""
    xd = comu.work("xmatch")
    ident = {}
    p = xd / f"IDENTIFICACIONS_{tren}.csv"
    if p.exists():
        for r in csv.DictReader(open(p)):
            ident[r["det"]] = r
    else:
        print(f"  ⚠️ falta {p}: només final_match")
    q = xd / f"final_match_{tren}.csv"
    n_extra = 0
    if q.exists():
        for r in csv.DictReader(open(q)):
            if r["det"] not in ident:
                ident[r["det"]] = r
                n_extra += 1
    if n_extra:
        print(f"  {tren}: {n_extra} identificació(ns) afegida(es) de final_match_{tren}.csv")
    return ident


def clau(r):
    """HIP si n'hi ha, si no TYC: per lligar les identificacions dels dos trens."""
    hip = (r.get("HIP") or "").strip()
    if hip and hip.lower() != "nan":
        return "HIP", str(int(float(hip)))
    tyc = (r.get("TYC") or "").strip()
    return ("TYC", tyc) if tyc else (None, None)


def nom_estrella(r):
    """«HIP 46345, K2, V=6,83» o «TYC 826-1182-1, V=8,15»."""
    tipus, val = clau(r)
    if tipus is None:
        return ""
    parts = [f"{tipus} {val}"]
    sp = (r.get("Sp") or "").strip()
    if sp and sp.lower() != "nan":
        parts.append(sp)
    v = (r.get("V") or "").strip()
    if v and v.lower() != "nan":
        parts.append(f"V={dec(v, 2)}")
    return ", ".join(parts)


def creuat(ident_a, ident_b):
    """{det_a: det_b} amb la mateixa estrella (HIP, o TYC si no hi ha HIP)."""
    inv = {}
    for det, r in ident_b.items():
        k = clau(r)
        if k[0]:
            inv.setdefault(k, det)
    return {det: inv.get(clau(r)) for det, r in ident_a.items() if clau(r)[0]}


# ------------------------------------------------------------------ Sony
def sony(ident_s, ident_v):
    p = comu.work("sony") / "catalog_sony.txt"
    files = []
    for line in open(p):
        if line.startswith("#") or not line.strip():
            continue
        t = line.split()
        files.append(dict(id=t[0], x=float(t[1]), y=float(t[2]), R_Rsun=t[3], R_deg=t[4],
                          flux=t[5], err=t[6], SN=t[7], SNR_A=t[8], SNR_C=t[9], nfr=t[10],
                          FWHM_as=t[11], ba=t[12], RG=t[13], BG=t[14], V_est=t[15]))
    x_s2v = creuat(ident_s, ident_v)
    out = []
    for f in files:
        det = f["id"]
        r = ident_s.get(det)
        nom = ""
        if r is not None and clau(r)[0]:
            v = x_s2v.get(det)
            cap = f"{det} / {v}" if v else det
            nom = f"{cap} = {nom_estrella(r)}"
        senyal = (f"{f['flux']} ADU/s, S/N {dec(f['SN'],1)}; "
                  f"A {dec(f['SNR_A'],1)} / C {dec(f['SNR_C'],1)}")
        fwhm = (f"{dec(f['FWHM_as'],1)}\" ({dec(float(f['FWHM_as'])/ESC_SONY,2)} px), "
                f"b/a {dec(f['ba'],2)}")
        nota = f"R = {dec(f['R_Rsun'],2)} Rsol ({dec(f['R_deg'],2)} graus). {f['nfr']} de 7 fotogrames."
        out.append([det, round(f["x"], 1), round(f["y"], 1), nom, senyal, fwhm, nota])
    return out


# ------------------------------------------------------------------ Vixen / R6
def r6(ident_v, ident_s):
    p = comu.work("vixen") / "catalog_vixen_fonts.csv"
    x_v2s = creuat(ident_v, ident_s)
    out = []
    for f in csv.DictReader(open(p)):
        classe = f["classe"].strip()
        if classe not in ("A", "B"):
            continue                                   # REBUTJADA: no es publica
        i = int(f["id"])
        idd = f"{classe}-{i:02d}"
        det = f"V{i:02d}"
        r = ident_v.get(det)
        nom = ""
        if r is not None and clau(r)[0]:
            s = x_v2s.get(det)
            cap = f"{s} / {det}" if s else det
            nom = f"{cap} = {nom_estrella(r)}"
        n3, n10 = f["n_fotogrames_3s"], f["n_10.3s"]
        llargs = f" ({n10}/3 de 10,3 s)" if int(n10) < 3 else ""
        senyal = (f"{dec(f['flux_G_ADUs'],0)} ADU/s; S/R {dec(f['SNR_pila'],1)}; "
                  f"{n3}/8 fotogrames{llargs}; R S/R {dec(f['SNR_R'],1)}")
        trac = f["traç_arcsec"].strip()
        fw = f"FWHM {dec(f['FWHM_arcsec'],1)}″"
        if not trac:
            fwhm = f"{fw}; traç no mesurable"
        elif float(trac) > 20:
            fwhm = f"traç no fiable ({dec(trac,0)}″: soroll)"
        else:
            fwhm = f"{fw}; traç {dec(trac,2)}″"
        nota = f"r = {dec(f['r_sol_deg'],2)}° ({dec(f['r_sol_Rlluna'],2)} radis lunars)."
        if classe == "B":
            nota = "PROBABLE. " + nota
        elif not nom and f["V_aprox_INFERIT"].strip():
            nota += f" V ≈ {dec(f['V_aprox_INFERIT'],1)} INFERIT."
        out.append([idd, float(f["x_px"]), float(f["y_px"]), nom, senyal, fwhm, nota])
    return out


def escriu(path, files):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "x", "y", "nom", "senyal", "fwhm", "nota"])
        for f in files:
            w.writerow(f)
    n_nom = sum(1 for f in files if f[3])
    print(f"  {path}  ({len(files)} files, {n_nom} amb nom)")


if __name__ == "__main__":
    ident_s = llegeix_ident("sony")
    ident_v = llegeix_ident("r6")
    escriu(comu.out() / "estrelles_sony.csv", sony(ident_s, ident_v))
    escriu(comu.out() / "estrelles_r6.csv", r6(ident_v, ident_s))
