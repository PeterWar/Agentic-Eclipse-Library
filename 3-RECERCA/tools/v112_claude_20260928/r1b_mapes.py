"""r1b · mapes de l'ajust dels anells (canal donat): D = ln A − ln B al solapament (blocs 8×8), el model d'anells p(ρA) − p(ρB)
i el residu D − suau − anells, amb el mateix estirament; i el perfil p(ρ) amb la part suau (c0 + c2 ρ² + c4 ρ⁴) treta."""
import sys, json
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v112_claude_20260928/anells'
CH = int(sys.argv[1]) if len(sys.argv) > 1 else 1
exec(open(Path(__file__).parent / 'r1_anells_AB.py').read().split('fitsel = tile == 0')[0])   # mateixes dades i disseny
z = np.load(O / f'p_canal{CH}.npz'); dl = z['delta']; p = z['p_all']; rho = z['rho']
# part suau de p (degenerada amb el camp suau): es treu per mostrar només els anells
m = rho < 6500; Vd = np.stack([np.ones(m.sum()), (rho[m]/1000)**2, (rho[m]/1000)**4], 1)
c = np.linalg.lstsq(Vd, p[m], rcond=None)[0]; pr = p - np.stack([np.ones_like(rho), (rho/1000)**2, (rho/1000)**4], 1) @ c
np.savez(O / f'p_anells_canal{CH}.npz', rho=rho, p_anells=pr, delta=dl, cA=z['cA'], cB=z['cB'])
cA, cB = z['cA'], z['cB']
rA = np.hypot(X - cA[0], Y - cA[1]); rB = np.hypot(X - cB[0], Y - cB[1])
ring = np.interp(rA, rho, pr) - np.interp(rB, rho, pr)
sol = fit(dl, np.ones(d.size, bool)); smooth = np.zeros((h, w)); 
S_full = np.stack([((X - W/2)/(W/2))**i * ((Y - H/2)/(W/2))**j for i in range(5) for j in range(5 - i)], -1) @ sol[K:]
full_ring = np.interp(rA, rho, p) - np.interp(rB, rho, p)
Dm = np.where(ok, D - S_full - (full_ring - ring), np.nan)       # D sense el camp suau (ni la part suau de p)
res = np.where(ok, D - S_full - full_ring, np.nan)
s = 0.006
def img(a):
    g = np.clip((np.nan_to_num(a) / s + 1) * 127.5, 0, 255).astype(np.uint8); g[~np.isfinite(a)] = 0; return g
rr = np.where(ok, ring, np.nan)
im = Image.fromarray(np.concatenate([img(Dm), np.full((h, 4), 255, np.uint8), img(rr), np.full((h, 4), 255, np.uint8), img(res)], 1))
dd = ImageDraw.Draw(im); dd.text((6, 6), f'D=lnA-lnB (sense suau) | model anells pA-pB | residu  (±{s})  canal {CH}  delta {dl}', fill=255)
im.save(R / f'4-RESULTATS/v112_claude_20260928/vistes/anells_AB_canal{CH}.png')
# perfil
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(11, 3.2)); ax.plot(rho * 0.6713, pr * 100, lw=1)
for rr_ in (1908, 2366, 2832): ax.axvline(rr_ * 0.6713, color='m', lw=0.6, ls='--')
ax.set_xlim(0, 4800); ax.set_xlabel('radi al sensor des de l\'eix òptic (px del sensor)'); ax.set_ylabel('p (%)'); ax.grid(alpha=.3)
ax.set_title(f'Perfil dels anells de la Sony (canal {CH}); línies lila = radis dels arcs 5, 3, 2 marcats per Pere')
fig.tight_layout(); fig.savefig(R / f'4-RESULTATS/v112_claude_20260928/vistes/perfil_anells_canal{CH}.png', dpi=110)
print('fet', dl, 'rms anells', float(np.nanstd(rr)))
