"""n5 (V108 · negres) · El mateix TERRA FÍSIC de la NRGF (el buit no pot baixar del cel) aplicat, com a ÚLTIM PAS DEL GENERADOR, a les altres
capes que enfosqueixen els buits sense mirar el S/N: 56 WOW bilateral (Superposar; blanqueja cada escala per la seva potència local),
45/46 RHEF locals (Multiplicar; rang dins del sector: un buit fluix hi té rang 0 igual que un de fort) i 54 MGN (Multiplicar; cada escala
dividida per la seva σ local). És una funció puntual del valor del ràster (com u_affine o el nivell al buit), de manera que fer-la aquí sobre
el ràster de la V107 és idèntic a fer-la al final de l'E2/E6. Cap píxel nou: només s'hi limita l'enfosquiment.
  Multiplicar: f = 1 − α(1 − u) ≥ f_cel·(1 − β_k·w), f_cel = 1 − α(1 − u_cel), u_cel = mediana de la capa a 6,5–8,5 R☉.
  Superposar (Cb < 0,5): 1 + α(2F − 1) ≥ 1 − β_k·w.
  α = opacitat × màscara × alfa de la V107 (el «pressupost» es declara amb la pila de la V107); w i la fosa radial, els de f3n (CEL_TER).
  Parts del pressupost: NRGF 0,6 (f3n) · 56: 0,15 · 45: 0,05 · 46: 0,05 · 54: 0,05 (queda 0,1 per a 47/49/51/55, sense terra).
Ús: [N5_BETA='{"56": 0.4}' N5_DIR=TERRA_56_b04] n5_terra_altres.py → 4-RESULTATS/v108_20260926/negres/candidats/<N5_DIR>/L{lid}_u16.npy"""
import sys, json, time
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_negres import *
import os
BETA = json.loads(os.environ.get('N5_BETA', '{"56": 0.15, "45": 0.05, "46": 0.05, "54": 0.05}')); BETA = {int(k): float(v) for k, v in BETA.items()}
DST = OUT / 'candidats' / os.environ.get('N5_DIR', 'TERRA_ALTRES'); DST.mkdir(parents=True, exist_ok=True); SUAU = {'MULTIPLY': 0.02, 'OVERLAY': 0.005}
t0 = time.time(); FULL = (0, 0, W, H)
B = np.empty((H, W), np.float32)
for y0 in range(0, H, 1024): B[y0:y0 + 1024] = lum(E.rgb(3, (0, y0, W, min(H, y0 + 1024))))
r, th = radi(FULL, 1); okb = E.alfa_efectiva(3) > 0.5
_, BS = cel_local(B, r, th, okb); w = np.clip(1 - BS / np.maximum(B, 1e-6), 0, 1).astype(np.float32); del BS, B
# fosa radial: la de f3n (mediana de w per anell, smoothstep 0,005–0,02)
ri = np.floor(r * RSOL).astype(np.int32); nr = int(ri.max()) + 1; sel = okb
cnt = np.bincount(ri[sel], minlength=nr); order = np.argsort(ri[sel], kind='stable'); ws = w[sel][order]; cut = np.r_[0, np.cumsum(cnt)]
wr = np.array([np.median(ws[cut[i]:cut[i + 1]]) if cnt[i] > 50 else 0 for i in range(nr)], np.float32); del ws, order
wr = gaussian_filter1d(wr, 4.0, mode='nearest'); q = np.clip((wr - 0.005) / 0.015, 0, 1); fade_r = q * q * (3 - 2 * q)
FADE = np.interp(r * RSOL, np.arange(nr) + 0.5, fade_r).astype(np.float32); del ri
print('w i fosa', round(time.time() - t0), flush=True)
rep = {}
cel = okb & (r >= 6.5) & (r < 8.5)
for lid, beta in BETA.items():
    c = E.capes[lid]; mode = c['mode']; o = c['opacitat'] / 255
    F = E.rgb(lid).astype(np.float32); alfa = E.alfa_efectiva(lid)            # opacitat × màscara × alfa
    if mode == 'MULTIPLY':
        u_cel = float(np.median(F[cel])); f_cel = 1 - alfa * (1 - u_cel); tgt = f_cel * (1 - beta * w)
        fl = np.where(alfa > 1e-4, 1 - (1 - tgt) / np.maximum(alfa, 1e-4), -np.inf)
    else:
        u_cel = 0.5; fl = np.where(alfa > 1e-4, 0.5 - beta * w / (2 * np.maximum(alfa, 1e-4)), -np.inf)
    s = SUAU[mode]; fin = np.isfinite(fl)
    Fs = np.where(fin, fl + s * np.logaddexp(0, (F - np.where(fin, fl, 0)) / s), F)
    Fn = (F + FADE * (Fs - F)).astype(np.float32)
    u16 = np.round(np.clip(Fn, 0, 1) * 65535).astype(np.uint16); np.save(DST / f'L{lid}_u16.npy', u16)
    ch = np.abs(u16.astype(np.int32) - np.round(F * 65535).astype(np.int32)); m3 = okb & (r >= 1.3) & (r < 4.5)
    rep[lid] = dict(mode=mode, opacitat=o, beta=beta, u_cel=u_cel, px_canviats_1_3_4_5=float((ch[m3] > 0).mean()), dif_mitjana_canviats=float(ch[m3][ch[m3] > 0].mean() / 65535) if (ch[m3] > 0).any() else 0.0)
    print(lid, rep[lid], round(time.time() - t0), flush=True); del F, alfa, fl, Fs, Fn, u16, ch
desa(DST / 'N5_TERRA_ALTRES.json', rep); print('FET')
