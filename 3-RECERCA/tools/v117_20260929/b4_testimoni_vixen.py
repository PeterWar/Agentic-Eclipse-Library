"""b4 (V117, 29-09-2026) · Pregunta de Pere: «no podies aconseguir el mateix efecte amb el Vixen?»
Posa la Vixen com a segon testimoni del filtre de la 415, amb el MATEIX nucli del b1 (log-polar centrat al Sol, detall azimutal 0,15°–1,5°,
suavitzat radial 1,5 % de r, coherència w a la finestra 5 % r × 1°, mínim concordant), sobre el suport comú A ∩ B ∩ Vixen.
La Vixen s'iguala abans a la resolució de la Sony (8,3″ contra 5,5″, mesura del 16-08): gaussiana de σ = √(8,3² − 5,5²)/2,355/escala.
Parelles A·B (referència, al mateix suport), A·V i B·V: coincidència (mediana de w), correlació del detall, control nul (el segon testimoni
girat 5° al voltant del Sol, més que l'escala més gran del filtre), i si el detall concordant A·V és el mateix que el A·B.
Només mesura: no toca cap PSB ni cap capa.
Ús: b4_testimoni_vixen.py <carpeta_sortida>"""
import sys, json, time, numpy as np, cv2
from pathlib import Path
from scipy import ndimage as ndi
sys.path.insert(0, str(Path(__file__).resolve().parent))
import b1_filtre_coherent_AB as b1          # només les funcions i la geometria (el b1 llegeix la mateixa carpeta de sortida)
t0 = time.time(); OUT = Path(sys.argv[1]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
R, H, W, RS = b1.R, b1.H, b1.W, b1.RS
AP = R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats'
ESCALA = 946.0 / RS                          # ″/px del llenç (radi solar aparent el 12-08-2026 ≈ 946″)
SIG_V = np.sqrt(8.3 ** 2 - 5.5 ** 2) / 2.355 / ESCALA
def llum_vixen():
    """lluminància (R + 2G + B)/4 de l'apilat de la Vixen TAL QUAL (com el b1 amb A i B), i el suport: canals finits i > 0, den > 0."""
    t = np.load(AP / 'vixen_total.npy', mmap_mode='r'); d = np.load(AP / 'vixen_den.npy', mmap_mode='r'); L = np.zeros((H, W), np.float32); m = np.zeros((H, W), bool)
    for y0 in range(0, H, 1024):
        s = slice(y0, min(H, y0 + 1024)); a = np.asarray(t[s], np.float32)
        L[s] = (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4; m[s] = np.all(np.isfinite(a) & (a > 0), axis=2) & (np.asarray(d[s]) > 0)
    return np.where(m, L, 0).astype(np.float32), m
LA, LB, mAB = b1.suport(); LV, mV = llum_vixen()
g = lambda x: cv2.GaussianBlur(x, (0, 0), float(SIG_V))
LV = np.where(mV, g(np.where(mV, LV, 0).astype(np.float32)) / np.maximum(g(mV.astype(np.float32)), 1e-6), 0).astype(np.float32)
m = mAB & ndi.binary_erosion(mV, iterations=4)
print(f'llegit {time.time() - t0:.0f}s · σ Vixen {SIG_V:.2f} px · suport A∩B {mAB.mean():.3f}, A∩B∩V {m.mean():.3f}', flush=True)
PM = b1.polar(m.astype(np.float32)) > 0.999; PM_AB = b1.polar(mAB.astype(np.float32)) > 0.999
_den = {}
def gn(x, sr, st, M, clau):
    if (sr, st, clau) not in _den: _den[(sr, st, clau)] = b1.gcv(M.astype(np.float32), sr, st)
    den = _den[(sr, st, clau)]; return b1.gcv(np.where(M, x, 0).astype(np.float32), sr, st) / np.maximum(den, 1e-6), den
def detall(L):
    x = np.where(PM, np.log(np.maximum(b1.polar(L), 1e-9)), 0).astype(np.float32)
    a, _ = gn(x, b1.SR, b1.S1, PM, 'PM'); c, _ = gn(x, b1.SR, b1.S2, PM, 'PM'); return np.where(PM, a - c, 0).astype(np.float32)
DA, DB, DV = detall(LA), detall(LB), detall(LV); del LA, LB, LV
def coh(D1, D2, M, clau):
    cov, den = gn(D1 * D2, b1.WR, b1.WT, M, clau); v1, _ = gn(D1 * D1, b1.WR, b1.WT, M, clau); v2, _ = gn(D2 * D2, b1.WR, b1.WT, M, clau)
    w = np.clip(cov / np.maximum(0.5 * (v1 + v2), 1e-12), 0, 1).astype(np.float32); w[~M] = 0; return w * np.clip((den - 0.6) / 0.4, 0, 1).astype(np.float32)
def dmin(D1, D2, w): return (w * np.where(D1 * D2 > 0, np.sign(D1) * np.minimum(np.abs(D1), np.abs(D2)), 0)).astype(np.float32)
GIR = int(round(5.0 / 360 * b1.NT)); roll = lambda x: np.roll(x, GIR, axis=1); PMg = PM & roll(PM)
w = {'A·B': coh(DA, DB, PM, 'PM'), 'A·V': coh(DA, DV, PM, 'PM'), 'B·V': coh(DB, DV, PM, 'PM'),
     'A·B nul 5°': coh(DA, roll(DB), PMg, 'g'), 'A·V nul 5°': coh(DA, roll(DV), PMg, 'g')}
Dm = {'A·B': dmin(DA, DB, w['A·B']), 'A·V': dmin(DA, DV, w['A·V']), 'B·V': dmin(DB, DV, w['B·V'])}
print(f'filtre {time.time() - t0:.0f}s', flush=True)
rR = (np.exp(b1.rho) / RS)[:, None]
rep = dict(guio=str(Path(__file__).relative_to(R)), sigma_vixen_px=round(float(SIG_V), 3), gir_nul_graus=5.0,
           suport=dict(A_B=float(mAB.mean()), A_B_V=float(m.mean())))
cc = lambda u, v, k: round(float(np.corrcoef(u[k], v[k])[0, 1]), 3)
for a, b in ((1.3, 2), (2, 3.5), (3.5, 5.5), (5.5, 9.5)):
    fila = (rR >= a) & (rR < b); k = PM & fila; kg = PMg & fila
    if k.sum() < 1000: rep[f'banda_{a}-{b}'] = dict(px=int(k.sum()), nota='la Vixen no hi arriba'); continue
    rep[f'banda_{a}-{b}'] = dict(
        cobertura_V_sobre_AB=round(float(k.sum() / max((PM_AB & fila).sum(), 1)), 3),
        coincidencia_mediana={p: round(float(np.median(w[p][kg if 'nul' in p else k])), 3) for p in w},
        correlacio_detall={'A·B': cc(DA, DB, k), 'A·V': cc(DA, DV, k), 'B·V': cc(DB, DV, k)},
        rms_detall_pct={'A': round(float(DA[k].std() * 100), 3), 'B': round(float(DB[k].std() * 100), 3), 'V': round(float(DV[k].std() * 100), 3)},
        rms_minim_concordant_pct={p: round(float(Dm[p][k].std() * 100), 3) for p in Dm},
        correlacio_minim_AV_amb_AB=cc(Dm['A·V'], Dm['A·B'], k), correlacio_minim_BV_amb_AB=cc(Dm['B·V'], Dm['A·B'], k))
rep['segons'] = round(time.time() - t0, 1)
(OUT / 'B4_VIXEN.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False, indent=1))
