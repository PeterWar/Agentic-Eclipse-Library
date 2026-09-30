"""A0 (V37fc) · Suport i base amb el forat circular: support_v37fc, base_G_v37fc, fusion_total_v37fc a partir dels de la V36."""
from comu37fc import *
r, t = coords(); m = np.load(CAU36 / 'support_v36.npy'); dins = r < RADI_FORAT_PX
m2 = m & ~dins; np.save(CAU37FC / 'support_v37fc.npy', m2)
G = np.load(CAU36 / 'base_G_v36.npy', mmap_mode='r'); g = np.asarray(G).copy(); g[dins] = 0; np.save(CAU37FC / 'base_G_v37fc.npy', g); del g
F = np.load(CAU36 / 'fusion_total_v36.npy', mmap_mode='r'); out = np.lib.format.open_memmap(CAU37FC / 'fusion_total_v37fc.npy', mode='w+', dtype=np.float32, shape=F.shape)
for y in range(0, H, 512):
    blk = np.asarray(F[y:y + 512]).copy(); blk[dins[y:y + 512]] = 0; out[y:y + 512] = blk
out.flush(); savejson(REB37FC / 'A0_forat_circular.json', {'radi_px': RADI_FORAT_PX, 'px_trets': int((m & dins).sum()), 'px_suport_abans': int(m.sum()), 'px_suport_despres': int(m2.sum())}); log(f'forat circular: {int((m & dins).sum())} px trets del suport')
