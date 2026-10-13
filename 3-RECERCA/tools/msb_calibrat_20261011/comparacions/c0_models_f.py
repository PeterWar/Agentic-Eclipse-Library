"""c0 · Models de corona F i de polarització de la corona K, verificats a la font. Encàrrec «comparacions», 11-10-2026.

Ús: executa.sh comparacions/c0_models_f.py <kl1985.pdf>
    (el PDF de Koutchmy & Lamy 1985 de Cambridge Core, doi:10.1017/S0252921100084359; NO es copia al projecte: se'n desa l'SHA-256).

1. Koutchmy & Lamy (1985), Fig. 3 (model ASNS, 400–600 nm): l'article NO dona ni fórmula ni taula, només la figura.
   Es digitalitza el mapa de bits original de la pàgina 68 (300 ppp, CCITT): eixos per les marques (R/R☉ dalt, log B a l'esquerra),
   traços gruixuts (components allargats, àrea ≥ 300 px) → línia mitjana per columna, separació equ./pol per sobre d'1,9 R☉,
   polinomi de grau 5 en log–log (els autors van fer servir polinomis de grau 6 en log–log).
   Proves: (a) pendents a > 4 R☉ contra les del text (−2,25 equador; −2,47 pols); (b) contra Saito, Poland & Munro (1977), Taules II i III
   (2,5–5 R☉), que el mateix K&L 1985 inclou entre les seves fonts.
2. van de Hulst (1950), eq. (7): F = (14,86 r^-7 + 4,99 r^-2,5)·1e-8 B☉ (fórmula, simetria esfèrica).
3. p(r) de la corona K per als tres models de densitat (u = 0,56) i la sensibilitat a u i a la banda (no verificada per banda: forquilla).
Escriu comparacions/models_f/ (JSON + figura de control)."""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmp_comu as cc   # noqa: E402

T0 = time.time()
OUT = cc.RES / 'models_f'; OUT.mkdir(parents=True, exist_ok=True)
if len(sys.argv) < 2:
    raise SystemExit('Ús: c0_models_f.py <kl1985.pdf>')
PDF = Path(sys.argv[1])

# ------------------------------------------------------------------------- 1. K&L 1985, Fig. 3
import subprocess                                                           # noqa: E402
from PIL import Image                                                       # noqa: E402
from scipy import ndimage as nd                                             # noqa: E402
tmp = PDF.parent / 'kl1985_p68'                                             # al costat del PDF (fora del projecte); no s'esborra res
tmp.mkdir(exist_ok=True)
subprocess.run(['pdfimages', '-f', '6', '-l', '6', '-png', str(PDF), str(tmp / 'p')], check=True)
a = np.asarray(Image.open(sorted(tmp.glob('p-*.png'))[0]).convert('L')) < 128
assert a.shape == (2820, 1842), a.shape


def grups(L):
    g, cur = [], []
    for y, n in L:
        if cur and y - cur[-1][0] > 1:
            g.append(cur); cur = []
        cur.append((y, n))
    if cur:
        g.append(cur)
    return [(float(np.mean([c[0] for c in gg])), max(c[1] for c in gg)) for gg in g]


# marc
rs, cs = a.sum(1), a.sum(0)
files_marc = np.nonzero(rs > 600)[0]; cols_marc = np.nonzero(cs > 600)[0]
y_top, y_bot = files_marc[files_marc < 1000].max(), files_marc[(files_marc > 1000) & (files_marc < 2500)].min()
x_left, x_right = cols_marc[cols_marc < 1000].max(), cols_marc[cols_marc > 1000].min()
# marques de l'eix log B (esquerra): les llargues (≥ 19 px) són els enters
L = []
for y in range(y_top + 1, y_bot):
    n = 0
    for x in range(x_left + 1, x_left + 70):
        if a[y, x]:
            n += 1
        else:
            break
    if n >= 8:
        L.append((y, n))
maj_y = [y for y, n in grups(L) if n >= 19]
# marques de l'eix R/R☉ (dalt): llargues = 1, 10, 100; curtes = 2…9, 20…90
T = []
for x in range(x_left + 1, x_right):
    n = 0
    for y in range(y_top + 1, y_top + 70):
        if a[y, x]:
            n += 1
        else:
            break
    if n >= 8:
        T.append((x, n))
