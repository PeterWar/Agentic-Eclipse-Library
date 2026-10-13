"""LS1 · Capes Larson-Sekanina (gradient rotacional) per a la V126: LS(Δθ) = 2·ℓ(r, θ) − ℓ(r, θ+Δθ) − ℓ(r, θ−Δθ),
amb ℓ = ln de la lluminància (R+2G+B)/4 de la fusió lineal SENSE ESTRELLES de la V120, girant al voltant del centre del Sol.
- La resolució segueix el S/N: ℓ suavitzada amb σ = 1,5 · 3 · 6 · 12 px (canvi a 1,6 · 2,5 · 4 R☉, suau en ln r).  Com que el
  pes només depèn del radi i el gir conserva el radi, LS(ℓ barrejada) = Σ pes·LS(ℓ_σ) exactament.
- Res fora de la dada: el filtre només existeix on hi ha dada al píxel i als seus dos companys girats; alfa esvaïda en 16 px
  (una textura que s'atura en sec fa vora).  La V125 és el retall enter (1386, 1225) del llenç (mesurat: correlació màxima).
- Capa en Superposar: 0,5 = neutre.  v = 0,5 + 0,5·tanh(LS/s0), s0 = p99(|LS|, 1,1–2,5 R☉)/1,2 (mateix s0 a tot el llenç).
⚠️ Propietat coneguda del filtre: un raig més estret que Δθ hi surt amb dues còpies fosques a ±Δθ (la meitat d'amplitud).
⛔ Primera versió: a la protuberància i a la franja del limbe saturava en taques blanques i negres (còpies d'objectes molt
brillants i compactes) → ara surten de l'ENTRADA (excés de vermell dilatat 6 px; < 0,035 R☉ de la Lluna de C2)."""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
A = Path(__file__).resolve().parents[3]                # 4-Photoshop
lg = np.load(OUT / 'ln_lum_llenc.npy') if (OUT / 'ln_lum_llenc.npy').exists() else None
if lg is None:
    F = np.load(A / '3-RECERCA/resultats/v120_20260929/cadena/v120/lineal/fusion_starless.npy', mmap_mode='r')
    S = np.load(A / '3-RECERCA/resultats/v120_20260929/cadena/v120/lineal/support.npy')
    lum = (F[..., 0].astype(np.float32) + 2 * F[..., 1] + F[..., 2]) / 4
    ok = S.astype(bool) & np.isfinite(lum) & (lum > 0)
    lg = np.where(ok, np.log(np.where(ok, lum, 1)), np.nan).astype(np.float32)
H, W = lg.shape
OFF = (1386, 1225)                                   # V125 = llenç[1225:1225+5021, 1386:1386+7933]
g = json.load(open(A / '3-RECERCA/resultats/comparacio_sdo_lasco_20261001/GEOMETRIA_FINAL.json'))
CX, CY = g['sol_px_efemeride'][0] + OFF[0], g['sol_px_efemeride'][1] + OFF[1]
RS = g['R_sol_px']
t0 = time.time()
m = np.isfinite(lg)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.hypot(xx - CX, yy - CY) / RS
# Protuberàncies i perles, sagrades: fora de l'ENTRADA del filtre (no s'hi pot fer res i al voltant queda transparent).
#  · franja del limbe: a menys de 0,035 R☉ de la vora de la Lluna de C2 (la de la V125)
#  · protuberàncies: excés de vermell (R/G) sobre la mediana de la corona del mateix anell, dilatat 6 px
LX, LY = g['lluna_px'][0] + OFF[0], g['lluna_px'][1] + OFF[1]; RL = g['R_lluna_px']
dm = (np.hypot(xx - LX, yy - LY) - RL) / RS
del xx, yy
Fr = np.load(A / '3-RECERCA/resultats/v120_20260929/cadena/v120/lineal/fusion_starless.npy', mmap_mode='r')
q = np.asarray(Fr[..., 0], np.float32) / np.maximum(np.asarray(Fr[..., 1], np.float32), 1e-6)
prom = np.zeros((H, W), bool)
for r0 in np.arange(1.0, 1.40, 0.01):
    k = m & (r >= r0) & (r < r0 + 0.01) & (dm > 0.0)
    if k.sum() > 200:
        prom |= k & (q > 1.12 * np.median(q[k]))
prom = cv2.dilate(prom.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))) > 0
excl = (dm < 0.035) | prom
print(f'exclosos de l\'entrada: franja del limbe {int((dm < 0.035).sum())} px · protuberàncies {int(prom.sum())} px')
m &= ~excl
lg = np.where(m, lg, np.nan).astype(np.float32)
del Fr, q
def suau(s):
    a = cv2.GaussianBlur(np.where(m, lg, 0).astype(np.float32), (0, 0), s)
    w = cv2.GaussianBlur(m.astype(np.float32), (0, 0), s)
    return np.where(m & (w > 0.5), a / np.maximum(w, 1e-6), np.nan).astype(np.float32)
