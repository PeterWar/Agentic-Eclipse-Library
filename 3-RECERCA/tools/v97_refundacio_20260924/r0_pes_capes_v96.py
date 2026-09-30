"""r0 (V97) · Pes de cada capa visible de la V96 al compost per sota de PixInsight (234), sense les capes d'ajust de Pere.
Pregunta de Pere (24-09): «començant pels filtres que més % de la imatge final generen».
Mètrica: compost emulat (v86_compost.comp) amb totes les capes visibles i sense cadascuna; pes = mitjana de |Δ| (en 0–1, per canal)
dins l'enquadrament final, i quota = |Δ_capa| / Σ|Δ_capes|. També el pes que tindrien les capes ocultes (MGN, RHEF…) si s'encenguessin.
Mostreig cada PAS píxels (la mètrica és global; no serveix per jutjar vores). Només llegeix; escriu R0_PES_CAPES_V96.json."""
import sys, json, time
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923'))
from psb69 import PSB
import v86_compost
def comp(layers, H, W):
    """v86_compost.comp amb el mode Aclarir (LIGHTEN = màxim per canal), que la V86 no necessitava."""
    Cb = np.zeros((H, W, 3), np.float32); ab = np.zeros((H, W), np.float32)
    for mode, F, a in layers:
        if mode == 'NORMAL': B = F
        elif mode == 'MULTIPLY': B = Cb * F
        elif mode == 'OVERLAY': B = np.where(Cb < 0.5, 2 * Cb * F, 1 - 2 * (1 - Cb) * (1 - F))
        elif mode == 'LINEAR_DODGE': B = np.clip(Cb + F, 0, 1)
        elif mode == 'DIFFERENCE': B = np.abs(Cb - F)
        elif mode == 'LIGHTEN': B = np.maximum(Cb, F)
        else: raise ValueError(mode)
        Cs = (1 - ab[..., None]) * F + ab[..., None] * B; ao = a + ab * (1 - a)
        num = a[..., None] * Cs + (1 - a[..., None]) * ab[..., None] * Cb
        Cb = np.where(ao[..., None] > 0, num / np.maximum(ao[..., None], 1e-9), 0).astype(np.float32); ab = ao.astype(np.float32)
    return Cb, ab
SORT = ARREL / '4-RESULTATS/v97_refundacio_20260924'; SORT.mkdir(exist_ok=True)
PAS = 3; MARC = (1325, 1142, 9348, 6263)  # enquadrament final (V78-FINAL)
p = PSB(str(ARREL / '1-PHOTOSHOP/V96.psb')); W, H = p.width, p.height
def capa(lid, forca_visible=False):
    L = p.layer(lid)
    F = np.stack([p.channel_box(lid, c, (0, 0, W, H))[::PAS, ::PAS] for c in range(3)], -1).astype(np.float32) / 65535
    a = p.channel_box(lid, -1, (0, 0, W, H))[::PAS, ::PAS].astype(np.float32) / 65535 if -1 in L['chans'] else np.ones(F.shape[:2], np.float32)
    if L['mask'] is not None and -2 in L['chans']:
        m = p.channel_box(lid, -2, (0, 0, W, H), fill=65535 if L['mask']['background'] == 255 else 0)[::PAS, ::PAS].astype(np.float32) / 65535
    else: m = 1.0
    return L['blend'], F, a * m * (L['opacity'] / 255.0)
ordre = [l for l in p.layers]; i234 = next(i for i, l in enumerate(ordre) if l['id'] == 234)
sota = [l for l in ordre[:i234] if l['right'] > l['left']]  # sense capes d'ajust (buides)
vis = [l['id'] for l in sota if l['visible']]; ocu = [48, 50, 52, 53, 54, 43, 44]  # filtres ocults (sota la base): es proven just a sobre de la 42
t = time.time(); C = {lid: capa(lid) for lid in vis + ocu}; print(f'llegides {len(C)} capes en {time.time()-t:.0f} s', flush=True)
h, w = C[vis[0]][1].shape[:2]; y0, y1, x0, x1 = MARC[1] // PAS, MARC[3] // PAS, MARC[0] // PAS, MARC[2] // PAS
ref, cob = comp([C[i] for i in vis], h, w); ref = ref[y0:y1, x0:x1]
res = dict(font='1-PHOTOSHOP/V96.psb', pas=PAS, marc=MARC, metrica='mitjana |Δ| 0–1 per canal dins el marc; compost emulat sota la 234, sense capes d\'ajust', visibles={}, ocultes={})
for lid in vis:
    c, _ = comp([C[i] for i in vis if i != lid], h, w); d = np.abs(ref - c[y0:y1, x0:x1])
    res['visibles'][lid] = dict(nom=p.layer(lid)['name'], mode=p.layer(lid)['blend'], opacitat=p.layer(lid)['opacity'], dmitja=float(d.mean()), p99=float(np.percentile(d, 99)), frac_px_gt_1pc=float((d.max(-1) > 0.01).mean()))
    print(lid, res['visibles'][lid], flush=True)
for lid in ocu:
    # la capa oculta encesa al seu lloc de la pila, amb la seva opacitat
    k = vis.index(42) + 1; pila = vis[:k] + [lid] + vis[k:]
    c, _ = comp([C[i] for i in pila], h, w); d = np.abs(ref - c[y0:y1, x0:x1])
    res['ocultes'][lid] = dict(nom=p.layer(lid)['name'], mode=p.layer(lid)['blend'], opacitat=p.layer(lid)['opacity'], dmitja_si_encesa=float(d.mean()), p99=float(np.percentile(d, 99)))
    print(lid, res['ocultes'][lid], flush=True)
tot = sum(v['dmitja'] for k, v in res['visibles'].items())
for v in res['visibles'].values(): v['quota'] = v['dmitja'] / tot
(SORT / 'R0_PES_CAPES_V96.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
for k, v in sorted(res['visibles'].items(), key=lambda kv: -kv[1]['dmitja']): print(f"{k:>4} {v['quota']*100:6.1f} %  {v['dmitja']:.4f}  {v['nom']}")
