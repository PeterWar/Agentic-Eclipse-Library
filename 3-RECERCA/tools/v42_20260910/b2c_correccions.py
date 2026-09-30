"""B2c (V42) · Converteix els desplaçaments A→B mesurats a les estrelles per a cada fotograma llarg de B (E2, píxels del llenç) en correccions de (sol_x, sol_y) al SENSOR
per a la B2: ε = k · Rm · M⁻¹ · s, amb Rm = [[ca, sa], [−sa, ca]] del run (f2.Ctx) i M la part lineal de COMMON_TO_FINAL; s = desplaçament a cancel·lar (canviat de signe).
Es verifica empíricament tornant a apilar DSC06993 sol amb la correcció (el desplaçament ha de caure a ~0; si dobla, el signe és l'altre)."""
from comu42 import *
FRAMES = ('DSC06993', 'DSC06996', 'DSC06999')


def main():
    run = comu.Run.obre(str(RUNS['sony'])); ctx = f2.Ctx(run); ca, sa, k = float(ctx.ca), float(ctx.sa), float(ctx.k)
    M = np.asarray(COMMON_TO_FINAL, float)[:2, :2]; Rm = np.array([[ca, sa], [-sa, ca]]); Minv = np.linalg.inv(M); corr = {}; rep = {}
    for f in FRAMES:
        e = json.loads((REB42 / f'E2_AB_{f}.json').read_text()); s = np.array(e['mitjana_AB'], float)   # A→B_fotograma al llenç: cal moure B per −s
        eps = k * Rm @ Minv @ (-s) * -1.0   # Δx_llenç = −M·Rmᵀ·ε/k  ⇒  ε = −k·Rm·M⁻¹·Δx ; volem Δx = −s ⇒ ε = k·Rm·M⁻¹·s
        eps = k * Rm @ Minv @ s
        corr[f + '.ARW'] = [float(eps[0]), float(eps[1])]; rep[f] = dict(desplacament_llenc_px=s.tolist(), n=e['n'], correccio_sensor_px=corr[f + '.ARW'])
        log(f'{f}: A→B ({s[0]:+.2f}, {s[1]:+.2f}) px al llenç → correcció de sol ({eps[0]:+.2f}, {eps[1]:+.2f}) px de sensor')
    (CAU42 / 'correccions_B.json').write_text(json.dumps(corr, indent=1)); savejson(REB42 / 'B2c_correccions.json', dict(ca=ca, sa=sa, k=k, M=M.tolist(), correccions=rep)); log('B2c fet')


if __name__ == '__main__':
    main()
