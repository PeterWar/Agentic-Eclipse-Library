"""Capa «CEL blau-gris» (19-08-2026, vespre): desplaça el color del cel (no de la corona) cap a un blau menys
saturat, del to de la corona exterior, perquè la transició corona→cel sigui només de luminància i no de croma
(l'ull llegeix una vora de croma com un halo). Additiu per píxel amb pes = (cel fosc per luminància) × (rampa
radial 3,5→5,5 R☉): Linear Light 0,5 + w·(objectiu − cel)/2. Dues variants: V1 (sat 0,42) i V2 (sat 0,32); el
cel actual és (0,093, 0,146, 0,197), sat 0,53, to 210°."""
import os, sys, numpy as np, cv2, tifffile
SCR = os.environ.get('FD3_SCR', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/5aa2c2e9-5325-491b-a6ff-4feeb4581ac0/scratchpad/sf3')
HO = os.path.join(SCR, 'halo'); OUT = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Capes_SEMIFINAL3_a_10')
W, H = 7648, 5353; SOL = (4021.35, 2737.90); R_SOL = 959 / 2.1495
ICC = open(os.path.join(SCR, 'perfil_semifinal2.icc'), 'rb').read()
def smooth01(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
def u16(a): return np.clip(np.rint(np.asarray(a, np.float32) * 65535.0), 0, 65535).astype(np.uint16)
m = np.load(os.path.join(HO, 'semifinal5_merged.npy'), mmap_mode='r')
yy = (np.arange(H, dtype=np.float32) - SOL[1])[:, None]; xx = (np.arange(W, dtype=np.float32) - SOL[0])[None, :]
rr = np.hypot(xx, yy).astype(np.float32)
lum = np.zeros((H, W), np.float32)
for c in range(3): lum += np.asarray(m[..., c], np.float32) / 65535.0 / 3
sky = np.array([np.median(np.asarray(m[..., c])[rr > 8 * R_SOL]) / 65535.0 for c in range(3)], np.float32)
print('cel actual', sky.round(4))
w = (smooth01((0.26 - lum) / 0.08) * smooth01((rr - 3.5 * R_SOL) / (2.0 * R_SOL))).astype(np.float32)
w = cv2.GaussianBlur(w, (0, 0), 3)
tifffile.imwrite(os.path.join(OUT, 'MASCARA_cel.tif'), u16(w), photometric='minisblack', compression='zlib', metadata=None, resolution=(300, 300), description='Mascara del cel: luminancia baixa i r > 3.5-5.5 R', extratags=[(34675, 7, len(ICC), ICC, False)])
np.save(os.path.join(HO, 'mascara_cel.npy'), u16(w))
for nom, tgt in (('V1_sat042', (0.110, 0.150, 0.190)), ('V2_sat032', (0.125, 0.155, 0.185))):
    shift = np.array(tgt, np.float32) - sky
    lay = np.empty((H, W, 3), np.uint16)
    for c in range(3): lay[..., c] = u16(0.5 + shift[c] / 2.0)          # constant; la màscara fa el pes
    tifffile.imwrite(os.path.join(OUT, f'CEL_blaugris_{nom}_LinearLight.tif'), lay, photometric='rgb', compression='zlib', metadata=None, resolution=(300, 300),
                     description=f'CEL blau-gris {nom}: Linear Light amb MASCARA_cel; desplacament {shift.round(4).tolist()}', extratags=[(34675, 7, len(ICC), ICC, False)])
    np.save(os.path.join(HO, f'cel_{nom}.npy'), lay)
    print(nom, 'desplaçament', shift.round(4))
print('fet')
