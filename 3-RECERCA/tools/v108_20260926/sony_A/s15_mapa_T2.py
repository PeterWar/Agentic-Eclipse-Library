"""s15 · Mapa (angle, desplaçament) de la profunditat al voltant de T2 (geometria M3), dθ ±4° (pas 0,1°) i t ±90 px (pas 1), a l'apilat A
(control, pilot, Wiener), al compost del pilot i als seus nuls (la mateixa graella centrada a rectes paral·leles a ±300 px). Serveix per
veure si el que la cerca troba després del flat 2D és T2 o una altra recta (p. ex. paral·lela a les files del sensor d'A, que al llenç
van a 136,3°). Sortida: S15_MAPA_T2.json."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
tr = TRACOS[2]; box = caixa_tr(tr, 900); TH = np.round(np.arange(-4.0, 4.001, 0.1), 2); TT = np.arange(-90, 90.1, 1.0); res = {}
ang0 = float(np.degrees(np.arctan2(tr['d'][1], tr['d'][0])) % 180)
FONTS2 = {'A_ctrl': FONTS['A_ctrl'], 'A_pilot': FONTS['A_f2d'], 'A_wiener': (OUT / 'variant_wiener/apilats/sony_A_total.npy', 1), 'compost_ctrl': FONTS['compost_ctrl'], 'compost_pilot': FONTS['compost_f2d']}
def mapa(r, c, d):
    M = np.full((len(TH), len(TT)), np.nan, np.float32)
    for i, g in enumerate(TH):
        t, pr, _ = perfil(r, box[:2], c, gira(d, g), tr['llarg'], tmax=160)
        for j, t0 in enumerate(TT): M[i, j] = profunditat(t, pr, t0)
    return M
for nom, (p, ch) in FONTS2.items():
    a = np.load(p, mmap_mode='r'); r = rel_map(retall(a, ch, box))
    M = mapa(r, tr['centre'], tr['d']); i, j = np.unravel_index(np.nanargmin(M), M.shape)
    nm = [np.nanmin(mapa(r, tr['centre'] + off * tr['n'], tr['d'])) for off in (-300, 300)]
    res[nom] = dict(minim=float(M[i, j]), dtheta=float(TH[i]), angle_llenc=float((ang0 + TH[i]) % 180), t=float(TT[j]), a_la_geometria_M3=float(M[len(TH) // 2, len(TT) // 2]), minims_nuls_300px=[float(x) for x in nm],
                    perfil_dtheta_al_minim=M[i].tolist(), perfil_angle_a_t_minim=M[:, j].tolist())
    print(f"{nom:13s}: mínim {M[i, j]*1e4:+.1f}‱ a dθ {TH[i]:+.1f}° (angle al llenç {(ang0 + TH[i]) % 180:.1f}°; files del sensor d'A: 136,3°), t {TT[j]:+.0f} px · a M3 {M[len(TH)//2, len(TT)//2]*1e4:+.1f}‱ · mínims dels mapes nuls a ±300 px: {nm[0]*1e4:+.1f} / {nm[1]*1e4:+.1f}‱", flush=True)
res['angle_M3'] = ang0; desa(OUT / 'S15_MAPA_T2.json', res)
