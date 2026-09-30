"""c5 · Perfil PERPENDICULAR a cada traç marró de Pere (són línies, no zones): lluminància dels renders natius (V0 tal com està, V6 sense filtres),
cada ràster de filtre visible, la seva màscara, i les vores de camp (suport de la Vixen i de la Sony, pes de la Vixen, σ de resolució).
Per trobar a quina vora de camp o de màscara hi ha la banda fosca. Sortida: C5_PERFILS.json i LAMINA_C5_perfils.png."""
from v93_comu import *
from psb69 import PSB
import cv2, tifffile
claim(); V85 = ARREL / '4-RESULTATS/v85_regeneracio_20260922'; RD = SORT / 'renders'
z = np.load(SORT / 'marques_v92_classes.npz'); org = z['origin']; M = z['to_30_40']
n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.dilate(M.astype(np.uint8), np.ones((9, 9), np.uint8)), 8)
tracos = []
for k in range(1, n):
    ys, xs = np.nonzero((lab == k) & M)
    if xs.size < 5000: continue
    X = np.stack([xs + org[0], ys + org[1]], 1).astype(np.float64); c = X.mean(0); U, S_, Vt = np.linalg.svd(X - c, full_matrices=False); u = Vt[0]; v = np.array([-u[1], u[0]])
    s = (X - c) @ u; tracos.append(dict(c=c, u=u, v=v, s0=float(s.min()), s1=float(s.max()), px=int(xs.size)))
log(f'{len(tracos)} traços')
T = np.arange(-400, 401, 2.0)
def grid(tr):
    S = np.arange(tr['s0'] + 20, tr['s1'] - 20, 8.0); SS, TT = np.meshgrid(S, T); P = tr['c'][None, None, :] + SS[..., None] * tr['u'] + TT[..., None] * tr['v']; return P[..., 0].astype(np.float32), P[..., 1].astype(np.float32)
def perfil_arr(A, gx, gy, escala=1.0):
    x0, x1 = max(int(gx.min() / escala) - 2, 0), min(int(gx.max() / escala) + 3, A.shape[1]); y0, y1 = max(int(gy.min() / escala) - 2, 0), min(int(gy.max() / escala) + 3, A.shape[0])
    sub = np.asarray(A[y0:y1, x0:x1], np.float32); return cv2.remap(sub, gx / escala - x0, gy / escala - y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]
fonts = {}
for nm in ('V0_tal_com_esta', 'V6_sense_filtres', 'V2_sense_capes_ajust'): fonts[nm] = (lum(tifffile.imread(RD / f'{nm}_quart.tif')[..., :3].astype(np.float32) / 65535), W / 2638.0)
p = PSB(str(PSB_PERE)); vis = [L['id'] for L in p.layers if L['visible'] and L['id'] in FILTRES]
for lid in vis: fonts[f'filtre_{lid}'] = (np.load(ARREL / f'4-RESULTATS/v92_20260924/filtres_v92/{FILTRES[lid]}_u16.npy', mmap_mode='r'), 1.0)
for lid in vis: fonts[f'mascara_{lid}'] = (p.channel(lid, -2)[0], 1.0)
for nm, pth in (('suport', V85 / 'd4_baseline/products/sources/support.npy'), ('pes_vixen', V85 / 'b3_baseline/cau/weight_vixen_v42.npy'), ('sigma_resolucio', V85 / 'fixed_inputs/resolution_sigma.npy')):
    if pth.exists(): fonts[nm] = (np.load(pth, mmap_mode='r'), 1.0)
vx = np.load(V85 / 'd4_baseline/products/sources/vixen_starless.npy', mmap_mode='r'); sx = np.load(V85 / 'd4_baseline/products/sources/sony_starless.npy', mmap_mode='r')
rep = {'T_px': T.tolist(), 'tracos': []}
for i, tr in enumerate(tracos):
    gx, gy = grid(tr); out = {}
    for nm, (A, esc) in fonts.items():
        A2 = A if A.ndim == 2 else A[..., 1]
        pr = perfil_arr(A2.astype(np.float32) if not isinstance(A2, np.memmap) else A2, gx, gy, esc); out[nm] = np.nanmean(pr, 1)
    for nm, A in (('vixen_G', vx), ('sony_G', sx)):
        pr = perfil_arr(A[..., 1] if A.ndim == 3 else A, gx, gy, 1.0); out[nm + '_valid'] = np.nanmean(np.isfinite(pr) & (np.nan_to_num(pr) > 0), 1)
    info = dict(centre=tr['c'].round(1).tolist(), direccio=tr['u'].round(3).tolist(), llarg=round(tr['s1'] - tr['s0']), px=tr['px'])
    y0 = out['V0_tal_com_esta']; base = np.polyval(np.polyfit(T[np.abs(T) > 150], y0[np.abs(T) > 150], 2), T); dip = y0 - base
    info['V0_minim_relatiu_t_px'] = float(T[np.argmin(dip[np.abs(T) < 200])]) if True else None
    j = np.abs(T) < 200; info['V0_minim_relatiu'] = round(float(dip[j].min() / np.nanmean(y0)), 4); info['V0_minim_t'] = float(T[j][np.argmin(dip[j])])
    for nm in out:
        pr = out[nm]
        if np.all(np.isnan(pr)): continue
        g = np.abs(np.gradient(np.nan_to_num(pr, nan=np.nanmean(pr))))
        info[f'salt_max_{nm}'] = [float(T[np.argmax(g)]), round(float(np.nanmax(pr) - np.nanmin(pr)), 4)]
    rep['tracos'].append(dict(info=info, perfils={k: np.round(v, 5).tolist() for k, v in out.items()}))
    log(f"traç {i}: centre {info['centre']} llarg {info['llarg']}; V0 mínim {info['V0_minim_relatiu']} a t={info['V0_minim_t']}; salts: " + ', '.join(f"{k[5:]}@{v[0]:.0f}({v[1]})" for k, v in info.items() if k.startswith('salt_max_') and ('suport' in k or 'pes' in k or 'valid' in k or 'sigma' in k or 'mascara' in k)))
desa_json('C5_PERFILS.json', rep)
