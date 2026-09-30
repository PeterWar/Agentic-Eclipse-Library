"""a4 · Continuació suau dels ràsters de filtre als píxels SENSE DADA tocant la Lluna: el disc de presentació i la tira d'≈1–2 px entre el
limbe observat i on comencen els fotogrames primerencs vàlids (a3a). És l'única zona sense dada: la franja escombrada ja porta la dada d'un sol instant.
Aquests píxels queden sota la Lluna opaca, llevat de la seva vora suau (≈1–2 px, fins a ≈10 px a la protuberància): allà cal un valor continu amb
el de just fora, perquè la vora suau de la Lluna es fongui amb la corona sense línia. La continuació parteix de 2 px dins de la dada: els primers px
de dada porten la resposta d'un sol costat dels filtres i el dèficit residual de la vora difuminada del limbe (prova del 23-09, 3:35, sobre el compost
emulat: amb 0–1 px quedava una línia fosca a dalt-esquerra i baix-esquerra; amb 3 px, una tira llisa a dalt i a baix). Mètode: piràmide pull-push +
relaxació de Laplace dels valors de pantalla del mateix filtre (v86_operadors), valors del domini intactes.
(Primer lliurament del 23-09: la dada començava a ~4 px, perquè a3a mesurava des del radi de l'efemèride, i amb 3 px de vora la continuació feia
una tira llisa de 4–6 px a dalt, a baix i a la dreta.)
Cel·les indefinides del RHEF local fora d'aquesta zona (menys de 50 mostres per sector, totes a la vora exterior dels camps, > 8,9 R☉):
mitjana normalitzada dels veïns (σ 4 px), declarades.
(Versió retirada el 23-09 a les 2 h, a4_franja_interpolacio_retirada.py: interpolació de tota la franja des de fora; deixava un anell llis
sense detall de 20–50 px al compost de Photoshop.)"""
from v88_comu import *
from v86_operadors import pull_push, relaxa, ng
claim()
MU = 6.0
TAGS = ['P01_NRGF', 'P01_NRGF_extrap', 'P02_RHEF', 'P02b_RHEF_ups0.35', 'P02c_RHEF_local60_native', 'P02d_RHEF_local30_native', '01', '04', '05', '06', '03', '03v30', '07', 'P03_MGN', 'P04_WOW', 'P05_WOW_bilateral']
C = SORT / 'filtres'; F = SORT / 'filtres_finals'; F.mkdir(exist_ok=True)
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
Q = np.load(SORT / 'A3A_franja_un_instant.npz'); by0, by1, bx0, bx1 = Q['box']; dom = Q['domini']
yy, xx = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xx - cx, yy - cy).astype('float32')
import cv2
VORA = 2.0     # els 2 primers px de dada porten la resposta d'un sol costat dels filtres i el dèficit residual de la vora difuminada (prova 0/1/2/3 px del 23-09)
# V88 · fosa SUAU sobre la distància ANALÍTICA a la corba llisa de la vora (a3a, DMIN per azimut), no sobre píxels: una màscara binària d'un cercle
# és un esglaonat i els filtres hi fan un gra a cada graó (el «cosit de cremallera» de la V87). Pes de la dada: smoothstep de VORA−1 a VORA+2 px.
NBZ = len(Q['DMIN']); th_ = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; dist = (rL - R) - Q['DMIN'][(th_ / 360 * NBZ).astype(int) % NBZ]
from v86_operadors import smoothstep
pes_dada = (smoothstep(dist, VORA - 1, VORA + 2) * dom).astype('float32')     # 0 a la vora (i fora del domini), 1 a partir de VORA+2
zona = (pes_dada < 0.999) & (rL < R + 60)          # on hi entra la continuació (del tot o en part)
r_ref = R + Q['DMIN'][(th_ / 360 * NBZ).astype(int) % NBZ] + VORA + 2.0         # radi de referència per azimut: dada plena
MX = (cx + r_ref * np.cos(np.radians(th_)) - bx0).astype('float32'); MY = (cy - r_ref * np.sin(np.radians(th_)) - by0).astype('float32')
rep = dict(mu_px=MU, vora_px=VORA, zona_px=int(zona.sum()), zona_fora_disc_px=int((zona & (rL > R)).sum()), capes={})
sup_full = np.load(FONTS / 'support.npy')
for tag in TAGS:
    u = np.load(C / f'{tag}_u16.npy'); extra = {}
    if tag.endswith('_native'):
        q = np.load(C / f'{tag}_float.npy', mmap_mode='r'); und = sup_full & ~np.isfinite(q)
        und[by0:by1, bx0:bx1] &= ~zona
        extra['indefinides_omplertes'] = int(und.sum())
        if und.any():
            uf = u.astype('float32') / 65535; fill = ng(uf, sup_full & ~und, 4.0); uf[und] = fill[und]; u = np.round(np.clip(uf, 0, 1) * 65535).astype('uint16')
    box = u[by0:by1, bx0:bx1].astype('float32') / 65535
    # V88 · continuació RADIAL: a cada azimut, el valor a la distància on la dada ja és plena (DMIN + VORA + 2 px) s'allarga radialment cap
    # endins i es fon amb la dada amb el pes suau. (La piràmide + Laplace de la V86 s'estenia per tot el disc i, arran de la vora, tirava cap a la
    # mitjana del disc: línia fosca o clara a la fosa, 23-09, 14:20.)
    new = cv2.remap(box.astype('float32'), MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    fos = np.where(zona, pes_dada * box + (1 - pes_dada) * new, box)
    out = u.copy(); out[by0:by1, bx0:bx1] = np.round(np.clip(fos, 0, 1) * 65535).astype('uint16')
    np.save(F / f'{tag}_u16.npy', out); rep['capes'][tag] = dict(sha256=sha(F / f'{tag}_u16.npy'), **extra); log(tag + ' continuat')
desa_json('A4_FRANJA.json', rep); log('A4 fet')
