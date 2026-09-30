"""c1 (V105) · Capa «Limbe de l'instant · sense corregir»: la dada observada dels fotogrames de l'instant (variant F: rampa 0,75→1,75 a dalt,
2→3 a l'esquerra, T aplicada com a la V104) portada a l'espai del compost emulat de la V104 (E/compost/v99_v103_compostB.npy) amb un ajust
afí en logaritme PER SECTOR DE 5° I PER CANAL, ajustat a 3–6 px de la silueta real (on el compost i la dada F coincideixen) i aplicat a
0–3,5 px. Alfa: 1 on la V104 no té dada, fosa a 0 a DMIN_E(PA) + 1 px; zero dins del cercle de presentació i fora de 30–270°.
NO és corona corregida: és la foto de l'instant (1/125 i 1/500 s i curts) a tocar de la Lluna, amb el dèficit de vora i la cromosfera tal com
són. Sortida: <sortida.npz> (box, RGB16, A16, report) i làmines. Ús: c1_capa_limbe_instant.py <F npz> <E npz> <compostB.npy> <sortida.npz>"""
import sys, json
from pathlib import Path
import numpy as np, cv2
F = np.load(sys.argv[1]); E = np.load(sys.argv[2]); C = np.load(sys.argv[3]); OUT = Path(sys.argv[4]); OUT.parent.mkdir(parents=True, exist_ok=True)
by0, by1, bx0, bx1 = [int(v) for v in F['box']]; LX, LY, RL = [float(v) for v in F['centre']]
CB = (4780, 3180, 5980, 4380)   # caixa del compost emulat (j14/j15)
R9 = Path(__file__).resolve().parents[3] / '4-RESULTATS/v99_banda_20260925'; S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
yy, xx = np.mgrid[by0:by1, bx0:bx1]; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360; dL = np.hypot(xx - LX, yy - LY) - RL
dp = dL - np.interp(th.ravel(), pag, eg, period=360).reshape(th.shape)
EF = F['E']; domF = F['domini_E']; DMINE = E['DMIN']; NBZ = DMINE.size; dmE = DMINE[(th / 360 * NBZ).astype(int) % NBZ]
# compost a la caixa F
Cc = np.zeros((by1 - by0, bx1 - bx0, 3), np.float32); ys, xs = max(by0, CB[1]), max(bx0, CB[0]); ye, xe = min(by1, CB[3]), min(bx1, CB[2])
Cc[ys - by0:ye - by0, xs - bx0:xe - bx0] = C[ys - CB[1]:ye - CB[1], xs - CB[0]:xe - CB[0]]
def ss(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
lead = (th >= 30) & (th < 270)
zona_fit = lead & domF & (dp >= 3.0) & (dp < 6.0) & (Cc[..., 1] > 0.02) & (EF[..., 1] > 0) & (dL >= dmE + 0.5)   # on la V104 ja té dada pròpia
zona_cap = lead & domF & (dp >= -0.5) & (dp < 4.0) & (EF[..., 1] > 0) & (dL >= 0)
RGB = np.zeros_like(Cc); rep = {}
for a0 in range(30, 270, 5):
    zb = (th >= a0 - 2.5) & (th < a0 + 7.5)   # bins de 5° amb solapament de 2,5° per continuïtat
    fz = zona_fit & zb; cz = zona_cap & (th >= a0) & (th < a0 + 5)
    if fz.sum() < 200 or not cz.any(): rep[str(a0)] = dict(px_fit=int(fz.sum()), px_capa=int(cz.sum()), ajust=None); continue
    coef = []
    for c in range(3):
        x = np.log(EF[..., c][fz]); y = np.log(np.maximum(Cc[..., c][fz], 1e-4)); ok = np.isfinite(x) & np.isfinite(y)
        b, a = np.polyfit(x[ok], y[ok], 1); r = y - (a + b * x); q = np.percentile(np.abs(r[ok]), 80); ok2 = ok & (np.abs(r) <= 1.5 * q)
        b, a = np.polyfit(x[ok2], y[ok2], 1); coef.append((a, b))
        RGB[..., c][cz] = np.exp(a + b * np.log(np.maximum(EF[..., c][cz], 1e-9)))
    # continuïtat: mediana de ln(capa / compost) a 3–3,5 px (solapament)
    ov = cz & (dp >= 3.0) & (dp < 3.5) & (Cc[..., 1] > 0.02)
    cont = float(np.median(np.log(RGB[..., 1][ov] / Cc[..., 1][ov]))) if ov.sum() > 20 else None
    rep[str(a0)] = dict(px_fit=int(fz.sum()), px_capa=int(cz.sum()), ajust=[[round(a, 4), round(b, 4)] for a, b in coef], continuitat_ln_3_35=None if cont is None else round(cont, 4))
alfa = np.where(zona_cap, 1 - ss(dL, dmE - 0.25, dmE + 1.0), 0.0) * ss(dp, -0.5, 0.25)   # entrada suau al primer mig píxel
alfa = (alfa * (RGB[..., 1] > 0)).astype(np.float32)
RGB16 = np.round(np.clip(RGB, 0, 1) * 65535).astype(np.uint16); A16 = np.round(np.clip(alfa, 0, 1) * 65535).astype(np.uint16)
np.savez_compressed(OUT, box=np.array([by0, by1, bx0, bx1]), RGB16=RGB16, A16=A16)
px = int((alfa > 0.5).sum()); (OUT.with_suffix('.json')).write_text(json.dumps(dict(px_alfa_gt_05=px, sectors=rep), ensure_ascii=False, indent=1))
# làmines 4:1: compost E (V104) | compost amb la capa a sobre (Normal)
comp = Cc * (1 - alfa[..., None]) + RGB * alfa[..., None]
def u8(a): return (np.clip(a, 0, 1) * 255).astype(np.uint8)
for nom, (x0, y0, x1, y1) in {'dalt': (5150, 3290, 5600, 3400), 'dalt_esq': (4930, 3330, 5200, 3560), 'baix_esq': (4930, 4000, 5250, 4240)}.items():
    a = u8(Cc[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]); b = u8(comp[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]); sep = np.full((a.shape[0], 4, 3), 255, np.uint8)
    L = cv2.resize(np.hstack([a, sep, b]), None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST); cv2.imwrite(str(OUT.parent / f'LAM_{nom}_V104_amb_capa_4a1.png'), cv2.cvtColor(L, cv2.COLOR_RGB2BGR))
print('capa: px amb alfa > 0,5 =', px); print(' '.join(f"{k}:{v['continuitat_ln_3_35']}" for k, v in rep.items() if v.get('continuitat_ln_3_35') is not None))