tk = grups(T)
maj_x = [x for x, n in tk if n >= 35]
# calibratge: els enters de log B, de dalt a baix, són −6, −7, …, −13 (els rètols de la figura: −7 … −13; la de dalt és −6)
yb = np.array(maj_y[:8]); lb_ticks = -6.0 - np.arange(len(yb))
cy_ = np.polyfit(yb, lb_ticks, 1)
# R: 1, 2, …, 9, 10, 20, …, 90, 100 (les curtes entre llargues; la marca de 66 px a la dreta és la cantonada del marc)
seq = []
i10 = [k for k, (x, n) in enumerate(tk) if n >= 35]
for k, (x, n) in enumerate(tk):
    if k < i10[0] or k > i10[2]:
        continue
    seq.append(x)
Rv = list(range(1, 10)) + list(range(10, 100, 10)) + [100]
assert len(seq) == len(Rv), (len(seq), seq)
cx_ = np.polyfit(np.array(seq), np.log10(Rv), 1)
res_x = np.log10(Rv) - np.polyval(cx_, np.array(seq)); res_y = lb_ticks - np.polyval(cy_, yb)
print(f'eixos: log R = {cx_[0]:.6f}·x + {cx_[1]:.4f} (residu màx {np.abs(res_x).max():.4f} dex); '
      f'log B = {cy_[0]:.6f}·y + {cy_[1]:.4f} (residu màx {np.abs(res_y).max():.4f} dex)', flush=True)

# traços gruixuts
sub = np.zeros_like(a); sub[y_top + 7:y_bot - 6, x_left + 36:x_right - 6] = a[y_top + 7:y_bot - 6, x_left + 36:x_right - 6]
lab, n = nd.label(sub); areas = nd.sum(sub, lab, np.arange(1, n + 1)); sl = nd.find_objects(lab)
P = []
for i, s in enumerate(sl):
    if areas[i] < 300:
        continue
    ys, xs = np.nonzero(lab[s] == i + 1); ys = ys + s[0].start; xs = xs + s[1].start
    c = np.cov(np.vstack([xs, ys])); ev = np.linalg.eigvalsh(c); el = math.sqrt(ev[-1] / max(ev[0], 1e-6))
    if el < 8 or xs.mean() > 1450:
        continue
    for x in range(xs.min(), xs.max() + 1):
        yy = np.sort(ys[xs == x]); runs = np.split(yy, np.nonzero(np.diff(yy) > 1)[0] + 1)
        for r_ in runs:
            if 8 <= len(r_) <= 40:
                P.append((x, r_.mean()))
P = np.array(P)
lR = np.polyval(cx_, P[:, 0]); lB = np.polyval(cy_, P[:, 1])
split = lR > math.log10(1.9)
c0 = np.polyfit(lR, lB, 4); res = lB - np.polyval(c0, lR)
up = (~split) | (res > 0); lo = (~split) | (res <= 0)
for _ in range(4):
    cu = np.polyfit(lR[up], lB[up], 5); cl = np.polyfit(lR[lo], lB[lo], 5)
    du = np.abs(lB - np.polyval(cu, lR)); dl = np.abs(lB - np.polyval(cl, lR))
    up = (~split & (du < 0.06)) | (split & (du < dl) & (du < 0.06)); lo = (~split & (dl < 0.06)) | (split & (dl < du) & (dl < 0.06))
rms_u = float(np.std(lB[up] - np.polyval(cu, lR[up]))); rms_l = float(np.std(lB[lo] - np.polyval(cl, lR[lo])))
print(f'K&L 1985: {up.sum()} punts equ., {lo.sum()} pol; rms {rms_u:.4f} / {rms_l:.4f} dex; log R de {lR.min():.3f} a {lR.max():.3f}', flush=True)

# proves
pend = {str(R): dict(equ=float(np.polyval(np.polyder(cu), math.log10(R))), pol=float(np.polyval(np.polyder(cl), math.log10(R))))
        for R in (4, 6, 10, 20)}
