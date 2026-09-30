"""a6 · Màscares de la V86 (decisió A de Pere, 23-09-2026: sota la vora suau de la Lluna hi ha corona, no un forat).
Filtres (17 capes): la màscara que Pere tenia a la V83 (abans que la V84 hi posés negre a tota la silueta lunar); a la zona de la Lluna
  (disc i franja escombrada fins a rb+3μ) el valor de la seva màscara just a fora es continua radialment cap endins, i tot es multiplica
  per (1 − Lluna opaca). Lluna opaca = alfa efectiva de la capa 30 (Earthshine · revelat de Pere) ≥ 0,999.
  Així: cap filtre no toca la Lluna, fora de la Lluna la màscara és la de Pere (pinzellades de la WOW bilateral incloses) i sota la
  vora suau de la Lluna els filtres continuen.
Base (capa 3): la màscara de Pere (V84 = V83), oberta a (1 − Lluna opaca) a la zona de la Lluna: sota la vora suau hi ha d'haver
  alguna cosa opaca (la V85 la tancava i deixava l'anell transparent r 451–465).
Sortida: 4-RESULTATS/v86_neta_20260923/mascares/L<id>_mask.npy (uint16, llenç sencer) i A6_MASCARES.json."""
from v86_comu import *
from psb69 import PSB
from scipy.ndimage import gaussian_filter1d
claim(); O = SORT / 'mascares'; O.mkdir(exist_ok=True)
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; g = np.load(SORT / 'A2_geometria.npz'); by0, by1, bx0, bx1 = g['box']; rb = g['rb_s']
MU = json.loads((SORT / 'A4_FRANJA.json').read_text())['mu_px'] if (SORT / 'A4_FRANJA.json').exists() else 6.0
cx, cy, R = geo['cx'], geo['cy'], geo['R']; NB = len(rb)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xx - cx, yy - cy).astype('float32'); th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
ib = (th / 360 * NB).astype(int) % NB; RB = rb[ib].astype('float32')
zona = rL <= RB + 3 * MU                         # disc + franja + transició (on a4 ha interpolat)
anell_ext = (rL > RB + 3 * MU + 2) & (rL <= RB + 3 * MU + 8)   # anell just a fora, d'on es pren el valor de la màscara de Pere
e30 = g['e30']; opaca = e30 >= 0.999
def full_mask(p, lid):
    L = p.layer(lid); m, org = p.channel(lid, -2); full = np.full((H, W), 65535 if L['mask']['background'] == 255 else 0, np.uint16); ox, oy = org; h, w = m.shape
    ys0, xs0 = max(oy, 0), max(ox, 0); full[ys0:min(oy + h, H), xs0:min(ox + w, W)] = m[ys0 - oy:min(oy + h, H) - oy, xs0 - ox:min(ox + w, W) - ox]; return full, L['mask']
p83 = PSB(str(ARREL / '1-PHOTOSHOP/V83.psb')); p84 = PSB(str(ARREL / '1-PHOTOSHOP/V84.psb')); rep = dict(opaca_px=int(opaca.sum()), zona_px=int(zona.sum()), mu=MU, capes={})
for lid in [41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 250]:
    full, md = full_mask(p83, lid); box = full[by0:by1, bx0:bx1].astype('float32') / 65535
    ext = np.full(NB, np.nan)
    for k in range(NB):
        v = box[anell_ext & (ib == k)]
        if v.size: ext[k] = np.median(v)
    ok = np.isfinite(ext); ext[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), ext[ok], period=NB); ext = gaussian_filter1d(ext, 2, mode='wrap')
    new = np.where(zona, ext[ib], box) * (1 - opaca)
    full[by0:by1, bx0:bx1] = np.round(np.clip(new, 0, 1) * 65535).astype(np.uint16); np.save(O / f'L{lid}_mask.npy', full)
    rep['capes'][lid] = dict(font='V83 (Pere)', fons=md['background'], mitjana_zona_V83=float(box[zona].mean()), mitjana_zona_V86=float(new[zona].mean()), mitjana_fora_zona=float(box[~zona].mean()), ext_min=float(ext.min()), ext_max=float(ext.max()))
    log(f'màscara {lid} feta')
full, md = full_mask(p84, 3); box = full[by0:by1, bx0:bx1].astype('float32') / 65535
new = np.where(zona, 1 - opaca, box); full[by0:by1, bx0:bx1] = np.round(np.clip(new, 0, 1) * 65535).astype(np.uint16); np.save(O / 'L3_mask.npy', full)
rep['capes'][3] = dict(font='V84 (Pere, igual que V83)', fons=md['background'], mitjana_zona_V84=float(box[zona].mean()), mitjana_zona_V86=float(new[zona].mean()))
desa_json('A6_MASCARES.json', rep); log('A6 fet')
