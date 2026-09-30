"""a4 (V90) · Continuació dels ràsters de filtre arran del limbe amb VALOR I PENDENT continus (C1), en lloc de la de la V88 (valor de DMIN+4
allargat pla cap endins, amb una fosa de 3 px): aquella feia un tram pla que es trobava amb el pendent real de la corona, i l'ull hi veia línies
paral·leles al limbe (bandes de Mach). Diagnosi: 4-RESULTATS/v88_marques_pere_20260923 i v89_proves_20260923.
Per a cada ràster (els 16 de a3, amb l'entrada sense la pujada de a3c): unió J(θ) = DMIN(θ) + 2 px (els 2 primers px de dada porten la resposta
d'un sol costat dels filtres, com a la V88); a cada píxel, el valor del mateix filtre a J al llarg del seu raig, més el pendent radial del filtre a
J..J+3 (mitjana per azimut de 0,25°, suavitzada 1°) × (d − J); fosa smoothstep de J − 1 a J + 1 amb la dada. Més enllà de J + 1, el ràster de a3
tal qual. Cel·les indefinides del RHEF local fora d'aquesta zona: com a la V88 (mitjana normalitzada dels veïns, σ 4 px).
Sortida: 4-RESULTATS/v90_20260923/filtres_finals/<tag>_u16.npy i A4_C1.json."""
from v90_comu import *
from v86_operadors import smoothstep, ng
from scipy.ndimage import gaussian_filter1d
import cv2
claim()
TAGS = ['P01_NRGF', 'P01_NRGF_extrap', 'P02_RHEF', 'P02b_RHEF_ups0.35', 'P02c_RHEF_local60_native', 'P02d_RHEF_local30_native', '01', '04', '05', '06', '03', '03v30', '07', 'P03_MGN', 'P04_WOW', 'P05_WOW_bilateral']
C = SORT / 'filtres'; F = SORT / 'filtres_finals'; F.mkdir(exist_ok=True)
GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
Q = np.load(SORT / 'A3A_franja_un_instant.npz'); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; DMIN = Q['DMIN']; NBZ = len(DMIN)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xx - cx, yy - cy).astype(np.float32); d = rL - R
th = ((np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360).astype(np.float32); ib = (th / 360 * NBZ).astype(int) % NBZ; ang = np.radians(th)
J = (DMIN[ib] + 2.0).astype(np.float32); zona = (d < J + 1.0) & (rL < R + 60); wgt = smoothstep(d, J - 1.0, J + 1.0).astype(np.float32)
cnt = np.maximum(np.bincount(ib.ravel(), minlength=NBZ), 1)
def at(X, rr): return cv2.remap(X, (cx + rr * np.cos(ang) - bx0).astype(np.float32), (cy - rr * np.sin(ang) - by0).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
rep = dict(unio='DMIN + 2 px', fosa_px=[-1, 1], pendent='J..J+3 px, mitjana per azimut 0,25°, gaussiana 1°', zona_px=int(zona.sum()), zona_fora_disc_px=int((zona & (d > 0)).sum()), capes={})
sup_full = np.load(FONTS / 'support.npy')
for tag in TAGS:
    u = np.load(C / f'{tag}_u16.npy'); extra = {}
    if tag.endswith('_native'):
        q = np.load(C / f'{tag}_float.npy', mmap_mode='r'); und = sup_full & ~np.isfinite(q); und[by0:by1, bx0:bx1] &= ~zona; extra['indefinides_omplertes'] = int(und.sum())
        if und.any():
            uf = u.astype('float32') / 65535; fill = ng(uf, sup_full & ~und, 4.0); uf[und] = fill[und]; u = np.round(np.clip(uf, 0, 1) * 65535).astype('uint16')
    X = u[by0:by1, bx0:bx1].astype(np.float32) / 65535
    vJ = at(X, R + J); v3 = at(X, R + J + 3.0)
    s = gaussian_filter1d(np.bincount(ib.ravel(), weights=((v3 - vJ) / 3.0).ravel(), minlength=NBZ) / cnt, 4, mode='wrap')[ib]
    Xc = vJ + s * (d - J); fos = np.where(zona, wgt * X + (1 - wgt) * Xc, X)
    out = u.copy(); out[by0:by1, bx0:bx1] = np.round(np.clip(fos, 0, 1) * 65535).astype('uint16')
    np.save(F / f'{tag}_u16.npy', out); rep['capes'][tag] = dict(sha256=sha(F / f'{tag}_u16.npy'), **extra); log(tag + ' continuat (C1)')
desa_json('A4_C1.json', rep); log('A4 C1 fet')
