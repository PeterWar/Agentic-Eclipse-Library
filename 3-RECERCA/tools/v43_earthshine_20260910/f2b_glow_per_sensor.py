"""F2b (V43) · El GLOW dins del limbe, per sensor: perfil radial G (mediana azimutal) de 0,90 a 1,06 R apilant NOMÉS Vixen o NOMÉS Sony-A (mateixos pesos de la F2, finestra
d'instant T0 ± τ), normalitzat a la corona a 1,02 R. Diu quin tren escampa més llum dins del disc (i quant), per decidir si al limbe hi ha de manar un sol tren."""
from comu43 import *
MC = (CX + 14.8, CY + 0.9); WIN = 700; RL = 453.5; T0 = 15.0; TAU = 10.0


def main():
    x0, y0 = int(round(MC[0])) - WIN, int(round(MC[1])) - WIN; yy, xx = np.mgrid[0:2 * WIN, 0:2 * WIN].astype(np.float32); cxt, cyt = MC[0] - x0, MC[1] - y0; r = np.hypot(xx - cxt, yy - cyt) / RL
    FR = json.loads((CAU43 / 'fotogrames_v43.json').read_text()); f1 = json.loads((ROOT / 'output/v42_20260910/4-rebuts/F1_earthshine.json').read_text()); gain = np.array(f1['guany_vixen_sobre_sony']['DSC06987'], np.float32)
    bins = np.arange(0.90, 1.061, 0.005); out = {}
    for sel, nom in ((lambda f: f['tren'] == 'vixen', 'vixen'), (lambda f: f['grup'] == 'sony_A', 'sony_A'), (lambda f: f['grup'] != 'sony_B', 'tots (A+Vixen)')):
        num = np.zeros((2 * WIN, 2 * WIN), np.float64); den = np.zeros_like(num); n = 0; noms = []
        for fr in FR:
            if not sel(fr): continue
            wt = np.exp(-((fr['t'] - T0) / TAU) ** 2)
            if wt < 0.05: continue
            stem = fr['nom'].split('.')[0]; a = np.load(CAU43 / f"lluna_{fr['tren']}_{stem}_v43.npy")[..., 1]; p = np.load(CAU43 / f"lluna_{fr['tren']}_{stem}_v43_pes.npy"); ok = np.isfinite(a) & (p > 0)
            g = gain[1] if fr['tren'] == 'sony' else 1.0; w = np.where(ok, p / max(float(p.max()), 1e-9), 0) * fr['exp'] * wt; num += np.nan_to_num(a) * g * w; den += w; n += 1; noms.append(f"{stem} ({fr['exp']:g} s, t {fr['t']:.0f})")
        G = np.where(den > 0, num / np.maximum(den, 1e-12), np.nan); prof = [float(np.nanmedian(G[(r >= b) & (r < b + 0.005)])) for b in bins]; c102 = float(np.nanmedian(G[(r >= 1.015) & (r < 1.025)])); c05 = float(np.nanmedian(G[(r >= 0.45) & (r < 0.55)]))
        out[nom] = {'n_fotogrames': n, 'fotogrames': noms, 'perfil_r': [float(b + 0.0025) for b in bins], 'perfil_G': prof, 'G_1.02R': c102, 'G_0.5R': c05, 'glow_relatiu': {f'{b + 0.0025:.3f}': (pv - c05) / c102 for b, pv in zip(bins, prof)}}
        log(f"{nom}: {n} fotogrames a T0±τ · G 0,5 R {c05:.0f} · 1,02 R {c102:.0f} · glow (G − interior)/corona: 0,95 R {(prof[10] - c05) / c102 * 100:.2f} % · 0,975 R {(prof[15] - c05) / c102 * 100:.2f} % · 0,99 R {(prof[18] - c05) / c102 * 100:.2f} % · 0,995 R {(prof[19] - c05) / c102 * 100:.2f} % · 1,005 R {prof[21] / c102 * 100:.0f} %")
        log('   ' + ', '.join(noms))
    savejson(REB43 / 'F2b_glow_per_sensor.json', out)


if __name__ == '__main__':
    main()
