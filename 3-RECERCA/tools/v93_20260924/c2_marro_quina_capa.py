"""c2 · Les marques marrons de Pere («parts lleugerament més fosques», lluny del limbe): quina capa les fa més fosques que la corona del costat.
Compost EMULAT (sense capes d'ajust) a 1/4 de resolució, capa a capa de baix a dalt. Per a cada component marró: lluminància mitjana a la marca
dividida per la de la corona a la MATEIXA distància del limbe i als azimuts del costat (fora de la marca). També cada capa sola (el seu valor i
la seva alfa × màscara a la marca i al costat). Sortida: C2_MARRO.json."""
from v93_comu import *
from psb69 import PSB
from vm_compost import comp, capa_box
import cv2
claim(); p = PSB(str(PSB_PERE)); F4 = 4; h4, w4 = H // F4, W // F4
vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left'] and L['id'] not in (239, 240, 241, 242, 243, 244, 269)]
z = np.load(SORT / 'marques_v92_classes.npz'); org = z['origin']; M = z['to_30_40']
full = np.zeros((H, W), bool); full[org[1]:org[1] + M.shape[0], org[0]:org[0] + M.shape[1]] = M; M4 = cv2.resize(full.astype(np.float32), (w4, h4), interpolation=cv2.INTER_AREA) > 0.5
cx, cy, R = GEO['cx'] / F4, GEO['cy'] / F4, GEO['R'] / F4
yy, xx = np.mgrid[:h4, :w4]; d = (np.hypot(xx - cx, yy - cy) - R) * F4; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
n, lab = cv2.connectedComponents(cv2.dilate(M4.astype(np.uint8), np.ones((5, 5), np.uint8)))
comps = []
for k in range(1, n):
    m = (lab == k) & M4
    if m.sum() < 30: continue
    a0, a1 = np.percentile(th[m], [1, 99]); d0, d1 = np.percentile(d[m], [5, 95]); span = max(a1 - a0, 2); dl = max(3.0, 0.6 * span)
    nb = (d >= d0) & (d <= d1) & ~(cv2.dilate(M4.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0) & ((((th - a0) % 360) > 360 - dl) | (((th - a1) % 360) < dl))
    comps.append(dict(m=m, nb=nb, info=dict(azimut=[round(float(a0), 1), round(float(a1), 1)], d=[round(float(d0)), round(float(d1))], px4=int(m.sum()), veins_px4=int(nb.sum()))))
log(f'{len(comps)} components marrons')
def redueix(A): return cv2.resize(A, (w4, h4), interpolation=cv2.INTER_AREA)
lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]
Cb = np.zeros((h4, w4, 3), np.float32); ab = np.zeros((h4, w4), np.float32); rep = {'components': [c['info'] for c in comps], 'etapes': []}
from vm_compost import comp as _comp
for lid in vis:
    md, F_, a_ = capa_box(p, lid, (0, 0, W, H)); F_ = redueix(F_.astype(np.float32)); a_ = redueix(a_.astype(np.float32))
    Cb, ab = _comp([('NORMAL', Cb, ab), (md, F_, a_)], h4, w4) if lid != vis[0] else _comp([(md, F_, a_)], h4, w4)
    Y = lum(Cb); Yl = lum(F_)
    et = dict(capa=lid, nom=p.layer(lid)['name'][:34], mode=md, quocient_marca_sobre_veins=[round(float(Y[c['m']].mean() / max(Y[c['nb']].mean(), 1e-6)), 4) for c in comps],
              capa_sola_valor=[[round(float(Yl[c['m']].mean()), 4), round(float(Yl[c['nb']].mean()), 4)] for c in comps],
              capa_sola_alfa=[[round(float(a_[c['m']].mean()), 3), round(float(a_[c['nb']].mean()), 3)] for c in comps])
    rep['etapes'].append(et); log(f"{lid} {et['nom']:34s} {md:12s} marca/veïns: {et['quocient_marca_sobre_veins']}")
    del F_, a_
desa_json('C2_MARRO.json', rep); log(json.dumps(rep['components']))
