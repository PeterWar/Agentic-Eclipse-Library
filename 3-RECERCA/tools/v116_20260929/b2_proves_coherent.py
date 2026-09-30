"""b2 (V116, 29-09-2026) · Proves del filtre coherent A·B (b1), només amb la nostra dada:
  T1 rebuig d'artefactes d'un sol apuntament: a la franja de la vora del camp d'A (línia dura a baix a la dreta) i de B (a dalt a l'esquerra),
     |D| respecte de |D_A| o |D_B|;
  T2 soroll: al cel de 9–10 R☉, σ(D)/σ(D_A) i σ(D)/σ(D_B);
  T3 coherència amb la fusió LINEAL (fonts_c): correlació de D amb el mateix detall radial de la fusió (lineal, independent del filtre);
  T4 control NUL: la mateixa coherència amb B girat 1° (registre trencat) ha de caure (si no, la «coherència» no ve del cel registrat).
Ús: b2_proves_coherent.py <carpeta_b1>"""
import sys, json, numpy as np, cv2
from pathlib import Path
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]; B1 = Path(sys.argv[1]).resolve()
H, W = 7506, 10551; SOL = (5361.768, 3775.748); RS = 440.603; f = 2
D = np.asarray(np.load(B1 / 'D_coherent_f32.npy', mmap_mode='r')[::f, ::f], np.float32); DA = np.asarray(np.load(B1 / 'DA_f16.npy', mmap_mode='r')[::f, ::f], np.float32)
DB = np.asarray(np.load(B1 / 'DB_f16.npy', mmap_mode='r')[::f, ::f], np.float32); Wc = np.asarray(np.load(B1 / 'W_coherencia_f16.npy', mmap_mode='r')[::f, ::f], np.float32)
yy, xx = np.mgrid[0:H:f, 0:W:f]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS; val = (DA != 0) & (DB != 0)
out = {}
# T1: vores dels camps (on un sol apuntament té una vora dura): gradient de la cobertura de cada un
Aw = np.load(R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v29/sony_A_weights.npy', mmap_mode='r'); Bw = np.load(R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_B/cau/sony_B_weights_v42.npy', mmap_mode='r')
mA = np.asarray(Aw[::f, ::f, 1]) > 0; mB = np.asarray(Bw[::f, ::f, 1]) > 0
voraA = ndi.binary_dilation(mA ^ ndi.binary_erosion(mA, iterations=2), iterations=40) & mA & mB & val
voraB = ndi.binary_dilation(mB ^ ndi.binary_erosion(mB, iterations=2), iterations=40) & mA & mB & val
out['T1_vora_A'] = dict(px=int(voraA.sum()), rms_DA=float(np.sqrt(np.mean(DA[voraA] ** 2))), rms_DB=float(np.sqrt(np.mean(DB[voraA] ** 2))), rms_D=float(np.sqrt(np.mean(D[voraA] ** 2))))
out['T1_vora_B'] = dict(px=int(voraB.sum()), rms_DA=float(np.sqrt(np.mean(DA[voraB] ** 2))), rms_DB=float(np.sqrt(np.mean(DB[voraB] ** 2))), rms_D=float(np.sqrt(np.mean(D[voraB] ** 2))))
# T2: cel exterior
k = val & (rr > 9) & (rr < 10.3)
out['T2_cel_9_10'] = dict(px=int(k.sum()), sd_DA=float(np.std(DA[k])), sd_DB=float(np.std(DB[k])), sd_D=float(np.std(D[k])), D_sobre_DA=float(np.std(D[k]) / np.std(DA[k])))
# T3: correlació amb el detall radial de la fusió lineal (mateixa operació, sense coherència): polar com b1 però sobre la fusió
L = np.load(R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/sources/fusion_starless.npy', mmap_mode='r')
LF = np.asarray(L[::f, ::f, 1], np.float32)
def detall_radial(img):
    r0, r1 = 1.12 * RS / f, 10.5 * RS / f; NR, NT = 2048, 12288; rho = np.linspace(np.log(r0), np.log(r1), NR); th = np.arange(NT) * 2 * np.pi / NT
    s0 = (SOL[0] / f, SOL[1] / f); rrp = np.exp(rho)[:, None]
    MX = (s0[0] + rrp * np.cos(th)[None, :]).astype(np.float32); MY = (s0[1] - rrp * np.sin(th)[None, :]).astype(np.float32)
    P = cv2.remap(img, MX, MY, cv2.INTER_LINEAR, borderValue=0); pm = P > 0; x = np.where(pm, np.log(np.maximum(P, 1e-9)), 0).astype(np.float32)
    dr = rho[1] - rho[0]; dth = 2 * np.pi / NT
    def g(v, sr, st):
        p = int(4 * st) + 2; vp = np.concatenate([v[:, -p:], v, v[:, :p]], 1); return cv2.GaussianBlur(vp, (0, 0), sigmaX=float(st), sigmaY=float(sr), borderType=cv2.BORDER_REFLECT)[:, p:-p]
    den1 = g(pm.astype(np.float32), 0.015 / dr, np.radians(0.15) / dth); den2 = g(pm.astype(np.float32), 0.015 / dr, np.radians(1.5) / dth)
    d = g(x, 0.015 / dr, np.radians(0.15) / dth) / np.maximum(den1, 1e-6) - g(x, 0.015 / dr, np.radians(1.5) / dth) / np.maximum(den2, 1e-6)
    d[~pm] = 0
    yq, xq = np.mgrid[0:img.shape[0], 0:img.shape[1]].astype(np.float32); rc = np.hypot(xq - s0[0], yq - s0[1]); tc = np.mod(np.arctan2(-(yq - s0[1]), xq - s0[0]), 2 * np.pi)
    IX = (tc / (2 * np.pi) * NT).astype(np.float32); IY = ((np.log(np.maximum(rc, 1)) - rho[0]) / dr).astype(np.float32)
    dd = cv2.remap(np.concatenate([d, d[:, :2]], 1).astype(np.float32), IX, IY, cv2.INTER_LINEAR, borderValue=0); dd[(IY < 0) | (IY > NR - 1)] = 0; return dd
DL = detall_radial(LF)
for a, b in ((1.3, 2), (2, 3.5), (3.5, 5.5), (5.5, 9.5)):
    k = val & (rr >= a) & (rr < b) & (DL != 0)
    cc = lambda u, v: float(np.corrcoef(u[k], v[k])[0, 1])
    out[f'T3_correlacio_amb_fusio_{a}-{b}'] = dict(D=cc(D, DL), DA=cc(DA, DL), DB=cc(DB, DL))
# T4: control nul, B girat 1° al voltant del Sol (el cel ja no coincideix): coherència local amb la mateixa finestra, a la mateixa escala
M_ = cv2.getRotationMatrix2D((SOL[0] / f, SOL[1] / f), 1.0, 1.0); DBr = cv2.warpAffine(DB, M_, (DB.shape[1], DB.shape[0]), flags=cv2.INTER_LINEAR, borderValue=0)
def coh(u, v, s=12):
    num = cv2.GaussianBlur(u * v, (0, 0), s); da = cv2.GaussianBlur(u * u, (0, 0), s); db = cv2.GaussianBlur(v * v, (0, 0), s); return np.clip(num / np.maximum(0.5 * (da + db), 1e-12), 0, 1)
for nom, v in (('registrat', DB), ('B_girat_1graus', DBr)):
    c_ = coh(DA, v)
    out[f'T4_coherencia_{nom}'] = {f'{a}-{b}': float(np.median(c_[val & (DBr != 0) & (rr >= a) & (rr < b)])) for a, b in ((1.3, 2), (2, 3.5), (3.5, 5.5), (5.5, 9.5))}
(B1 / 'B2_PROVES.json').write_text(json.dumps(out, ensure_ascii=False, indent=1)); print(json.dumps(out, ensure_ascii=False, indent=1))
