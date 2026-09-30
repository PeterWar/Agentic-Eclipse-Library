"""e2 (V97) · La Sony al MARC DE LA LLUNA, per a l'Earthshine: els fotogrames llargs de l'apuntament A (0,25, 1, 2 i 8 s), rellegits dels RAW
amb la calibració (F0), el registre (F1.3), el guany k (F2.2) i els offsets c03 congelats, com la b2 i la caixa lunar a9, però:
  · sense màscara lunar (la Lluna és el que es vol);
  · cada fotograma es desplaça (una translació al pla del fotograma) perquè el SEU centre de la Lluna (sol + vector Lluna−Sol de l'F1.3)
    caigui on és la Lluna de presentació de Pere (t = 18,43 s), a la graella final;
  · sense els camps de nivell φ (són ajustos de la corona, fora de la Lluna no mesurats) — declarat.
L'apuntament B no hi entra: porta un vel de ~40 comptes a la Lluna (research/126–127, pes ~0).
Sortida: <out>/E2_sony_lluna.npz (caixa de limb_frames: numerador i pes per canal natiu, i la imatge balancejada amb matriu) i E2_SONY_LLUNA.json.
Ús: e2_sony_lluna.py <out>"""
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from a4_sources import *
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True); guard(); t0 = time.time()
ns, fr = context(); ns.update(FLAT_CENTRE_YX={'sony': (2660., 4000.)}, FLAT_SIGMA_PX=32.)
definition(fr['sources']['common32']['copy'], 'flat_ripple_correction', ns); COMMON_TO_FINAL = ns['COMMON_TO_FINAL']
LLUNA = (5375.786804312011, 3775.9774911631)            # Lluna de presentació (V86 A2, t = 18,43 s)
path = f12dirs['sony']; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
meta = json.loads((O / 'sources_v36/cau/sony_meta.json').read_text())['frames']
SEL = [m for m in meta if m['group'] == 'sony_A' and m['exp'] >= 0.25]
lf = json.loads((O / 'limb_frames/METADATA.json').read_text()); y0, y1, x0, x1 = lf['box_y0y1x0x1']; h, w = y1 - y0, x1 - x0
fcorr, _ = ns['flat_ripple_correction'](ctx, 'sony'); inv = cv2.invertAffineTransform(COMMON_TO_FINAL)
yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
def al_fotograma(X, Y, v):
    qx = inv[0, 0] * X + inv[0, 1] * Y + inv[0, 2]; qy = inv[1, 0] * X + inv[1, 1] * Y + inv[1, 2]; dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
    return (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32), (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32)
Nn = np.zeros((len(SEL), h, w, 3), np.float32); Wg = np.zeros_like(Nn); info = []
for j, m in enumerate(SEL):
    n = m['name']; v = pos[n]; k = kq.get(n, 1.0)
    rx, ry = al_fotograma(xx, yy, v); rL, sL = al_fotograma(np.float32(LLUNA[0]), np.float32(LLUNA[1]), v)
    mlx = v['sol_x'] + float(v['lluna_dx']); mly = v['sol_y'] + float(v['lluna_dy']); ox_, oy_ = mlx - float(rL), mly - float(sL)
    rx = rx + ox_; ry = ry + oy_
    for i, (pl, wgt) in ctx.plans(n, v['exp']).items():
        c = comu.IDX_CANAL[i]; oy, ox = ctx.orig[i]
        if fcorr is not None: pl = pl * fcorr[i]
        mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
        dd = cv2.remap(wgt, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); nn = cv2.remap(pl * wgt * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        b = float(m['offset_RGB'][c])
        if b != 0: nn = nn + b * dd
        Nn[j, ..., c] += nn; Wg[j, ..., c] += dd
    info.append(dict(nom=n, t=m['t'], exposicio=m['exp'], k=k, desplacament_pla_px=[round(ox_, 3), round(oy_, 3)])); print(n, m['exp'], 's', f'{time.time()-t0:.0f}s', flush=True)
Nt = Nn.sum(0); Wt = Wg.sum(0); E = np.where(Wt > 0, Nt / np.maximum(Wt, 1e-30), 0)
Ec = np.einsum('ij,...j->...i', np.array(run.matriu), E * np.array(run.color['guany']))
np.savez_compressed(OUT / 'E2_sony_lluna.npz', box=np.array([y0, y1, x0, x1]), E=Ec.astype(np.float32), W=Wt.astype(np.float32), N_f=Nn, W_f=Wg, centre=np.array(LLUNA))
save(OUT / 'E2_SONY_LLUNA.json', dict(fotogrames=info, caixa=[y0, y1, x0, x1], segons=time.time() - t0, nota=__doc__.split('\n')[0])); print('FET', flush=True)
