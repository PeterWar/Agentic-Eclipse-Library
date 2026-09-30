"""b8 (V118, 29-09-2026) · EL FILTRE DE TRES TESTIMONIS (b5), AMB CADA TESTIMONI REGISTRAT A LA GEOMETRIA DEL COMPOST.
Troballa del 29-09, en revisar la primera V118 (b5):
  · la Vixen i la Sony A NO tenen la mateixa geometria al llenç: les estrelles donen Vixen − A de 3–7 px (−0,06° a −0,12° en angle, sempre
    el mateix signe) i el detall dels raigs, fins a −0,25° a 100–220°; B − A, 1–4 px (±0,1–0,2°);
  · el compost de la V115 té la geometria de la VIXEN a la corona interior (1,6–2,5 R☉: ±0,05°) i s'acosta a la de la Sony més enfora;
  · la 415 de la V117 es va fer a la geometria d'A: sobre el compost queda desplaçada fins a 0,25–0,29° (5–12 px), i una capa de detall en
    Superposar desplaçada fa RELLEU (aclareix un costat del raig i enfosqueix l'altre);
  · al b5, el mínim concordant exigeix el mateix signe al mateix lloc: el desplaçament Vixen–Sony s'hi menjava el detall a les vores dels raigs.
Cura: abans de la concordança, el detall azimutal de cada testimoni (D_A, D_B, D_V, al pla log-polar del b1) es desplaça en angle fins a la
geometria del compost (el detall D_U del render natiu de la V115, amb el mateix operador): per finestres de 6° × 0,08 en ln r es busca el
desplaçament de màxima correlació (±0,6°, subpíxel), es conserven les finestres amb correlació ≥ 0,5 i s'interpola un mapa suau
(gaussiana normalitzada, σ 10° × 0,15 en ln r). El desplaçament radial no compta: el detall és azimutal i ja va suavitzat al llarg del radi.
Tota la resta, com al b5 (entrades sense estrelles, peus d'halo del b5, Vixen a la resolució de la Sony, w₃ i mínim concordant de tres).
Ús: b8_filtre_registrat.py <carpeta_b5> <carpeta_sortida>  → D_minim_f32.npy, W3_coherencia_f16.npy, DA/DB/DV_f16.npy (registrats), B8_REBUT.json"""
import sys, json, time, importlib.util, numpy as np, cv2, tifffile
from pathlib import Path
from scipy import ndimage as ndi
B5D, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
sys.argv = [sys.argv[0], str(OUT)]
spec = importlib.util.spec_from_file_location('b5', Path(__file__).with_name('b5_filtre_tres_testimonis.py')); b5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b5)
b1, R, H, W, SOL, RS = b5.b1, b5.R, b5.H, b5.W, b5.SOL, b5.RS
REF = R / '4-RESULTATS/v115_nrgf_20260929/V115_natiu/visible_complet.tif'
FT, FR, MAXD, CMIN, ST, SR_ = 6.0, 0.08, 0.6, 0.5, 10.0, 0.15          # finestra (°, ln r), desplaçament màxim (°), correlació mínima, suavitzat (°, ln r)
DS = 4                                                                    # delmat per a la mesura (pla 1024 × 6144)
t0 = time.time()
HALO = json.load(open(B5D / 'B5_AJUSTOS_ESTRELLES.json'))['halo']; RADIS = {tuple(int(v) for v in k.split(',')): d['radi'] for k, d in HALO.items()}
LA, LB, LV, m, info = b5.entrades(RADIS); print(f'entrades {time.time() - t0:.0f}s · suport comú {m.mean():.3f}', flush=True)
PM = b1.polar(m.astype(np.float32)) > 0.999; den_c = {}
def gn(x, sr, st_, M=PM, clau='PM'):
    if (sr, st_, clau) not in den_c: den_c[(sr, st_, clau)] = b1.gcv(M.astype(np.float32), sr, st_)
    den = den_c[(sr, st_, clau)]; return b1.gcv(np.where(M, x, 0).astype(np.float32), sr, st_) / np.maximum(den, 1e-6), den
def detall(L, M=PM, clau='PM'):
    x = np.where(M, np.log(np.maximum(b1.polar(L), 1e-9)), 0).astype(np.float32); a, _ = gn(x, b1.SR, b1.S1, M, clau); c, _ = gn(x, b1.SR, b1.S2, M, clau)
    return np.where(M, a - c, 0).astype(np.float32)
