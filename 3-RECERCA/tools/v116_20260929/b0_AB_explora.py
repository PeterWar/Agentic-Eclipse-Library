"""b0 (V116, 29-09-2026) · Exploració dels dos apuntaments de la Sony (A abans del «relliscament», B després; ~750 px de desplaçament al sensor):
la mateixa corona vista des de dues posicions del sensor. Aquí, a 1/2 del llenç i al canal verd:
  A = sony_A_corr (A igualada a B a gran escala, V113) / pesos A;  B = sony_B_total_v42 / pesos B (tots dos amb el flat 2D v5).
  cobertura, quocient A/B a gran escala, i el detall d = ln X − ln G_σ(X) (DoG 2–48 px) a totes dues; correlació local ρ(d_A, d_B) (finestra σ 24 px).
Sortides a 4-RESULTATS/v116_20260929/AB/: B0_EXPLORA.json i vistes (llenç sencer, 1/4): cobertura, ρ, detall A, detall B, detall A − B."""
import json, numpy as np, cv2
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929/AB'; O.mkdir(parents=True, exist_ok=True)
F = dict(A=R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/b3/cau/sony_A_corr_v42.npy', Aw=R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v29/sony_A_weights.npy',
         B=R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_total_v42.npy', Bw=R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_B/cau/sony_B_weights_v42.npy')
def mig(path):
    a = np.load(path, mmap_mode='r'); x = np.asarray(a[..., 1], np.float32)
    h, w = x.shape; return cv2.resize(x, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
Aw, Bw = mig(F['Aw']), mig(F['Bw']); A = mig(F['A']) / np.maximum(Aw, 1e-6); B = mig(F['B']) / np.maximum(Bw, 1e-6)
mA, mB = Aw > 0.2 * np.median(Aw[Aw > 0]), Bw > 0.2 * np.median(Bw[Bw > 0]); m = mA & mB & (A > 0) & (B > 0)
SOL = (5361.768 / 2, 3775.748 / 2); RS = 440.603 / 2; H, W = A.shape; yy, xx = np.mgrid[0:H, 0:W]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
def gnorm(x, msk, s):
    return cv2.GaussianBlur(np.where(msk, x, 0).astype(np.float32), (0, 0), s) / np.maximum(cv2.GaussianBlur(msk.astype(np.float32), (0, 0), s), 1e-6)
lA, lB = np.log(np.maximum(A, 1e-6)), np.log(np.maximum(B, 1e-6))
dA = np.where(m, gnorm(lA, m, 1) - gnorm(lA, m, 24), 0); dB = np.where(m, gnorm(lB, m, 1) - gnorm(lB, m, 24), 0)    # DoG 2–48 px del llenç
cov = gnorm(dA * dB, m, 12); vA = gnorm(dA * dA, m, 12); vB = gnorm(dB * dB, m, 12); rho = np.where(m, cov / np.sqrt(np.maximum(vA * vB, 1e-12)), np.nan)
q = np.where(m, gnorm(A, m, 100) / np.maximum(gnorm(B, m, 100), 1e-6), np.nan)
out = dict(cobertura=dict(A=float(mA.mean()), B=float(mB.mean()), les_dues=float(m.mean())), bandes={})
for a, b in ((1.3, 2), (2, 3.5), (3.5, 5.5), (5.5, 9.5)):
    k = m & (rr >= a) & (rr < b)
    if k.sum() < 1000: continue
    out['bandes'][f'{a}-{b}'] = dict(rho_mediana=round(float(np.nanmedian(rho[k])), 3), rho_p10_p90=[round(float(v), 3) for v in np.nanpercentile(rho[k], [10, 90])],
                                     quocient_AB_p5_p50_p95=[round(float(v), 4) for v in np.nanpercentile(q[k], [5, 50, 95])], sd_dA_pct=round(float(np.std(dA[k])) * 100, 3), sd_dB_pct=round(float(np.std(dB[k])) * 100, 3),
                                     sd_dA_menys_dB_pct=round(float(np.std((dA - dB)[k])) * 100, 3))
(O / 'B0_EXPLORA.json').write_text(json.dumps(out, ensure_ascii=False, indent=1)); print(json.dumps(out, ensure_ascii=False, indent=1))
np.savez_compressed(O / 'B0_mig.npz', dA=dA.astype(np.float16), dB=dB.astype(np.float16), rho=np.nan_to_num(rho).astype(np.float16), m=m)
try: FT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 28)
except Exception: FT = ImageFont.load_default()
def vista(x, exc, nom, t):
    g = np.clip(128 + np.nan_to_num(x[::2, ::2]) / exc * 127, 0, 255).astype(np.uint8); g = np.stack([g] * 3, 2); g[~m[::2, ::2]] = (40, 40, 40)
    im = Image.fromarray(g); ImageDraw.Draw(im).text((12, 10), t, fill=(255, 255, 0), font=FT, stroke_width=2, stroke_fill=(0, 0, 0)); im.save(O / f'{nom}.png')
vista(dA, 0.04, 'B0_detall_A', 'Sony A: detall 2–48 px (±4 %)'); vista(dB, 0.04, 'B0_detall_B', 'Sony B: detall 2–48 px (±4 %)')
vista(dA - dB, 0.04, 'B0_detall_A_menys_B', 'A − B: el que no coincideix (±4 %)'); vista(rho - 0.5, 0.5, 'B0_rho', 'correlació local ρ(A, B): blanc 1, gris 0,5, negre 0')
