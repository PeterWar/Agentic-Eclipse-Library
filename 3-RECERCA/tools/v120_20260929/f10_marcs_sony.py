"""f10 (V120, 29-09-2026) · ELS MARCS DE LA SONY (A i B) I LA DISTÀNCIA A LA SEVA VORA, per esvair el camp de deformació a prop de la vora.
Lliçó de la primera V120: amb el camp sencer fins a la vora, la deformació treia la Sony del seu propi marc fins a ~13 px. A la vora del llenç la
base quedava sense dada (tira negra de 2–4 px i rampa de 6 px; les capes de detall s'hi aclarien 20–30 px), i a la vora diagonal de la B, a la
cantonada del camp de la Vixen (9,3 R☉), el triangle on només hi ha la Vixen creixia i sortia com una taca ovalada brillant.
Marc de cada tren = on hi ha dada a TOTES les seves variants (tots els canals finits i > 0) i pes G > 0, amb els forats interiors omplerts (la
Lluna, taques); la vora del llenç compta com a vora. Distància (px del llenç) de cada píxel a la vora del marc, a 1/4 (bilineal, prou per a un
esvaïment de 200 px). El camp_v120 hi multiplica u per smoothstep(d / L): u = 0 a la vora (el marc no es mou) i sencer a d ≥ L.
Sortides: <carpeta_f1>/MARC_{A,B}_dist_quart.npy (float32, px del llenç) i F10_REBUT.json. Ús: f10_marcs_sony.py <carpeta_f1>"""
import sys, json, time, numpy as np
from pathlib import Path
from scipy import ndimage as ndi
F1 = Path(sys.argv[1]).resolve(); R = Path(__file__).resolve().parents[3]; H, W = 7506, 10551; t0 = time.time()
AP = R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats'; S29 = R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v29'; B2 = R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_B/cau'
FONTS = {'A': dict(dades=[R / '4-RESULTATS/v112_claude_20260928/fonts_v113_vora/apilats/sony_A_total.npy', AP / 'sony_A_total.npy'], pesos=[S29 / 'sony_A_weights.npy']),
         'B': dict(dades=[AP / 'cau/sony_B_total_v42.npy'], pesos=[B2 / 'sony_B_weights_v42.npy', S29 / 'sony_B_weights.npy'])}
rep = dict(guio=str(Path(__file__).relative_to(R)), marcs={})
for X, f in FONTS.items():
    m = np.ones((H, W), bool)
    for p in f['dades']:
        a = np.load(p, mmap_mode='r')
        for y0 in range(0, H, 1024):
            b = np.asarray(a[y0:y0 + 1024], np.float32); m[y0:y0 + 1024] &= np.all(np.isfinite(b) & (b > 0), axis=2)
    for p in f['pesos']:
        a = np.load(p, mmap_mode='r')
        for y0 in range(0, H, 1024): m[y0:y0 + 1024] &= np.asarray(a[y0:y0 + 1024, :, 1]) > 0
    ple = ndi.binary_fill_holes(m); forats = int((ple & ~m).sum())
    q = ple[::4, ::4]; qp = np.pad(q, 1, constant_values=False)                 # la vora del llenç és vora
    d = (ndi.distance_transform_edt(qp)[1:-1, 1:-1] * 4).astype(np.float32)
    np.save(F1 / f'MARC_{X}_dist_quart.npy', d)
    rep['marcs'][X] = dict(fonts=[str(p.relative_to(R)) for p in f['dades'] + f['pesos']], pixels_marc=int(ple.sum()), forats_omplerts_px=forats)
    print(X, rep['marcs'][X], f'{time.time() - t0:.0f}s', flush=True)
json.dump(rep, open(F1 / 'F10_REBUT.json', 'w'), ensure_ascii=False, indent=1)
