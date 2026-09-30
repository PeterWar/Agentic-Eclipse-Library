"""b3 (V116, 29-09-2026) · Ràster de la capa nova «Detall radial coherent Sony A·B» (Superposar), a partir del detall coherent D de b1.
    u = ½ · exp(κ(r) · D)        (en Superposar sobre una base b < ½, el factor és 2u = e^{κD}: resposta SIMÈTRICA en logaritmes, el buit
                                  s'enfosqueix tant com s'aclareix el raig; fora del camp comú, D = 0 → u = ½, neutre)
    κ(r) = β(r): el guany amb què el compost de la V115 ja mostra aquest mateix detall coherent (BETA_V115.json), interpolat en r, i esvaït
           de 1,15 a 1,35 R☉ (arran del limbe la Lluna es mou entre A i B i la coherència no s'hi pot establir).
Amb l'opacitat α de la capa, el detall confirmat per tots dos apuntaments guanya ≈ α·κ·D en logaritme (α = 40 % → +40 % del que ja es veu).
Sortida: <carpeta>/L415_G.npy (u16) i L415_alfa.npy (u16, 65535), i B3_REBUT.json. Ús: b3_capa_coherent.py <carpeta_b1> <carpeta_sortida>"""
import sys, json, hashlib, numpy as np
from pathlib import Path
B1, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
H, W = 7506, 10551; SOL = (5361.768, 3775.748); RS = 440.603
b = json.load(open(B1 / 'BETA_V115.json')); rc = np.array(b['r_centres']); bt = np.array([np.nan if v is None else v for v in b['beta']], float)
ok = np.isfinite(bt); rc, bt = rc[ok], bt[ok]
bs = np.convolve(np.pad(bt, 1, mode='edge'), np.ones(3) / 3, mode='valid')          # suavitzat lleu entre trams veïns
D = np.load(B1 / 'D_coherent_f32.npy', mmap_mode='r'); u16 = np.empty((H, W), np.uint16)
xs = np.arange(W, dtype=np.float32)
def smooth(x, a, c): t = np.clip((x - a) / (c - a), 0, 1); return t * t * (3 - 2 * t)
for y0 in range(0, H, 512):
    ys = np.arange(y0, min(H, y0 + 512), dtype=np.float32)[:, None]; r = np.hypot(xs[None, :] - SOL[0], ys - SOL[1]) / RS
    k = np.interp(r, rc, bs) * smooth(r, 1.15, 1.35)
    u = 0.5 * np.exp(k * np.asarray(D[y0:y0 + 512], np.float32)); u16[y0:y0 + 512] = np.round(np.clip(u, 0, 1) * 65535).astype(np.uint16)
np.save(OUT / 'L415_G.npy', u16); np.save(OUT / 'L415_alfa.npy', np.full((H, W), 65535, np.uint16))
uf = u16[::4, ::4].astype(np.float32) / 65535
rep = dict(guio=str(Path(__file__).name), kappa=dict(r=list(map(float, rc)), beta_suau=list(map(float, bs))), esvait_limbe_Rsol=[1.15, 1.35],
           u_p1_p50_p99=[float(np.percentile(uf, q)) for q in (1, 50, 99)], frac_no_neutra=float(np.mean(np.abs(uf - 0.5) > 1 / 512)),
           sha256_D=hashlib.sha256(open(B1 / 'D_coherent_f32.npy', 'rb').read()).hexdigest())
(OUT / 'B3_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False)[:800])