SAITO = {   # Saito, Poland & Munro 1977, Sol. Phys. 55, 121, Taula II (B_F, equador) i Taula III (B_F, model polar esfèric), B/B☉ mitjà
    'equ': {2.5: 5.2e-9, 3.0: 3.3e-9, 4.0: 1.5e-9, 5.0: 9.2e-10},
    'pol': {2.5: 4.7e-9, 3.0: 2.6e-9, 4.0: 1.3e-9, 5.0: 7.0e-10},
}
cmp_saito = []
for R in (2.5, 3.0, 4.0, 5.0):
    cmp_saito.append(dict(r=R, saito_equ=SAITO['equ'][R], KL_equ=float(10 ** np.polyval(cu, math.log10(R))),
                          saito_pol=SAITO['pol'][R], KL_pol=float(10 ** np.polyval(cl, math.log10(R))),
                          vdH=float(cc.f_vdh1950(R)),
                          dex_KL_menys_saito_equ=float(np.polyval(cu, math.log10(R)) - math.log10(SAITO['equ'][R])),
                          dex_KL_menys_saito_pol=float(np.polyval(cl, math.log10(R)) - math.log10(SAITO['pol'][R]))))
taula = []
for R in (1.10, 1.15, 1.2, 1.25, 1.3, 1.4, 1.5, 1.7, 2.0, 2.25, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0):
    taula.append(dict(r=R, KL_equ=float(10 ** np.polyval(cu, math.log10(R))), KL_pol=float(10 ** np.polyval(cl, math.log10(R))),
                      vdH1950=float(cc.f_vdh1950(R))))
kl = dict(
    font='Koutchmy, S., Lamy, P. L. 1985, «The F-corona and the circum-solar dust: evidences and properties [G. Nikolsky Memorial '
         'Lecture]», in Properties and Interactions of Interplanetary Dust (IAU Colloq. 85), eds. R. H. Giese & P. Lamy, ASSL 119, 63–74. '
         'doi:10.1017/S0252921100084359 (també 10.1007/978-94-009-5464-9_14)',
    que='Fig. 3 (p. 68): «The axi-symmetric non-spherical model of the F-corona», λλ 400–600 nm, log B en B/B☉ (brillantor mitjana del disc). '
        'Text (p. 67): més enllà de 4 R☉, lleis r^-n amb n = 2,25 a l\'equador i 2,47 als pols.',
    pdf_url='https://www.cambridge.org/core/services/aop-cambridge-core/content/view/430F969D2B9FBA0BAC746FE9E654933A/'
            'S0252921100084359a.pdf/the-f-corona-and-the-circum-solar-dust-evidences-and-properties-g-nikolsky-memorial-lecture.pdf',
    pdf_sha256=cc.sha256(PDF), pdf_fora_del_projecte=str(PDF),
    metode='mapa de bits original de la p. 68 (pdfimages, 1842×2820, 300 ppp); eixos per marques; línia mitjana dels traços gruixuts; '
           'polinomi de grau 5 en (log R, log B), separació equ./pol per sobre d\'1,9 R☉',
    eixos=dict(logR_per_px=list(map(float, cx_)), logB_per_px=list(map(float, cy_)), residu_max_logR=float(np.abs(res_x).max()),
               residu_max_logB=float(np.abs(res_y).max())),
    coef_equ=list(map(float, cu)), coef_pol=list(map(float, cl)), rms_equ_dex=rms_u, rms_pol_dex=rms_l,
    n_punts_equ=int(up.sum()), n_punts_pol=int(lo.sum()), valid_logR=[float(lR.min()), float(lR.max())],
    error_lectura_dex=0.02,
    pendents_digitalitzades=pend, pendents_text=dict(equ=-2.25, pol=-2.47),
    prova_saito1977=cmp_saito,
    avis='Model publicat NOMÉS com a figura: els valors són una lectura (error estimat ±0,02 dex ≈ ±5 %). '
         'Per sota d\'1,9 R☉ els dos perfils coincideixen a la figura.',
)
json.dump(kl, open(OUT / 'F_KL1985_digitalitzat.json', 'w'), indent=1, ensure_ascii=False)

# ------------------------------------------------------------------------- 2. p(r) i transferència de banda
pt = {}
for nom in cc.MODELS_DENSITAT:
    pt[nom] = {f'{r:.3f}': float(cc.polaritzacio(r, cc.MODELS_DENSITAT[nom])) for r in (1.15, 1.20, 1.25, 1.325, 1.40, 1.55, 1.70, 1.85, 2.0, 2.25, 2.5)}
