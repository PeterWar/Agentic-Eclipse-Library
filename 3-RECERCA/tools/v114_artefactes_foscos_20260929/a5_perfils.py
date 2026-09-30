"""a5 (29-09-2026) · Perfils a través de cada marca: base lineal (3), pila sota els ajustos (S0 = pis 301), compost desat amb els ajustos de Pere (U)
i Brno 200 mm (230, jutge). Dos perfils per marca, sobre l'eix llarg de la marca i perpendicular al centre, mitjana en una franja de ±150 px;
cada corba és ln(nivell) − ln(tendència lineal ajustada als extrems del perfil), en %, perquè el que es compara és l'estructura, no el to.
Sortida: vistes/perfils_marca_NN.png i PERFILS.json (profunditat mínima de cada corba dins de la marca)."""
import json, numpy as np
from pathlib import Path
from scipy import ndimage as ndi
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ARREL = Path(__file__).resolve().parents[3]; OUT = ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929'; E = OUT / 'estadis_1a4'
lab = np.load(OUT / 'marques_414_etiquetes.npy'); M = json.load(open(OUT / 'MARQUES_414.json'))['marques']
CURVES = [('base lineal (capa 3)', np.load(E / '003_L.npy'), '#888888'), ('amb els filtres (sota els ajustos)', np.load(E / '301_L.npy'), '#1f77b4'),
          ('compost amb els ajustos de Pere', np.load(E / 'U_L.npy'), '#d62728'), ('Brno 200 mm (jutge)', np.load(E / 'brno_230_L.npy'), '#2ca02c')]
f = 4; lab4 = lab[:lab.shape[0] // f * f:f, :lab.shape[1] // f * f:f]
def perfil(img, c, u, v, llarg, amp):
    t = np.arange(-llarg, llarg + 1, 1.0); s = np.arange(-amp, amp + 1, 2.0)
    X = c[0] + t[:, None] * u[0] + s[None, :] * v[0]; Y = c[1] + t[:, None] * u[1] + s[None, :] * v[1]
    val = ndi.map_coordinates(img, [Y, X], order=1, cval=np.nan)
    return t * f, np.nanmean(np.where(val > 0.004, val, np.nan), 1)
def normal(t, y):
    ok = np.isfinite(y) & (y > 0)
    if ok.sum() < 10: return y * np.nan
    ly = np.log(np.where(ok, y, np.nan)); ext = ok & (np.abs(t) > 0.8 * np.abs(t).max())
    if ext.sum() < 4: ext = ok
    a, b = np.polyfit(t[ext], ly[ext], 1); return (ly - (a * t + b)) * 100
res = {}
for m in M:
    k = m['marca']; ys, xs = np.nonzero(lab4 == k); c = np.array([xs.mean(), ys.mean()])
    ev, evec = np.linalg.eigh(np.cov(np.vstack([xs - c[0], ys - c[1]]))); u = evec[:, 1]; v = evec[:, 0]
    llarg_marca = np.sqrt(ev[1]) * 2.2; ample_marca = max(np.sqrt(ev[0]) * 2.2, 8)
    fig, axs = plt.subplots(1, 2, figsize=(15, 5)); res[k] = {}
    for ax, (nom, dir1, dir2, L) in zip(axs, (('al llarg de la marca', u, v, llarg_marca * 1.6), ('de través (perpendicular)', v, u, max(300, ample_marca * 5)))):
        mitja = min(150 / f, (ample_marca if dir1 is u else llarg_marca) * 0.8)
        for cn, img, col in CURVES:
            t, y = perfil(img, c, dir1, dir2, int(L), int(mitja)); yn = normal(t, y)
            ax.plot(t, yn, color=col, lw=1.6, label=cn)
            dins = np.abs(t) <= (llarg_marca if dir1 is u else ample_marca) * f
            res[k].setdefault(nom, {})[cn] = round(float(np.nanmin(yn[dins])), 2) if np.isfinite(yn[dins]).any() else None
        lim = (llarg_marca if dir1 is u else ample_marca) * f
        ax.axvspan(-lim, lim, color='#ff8c00', alpha=0.12, label='la marca de Pere'); ax.axhline(0, color='k', lw=0.6)
        ax.set_title(f'Marca {k} · {nom}'); ax.set_xlabel('px (llenç)'); ax.set_ylabel('nivell respecte de la tendència (%)'); ax.grid(alpha=0.3)
    axs[0].legend(fontsize=8, loc='lower left'); fig.suptitle(f"Marca {k}: r = {m['r_Rsol']} R☉, {m['angle_des_del_nord']}° des del nord", fontsize=11)
    fig.tight_layout(); fig.savefig(OUT / f'vistes/perfils_marca_{k:02d}.png', dpi=90); plt.close(fig)
json.dump(dict(nota='mínim dins de la marca de ln(nivell) − tendència, en %', marques=res), open(OUT / 'PERFILS.json', 'w'), ensure_ascii=False, indent=1)
for k, d in res.items(): print(k, json.dumps(d, ensure_ascii=False))
