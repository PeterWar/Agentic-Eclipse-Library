"""a2 (V116, 29-09-2026) · Criteri NOMÉS amb la nostra dada: el realç ha de tractar igual el fosc que el clar.
Per a cada marca de Pere k (buit fosc) i el seu anell F_k (60–300 px): a la dada LINEAL (fusió sense estrelles de la cadena viva, fonts_c) i a
la sortida (compost desat), en logaritmes (on la corba de pantalla és simètrica):
    c_buit  = ln⟨L⟩_marca − ln⟨L⟩_anell                           (el buit, negatiu)
    c_raig  = ln⟨L⟩_raigs − ln⟨L⟩_anell, amb raigs = el 25 % més clar de l'anell segons la dada lineal suavitzada (σ 6 px)
    g− = c_buit(sortida)/c_buit(lineal),  g+ = c_raig(sortida)/c_raig(lineal),  A = g−/g+
A ≈ 1: el buit s'aprofundeix tant com s'aclareixen els raigs del costat (realç simètric). A > 1: foscor afegida pel realç.
Ús: a2_simetria_marques.py <sortida.json> <nom=render.tif|.npy> [...]"""
import sys, json, numpy as np, tifffile
from pathlib import Path
from scipy import ndimage as ndi
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v116_20260929'
lab = np.load(O / 'marques_V115_etiquetes.npy'); M = json.load(open(O / 'MARQUES_V115.json'))['marques']; H, W = lab.shape
def quart(x): return x[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4).mean((1, 3))
def llum(path):
    a = np.load(path, mmap_mode='r') if str(path).endswith('.npy') else tifffile.memmap(path, mode='r')
    return np.mean([quart(np.asarray(a[..., c], np.float32)) for c in range(3)], 0)
LIN = llum(ARREL / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/sources/fusion_starless.npy')
LINs = ndi.gaussian_filter(LIN, 1.5)
lab4 = lab[:H // 4 * 4:4, :W // 4 * 4:4]; dist = {m['marca']: ndi.distance_transform_edt(lab4 != m['marca']) * 4 for m in M}
def mesura(L4):
    o = {}
    for m in M:
        k = m['marca']; v = (L4 > 1e-6) & (LIN > 0) & np.isfinite(LIN)
        d = (lab4 == k) & v; f = (dist[k] > 60) & (dist[k] < 300) & (lab4 == 0) & v
        if not d.any() or not f.any(): o[k] = None; continue
        thr = np.percentile(LINs[f], 75); ra = f & (LINs >= thr)
        o[k] = dict(buit=float(np.log(L4[d].mean()) - np.log(L4[f].mean())), raig=float(np.log(L4[ra].mean()) - np.log(L4[f].mean())))
    return o
ref = mesura(LIN); res = {'lineal (fusió sense estrelles)': {k: {kk: round(vv * 100, 3) for kk, vv in v.items()} for k, v in ref.items()}}
for a in sys.argv[2:]:
    nom, path = a.split('=', 1); s = mesura(llum(ARREL / path)); r = {}
    for m in M:
        k = m['marca']
        if s[k] is None or ref[k] is None: continue
        gm = s[k]['buit'] / ref[k]['buit'] if abs(ref[k]['buit']) > 1e-4 else float('nan'); gp = s[k]['raig'] / ref[k]['raig']
        r[k] = dict(buit_pct=round(s[k]['buit'] * 100, 2), raig_pct=round(s[k]['raig'] * 100, 2), g_fosc=round(gm, 2), g_clar=round(gp, 2), A=round(gm / gp, 2))
    res[nom] = r
json.dump(dict(nota='contrastos en log (×100); g = sortida/lineal; A = g_fosc/g_clar (1 = simètric)', resultats=res), open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
print('marca'.ljust(8), ''.join(f'{m["marca"]:>7d}' for m in M))
print('lin buit'.ljust(8), ''.join(f"{res['lineal (fusió sense estrelles)'][m['marca']]['buit']:7.2f}" for m in M))
print('lin raig'.ljust(8), ''.join(f"{res['lineal (fusió sense estrelles)'][m['marca']]['raig']:7.2f}" for m in M))
for nom in list(res)[1:]:
    for camp in ('buit_pct', 'raig_pct', 'g_fosc', 'g_clar', 'A'):
        print(f'{nom[:10]} {camp}'.ljust(18), ''.join(f"{res[nom][m['marca']][camp]:7.2f}" if m['marca'] in res[nom] else '    nan' for m in M))
