"""a3a · La franja amb dada d'UN SOL INSTANT (norma de Pere del 17-09, research/165: «o s'omple amb un sol instant»).
Per què: els arcs de la franja neixen de BARREJAR fotogrames amb el limbe a llocs diferents (la Lluna es mou 28,5 px). Els fotogrames dels
primers segons (t ≤ 22,3 s: 8 × 1/3200 s + 1/2000, 1/500 i 1/125 s) tenen el limbe on és la Lluna que es mostra (la capa 30 de Pere =
Lluna a t ≈ 18,4 s); junts no fan arcs i ensenyen la cromosfera i la protuberància d'aquell instant. Dada real, res inventat.
(La primera versió de la V86 excloïa la franja i la interpolava (decisió B literal): quedava un anell llis sense detall de 20–50 px,
visible al compost de Photoshop; es va refusar abans de lliurar. La prova d'aplanar els arcs al llarg del raig també es va refusar: escampava
el perfil del limbe i feia un anell clar amb perles.)
Construcció (caixa de 4-RESULTATS/v85.../limb_frames, 67 fotogrames Vixen amb numeradors, pesos i distància al limbe modelat per fotograma):
  E_c = Σ num_f,c / Σ w_f,c sobre els fotogrames primerencs, només on el píxel és fora del limbe modelat d'aquell fotograma (D_f ≥ 1 px)
        i almenys 8 dels 11 fotogrames hi contribueixen (al verd); buits del mosaic CFA omplerts per convolució normalitzada σ 0,8 px per canal;
        després, guanys de balanç i matriu de color del rebut (mateix espai que la fusió);
  nivell: c(d) = mediana sobre tots els azimuts de font/E a cada distància d al limbe (calaixos de 0,5 px, suavitzada): corregeix el dèficit de vora
        dels curts (la fusió ja el té corregit) i el biaix del terra, sense portar l'estructura azimutal de la fusió;
  font nova = (1−β)·font + β·c(d)·E, amb β = 1 dins de la franja i rampa smoothstep de rb−6 a rb+6, només on E és vàlida, fora del disc i fins a 45 px del limbe.
Domini nou dels filtres: el suport fora del disc de presentació, més la franja amb dada d'un instant; dins del disc (tapat per la Lluna opaca) no hi ha dada
i els operadors hi usen la condició de contorn (continuació).
Sortida: A3A_franja_un_instant.npz (caixa) i A3A_FRANJA_UN_INSTANT.json."""
from v86_comu import *
from v86_operadors import smoothstep
claim()
meta = json.loads((V85D / 'limb_frames/METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(V85D / 'limb_frames/numerator.npy', mmap_mode='r'); wt = np.load(V85D / 'limb_frames/weight.npy', mmap_mode='r'); Dm = np.load(V85D / 'limb_frames/distance_model.npy', mmap_mode='r')
T_MAX, D_MIN, N_MIN = 22.3, 1.0, 8        # ≥ 8 dels 11 fotogrames: la fila de vora amb 2–4 fotogrames feia una costura en ziga-zaga (23-09, 2:20)
early = [i for i, f in enumerate(fr) if f['time'] <= T_MAX]
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
g = np.load(SORT / 'A2_geometria.npz'); rb = g['rb_s']; NB = len(rb)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xx - cx, yy - cy); th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; RB = rb[(th / 360 * NB).astype(int) % NB]
import cv2
E = np.zeros((by1 - by0, bx1 - bx0, 3), np.float32); W = np.zeros_like(E); NF = np.zeros(E.shape[:2], np.int16)
for c in range(3):
    N_ = np.zeros(E.shape[:2], np.float64); W_ = np.zeros(E.shape[:2], np.float64); n_ = np.zeros(E.shape[:2], np.int16)
    for i in early:
        ok = np.asarray(Dm[i]) >= D_MIN; w_ = np.where(ok, np.asarray(wt[i, :, :, c], np.float64), 0); N_ += np.where(ok, np.asarray(num[i, :, :, c], np.float64), 0); W_ += w_; n_ += (w_ > 0)
    # mostres CFA: el R i el B no tenen mostra a cada píxel; convolució normalitzada molt petita (σ 0,8 px) per omplir els buits del mosaic
    Ns = cv2.GaussianBlur(N_.astype(np.float32), (0, 0), 0.8); Ws = cv2.GaussianBlur(W_.astype(np.float32), (0, 0), 0.8)
    E[..., c] = np.where(Ws > 0, Ns / np.maximum(Ws, 1e-30), 0); W[..., c] = Ws
    if c == 1: NF = n_
validE = (NF >= N_MIN) & (W > 0).all(-1)        # validesa pel nombre de fotogrames al verd (≥ 8 dels 11)
# mateix espai de color que la fusió: guanys de balanç i matriu de color del rebut dels fotogrames (METADATA), com a la cadena
Mx = np.array(meta['matrix'], np.float32); gn = np.array(meta['gain'], np.float32); E = np.einsum('ij,...j->...i', Mx, E * gn).astype(np.float32)
validE &= (E[..., 1] > 0)     # i G positiu després de la matriu; validesa pel G (el blau matricial pot sortir ≤ 0 pel soroll dels curts: l'ACHF ja descarta canal per canal)
D_US = 45.0     # només es fa servir dada primerenca fins a 45 px del limbe (més enllà els curts s'acosten al terra de la suma i la mitjana s'esbiaixa)
beta = ((1 - smoothstep(rL, RB - 6, RB + 6)) * validE * (rL > R) * (rL - R <= D_US)).astype(np.float32)
fonts = dict(G=np.load(FONTS / 'base_G.npy', mmap_mode='r'), F=np.load(FONTS / 'fusion_starless.npy', mmap_mode='r'), V=np.load(FONTS / 'vixen_starless.npy', mmap_mode='r'))
sup = np.load(FONTS / 'support.npy')[by0:by1, bx0:bx1]
from scipy.ndimage import gaussian_filter1d
dL = (rL - R); nb = np.clip((dL / 0.5).astype(int), 0, 199)                    # calaixos de 0,5 px de distància al limbe (0–100 px)
def perfil_c(font, e):
    # c(d) = mediana, sobre TOTS els azimuts, de font/primerencs a cada distància d al limbe: iguala el nivell mitjà (dèficit de vora dels curts,
    # que la fusió ja té corregit, i biaix del terra) sense importar l'estructura azimutal de la fusió (els arcs no són coherents en 360°)
    ok = (font > 0) & (e > 0) & sup & (dL > 0) & (dL < 100); c = np.ones(200)
    for k in range(200):
        s = ok & (nb == k)
        if s.sum() > 200: c[k] = np.median(font[s] / e[s])
    return np.clip(gaussian_filter1d(c, 3, mode='nearest'), 0.7, 1.3)
out = {}; esc = {}
Gb = np.asarray(fonts['G'][by0:by1, bx0:bx1]); cG = perfil_c(Gb, E[..., 1]); esc['c_G_per_distancia'] = {f'{d:.1f}': float(cG[int(d / 0.5)]) for d in [1, 2, 3, 5, 8, 12, 20, 30, 40, 45]}
out['G'] = np.where(beta > 0, (1 - beta) * Gb + beta * cG[nb] * E[..., 1], Gb).astype(np.float32)
Fb = np.asarray(fonts['F'][by0:by1, bx0:bx1]).astype(np.float32); Fn = Fb.copy()
for c in range(3):
    cc = perfil_c(Fb[..., c], E[..., c]); esc[f'c_F{c}_1_5_12_30px'] = [float(cc[int(d / 0.5)]) for d in [1, 5, 12, 30]]
    Fn[..., c] = np.where(beta > 0, (1 - beta) * Fb[..., c] + beta * cc[nb] * E[..., c], Fb[..., c])
out['F'] = Fn
Vb = np.asarray(fonts['V'][by0:by1, bx0:bx1, 1]).astype(np.float32); cV = perfil_c(Vb, E[..., 1]); esc['c_V_1_5_12_30px'] = [float(cV[int(d / 0.5)]) for d in [1, 5, 12, 30]]
out['V'] = np.where(beta > 0, (1 - beta) * Vb + beta * cV[nb] * E[..., 1], Vb).astype(np.float32)
# comprovació: dispersió de ln(fusió/primerencs corregits) per distància (al costat dret, fora de la franja escombrada, la fusió és neta)
chk = {}
for d0, d1 in [(3, 6), (6, 12), (12, 20), (20, 30), (30, 45)]:
    s = (Gb > 0) & (E[..., 1] > 0) & sup & (dL >= d0) & (dL < d1); rr_ = np.log(Gb[s] / (cG[nb][s] * E[..., 1][s])); chk[f'{d0}-{d1}'] = [float(np.median(rr_)), float(np.percentile(rr_, 16)), float(np.percentile(rr_, 84))]
esc['comprovacio_ln_fusio_sobre_primerencs_corregits'] = chk
# domini: fora del disc de presentació; a la franja només on hi ha dada d'un instant
dins_franja = rL < RB
domini = (rL > R) & ((sup & ~dins_franja) | (dins_franja & validE))
np.savez_compressed(SORT / 'A3A_franja_un_instant.npz', box=np.array([by0, by1, bx0, bx1]), G=out['G'], F=out['F'], V=out['V'], domini=domini, dins_franja=dins_franja, beta=beta, E=E, NF=NF)
rep = dict(fotogrames=[dict(i=i, nom=fr[i]['name'], t=fr[i]['time'], exposicio=fr[i]['exposure']) for i in early], D_min_px=D_MIN, fotogrames_min=N_MIN, escales=esc,
           franja_px_fora_disc=int((dins_franja & (rL > R)).sum()), franja_amb_dada_un_instant=int((dins_franja & (rL > R) & validE).sum()),
           franja_sense_dada=int((dins_franja & (rL > R) & ~validE).sum()), domini_caixa=int(domini.sum()), suport_caixa=int(sup.sum()))
desa_json('A3A_FRANJA_UN_INSTANT.json', rep); log('A3A fet ' + json.dumps(esc['comprovacio_ln_fusio_sobre_primerencs_corregits']) + ' c_G ' + json.dumps(esc['c_G_per_distancia']))