sens_u = {}
for u in (0.45, 0.56, 0.65, 0.75):
    sens_u[f'u={u}'] = {f'{r:.2f}': float(cc.polaritzacio(r, cc.MODELS_DENSITAT['Baumbach-Allen'], u)) for r in (1.2, 1.5, 2.0, 2.5)}
transf = []
for ug, uk in ((0.65, 0.50), (0.70, 0.45), (0.60, 0.55), (0.56, 0.56), (0.75, 0.50)):
    transf.append(dict(u_nostra=ug, u_kcor=uk, **{f'r{r:.2f}': float(cc.transfer_banda_k(r, cc.MODELS_DENSITAT['Baumbach-Allen'], ug, uk))
                                                   for r in (1.2, 1.5, 2.0, 2.5)}))
json.dump(dict(
    font_p='van de Hulst 1950 (Thomson, enfosquiment lineal u), A, B, C, D com a c9_brillantor.py; integral fins a z = 20 R☉',
    u_adoptat=cc.U_ADOPTAT, p=pt, sensibilitat_u=sens_u,
    transferencia_banda_K=transf,
    avis_u='Els valors de u per banda NO s\'han verificat a cap font: la taula és una forquilla per veure l\'ordre de magnitud.',
    F_taula=taula,
    vdH1950=dict(formula='F = (14,86 r^-7 + 4,99 r^-2,5)·1e-8 B☉ (mitjana del disc)',
                 font='van de Hulst, H. C. 1950, «The electron density of the solar corona», BAN 11, 135–150 (núm. 410), eq. (7), p. 139; '
                      'unitats a la p. 136. Escaneig de l\'ADS 1950BAN....11..135V.'),
    saito1977=dict(font='Saito, K., Poland, A. I., Munro, R. H. 1977, Sol. Phys. 55, 121–134, doi:10.1007/BF00150879, Taules II i III '
                        '(escaneig de l\'ADS 1977SoPh...55..121S); B/B☉ = brillantor mitjana del disc (p. 123)', valors=SAITO,
                   us='Només 2,5–5 R☉: no cobreix els anells del K-Cor. Serveix de prova de la digitalització de K&L 1985.'),
), open(OUT / 'MODELS_K_F.json', 'w'), indent=1, ensure_ascii=False)

# figura de control
import matplotlib; matplotlib.use('Agg')                                    # noqa: E401,E402
import matplotlib.pyplot as plt                                             # noqa: E402
fig, ax = plt.subplots(1, 2, figsize=(11, 5))
ax[0].plot(lR, lB, ',', color='0.6')
g = np.linspace(0.0, 2.35, 300)
ax[0].plot(g, np.polyval(cu, g), 'C0', lw=1, label='K&L equ (fit)'); ax[0].plot(g, np.polyval(cl, g), 'C1', lw=1, label='K&L pole (fit)')
ax[0].plot(g, np.log10(cc.f_vdh1950(10 ** g)), 'k--', lw=1, label='van de Hulst 1950')
for k_, c_ in (('equ', 'C0'), ('pol', 'C1')):
    ax[0].plot(np.log10(list(SAITO[k_].keys())), np.log10(list(SAITO[k_].values())), 'o', color=c_, mfc='none', label=f'Saito 1977 {k_}')
ax[0].set_xlabel('log R/Rsun'); ax[0].set_ylabel('log B/Bsun'); ax[0].legend(fontsize=7); ax[0].set_title('F-corona models (digitisation check)')
im = Image.open(sorted(tmp.glob('p-*.png'))[0]).convert('L')
ax[1].imshow(np.asarray(im)[y_top:y_bot, x_left:x_left + 700], cmap='gray', extent=(x_left, x_left + 700, y_bot, y_top))
xx = np.linspace(np.min(P[:, 0]), x_left + 700, 400); lx = np.polyval(cx_, xx)
iy = lambda lb: (lb - cy_[1]) / cy_[0]                                       # noqa: E731
ax[1].plot(xx, iy(np.polyval(cu, lx)), 'c', lw=0.7); ax[1].plot(xx, iy(np.polyval(cl, lx)), 'm', lw=0.7)
ax[1].set_title('fit over the original bitmap (p. 68)')
fig.tight_layout(); fig.savefig(OUT / 'control_digitalitzacio_KL1985.png', dpi=130); plt.close(fig)
print(json.dumps(cmp_saito, indent=1)); print(json.dumps(pend, indent=1))
print(f'fet ({time.time() - T0:.0f} s)')
