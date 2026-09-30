"""a4v (V93) · Continuació dels ràsters de filtre als píxels sense dada tocant la Lluna, NOMÉS AMB EL NIVELL (sense textura inventada).
Per què: la V88 (a4) hi copiava el valor al llarg del radi (textura estirada = «lent»); la V92 (a4m) hi feia mirall de la textura a través de
r_ref, i Pere hi va veure el mirall (capa «Artefactes V92», línia grisa a 3,5–5,5 px: «com si la línia actués com a mirall, un vertical
mirror flip along the line»). Allà no hi ha dada: qualsevol textura que s'hi posi és inventada i es veu (estirada o en mirall). Ara:
  - pes de la dada smoothstep(dist, VORA−1, VORA+2) amb VORA = 2 com a la V88–V92 (amb VORA = 1 la vora dreta s'enfosquia un 1,6 %, c8);
  - on no hi ha dada plena, el valor és el NIVELL al llarg de l'arc (gaussiana d'azimut σ 3 px, només dada) a r_ref = R + DMIN + VORA + 2,
    sense textura: ni copiada ni en mirall;
  - dins del disc (d < −6 px) el ràster és 0,5 (pla): allà l'Earthshine és opac.
Entrada: 4-RESULTATS/v88_20260923/filtres/ (els 16, abans de continuar). Sortida: 4-RESULTATS/v93_20260924/filtres_nivell/ i A4V.json."""
from v93_comu import *
import cv2
from scipy.ndimage import gaussian_filter1d
from v86_operadors import smoothstep
claim(); V88 = ARREL / '4-RESULTATS/v88_20260923'; OUT = SORT / __import__('os').environ.get('SORTIDA_A4V', 'filtres_nivell'); OUT.mkdir(exist_ok=True)
TAGS = list(dict.fromkeys(FILTRES.values()))
Q = np.load(V88 / 'A3A_franja_un_instant.npz'); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; dom = Q['domini']; DMIN = Q['DMIN']; NBZ = len(DMIN); cx, cy, R = [float(v) for v in Q['centre']]
VORA = float(__import__("os").environ.get("VORA_V93", "2.0")); yq, xq = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xq - cx, yq - cy).astype('float32'); th = (np.degrees(np.arctan2(-(yq - cy), xq - cx)) + 360) % 360
dmin = DMIN[(th / 360 * NBZ).astype(int) % NBZ]; dist = (rL - R) - dmin; pes = (smoothstep(dist, VORA - 1, VORA + 2) * dom).astype('float32')
zona = (pes < 0.999) & (rL < R + 60); r_ref = (R + dmin + VORA + 2.0).astype('float32'); disc = (rL - R) < -6
DT = 0.05; NT = int(360 / DT); PAD = 8; R0, DR = R - 40.0, 0.25; RHO = R0 + np.arange(int(120 / DR) + 1) * DR
TS = np.radians((np.arange(-PAD, NT + PAD) + 0.5) * DT); TT, RR = np.meshgrid(TS, RHO)
PX = (cx + RR * np.cos(TT) - bx0).astype('float32'); PY = (cy - RR * np.sin(TT) - by0).astype('float32'); sig_cols = 3.0 / (RHO * np.radians(DT))
MV = cv2.remap(dom.astype('float32'), PX, PY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
IXc = (th / DT - 0.5 + PAD).astype('float32'); IYref = ((r_ref - R0) / DR).astype('float32')
def arc(Z):
    out = np.empty_like(Z)
    for i in range(Z.shape[0]): out[i] = gaussian_filter1d(Z[i], sig_cols[i], mode='wrap')
    return out
den = arc(MV); rep = dict(vora_px=VORA, sigma_arc_px=3.0, disc_pla_d_menys_de=-6, capes={})
for tag in TAGS:
    u = np.load(V88 / 'filtres' / f'{tag}_u16.npy'); box = u[by0:by1, bx0:bx1].astype('float32') / 65535
    P = cv2.remap(box, PX, PY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE); niv = (arc(P * MV) / np.maximum(den, 1e-6)).astype('float32')
    new = cv2.remap(niv, IXc, IYref, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    fos = np.where(zona, pes * box + (1 - pes) * new, box); fos = np.where(disc, 0.5, fos)
    out = u.copy(); out[by0:by1, bx0:bx1] = np.round(np.clip(fos, 0, 1) * 65535).astype('uint16'); np.save(OUT / f'{tag}_u16.npy', out)
    rep['capes'][tag] = dict(sha256=sha(OUT / f'{tag}_u16.npy')); log(tag + ' continuat amb el nivell')
desa_json('A4V.json', rep); log('A4V fet')
