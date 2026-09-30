"""w1 (V95) · Les dues WOW (P04 WOW i P05 WOW bilateral) al llenç sencer amb l'operador wow_v95 (parells simètrics; a la vora difuminada de la
Lluna, d < 12 px comptats des de la cresta de la dada, només parells a la mateixa distància del limbe; escales gruixudes només on el seu suport és complet; nivell de cada escala
centrat dins l'operador). CAP correcció posterior: ni neutralitza, ni a5d, ni el biaix de vora de la V94 (w2). Res inventat ni reflectit:
els píxels sense dada queden TRANSPARENTS (alfa de la V94, que és la del mateix domini; es comprova).
Entrades: les mateixes que la V94 (base_G amb la franja d'un instant a la caixa de la Lluna; domini).
Escala de visualització: 0,5 + k·q, amb k tal que el detall fi (pas alt σ 8 px) a 100–600 px del limbe tingui l'amplitud de la V93 (com la V94).
Sortida: 4-RESULTATS/v95_20260924/wow/<tag>_u16.npy, <tag>_alfa_u16.npy, <tag>_q.npy (float, NaN fora) i W1_WOW.json."""
import sys, json, time, hashlib, gc
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v95_20260924'; OUT = SORT / 'wow'; OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(__file__).parent)); from wow_v95 import wow_v95, desplacament_cresta, dmap_vora
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
H, W = 7506, 10551; V85 = ARREL / '4-RESULTATS/v85_regeneracio_20260922'; FONTS = V85 / 'd4_baseline/products/sources'; V88 = ARREL / '4-RESULTATS/v88_20260923'
Q = np.load(V88 / 'A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
a = np.load(FONTS / 'base_G.npy').astype(np.float32); m = np.load(FONTS / 'support.npy') & np.isfinite(a) & (a > 0)
a[qy0:qy1, qx0:qx1] = Q['G']; m[qy0:qy1, qx0:qx1] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a); log(f'domini: {m.sum()} px')
yy, xx = np.ogrid[:H, :W]; dmap = (np.hypot(xx - cx, yy - cy) - R).astype(np.float32); ref = (dmap > 100) & (dmap < 600) & m
off, cresta = desplacament_cresta(Q['G'], Q['domini'] & (Q['G'] > 0), (qy0, qx0), cx, cy, R); dmap = dmap_vora(dmap, xx, yy, cx, cy, off)
np.savez_compressed(SORT / 'W1_cresta.npz', off=off, cresta=cresta); log(f'cresta: desplaçament màx {off.max():.2f} px')
rep = dict(domini_px=int(m.sum()), escales=8, cresta_px_cada_30_graus=[round(float(cresta[int(i * len(cresta) / 12)]), 2) for i in range(12)], operador='wow_v95 (3-RECERCA/tools/v95_20260924/wow_v95.py)', capes={})
# paràmetres finals (proves t14–t16): centratge local de cada escala ponderat per la seva participació radial (els parells que veuen el perfil radial);
# tolerància «mateixa distància del limbe» 0,5–1,5 px a la bilateral (l'estricta li treu textura) i 0,25–0,75 px a la lineal (la normal li deixa l'anell de la cresta)
# centratge local de cada escala amb σ = min(150, max(32, 4·2^s)) px (t17: amb σ 256/512 a les escales 6–7 quedava un anell fosc ample, 0,48–0,49 a 150–500 px)
SIG = lambda s: min(150.0, max(32.0, 4.0 * 2 ** s))
PARAM = {'P05_WOW_bilateral': dict(centra_rad=True, iso=(0.5, 1.5), sig_rad=SIG), 'P04_WOW': dict(centra_rad=True, iso=(0.25, 0.75), sig_rad=SIG)}
for tag, bil in (('P05_WOW_bilateral', True), ('P04_WOW', False)):
    t0 = time.time(); q, pesos, mus = wow_v95(a, m, dmap, 8, bil, log=log, **PARAM[tag]); del pesos; gc.collect(); log(f'{tag}: WOW en {time.time() - t0:.0f} s')
    np.save(OUT / f'{tag}_q.npy', q)
    old = np.load(ARREL / f'4-RESULTATS/v93_20260924/filtres_v93/{tag}_u16.npy', mmap_mode='r').astype(np.float32) / 65535
    hp = lambda X: X - cv2.GaussianBlur(X, (0, 0), 8); qz = np.nan_to_num(q)
    k = float(np.std(hp(old)[ref]) / np.std(hp(qz)[ref])); disp = np.where(m, 0.5 + k * qz, 0.5).astype(np.float32); del old, qz, q; gc.collect()
    u = np.round(np.clip(disp, 0, 1) * 65535).astype(np.uint16); u[~m] = 32768; np.save(OUT / f'{tag}_u16.npy', u)
    a94w1 = np.load(ARREL / f'4-RESULTATS/v94_20260924/wow/{tag}_alfa_w1.npy', mmap_mode='r'); assert np.array_equal(np.asarray(a94w1) > 32767, m), 'el domini no és el de la V94'
    al = np.load(ARREL / f'4-RESULTATS/v94_20260924/wow/{tag}_alfa_u16.npy'); np.save(OUT / f'{tag}_alfa_u16.npy', al)
    rep['capes'][tag] = dict(bilateral=bil, parametres={'centra_rad': True, 'iso_px': list(PARAM[tag]['iso']), 'sigma_centratge_px': [SIG(e) for e in range(8)]}, k=round(k, 5), mitjanes_escala=[round(v, 5) for v in mus], sha256=sha(OUT / f'{tag}_u16.npy'), alfa='la de la V94 (w3), domini idèntic comprovat',
                             mitjana_domini=round(float(disp[m].mean()), 4), fora_de_0_1=int(((disp < 0) | (disp > 1))[m].sum()), segons=round(time.time() - t0))
    log(f"{tag}: k {k:.5f}, mitjana {rep['capes'][tag]['mitjana_domini']}, retallats {rep['capes'][tag]['fora_de_0_1']}"); del disp, u, al; gc.collect()
(SORT / 'W1_WOW.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); log('W1 fet')
