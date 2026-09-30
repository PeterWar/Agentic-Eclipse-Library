"""a3 (V116, 29-09-2026) · Guany del realç sobre l'estructura LOCAL, NOMÉS amb la nostra dada.
d = ln X(σ 8 px) − ln X(σ 150 px): l'estructura local (el fons de 150 px s'emporta el gradient radial i el del cel). X = la fusió LINEAL sense estrelles
(fonts_c, la dada) o una sortida (compost desat). Per bandes de radi, fora de les marques:
    g+ = mediana d_sortida / mediana d_lineal als píxels del quartil clar (raigs);  g− = el mateix al quartil fosc (buits);  A = g−/g+
i, per a cada marca de Pere, E = (⟨d_sortida⟩ / ⟨d_lineal⟩ a la marca) / g+ de la seva banda: E > 1 vol dir que aquell buit s'aprofundeix més
que no s'aclareix un raig de la mateixa banda (foscor afegida pel realç); E ≤ 1, realç simètric o menor.
Ús: a3_guany_local.py <sortida.json> <nom=render.tif|.npy> [...]"""
import sys, json, numpy as np, tifffile
from pathlib import Path
from scipy import ndimage as ndi
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v116_20260929'
lab = np.load(O / 'marques_V115_etiquetes.npy'); M = json.load(open(O / 'MARQUES_V115.json'))['marques']; H, W = lab.shape
def quart(x): return x[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4).mean((1, 3))
def llum(path):
    a = np.load(path, mmap_mode='r') if str(path).endswith('.npy') else tifffile.memmap(path, mode='r')
    return np.mean([quart(np.asarray(a[..., c], np.float32)) for c in range(3)], 0)
def dev(L):
    v = (L > 0) & np.isfinite(L); s = ndi.gaussian_filter(np.where(v, L, 0), 2) / np.maximum(ndi.gaussian_filter(v.astype(np.float32), 2), 1e-9)
    bg = ndi.gaussian_filter(np.where(v, L, 0), 37.5) / np.maximum(ndi.gaussian_filter(v.astype(np.float32), 37.5), 1e-9)
    return np.where(v & (s > 0) & (bg > 0), np.log(np.maximum(s, 1e-12)) - np.log(np.maximum(bg, 1e-12)), np.nan)
LIN = llum(ARREL / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/sources/fusion_starless.npy'); dl = dev(LIN)
lab4 = lab[:H // 4 * 4:4, :W // 4 * 4:4]
SOL = (5361.768 / 4, 3775.748 / 4); RS = 440.603 / 4; yy, xx = np.mgrid[0:H // 4, 0:W // 4]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
BANDES = ((1.3, 2.0), (2.0, 3.5), (3.5, 5.5), (5.5, 9.5))
def banda(r): return next((f'{a}-{b}' for a, b in BANDES if a <= r < b), None)
res = {}
for arg in sys.argv[2:]:
    nom, path = arg.split('=', 1); do = dev(llum(ARREL / path)); r = dict(bandes={}, marques={})
    for a, b in BANDES:
        k = (rr >= a) & (rr < b) & (lab4 == 0) & np.isfinite(dl) & np.isfinite(do)
        q25, q75 = np.percentile(dl[k], [25, 75]); cl, fs = k & (dl > q75), k & (dl < q25)
        gp = float(np.median(do[cl]) / np.median(dl[cl])); gm = float(np.median(do[fs]) / np.median(dl[fs]))
        r['bandes'][f'{a}-{b}'] = dict(g_clar=round(gp, 3), g_fosc=round(gm, 3), A=round(gm / gp, 3))
    for m in M:
        kk = (lab4 == m['marca']) & np.isfinite(dl) & np.isfinite(do); bn = banda(m['r_Rsol'])
        if not kk.any() or bn is None: continue
        cl_, co_ = float(np.mean(dl[kk])), float(np.mean(do[kk])); gp = r['bandes'][bn]['g_clar']
        r['marques'][m['marca']] = dict(banda=bn, d_lineal_pct=round(cl_ * 100, 2), d_sortida_pct=round(co_ * 100, 2), E=round((co_ / cl_) / gp, 2) if cl_ < -1e-3 else None,
                                         esperat_pct=round(cl_ * gp * 100, 2))
    res[nom] = r
json.dump(dict(nota=__doc__.split('\n')[0], resultats=res), open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
for nom, r in res.items():
    print(nom, 'bandes:', json.dumps(r['bandes'], ensure_ascii=False))
    print('   marca:', ' '.join(f"{k}:{v['d_sortida_pct']:.1f}/{v['esperat_pct']:.1f}(E {v['E']})" for k, v in r['marques'].items()))
