"""b1 (V117, 29-09-2026) · FILTRE DE DETALL RADIAL COHERENT ENTRE ELS DOS APUNTAMENTS DE LA SONY («l'accident fortuït» de Pere), CORREGIT.
Còpia de v116_20260929/b1_filtre_coherent_AB.py amb TRES canvis (els dos primers són errors de la V116):
  1. A i B entren TAL QUAL: els apilats «_total» ja són normalitzats; la V116 els dividia pels pesos, que segueixen el senyal i n'esborraven
     estructura real (lliçó de la marca taronja, 29-09). Els pesos només diuen ON hi ha dada (pes > 0).
  2. A és l'apilat ORIGINAL (flat2d_v5/apilats/sony_A_total.npy), no el corregit de la V113: aquella cura hi copiava l'estructura de B a escales de
     25–600 px al domini de les marques 2, 3, 5 i a la vora d'A, i això hi fabricaria coincidència falsa entre A i B.
  3. La taca de l'eix òptic d'A (radi 320 px, com f1_correccio_sonyA) queda fora del camp comú.
La matemàtica, la de la V116: pla LOG-POLAR centrat al Sol; a cada apuntament, detall azimutal D_X = G_θ(0,15°)·ln X − G_θ(1,5°)·ln X amb
suavitzat radial d'un 1,5 % de r; coherència local w = max(0, ⟨D_A·D_B⟩) / (½(⟨D_A²⟩ + ⟨D_B²⟩)) (finestra 5 % de r × 1°); D = w·(D_A + D_B)/2.
Ús: b1_filtre_coherent_AB.py <carpeta_sortida>  → D_coherent_f32.npy, W_coherencia_f16.npy, DA_f16.npy, DB_f16.npy, B1_REBUT.json"""
import sys, json, time, hashlib, numpy as np, cv2
from pathlib import Path
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]; OUT = Path(sys.argv[1]).resolve(); OUT.mkdir(parents=True, exist_ok=True); t0 = time.time()
F = dict(A=R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/sony_A_total.npy', Aw=R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v29/sony_A_weights.npy',
         B=R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_total_v42.npy', Bw=R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_B/cau/sony_B_weights_v42.npy',
         estrelles=R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/sources/star_footprints.npy')
H, W = 7506, 10551; SOL = (5361.768, 3775.748); RS = 440.603
geo = json.loads((R / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/v36_rgb_dependencies/geometry.json').read_text())
GX, GY = (np.array(geo['M_llenc_a_v23']) @ np.array([2825, 3988, 1.0])).tolist()          # la taca de l'eix d'A (com f1 i el b3)
def llum(ft, fw):
    """lluminància (R + 2G + B)/4 de l'apilat TAL QUAL, i el suport: tots els canals finits i > 0, i pes > 0."""
    t = np.load(ft, mmap_mode='r'); w = np.load(fw, mmap_mode='r'); L = np.zeros((H, W), np.float32); m = np.ones((H, W), bool)
    for y0 in range(0, H, 1024):
        s = slice(y0, min(H, y0 + 1024)); a = np.asarray(t[s], np.float32); ww = np.asarray(w[s], np.float32)
        L[s] = (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4; m[s] = np.all(np.isfinite(a) & (a > 0) & (ww > 0), axis=2)
    return np.where(m, L, 0).astype(np.float32), m
def suport():
    """suports d'A i de B (tots els canals finits i > 0, pes > 0; A sense la taca de l'eix) i les estrelles fora; lluminàncies."""
    LA, mA = llum(F['A'], F['Aw']); LB, mB = llum(F['B'], F['Bw'])
    yy_, xx_ = np.ogrid[:H, :W]; mA &= np.hypot(xx_ - GX, yy_ - GY) > 320
    st = np.load(F['estrelles'], mmap_mode='r'); st = ndi.binary_dilation(np.asarray(st) > 0, iterations=3)
    return LA, LB, mA & mB & ~st
r0, r1 = 1.12 * RS, 10.5 * RS; NR = 4096; NT = 24576
rho = np.linspace(np.log(r0), np.log(r1), NR).astype(np.float32); th = (np.arange(NT) * 2 * np.pi / NT).astype(np.float32)
_rr = np.exp(rho)[:, None]; MX = (SOL[0] + _rr * np.cos(th)[None, :]).astype(np.float32); MY = (SOL[1] - _rr * np.sin(th)[None, :]).astype(np.float32)
dr = float(rho[1] - rho[0]); dth = 2 * np.pi / NT
SR = 0.015 / dr; S1, S2 = np.radians(0.15) / dth, np.radians(1.5) / dth; WR, WT = 0.05 / dr, np.radians(1.0) / dth
cv2.setNumThreads(8)
def polar(x, interp=cv2.INTER_LINEAR): return cv2.remap(x.astype(np.float32), MX, MY, interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
def gcv(x, sr, st_):
    """gaussiana (σ_ρ, σ_θ en mostres) amb θ periòdic: farciment circular manual (cv2 no fa BORDER_WRAP) i cv2.GaussianBlur (multifil)."""
    p = int(4 * st_) + 2; xp = np.concatenate([x[:, -p:], x, x[:, :p]], 1)
    return cv2.GaussianBlur(xp, (0, 0), sigmaX=float(st_), sigmaY=float(sr), borderType=cv2.BORDER_REFLECT)[:, p:-p]
def nucli(LA, LB, m):
    """el filtre al pla log-polar: torna PM, DA, DB, w, D_wiener = w·(DA + DB)/2 i D_min = w·[mateix signe]·signe·min(|DA|, |DB|) (el que veuen totes dues)."""
    PM = polar(m.astype(np.float32)) > 0.999
    xA = np.where(PM, np.log(np.maximum(polar(LA), 1e-9)), 0).astype(np.float32); xB = np.where(PM, np.log(np.maximum(polar(LB), 1e-9)), 0).astype(np.float32)
    den_cache = {}
    def gn(x, sr, st_):
        if (sr, st_) not in den_cache: den_cache[(sr, st_)] = gcv(PM.astype(np.float32), sr, st_)
        den = den_cache[(sr, st_)]; num = gcv(np.where(PM, x, 0).astype(np.float32), sr, st_); return num / np.maximum(den, 1e-6), den
    def detall(x):
        a, _ = gn(x, SR, S1); b, _ = gn(x, SR, S2); return np.where(PM, a - b, 0).astype(np.float32)
    DA, DB = detall(xA), detall(xB); del xA, xB
    cov, den = gn(DA * DB, WR, WT); vA, _ = gn(DA * DA, WR, WT); vB, _ = gn(DB * DB, WR, WT)
    w = np.clip(cov / np.maximum(0.5 * (vA + vB), 1e-12), 0, 1).astype(np.float32); w[~PM] = 0
    feather = np.clip((den - 0.6) / 0.4, 0, 1).astype(np.float32); w *= feather
    Dw = (w * 0.5 * (DA + DB)).astype(np.float32)
    Dm = (w * np.where(DA * DB > 0, np.sign(DA) * np.minimum(np.abs(DA), np.abs(DB)), 0)).astype(np.float32)
    return PM, DA, DB, w, Dw, Dm
_IXY = {}
def cart(P):
    if not _IXY:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rc = np.hypot(xx - SOL[0], yy - SOL[1]); tc = np.mod(np.arctan2(-(yy - SOL[1]), xx - SOL[0]), 2 * np.pi)
        _IXY['IX'] = (tc / (2 * np.pi) * NT).astype(np.float32); _IXY['IY'] = ((np.log(np.maximum(rc, 1)) - rho[0]) / dr).astype(np.float32)
        _IXY['fora'] = (_IXY['IY'] < 0) | (_IXY['IY'] > NR - 1)
    Pw = np.concatenate([P, P[:, :2]], 1)
    out = cv2.remap(Pw, _IXY['IX'], _IXY['IY'], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0); out[_IXY['fora']] = 0; return out
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
if __name__ == '__main__':
    OUT = Path(sys.argv[1]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
    LA, LB, m = suport(); print(f'llegit {time.time() - t0:.0f}s · camp comú {m.mean():.3f}', flush=True)
    PM, DA, DB, w, Dw, Dm = nucli(LA, LB, m); del LA, LB
    print(f'filtre {time.time() - t0:.0f}s', flush=True)
    viu = ~m & ~ndi.binary_dilation(m, iterations=2)
    for nom, P in (('D_coherent_f32.npy', Dw), ('D_minim_f32.npy', Dm)):
        c = cart(P); c[viu] = 0; np.save(OUT / nom, c.astype(np.float32))
    Wc = cart(w); np.save(OUT / 'W_coherencia_f16.npy', Wc.astype(np.float16))
    np.save(OUT / 'DA_f16.npy', cart(DA).astype(np.float16)); np.save(OUT / 'DB_f16.npy', cart(DB).astype(np.float16))
    Dc = np.load(OUT / 'D_coherent_f32.npy', mmap_mode='r'); Dmc = np.load(OUT / 'D_minim_f32.npy', mmap_mode='r')
    rep = dict(guio=str(Path(__file__).relative_to(R)), entrades={k: str(v.relative_to(R)) for k, v in F.items()}, sha256_entrades={k: sha(v) for k, v in F.items() if k in ('A', 'B')},
               canvis_sobre_la_V116=['A i B tal qual (sense dividir pels pesos; els pesos només com a suport)', 'A original (flat2d_v5), sense la cura V113 que hi copiava estructura de B', 'taca de l\'eix d\'A fora (r 320 px)', 'a més de D = w·(DA + DB)/2, la combinació «mínim concordant» D_min = w·signe·min(|DA|, |DB|) si DA i DB tenen el mateix signe (0 si no)'],
               taca_eix_A=[GX, GY, 320], log_polar=dict(r0_Rsol=1.12, r1_Rsol=10.5, NR=NR, NT=NT), suavitzat_radial_frac_r=0.015, detall_azimutal_graus=[0.15, 1.5], finestra_coherencia=dict(frac_r=0.05, graus=1.0),
               camp_comu=float(m.mean()), segons=round(time.time() - t0, 1))
    for a, b in ((1.3, 2), (2, 3.5), (3.5, 5.5), (5.5, 9.5)):
        rq = np.hypot(np.arange(W)[None, ::4] - SOL[0], np.arange(H)[::4, None] - SOL[1]) / RS; k = (rq >= a) & (rq < b) & m[::4, ::4]
        rep[f'banda_{a}-{b}'] = dict(w_mediana=float(np.median(Wc[::4, ::4][k])), sd_D_pct=float(np.std(Dc[::4, ::4][k]) * 100), sd_Dmin_pct=float(np.std(Dmc[::4, ::4][k]) * 100))
    (OUT / 'B1_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False)[:1800])