sig = [1.5, 3.0, 6.0, 12.0]; talls = [1.6, 2.5, 4.0]
lr = np.log(np.maximum(r, 1e-3))
pes = []
prev = np.zeros_like(r)
for k, t in enumerate(talls + [None]):
    if t is None:
        w = 1.0 - prev
    else:
        up = np.clip((lr - (np.log(t) - 0.10)) / 0.20, 0, 1); up = up * up * (3 - 2 * up)   # 0 → 1 en ±0,1 de ln r
        w = (1.0 - up) - prev
        prev = prev + w
    pes.append(w.astype(np.float32))
lb = np.zeros((H, W), np.float32); valid = np.ones((H, W), bool)
for s, w in zip(sig, pes):
    x = suau(s); valid &= np.isfinite(x) | (w < 1e-6)
    lb += np.where(np.isfinite(x), x, 0) * w
lb[~(valid & m)] = np.nan
print(f'ℓ barrejada {time.time() - t0:.0f} s')
res = {}
for dth in (0.4, 1.0):
    acc = 2 * np.nan_to_num(lb); ok = np.isfinite(lb)
    for sgn in (+1, -1):
        M = cv2.getRotationMatrix2D((float(CX), float(CY)), sgn * dth, 1.0)
        rot = cv2.warpAffine(np.nan_to_num(lb), M, (W, H), flags=cv2.INTER_CUBIC)
        okr = cv2.warpAffine(np.isfinite(lb).astype(np.float32), M, (W, H), flags=cv2.INTER_LINEAR) > 0.999
        acc -= rot; ok &= okr
    ls = np.where(ok, acc, np.nan).astype(np.float32)
    k = ok & (r > 1.1) & (r < 2.5)
    s0 = float(np.percentile(np.abs(ls[k]), 99)) / 1.2
    v = np.where(ok, 0.5 + 0.5 * np.tanh(ls / s0), 0.5).astype(np.float32)
    d = cv2.distanceTransform(np.pad(ok, 1).astype(np.uint8), cv2.DIST_L2, 5)[1:-1, 1:-1]
    al = np.clip(d / 16.0, 0, 1); al = (al * al * (3 - 2 * al)).astype(np.float32)
    vc = v[OFF[1]:OFF[1] + 5021, OFF[0]:OFF[0] + 7933]; ac = al[OFF[1]:OFF[1] + 5021, OFF[0]:OFF[0] + 7933]
    rc = r[OFF[1]:OFF[1] + 5021, OFF[0]:OFF[0] + 7933]
    # portes: nivell per anell (H1: |mediana − 0,5| ≤ 0,05), res fora de la dada, cobertura
    nivell = []
    for r0 in np.arange(1.05, 8.0, 0.05):
        q = (ac > 0.5) & (rc >= r0) & (rc < r0 + 0.05)
        if q.sum() > 500: nivell.append((round(float(r0), 2), float(np.median(vc[q]) - 0.5)))
    pitjor = max(nivell, key=lambda t: abs(t[1]))
    sense_dada = ~np.asarray(m[OFF[1]:OFF[1] + 5021, OFF[0]:OFF[0] + 7933])
    res_prom = int((ac[np.asarray(prom[OFF[1]:OFF[1] + 5021, OFF[0]:OFF[0] + 7933])] > 0).sum())
    res[str(dth)] = dict(s0=s0, H1_pitjor=pitjor, H1_passa=abs(pitjor[1]) <= 0.05,
                         inventats=int(((ac > 0) & sense_dada).sum()), cobertura=float((ac > 0.5).mean()),
                         dada=float((~sense_dada).mean()), alfa_sobre_protuberancies=res_prom, p90_desviacio=float(np.percentile(np.abs(vc[ac > 0.5] - 0.5), 90)))
    np.save(OUT / f'ls_{dth}_v.npy', vc.astype(np.float32)); np.save(OUT / f'ls_{dth}_alfa.npy', ac.astype(np.float32))
    print(f'LS {dth}°: s0 {s0:.4f} · H1 pitjor {pitjor} · inventats {res[str(dth)]["inventats"]} · cobertura {res[str(dth)]["cobertura"]:.3f} de {res[str(dth)]["dada"]:.3f} amb dada · {time.time() - t0:.0f} s')
json.dump(dict(sol_llenc=[CX, CY], R_sol_px=RS, OFF=OFF, sigma_px=sig, talls_rsun=talls, capes=res), open(OUT / 'LS1_REBUT.json', 'w'), indent=1)
