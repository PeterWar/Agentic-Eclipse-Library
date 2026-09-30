"""Capa radial que compensa la MITJANA dels filtres Overlay de Pere al camp exterior (19-08-2026, tarda).

Amb el halo fora, la base a 4–6,5 R☉ ja és al nivell del cel; els filtres en Overlay (v2_40 amb la
seva màscara, NRGF, radials) hi deixen un enfosquiment mitjà de fins a 3 nivells que abans quedava
amagat sota el halo: sota estirament es veu com un fossat fosc. Aquesta capa (Linear Light, a dalt
de tot) afegeix ρ(r) = mediana per anell de (base+FLAT+HALO) − mediana per anell de la composició
amb els filtres, rampa d'entrada de 3,0 a 3,8 R☉, suavitzada. Només radial, petita i llisa: no
pot crear estructura. Si es canvien opacitats o màscares dels filtres cal recalcular-la.
Entrades: halo/base_flat_halo_fora.npy, halo/semifinal4_merged.npy  → halo/anell_rho.json, halo/anell_delta.npy
"""
import os, json, numpy as np, cv2
SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
HO = os.path.join(SCR, 'halo')
W, H = 7648, 5353; SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495
BASE = os.environ.get('AC_BASE', os.path.join(HO, 'base_flat_halo_fora.npy'))
COMPO = os.environ.get('AC_COMP', os.path.join(HO, 'semifinal4_merged.npy'))
TAG = os.environ.get('AC_TAG', 'fora')
def smootherstep(t):
    t = np.clip(t, 0, 1); return t * t * t * (t * (t * 6 - 15) + 10)
def mediana_anells(img, rr, dr, r_min=0.0):
    n = int(rr.max() / dr) + 1
    idx = np.minimum((rr / dr).astype(np.int32), n - 1)
    sel = rr >= r_min
    v = img[sel]; ii = idx[sel]
    order = np.argsort(ii, kind='stable'); v = v[order]; ii = ii[order]
    b = np.searchsorted(ii, np.arange(n + 1))
    med = np.full(n, np.nan, np.float32)
    for k in range(n):
        if b[k + 1] - b[k] >= 30: med[k] = np.median(v[b[k]:b[k + 1]])
    return (np.arange(n) + 0.5) * dr, med
yy = (np.arange(H, dtype=np.float32) - SOL[1])[:, None]; xx = (np.arange(W, dtype=np.float32) - SOL[0])[None, :]
rr = np.hypot(xx, yy).astype(np.float32)
base = np.load(BASE, mmap_mode='r'); comp = np.load(COMPO, mmap_mode='r')
delta = np.empty((H, W, 3), np.float32); rhos = []
for c in range(3):
    r_c, mb = mediana_anells(np.asarray(base[..., c], np.float32) / 65535.0, rr, 4.0, r_min=1.2 * R_SOL)
    r_c, mc = mediana_anells(np.asarray(comp[..., c], np.float32) / 65535.0, rr, 4.0, r_min=1.2 * R_SOL)
    ok = np.isfinite(mb) & np.isfinite(mc)
    rho = np.interp(r_c, r_c[ok], (mb - mc)[ok]).astype(np.float32)
    rho *= smootherstep((r_c - 3.0 * R_SOL) / (0.8 * R_SOL))
    rho = cv2.GaussianBlur(rho.reshape(1, -1), (0, 0), 4.0, borderType=cv2.BORDER_REPLICATE).ravel()
    rho[r_c > 11.5 * R_SOL] = 0
    rhos.append(rho)
    delta[..., c] = np.interp(rr, r_c, rho).astype(np.float32)
    print(f'canal {c}: ρ a 3.5/4/4.5/5/5.5/6/6.5/7/8/9 R☉:', [round(float(np.interp(R * R_SOL, r_c, rho)), 4) for R in (3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 8, 9)])
np.save(os.path.join(HO, f'anell_delta_{TAG}.npy'), delta)
json.dump(dict(r_c=r_c.tolist(), rho=[r.tolist() for r in rhos]), open(os.path.join(HO, f'anell_rho_{TAG}.json'), 'w'))
print('fet')
