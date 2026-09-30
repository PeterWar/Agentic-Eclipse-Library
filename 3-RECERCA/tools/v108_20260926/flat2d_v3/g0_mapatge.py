"""g0_mapatge (V108, flat2d_v3) · El mapatge llenç ↔ sensor de cada fotograma dels tres grups (vixen, sony_A, sony_B), amb el MATEIX codi que fan
servir els apilats (b2_v97 per a vixen i sony_A; el programa congelat B2 V42 per a sony_B: gir δ = +8,10′ i correccions (cx, cy) per fotograma).
  llenç (x, y) → q = inv(COMMON_TO_FINAL)·(x, y, 1); d = (q − (CX, CY))·k; [sony_B: d girat δ]; sensor RAW rx = ca·dx + sa·dy + sol_x + cx, ry = −sa·dx + ca·dy + sol_y + cy
Per a cada grup desa també l'afí de referència (sensor RAW → llenç) amb la posició mitjana ponderada per l'exposició (la deriva dins d'un grup
és de pocs píxels: A ≤ 3, B ≈ 5, Vixen ≈ 20 px RAW) i la dispersió de les posicions.
Sortida: 4-RESULTATS/v108_20260926/flat2d_v3/diag/MAPATGE_V3.json. Només lectura (cal el claim viu perquè obre el context de la cadena)."""
import sys, json, math
from pathlib import Path
CRT = Path(__file__).resolve().parents[2] / 'v97_refundacio_20260924/cadena_raw'; sys.path.insert(0, str(CRT))
import a4_sources as _A4; _A4.CID = json.loads((_A4.R / '.coordination/claim.lock/owner.json').read_text())['claim_id']
assert _A4.CID == 'CLAUDE_V108_MARRONS_I_ZONES_NEGRES_20260926', _A4.CID
from a4_sources import *
guard()
OUT = _A4.R / '4-RESULTATS/v108_20260926/flat2d_v3/diag'; OUT.mkdir(parents=True, exist_ok=True)
ns, fr = context(); inv = cv2.invertAffineTransform(ns['COMMON_TO_FINAL'])
CORR_B = json.loads((H / 'b2_v42_correccions_B.json').read_text()); DELTA_B = math.radians(8.10 / 60.0)
res = dict(nota=__doc__.split('\n')[1:3], inv_common_to_final=inv.tolist(), delta_B_rad=DELTA_B, trens={})
for tag in ('vixen', 'sony'):
    path = f12dirs[tag]; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
    pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']
    meta = json.loads((O / 'sources_v36/cau' / f'{tag}_meta.json').read_text())['frames']
    grups = ['vixen'] if tag == 'vixen' else ['sony_A', 'sony_B']
    T = dict(CX=float(ctx.CX), CY=float(ctx.CY), k=float(ctx.k), ca=float(ctx.ca), sa=float(ctx.sa), RL=float(ctx.RL), forma_sensor=list(ctx.flat.shape), grups={},
             matriu=np.asarray(run.matriu, float).tolist(), guany=np.asarray(run.color['guany'], float).tolist())   # u = (M · u_càmera) · guany (comu.lluminancia)
    for g in grups:
        fot = {}
        for m in meta:
            if tag == 'sony' and m['group'] != g: continue
            n = m['name']; v = pos[n]; cx_, cy_ = CORR_B.get(n, (0.0, 0.0)) if g == 'sony_B' else (0.0, 0.0)
            fot[n] = dict(exp=float(v['exp']), t=m.get('t'), sol_x=float(v['sol_x']) + float(cx_), sol_y=float(v['sol_y']) + float(cy_))
        wsum = sum(f['exp'] for f in fot.values()); sx = sum(f['exp'] * f['sol_x'] for f in fot.values()) / wsum; sy = sum(f['exp'] * f['sol_y'] for f in fot.values()) / wsum
        def a_sensor(x, y, sx=sx, sy=sy, g=g):
            qx = inv[0, 0] * x + inv[0, 1] * y + inv[0, 2]; qy = inv[1, 0] * x + inv[1, 1] * y + inv[1, 2]; dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
            if g == 'sony_B': c_, s_ = math.cos(DELTA_B), math.sin(DELTA_B); dx, dy = c_ * dx - s_ * dy, s_ * dx + c_ * dy
            return np.array([ctx.ca * dx + ctx.sa * dy + sx, -ctx.sa * dx + ctx.ca * dy + sy])
        P = np.array([[0., 0.], [3000., 0.], [0., 3000.], [3000., 3000.]]); S = np.array([a_sensor(x, y) for x, y in P])
        A_s2l = np.linalg.lstsq(np.c_[S, np.ones(len(S))], P, rcond=None)[0].T       # llenç = A · (rx, ry, 1)
        A_l2s = np.linalg.lstsq(np.c_[P, np.ones(len(P))], S, rcond=None)[0].T       # sensor RAW = A · (x, y, 1)
        disp = float(np.sqrt(np.mean([(f['sol_x'] - sx) ** 2 + (f['sol_y'] - sy) ** 2 for f in fot.values()])))
        dmax = float(max(np.hypot(f['sol_x'] - sx, f['sol_y'] - sy) for f in fot.values()))
        T['grups'][g] = dict(fotogrames=fot, sol_mitja_ponderat_exp=[sx, sy], dispersio_rms_px_RAW=disp, dispersio_max_px_RAW=dmax,
                             afi_sensor_a_llenc=A_s2l.tolist(), afi_llenc_a_sensor=A_l2s.tolist(), escala_llenc_per_px_RAW=float(np.sqrt(abs(np.linalg.det(A_s2l[:, :2])))))
        print(tag, g, len(fot), 'fotogrames · dispersió rms', round(disp, 2), 'màx', round(dmax, 2), 'px RAW · escala', round(T['grups'][g]['escala_llenc_per_px_RAW'], 4), flush=True)
    res['trens'][tag] = T; del ctx, run
save(OUT / 'MAPATGE_V3.json', res); print('FET')