DA, DB, DV = detall(LA), detall(LB), detall(LV); del LA, LB, LV
# la referència: el detall del compost de la V115 (canal G del render natiu), amb el mateix operador, al seu propi suport
U = tifffile.memmap(REF, mode='r'); G = np.empty((H, W), np.float32)
for y0 in range(0, H, 1024): G[y0:y0 + 1024] = np.asarray(U[y0:y0 + 1024, :, 1], np.float32) / 65535
MU = b1.polar((G > 0.004).astype(np.float32)) > 0.999; DU = detall(G, MU, 'MU'); del G
print(f'detalls {time.time() - t0:.0f}s', flush=True)
NR, NT = PM.shape; dth = 360.0 / NT
def redueix(X): return cv2.resize(X, (NT // DS, NR // DS), interpolation=cv2.INTER_AREA)
def mapa_desplacament(DX, nom):
    """desplaçament angular (en mostres del pla complet) que porta DX a la geometria de DU, suau, a tot el pla; i les mesures de finestra."""
    x, u = redueix(np.where(PM, DX, 0)), redueix(np.where(MU, DU, 0)); v = redueix((PM & MU).astype(np.float32)) > 0.99
    nt, nr = x.shape[1], x.shape[0]; wt = int(round(FT / 360 * nt)); wr = int(round(FR / (b1.dr * DS))); ms = int(np.ceil(MAXD / 360 * nt))
    box = lambda z: cv2.boxFilter(np.concatenate([z[:, -wt:], z, z[:, :wt]], 1), -1, (wt, wr), normalize=True, borderType=cv2.BORDER_REFLECT)[:, wt:-wt]
    uu = box(np.where(v, u * u, 0)); cor = []
    for s in range(-ms, ms + 1):
        xs = np.roll(x, -s, axis=1); vs = v & np.roll(v, -s, axis=1)
        num = box(np.where(vs, xs * u, 0)); xx = box(np.where(vs, xs * xs, 0)); cov = box(vs.astype(np.float32))
        cor.append(np.where(cov > 0.9, num / np.sqrt(np.maximum(xx * uu, 1e-20)), np.nan))
    cor = np.stack(cor); cor_ok = np.nan_to_num(cor, nan=-1); i = np.argmax(cor_ok, 0); cmax = np.take_along_axis(cor_ok, i[None], 0)[0]
    ii = np.clip(i, 1, 2 * ms - 1); y0, y1, y2 = [np.take_along_axis(cor_ok, (ii + k)[None], 0)[0] for k in (-1, 0, 1)]
    sub = np.where(np.abs(y0 - 2 * y1 + y2) > 1e-9, 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2), 0)
    d = (ii + sub - ms).astype(np.float32)                                 # en mostres del pla delmat
    bo = (cmax >= CMIN) & (i > 0) & (i < 2 * ms) & v
    # mostreig en una graella de finestres (no solapades a mig pas) i interpolació suau
    g = np.zeros_like(d); g[::max(wr // 2, 1), ::max(wt // 2, 1)] = 1; pes = (bo & (g > 0)).astype(np.float32)
    sgt, sgr = ST / 360 * nt, SR_ / (b1.dr * DS)
    sm = lambda z: cv2.GaussianBlur(np.concatenate([z[:, -3 * int(sgt):], z, z[:, :3 * int(sgt)]], 1), (0, 0), sigmaX=sgt, sigmaY=sgr, borderType=cv2.BORDER_REFLECT)[:, 3 * int(sgt):-3 * int(sgt)]
    num, den = sm(d * pes), sm(pes); dsm = np.where(den > 1e-3, num / np.maximum(den, 1e-9), 0).astype(np.float32)
    mes = d[pes > 0] * 360 / nt; rr = (np.exp(b1.rho[::DS][:nr]) / RS)[:, None] * np.ones((1, nt)); rrm = rr[pes > 0]
    est = dict(finestres_bones=int(pes.sum()), finestres=int(g.sum()), mediana_graus=round(float(np.median(mes)), 3), p10_p90_graus=[round(float(np.percentile(mes, q)), 3) for q in (10, 90)],
               per_radi={f'{a}-{b}': (round(float(np.median(mes[(rrm >= a) & (rrm < b)])), 3) if ((rrm >= a) & (rrm < b)).sum() > 5 else None) for a, b in ((1.3, 2), (2, 3), (3, 4), (4, 5.5))})
    full = cv2.resize(dsm, (NT, NR), interpolation=cv2.INTER_LINEAR) * DS   # a mostres del pla complet
    print(nom, json.dumps(est, ensure_ascii=False), flush=True); return full, est
def desplaca(DX, dm):
    """DX(ρ, θ) → DX(ρ, θ + δ): la mostra que el compost té a θ, el testimoni la té a θ + δ."""
    mx = (np.arange(NT, dtype=np.float32)[None, :] + dm).astype(np.float32) % NT; my = np.repeat(np.arange(NR, dtype=np.float32)[:, None], NT, 1)
    Xw = np.concatenate([DX, DX[:, :2]], 1); Mw = np.concatenate([PM, PM[:, :2]], 1).astype(np.float32)
    out = cv2.remap(Xw, mx, my, cv2.INTER_LINEAR, borderValue=0); ok = cv2.remap(Mw, mx, my, cv2.INTER_LINEAR, borderValue=0) > 0.999
    return np.where(ok & PM, out, 0).astype(np.float32), ok
reg = {}; ok_all = PM.copy()
for nom in ('A', 'B', 'V'):
    DX = {'A': DA, 'B': DB, 'V': DV}[nom]; dm, est = mapa_desplacament(DX, nom); Dr, ok = desplaca(DX, dm); ok_all &= ok
    reg[nom] = dict(D=Dr, est=est, dm=dm)
del DA, DB, DV
# comprovació: el desplaçament residual, després del registre, ha de ser ~0
res_est = {}
for nom in ('A', 'B', 'V'):
    _, e = mapa_desplacament(reg[nom]['D'], nom + ' registrat'); res_est[nom] = e
PMr = PM & ok_all
DA, DB, DV = (np.where(PMr, reg[n]['D'], 0).astype(np.float32) for n in ('A', 'B', 'V'))
def coh(u, v):
    cov, den = gn(u * v, b1.WR, b1.WT, PMr, 'PMr'); vu, _ = gn(u * u, b1.WR, b1.WT, PMr, 'PMr'); vv, _ = gn(v * v, b1.WR, b1.WT, PMr, 'PMr')
    w = np.clip(cov / np.maximum(0.5 * (vu + vv), 1e-12), 0, 1).astype(np.float32); w[~PMr] = 0; return w * np.clip((den - 0.6) / 0.4, 0, 1).astype(np.float32)
wp = {'A·B': coh(DA, DB), 'A·V': coh(DA, DV), 'B·V': coh(DB, DV)}; w3 = np.minimum(np.minimum(wp['A·B'], wp['A·V']), wp['B·V'])
mag = np.minimum(np.minimum(np.abs(DA), np.abs(DB)), np.abs(DV)); igual = (DA * DB > 0) & (DA * DV > 0)
D3 = (w3 * np.where(igual, np.sign(DA) * mag, 0)).astype(np.float32)
print(f'filtre {time.time() - t0:.0f}s', flush=True)
mc = b1.cart(PMr.astype(np.float32)) > 0.5; viu = ~mc & ~ndi.binary_dilation(mc, iterations=2)
c = b1.cart(D3); c[viu] = 0; np.save(OUT / 'D_minim_f32.npy', c.astype(np.float32)); np.save(OUT / 'W3_coherencia_f16.npy', b1.cart(w3).astype(np.float16))
for nom, P in (('DA', DA), ('DB', DB), ('DV', DV)): np.save(OUT / f'{nom}_f16.npy', b1.cart(P).astype(np.float16))
for nom in ('A', 'B', 'V'): np.save(OUT / f'desplacament_{nom}_graus_f16.npy', (reg[nom]['dm'][::4, ::4] * dth).astype(np.float16))
rR = (np.exp(b1.rho) / RS)[:, None]; bandes = {}
for a, b in ((1.3, 2), (2, 3.5), (3.5, 5.5), (5.5, 9.5)):
    k = PMr & (rR >= a) & (rR < b)
    if k.sum() < 1000: bandes[f'{a}-{b}'] = dict(px=int(k.sum())); continue
    bandes[f'{a}-{b}'] = dict(coincidencia_mediana={**{p: round(float(np.median(v[k])), 3) for p, v in wp.items()}, 'tres (mínim)': round(float(np.median(w3[k])), 3)},
                              sd_D3_pct=round(float(D3[k].std() * 100), 3))
rep = dict(guio=str(Path(__file__).relative_to(R)), base_b5=str(B5D.relative_to(R)), referencia_geometria=str(REF.relative_to(R)),
           registre=dict(finestra_graus=FT, finestra_ln_r=FR, desplacament_max_graus=MAXD, correlacio_minima=CMIN, suavitzat=dict(graus=ST, ln_r=SR_),
                         abans={n: reg[n]['est'] for n in reg}, despres=res_est),
           combinacio='D = min(w_AB, w_AV, w_BV) · [A, B i V del mateix signe] · signe · min(|D_A|, |D_B|, |D_V|), amb cada D registrat a la geometria del compost',
           suport_comu=float(PMr.mean()), bandes=bandes, segons=round(time.time() - t0, 1))
(OUT / 'B8_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(dict(bandes=bandes), ensure_ascii=False))
