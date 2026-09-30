"""a3a · La franja amb dada d'UN SOL INSTANT (norma de Pere del 17-09, research/165: «o s'omple amb un sol instant»).
Per què: els arcs de la franja neixen de BARREJAR fotogrames amb el limbe a llocs diferents (la Lluna es mou 28,5 px). Els fotogrames dels
primers segons (t ≤ 22,3 s: 8 × 1/3200 s + 1/2000, 1/500 i 1/125 s) tenen el limbe on és la Lluna que es mostra (la capa 30 de Pere =
Lluna a t ≈ 18,4 s); junts no fan arcs i ensenyen la cromosfera i la protuberància d'aquell instant. Dada real, res inventat.
(La primera versió de la V86 excloïa la franja i la interpolava (decisió B literal): quedava un anell llis sense detall de 20–50 px,
visible al compost de Photoshop; es va refusar abans de lliurar. La prova d'aplanar els arcs al llarg del raig també es va refusar: escampava
el perfil del limbe i feia un anell clar amb perles.)
Construcció (caixa de 4-RESULTATS/v85.../limb_frames, 67 fotogrames Vixen amb numeradors, pesos i distància al limbe modelat per fotograma):
  E_c = Σ num_f,c / Σ w_f,c sobre els fotogrames primerencs, només on el píxel és a ≥ 1 px fora del limbe OBSERVAT d'aquell fotograma
        i almenys 8 dels 11 fotogrames hi contribueixen (al verd); buits del mosaic CFA omplerts per convolució normalitzada σ 0,8 px per canal;
        després, guanys de balanç i matriu de color del rebut (mateix espai que la fusió);
  pes arran del limbe: el pes de cada fotograma es multiplica per una rampa smoothstep de la seva distància al SEU limbe (1→3 px als de 1/3200 s,
        2→6 px als de 1/2000–1/125 s, que pesen el 81 %). Arran del limbe, als costats, els llargs són més foscos: a la dreta la vora hi és més
        difuminada (a 1,5 px, −35..−63 % contra −4..−24 % als curts); a l'esquerra, a més, la Lluna hi va tapant la cromosfera (el limbe lunar és
        just sobre el solar: a t = 15 s hi ha 3–5 vegades la llum de 7–9 px, a t = 22 s la meitat). A dalt i a baix, cap dèficit.
        A més, cal un pes efectiu d'almenys 1,5 fotogrames curts;
  limbe observat: la distància del rebut (distance_model) és al radi de l'EFEMÈRIDE (455,5 px), 2,5 px més gran que el limbe que es veu als
        fotogrames (màxim gradient dels primerencs a d ≈ −1…+0,5 de la Lluna de Pere, R 453,0). D_obs = D_model + (R_model − R_Lluna).
        (La primera V86 del 23-09 mesurava des del radi de l'efemèride: perdia ~3 px de corona real arran del limbe i els filtres hi deixaven
        una tira llisa de 4–6 px a dalt, a baix i a la dreta; versió retirada a a3a_franja_un_instant_radi_efemeride_retirat.py.)
  nivell: un factor CONSTANT per canal, c = mediana de font/E a 12–45 px del limbe (tots els azimuts). No depèn de la distància: arran del limbe
        la fusió porta una vora clara artificial (el quocient fusió/primerencs puja de 1,12 a 1,65 en 4 px a dalt, on els primerencs no tenen
        dèficit: correcció de vora de la cadena amb el radi de l'efemèride), i una c(d) la importava als filtres (+9 % a 1 px, +4 % a 5 px);
  font nova = (1−β)·font + β·c·E, amb β = 1 dins de la franja i rampa smoothstep de rb−6 a rb+6, només on E és vàlida, fora del disc i fins a 45 px del limbe.
Domini nou dels filtres: el suport fora del disc de presentació, més la franja amb dada d'un instant; dins del disc (tapat per la Lluna opaca) no hi ha dada
i els operadors hi usen la condició de contorn (continuació).
Sortida: A3A_franja_un_instant.npz (caixa) i A3A_FRANJA_UN_INSTANT.json."""
from v86_comu import *
from v86_operadors import smoothstep
claim()
meta = json.loads((V85D / 'limb_frames/METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(V85D / 'limb_frames/numerator.npy', mmap_mode='r'); wt = np.load(V85D / 'limb_frames/weight.npy', mmap_mode='r'); Dm = np.load(V85D / 'limb_frames/distance_model.npy', mmap_mode='r')
T_MAX, D_MIN, N_MIN = 22.3, 1.0, 8        # ≥ 8 dels 11 fotogrames: la fila de vora amb 2–4 fotogrames feia una costura en ziga-zaga (23-09, 2:20)
RAMPA_CURTS, RAMPA_LLARGS = (1.0, 3.0), (2.0, 6.0)   # rampa del pes de cada fotograma segons la seva distància al limbe observat (px):
# arran del limbe, als costats, els fotogrames llargs (81 % del pes) són més foscos (vora més difuminada a la dreta; cromosfera tapada a l'esquerra);
# a dalt i a baix, cap dèficit. Sense la rampa, la suma feia una línia fosca arran del limbe a dalt-esquerra i baix-esquerra (23-09, 3:35)
early = [i for i, f in enumerate(fr) if f['time'] <= T_MAX]
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
g = np.load(SORT / 'A2_geometria.npz'); rb = g['rb_s']; NB = len(rb)
DR = float(meta['radius_model']) - R      # radi de l'efemèride − radi observat (Lluna de Pere): la distància del rebut es mesura des de l'efemèride
yy, xx = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xx - cx, yy - cy); th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; RB = rb[(th / 360 * NB).astype(int) % NB]
import cv2
E = np.zeros((by1 - by0, bx1 - bx0, 3), np.float32); W = np.zeros_like(E); NF = np.zeros(E.shape[:2], np.int16)
curts = [i for i in early if fr[i]['exposure'] < 0.0004]; W_CURT = float(np.median(np.asarray(wt[curts[0], ::7, ::7, 1])[np.asarray(Dm[curts[0], ::7, ::7]) > 60]))
for c in range(3):
    N_ = np.zeros(E.shape[:2], np.float64); W_ = np.zeros(E.shape[:2], np.float64); n_ = np.zeros(E.shape[:2], np.int16)
    for i in early:
        Dobs = np.asarray(Dm[i]) + DR; ok = Dobs >= D_MIN; a_, b_ = RAMPA_CURTS if fr[i]['exposure'] < 0.0004 else RAMPA_LLARGS
        rampa = smoothstep(Dobs, a_, b_)          # pes del fotograma arran del SEU limbe: la vora hi és difuminada (més als llargs)
        wc = np.asarray(wt[i, :, :, c], np.float64); w_ = np.where(ok, wc * rampa, 0); N_ += np.where(ok, np.asarray(num[i, :, :, c], np.float64) * rampa, 0); W_ += w_; n_ += ok & (wc > 0)
    # mostres CFA: el R i el B no tenen mostra a cada píxel; convolució normalitzada molt petita (σ 0,8 px) per omplir els buits del mosaic
    Ns = cv2.GaussianBlur(N_.astype(np.float32), (0, 0), 0.8); Ws = cv2.GaussianBlur(W_.astype(np.float32), (0, 0), 0.8)
    E[..., c] = np.where(Ws > 0, Ns / np.maximum(Ws, 1e-30), 0); W[..., c] = Ws
    if c == 1: NF = n_
validE = (NF >= N_MIN) & (W > 0).all(-1)        # validesa pel nombre de fotogrames al verd (≥ 8 dels 11)
validE &= W[..., 1] >= 1.5 * W_CURT          # i almenys 1,5 fotogrames curts equivalents de pes efectiu (la rampa pot deixar-lo molt baix)
# NOTA (23-09, V88): W_CURT sortia 0 (mediana d'una mostra amb molts pesos nuls), de manera que aquesta condició NO feia res a la V86. Corregit a la V88.
# mateix espai de color que la fusió: guanys de balanç i matriu de color del rebut dels fotogrames (METADATA), com a la cadena
Mx = np.array(meta['matrix'], np.float32); gn = np.array(meta['gain'], np.float32); E = np.einsum('ij,...j->...i', Mx, E * gn).astype(np.float32)
validE &= (E[..., 1] > 0)     # i G positiu després de la matriu; validesa pel G (el blau matricial pot sortir ≤ 0 pel soroll dels curts: l'ACHF ja descarta canal per canal)
D_US = 45.0     # només es fa servir dada primerenca fins a 45 px del limbe (més enllà els curts s'acosten al terra de la suma i la mitjana s'esbiaixa)
beta = ((1 - smoothstep(rL, RB - 6, RB + 6)) * validE * (rL > R) * (rL - R <= D_US)).astype(np.float32)
fonts = dict(G=np.load(FONTS / 'base_G.npy', mmap_mode='r'), F=np.load(FONTS / 'fusion_starless.npy', mmap_mode='r'), V=np.load(FONTS / 'vixen_starless.npy', mmap_mode='r'))
sup = np.load(FONTS / 'support.npy')[by0:by1, bx0:bx1]
from scipy.ndimage import gaussian_filter1d
dL = (rL - R); nb = np.clip((dL / 0.5).astype(int), 0, 199)                    # calaixos de 0,5 px de distància al limbe (0–100 px)
def quocient_per_distancia(font, e):
    # només per al rebut: mediana, sobre tots els azimuts, de font/primerencs a cada distància (hi surt la vora clara de la fusió arran del limbe)
    ok = (font > 0) & (e > 0) & sup & (dL > 0) & (dL < 100) & validE; c = np.full(200, np.nan)
    for k in range(200):
        s = ok & (nb == k)
        if s.sum() > 200: c[k] = np.median(font[s] / e[s])
    return c
def perfil_c(font, e):
    # nivell CONSTANT: mediana de font/primerencs a 12–45 px del limbe (tots els azimuts, píxels vàlids); el mateix valor a totes les distàncies
    ok = (font > 0) & (e > 0) & sup & validE & (dL >= 12) & (dL <= 45)
    return np.full(200, float(np.median(font[ok] / e[ok])))
out = {}; esc = {}
Gb = np.asarray(fonts['G'][by0:by1, bx0:bx1]); cG = perfil_c(Gb, E[..., 1]); esc['c_G_constant'] = float(cG[0])
qG = quocient_per_distancia(Gb, E[..., 1]); esc['quocient_fusio_primerencs_G_per_distancia (no aplicat)'] = {f'{d:.1f}': (None if not np.isfinite(qG[int(d / 0.5)]) else float(qG[int(d / 0.5)])) for d in [1, 1.5, 2, 3, 4, 5, 6, 8, 12, 20, 30, 40, 45]}
out['G'] = np.where(beta > 0, (1 - beta) * Gb + beta * cG[nb] * E[..., 1], Gb).astype(np.float32)
Fb = np.asarray(fonts['F'][by0:by1, bx0:bx1]).astype(np.float32); Fn = Fb.copy()
for c in range(3):
    cc = perfil_c(Fb[..., c], E[..., c]); esc[f'c_F{c}_constant'] = float(cc[0])
    Fn[..., c] = np.where(beta > 0, (1 - beta) * Fb[..., c] + beta * cc[nb] * E[..., c], Fb[..., c])
out['F'] = Fn
Vb = np.asarray(fonts['V'][by0:by1, bx0:bx1, 1]).astype(np.float32); cV = perfil_c(Vb, E[..., 1]); esc['c_V_constant'] = float(cV[0])
out['V'] = np.where(beta > 0, (1 - beta) * Vb + beta * cV[nb] * E[..., 1], Vb).astype(np.float32)
# comprovació: dispersió de ln(fusió/primerencs corregits) per distància (al costat dret, fora de la franja escombrada, la fusió és neta)
chk = {}
for d0, d1 in [(1, 2), (2, 3), (3, 6), (6, 12), (12, 20), (20, 30), (30, 45)]:
    s = (Gb > 0) & (E[..., 1] > 0) & sup & (dL >= d0) & (dL < d1); rr_ = np.log(Gb[s] / (cG[nb][s] * E[..., 1][s])); chk[f'{d0}-{d1}'] = [float(np.median(rr_)), float(np.percentile(rr_, 16)), float(np.percentile(rr_, 84))]
esc['comprovacio_ln_fusio_sobre_primerencs_corregits'] = chk
# domini: fora del disc de presentació; a la franja només on hi ha dada d'un instant
dins_franja = rL < RB
domini = (rL > R) & ((sup & ~dins_franja) | (dins_franja & validE))
np.savez_compressed(SORT / 'A3A_franja_un_instant.npz', box=np.array([by0, by1, bx0, bx1]), G=out['G'], F=out['F'], V=out['V'], domini=domini, dins_franja=dins_franja, beta=beta, E=E, NF=NF)
rep = dict(fotogrames=[dict(i=i, nom=fr[i]['name'], t=fr[i]['time'], exposicio=fr[i]['exposure']) for i in early], D_min_px=D_MIN, limbe='observat (R Lluna de Pere)', DR_efemeride_menys_observat_px=DR, rampa_pes_curts_px=RAMPA_CURTS, rampa_pes_llargs_px=RAMPA_LLARGS, pes_efectiu_min_fotogrames_curts=1.5, fotogrames_min=N_MIN, escales=esc,
           franja_px_fora_disc=int((dins_franja & (rL > R)).sum()), franja_amb_dada_un_instant=int((dins_franja & (rL > R) & validE).sum()),
           franja_sense_dada=int((dins_franja & (rL > R) & ~validE).sum()), domini_caixa=int(domini.sum()), suport_caixa=int(sup.sum()))
desa_json('A3A_FRANJA_UN_INSTANT.json', rep); log('A3A fet ' + json.dumps(esc['comprovacio_ln_fusio_sobre_primerencs_corregits']) + ' c_G ' + json.dumps(esc['c_G_constant']) + ' DR ' + f'{DR:.3f}')
