"""a5c (V91) · El suavitzat radial dels filtres prop del limbe (V90, a5_radial) NOMÉS on hi havia les línies: 104–228° d'azimut.
Per què: a la V90 el suavitzat (σ 4 px → 0 a 14 px) es va aplicar a tot el voltant. On no hi havia línies, estirava la textura en la direcció
del radi i Pere hi va veure una «lent» (capa «Artefactes V90», marques roses a 0–32°, 45–98° i 230,5–305°). El primer criteri (a5b: l'alçada
del limbe lunar sobre el solar) encara suavitzava a 230–258° (la lent hi quedava, vist a 4:1 al compost de Photoshop). Les línies eren on Pere
les va marcar a la V88 (104–119°, 121–152°, 211°, 216–229°) i la lent comença just on acaben (230,5°). L'índex d'estructura paral·lela al limbe
(a6) no discrimina (el domina el salt de la Lluna), o sigui que el criteri són les dues marques de Pere. Força: S(θ) = 4 px ×
smoothstep(θ, 99°, 104°) × (1 − smoothstep(θ, 228°, 232°)). σ(θ, d) = S(θ) × (1 − smoothstep(d, 4, 14)). Polars 0,05° × 0,25 px, aplicat com a
diferència: on σ = 0 el ràster és bit a bit el de la V88. Entrada: els 16 ràsters finals de la V88. Sortida: filtres_radial_c/<tag>_u16.npy
i A5C_RADIAL.json."""
from v91_comu import *
from v86_operadors import smoothstep
import cv2
claim(); GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
TAGS = ['P01_NRGF', 'P01_NRGF_extrap', 'P02_RHEF', 'P02b_RHEF_ups0.35', 'P02c_RHEF_local60_native', 'P02d_RHEF_local30_native', '01', '04', '05', '06', '03', '03v30', '07', 'P03_MGN', 'P04_WOW', 'P05_WOW_bilateral']
S0, D1, D2, A0, A1, A2, A3 = 4.0, 4.0, 14.0, 99.0, 104.0, 228.0, 232.0; DMIN_P, DMAX_P, DR = -30.0, 30.0, 0.25; NT = 7200
FIN = ARREL / '4-RESULTATS/v88_20260923/filtres_finals'; OUT = SORT / 'filtres_radial_c'; OUT.mkdir(exist_ok=True)
m = int(R + DMAX_P + 4); bx0, bx1, by0, by1 = int(cx) - m, int(cx) + m + 1, int(cy) - m, int(cy) + m + 1
TS = np.radians((np.arange(NT) + 0.5) * 360 / NT); DS = np.arange(DMIN_P, DMAX_P + 1e-6, DR); TT, DD = np.meshgrid(TS, DS)
h = np.hypot(cx + R * np.cos(TS) - CX, cy - R * np.sin(TS) - CY) - RS; TSg = np.degrees(TS); S = S0 * smoothstep(TSg, A0, A1) * (1 - smoothstep(TSg, A2, A3))
SIG = (S[None, :] * (1 - smoothstep(DS, D1, D2))[:, None]).astype(np.float32)          # (len(DS), NT)
MX = (cx + (R + DD) * np.cos(TT) - bx0).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT) - by0).astype(np.float32)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; tt = (np.arctan2(-(yy - cy), xx - cx) + 2 * np.pi) % (2 * np.pi)
IX = (tt / (2 * np.pi) * NT - 0.5).astype(np.float32); IY = ((d - DS[0]) / DR).astype(np.float32); dins = (d > DMIN_P) & (d < DMAX_P)
K = np.clip(np.floor(SIG).astype(int), 0, 3); FR = (SIG - K).astype(np.float32)
def radial(X):
    P = cv2.remap(X, MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    St = np.stack([P] + [cv2.GaussianBlur(P, (1, 0), sigmaX=1e-3, sigmaY=s / DR) for s in (1.0, 2.0, 3.0, 4.0)])     # (5, len(DS), NT)
    A = np.take_along_axis(St, K[None], 0)[0]; B = np.take_along_axis(St, (K + 1)[None], 0)[0]; Q_ = np.where(SIG > 0, (1 - FR) * A + FR * B, P)
    back = lambda Z: cv2.remap(Z, np.mod(IX, NT), IY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return np.where(dins, X + (back(Q_) - back(P)), X)
TSd = np.degrees(TS)
rep = dict(sigma_max_px=S0, fosa_radial_px=[D1, D2], finestra_azimut_graus=[A0, A1, A2, A3], S_per_sector={f'{a}-{a + 20}': round(float(S[(TSd >= a) & (TSd < a + 20)].mean()), 2) for a in range(0, 360, 20)},
           h_per_sector={f'{a}-{a + 20}': round(float(h[(TSd >= a) & (TSd < a + 20)].mean()), 1) for a in range(0, 360, 20)}, caixa=[bx0, by0, bx1, by1], font=str(FIN.relative_to(ARREL)), capes={})
for tag in TAGS:
    u = np.load(FIN / f'{tag}_u16.npy'); X = u[by0:by1, bx0:bx1].astype(np.float32) / 65535; Xn = np.clip(radial(X), 0, 1)
    out = u.copy(); out[by0:by1, bx0:bx1] = np.round(Xn * 65535).astype(np.uint16); np.save(OUT / f'{tag}_u16.npy', out)
    dif = np.abs(out.astype(np.int32) - u.astype(np.int32)); ys_, xs_ = np.nonzero(dif > 0)
    az = (np.degrees(np.arctan2(-(ys_ - cy), xs_ - cx)) + 360) % 360 if xs_.size else np.array([])
    rep['capes'][tag] = dict(sha256=sha(OUT / f'{tag}_u16.npy'), px_canviats=int(xs_.size), fraccio_canvis_fora_de_99_232_graus=round(float(((az < 98.5) | (az > 232.5)).mean()), 4) if az.size else 0.0)
    log(f"{tag}: px canviats {xs_.size}; fora de 99–232° {rep['capes'][tag]['fraccio_canvis_fora_de_99_232_graus']}")
desa_json('A5C_RADIAL.json', rep); log('S per sector: ' + json.dumps(rep['S_per_sector'])); log('A5C fet')
