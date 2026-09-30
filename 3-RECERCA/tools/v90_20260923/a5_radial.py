"""a5 (V90) · Els filtres perden resolució RADIAL prop del limbe (a l'estil de Brno, on els filtres no pesen arran del limbe): a la vora, la
dada és desenfocament del limbe lunar, la vora del domini i la continuació, i els filtres hi dibuixaven línies paral·leles al limbe (marques de
Pere a la V87 i la V88). Suavitzat gaussià NOMÉS al llarg del radi (els raigs, que són estructura azimutal real, no es toquen), amb σ_r(d) =
4 px × (1 − smoothstep(d, 4, 14)): 4 px fins a 4 px del limbe, 0 a partir de 14 px. Es fa en polars (0,05° × 0,25 px) i s'aplica com a DIFERÈNCIA
(tornada del suavitzat − tornada del polar sense suavitzar), de manera que on σ = 0 el ràster no canvia ni un bit.
Entrada: els 16 ràsters finals de la V88 (4-RESULTATS/v88_20260923/filtres_finals). Sortida: 4-RESULTATS/v90_20260923/filtres_radial/<tag>_u16.npy
i A5_RADIAL.json. Prova prèvia (compost emulat): les línies dobles i els grans de les marques desapareixen; nivell a 1–12 px 0,4760 → 0,4755."""
from v90_comu import *
from v86_operadors import smoothstep
import cv2
claim(); GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
TAGS = ['P01_NRGF', 'P01_NRGF_extrap', 'P02_RHEF', 'P02b_RHEF_ups0.35', 'P02c_RHEF_local60_native', 'P02d_RHEF_local30_native', '01', '04', '05', '06', '03', '03v30', '07', 'P03_MGN', 'P04_WOW', 'P05_WOW_bilateral']
S0, D1, D2 = 4.0, 4.0, 14.0; DMIN_P, DMAX_P, DR = -30.0, 30.0, 0.25; NT = 7200
FIN = ARREL / '4-RESULTATS/v88_20260923/filtres_finals'; OUT = SORT / 'filtres_radial'; OUT.mkdir(exist_ok=True)
m = int(R + DMAX_P + 4); bx0, bx1, by0, by1 = int(cx) - m, int(cx) + m + 1, int(cy) - m, int(cy) + m + 1
DS = np.arange(DMIN_P, DMAX_P + 1e-6, DR); TT, DD = np.meshgrid(np.radians((np.arange(NT) + 0.5) * 360 / NT), DS)
MX = (cx + (R + DD) * np.cos(TT) - bx0).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT) - by0).astype(np.float32)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; tt = (np.arctan2(-(yy - cy), xx - cx) + 2 * np.pi) % (2 * np.pi)
IX = (tt / (2 * np.pi) * NT - 0.5).astype(np.float32); IY = ((d - DS[0]) / DR).astype(np.float32)
sig = S0 * (1 - smoothstep(DS, D1, D2)); nivells = [0.0, 1.0, 2.0, 3.0, 4.0]; dins = (d > DMIN_P) & (d < DMAX_P)
def radial(X):
    P = cv2.remap(X, MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    Ps = [P] + [cv2.GaussianBlur(P, (1, 0), sigmaX=1e-3, sigmaY=s / DR) for s in nivells[1:]]
    Q_ = P.copy()
    for i in range(len(DS)):
        s = sig[i]
        if s <= 0: continue
        k = min(int(s), len(nivells) - 2); f = s - k; Q_[i] = (1 - f) * Ps[k][i] + f * Ps[k + 1][i]
    back = lambda A: cv2.remap(A, np.mod(IX, NT), IY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return np.where(dins, X + (back(Q_) - back(P)), X)
rep = dict(sigma_radial_px=S0, fosa_px=[D1, D2], polar=dict(azimut_graus=360 / NT, radi_px=DR), caixa=[bx0, by0, bx1, by1], font=str(FIN.relative_to(ARREL)), capes={})
for tag in TAGS:
    u = np.load(FIN / f'{tag}_u16.npy'); X = u[by0:by1, bx0:bx1].astype(np.float32) / 65535; Xn = np.clip(radial(X), 0, 1)
    out = u.copy(); out[by0:by1, bx0:bx1] = np.round(Xn * 65535).astype(np.uint16); np.save(OUT / f'{tag}_u16.npy', out)
    dif = np.abs(out.astype(np.int32) - u.astype(np.int32)); fora = dif[by0:by1, bx0:bx1][d >= D2]
    rep['capes'][tag] = dict(sha256=sha(OUT / f'{tag}_u16.npy'), canvi_max_DN16=int(dif.max()), canvi_max_mes_enlla_de_14px=int(fora.max()) if fora.size else 0, px_canviats=int((dif > 0).sum()))
    log(f"{tag}: canvi màx {rep['capes'][tag]['canvi_max_DN16']} DN16; més enllà de 14 px {rep['capes'][tag]['canvi_max_mes_enlla_de_14px']}")
desa_json('A5_RADIAL.json', rep); log('A5 fet')
