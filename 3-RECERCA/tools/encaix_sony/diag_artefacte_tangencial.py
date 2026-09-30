"""L'artefacte tangencial que Pere marca a 1,7–1,9 R☉ (baix a l'esquerra): d'on surt?
La zona és r < 3 → la meva capa hi és exactament la capa Vixen de Pere. Es mira:
 - la capa de Pere i la meva (idèntiques allà),
 - els apilats lineals de l'HDR4 (10,3 s, 2 s, 1 s, 1/2 s, 1/4 s) a la mateixa reixa (llenç = [87:4640,143:6891]),
amb la regió girada perquè la línia de Pere quedi horitzontal, i perfils perpendiculars promitjats.
També la saturació del 10,3 s (i el 2 s) al voltant de la línia."""
import os, glob, numpy as np, rawpy, tifffile
from scipy import ndimage as ndi
from PIL import Image, ImageDraw

SP = os.path.dirname(os.path.abspath(__file__))
D = os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT/')
vix = np.load(os.path.join(SP, 'vixen_canvas_rgb.npy'))
new = tifffile.imread(D + 'APILAT_Capa_Sony_encaixada_VORESNETES_EXTENSIO_TANGENCIAL_MITJA_6748x4553.tif').astype(np.float32) / 65535
r = np.load(os.path.join(SP, 'r_rsol.npy'))
lum = lambda a: 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
# línia de Pere (llenç): A=(2735,2714) B=(3440,3006)
A = np.array([2735.0, 2714.0]); Bp = np.array([3440.0, 3006.0])
ang = np.degrees(np.arctan2(Bp[1] - A[1], Bp[0] - A[0]))   # graus, y cap avall
C = 0.5 * (A + Bp); L = np.hypot(*(Bp - A))
print(f'línia: angle {ang:.1f}° (y avall), llargada {L:.0f} px, centre {C}, r al centre {r[int(C[1]), int(C[0])]:.2f}')

def rot_crop(img, cx, cy, ang_deg, w=1100, h=700):
    """Retall centrat a (cx,cy) girat perquè la direcció ang quedi horitzontal."""
    yy, xx = np.mgrid[-h // 2:h // 2, -w // 2:w // 2].astype(np.float64)
    a = np.radians(ang_deg)
    X = cx + xx * np.cos(a) - yy * np.sin(a); Y = cy + xx * np.sin(a) + yy * np.cos(a)
    return ndi.map_coordinates(img, [Y, X], order=1, mode='nearest')

srcs = {'capa Pere (L)': lum(vix), 'la meva capa (L)': lum(new)}
# HDR4 lineals
for f in sorted(glob.glob(os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Vixen/HDR4/apilats/0[1-6]_*.dng'))):
    with rawpy.imread(f) as rr:
        raw = rr.raw_image_visible.copy()
    g = (raw[..., 1].astype(np.float32) - 512.0)[87:4640, 143:6891]
    nom = os.path.basename(f).split('_')[1]
    srcs[f'HDR4 {nom} (G lineal)'] = g
    sat = (raw[..., :3].max(-1) >= 13990)[87:4640, 143:6891]
    srcs[f'HDR4 {nom} SAT'] = sat.astype(np.float32)

rows = []
prof = {}
for nom, img in srcs.items():
    rc = rot_crop(img, C[0], C[1], ang)
    prof[nom] = rc[:, 250:850].mean(1)   # perfil perpendicular, promitjat al llarg de 600 px de la línia
    if 'SAT' in nom:
        continue
    hp = rc - ndi.gaussian_filter(rc, 20)
    sd = 1.4826 * np.median(np.abs(hp - np.median(hp))) + 1e-9
    v = (np.clip(0.5 + hp / (8 * sd), 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(v); ImageDraw.Draw(im).text((5, 5), nom, fill=255)
    ImageDraw.Draw(im).line([(0, 350), (1100, 350)], fill=128)
    rows.append(np.asarray(im))
Image.fromarray(np.concatenate(rows, 0)).save(D + 'zoom_artefacte_girat_passalt.png')
print('PNG girat (línia horitzontal al mig, y=350):', len(rows), 'panells')
# perfils: derivada del perfil (a mode de detector de graons) i saturació al voltant de la línia
y = np.arange(-350, 350)
for nom, p in prof.items():
    if 'SAT' in nom:
        idx = np.where(p > 0.5)[0]
        print(f'  {nom:22s}: saturat (>50 % de la línia) fins a y = {y[idx].max() if len(idx) else None} px (línia a y=0, y<0 cap al Sol)')
        continue
    pn = p / max(np.median(p), 1e-9)
    hpp = pn - ndi.gaussian_filter1d(pn, 25)
    j = np.argmax(np.abs(hpp[300:400])) + 300
    print(f'  {nom:22s}: passa-alt màx a |y|<50: {100*hpp[j]:+.2f} % a y={y[j]}; rang passa-alt −150..150: {100*hpp[200:500].min():+.2f}…{100*hpp[200:500].max():+.2f} %')
np.savez(os.path.join(SP, 'perfils_artefacte.npz'), y=y, **{k.replace(' ', '_'): v for k, v in prof.items()})
