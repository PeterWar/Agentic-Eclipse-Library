"""e1 · Massa d'aire i factor E al marc de la FINAL (7933 × 5021), amb la geometria pròpia de la final (GEOMETRIA_FINAL.json).

- Graella exacta d'astropy cada 64 px (la mateixa recepta que msb_comu: altura aparent, refracció de zp.py, Kasten–Young),
  a la meitat de la totalitat (DATE-OBS 18:29:34 UT).
- Proves:
  (a) la mateixa graella feta al llenç V42 (msb_comu, massa_aire_graella.npz) i portada a la final amb el retall OFF ha de
      donar la mateixa X (dues geometries escrites per separat);
  (b) PA del zenit (escaneig de 0,05°) a 1 i 4 R☉, i direcció a la imatge; ha de coincidir amb la del gradient de X;
  (c) E = 1 al centre del Sol de la final;
  (d) X i E a ±1,5, ±2 i ±4 R☉ al llarg de l'eix del zenit (les xifres del LLEGEIX-ME).
Escriu resultats/extincio_diferencial_20261012/massa_aire_graella_final.npz i E1_MASSA_AIRE_FINAL.json."""
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ed_comu as ed            # noqa: E402

mc = ed.mc
T0 = time.time()
ed.RES.mkdir(parents=True, exist_ok=True)
g = ed.geo_final()
g42 = mc.geo_llenc()
PAS = 64
files = np.unique(np.r_[np.arange(0, ed.HF, PAS), ed.HF - 1]).astype(np.float64)
cols = np.unique(np.r_[np.arange(0, ed.WF, PAS), ed.WF - 1]).astype(np.float64)
yy, xx = np.meshgrid(files, cols, indexing='ij')
alt = ed.altures(g, xx.ravel(), yy.ravel()).reshape(yy.shape)
h_sol = float(ed.altures(g, np.array([g.cx]), np.array([g.cy]))[0])
np.savez(ed.GRAELLA_FINAL, files=files, cols=cols, alt=alt, h_sol=h_sol, pas=PAS, data=mc.DATE_OBS, refractat=True,
         geometria=ed.rel(ed.GEOF))
sp = ed.Spline(ed.GRAELLA_FINAL)
X_sol = sp.X_sol
print(f'graella {alt.shape}, h☉ {h_sol:.4f}°, X☉ {X_sol:.4f} ({time.time() - T0:.0f} s)', flush=True)

# (a) contra la graella del llenç V42 (msb_comu) portada amb el retall
sp42 = ed.Spline(ed.GRAELLA_V42)
rng = np.random.default_rng(12)
px = rng.uniform(0, ed.WF - 1, 4000); py = rng.uniform(0, ed.HF - 1, 4000)
Xf = sp.X_punts(px, py)
X42 = sp42.X_punts(px + mc.OFF[0], py + mc.OFF[1])
dX = Xf - X42
# exacte d'astropy en 200 punts (prova de la spline)
k = rng.choice(len(px), 200, replace=False)
Xexacte = mc.kasten_young(ed.altures(g, px[k], py[k]))
err_spline = float(np.max(np.abs(Xexacte - Xf[k])))

# (b) zenit
pa_scan = np.arange(0.0, 360.0, 0.05)
zen = {}
for rr in (1.0, 4.0):
    xs, ys = g.px(np.full_like(pa_scan, rr), pa_scan)
    a = ed.altures(g, xs, ys)
    zen[f'r{rr:g}'] = float(pa_scan[int(np.argmax(a))])
PAZ = zen['r1']
x1, y1 = g.px(1.0, PAZ)
vz = np.array([x1 - g.cx, y1 - g.cy]); vz /= np.linalg.norm(vz)
# gradient de X al voltant del Sol (diferències centrades a ±1 R☉): −∇X apunta al zenit
d = g.R
gx = (sp.X_punts(g.cx + d, g.cy) - sp.X_punts(g.cx - d, g.cy)) / (2 * d)
gy = (sp.X_punts(g.cx, g.cy + d) - sp.X_punts(g.cx, g.cy - d)) / (2 * d)
vg = -np.array([float(np.ravel(gx)[0]), float(np.ravel(gy)[0])]); vg /= np.linalg.norm(vg)
ang_grad_zenit = math.degrees(math.acos(float(np.clip(vz @ vg, -1, 1))))
ang_vertical = math.degrees(math.atan2(vz[0], -vz[1]))          # + = a la dreta de la vertical cap amunt
# el mateix al llenç V42 (geometria de msb_comu)
x1b, y1b = g42.px(1.0, PAZ)
vz42 = np.array([x1b - g42.cx, y1b - g42.cy]); vz42 /= np.linalg.norm(vz42)

# (c) E al centre del Sol i a la Lluna
E_sol = float(np.ravel(ed.factor_E(sp.X_punts(g.cx, g.cy), X_sol))[0])
E_lluna = float(np.ravel(ed.factor_E(sp.X_punts(*ed.LLUNA_F), X_sol))[0])

# (d) eix del zenit
eix = []
for rr in (1.0, 1.5, 2.0, 3.0, 4.0, 5.0):
    fila = dict(r_Rsol=rr)
    for nom, pa0 in (('zenit', PAZ), ('horitzo', (PAZ + 180.0) % 360)):
        xs, ys = g.px(rr, pa0)
        Xp = float(mc.kasten_young(ed.altures(g, np.array([xs]), np.array([ys]))[0]))
        E = float(ed.factor_E(Xp, X_sol))
        fila[nom] = dict(x=float(xs), y=float(ys), X=Xp, E=E, E_menys_1_pc=100 * (E - 1),
                         llum_rebuda_respecte_del_Sol_pc=100 * (1 / E - 1))
    eix.append(fila)
    print(f"r {rr:3.1f}: zenit X {fila['zenit']['X']:.3f} E {fila['zenit']['E']:.3f} | horitzó X {fila['horitzo']['X']:.3f} "
          f"E {fila['horitzo']['E']:.3f}", flush=True)

out = dict(
    guio=ed.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
    geometria=dict(fitxer=ed.rel(ed.GEOF), centre_sol=[g.cx, g.cy], R_sol_px=g.R, nord_solar=g.n.tolist(), est_solar=g.e.tolist(),
                   angle_nord_est_deg=math.degrees(math.acos(float(np.clip(g.n @ g.e, -1, 1)))),
                   lluna=list(ed.LLUNA_F), R_lluna_px=ed.R_LLUNA_F),
    recepta=dict(instant=mc.DATE_OBS, lloc=mc.LLOC, refraccio=mc.REFRACCIO, model='Kasten–Young (altura aparent)',
                 k=ed.K, E='10^(0,4·k·(X − X☉))', P_deg=mc.P_DEG, R_sol_arcsec=mc.RSOL_ARCSEC, pas_graella_px=PAS),
    h_sol_deg=h_sol, X_sol=X_sol,
    prova_a_contra_llenc_V42=dict(n=len(px), max_abs_dX=float(np.max(np.abs(dX))), mediana_dX=float(np.median(dX)),
                                  X_sol_V42=sp42.X_sol, h_sol_V42=sp42.h_sol, OFF=mc.OFF.tolist(),
                                  passa=bool(np.max(np.abs(dX)) < 5e-3),
                                  max_abs_dE=float(np.max(np.abs(10 ** (0.4 * ed.K * dX) - 1))),
                                  gir_entre_geometries_deg=math.degrees(math.atan2(g.n[1], g.n[0]) - math.atan2(g42.n[1], g42.n[0])),
                                  escala_R_final_sobre_V42=g.R / g42.R,
                                  lectura=('Les dues geometries (GEOMETRIA_FINAL.json i msb_comu) s\'escriuen per separat: difereixen '
                                           '0,13° de gir (N i E de la final passen per la semblança de les estrelles) i 0,08 % d\'escala '
                                           '(2,15201 contra 2,15035 ″/px). Al centre del Sol coincideixen exactament; la diferència creix '
                                           'cap a les cantonades (r ≈ 10,7 R☉). Efecte en E: el que diu max_abs_dE.')),
    prova_spline=dict(n=200, max_abs_err_X=err_spline, passa=err_spline < 1e-4),
    zenit=dict(PA_solar_deg=zen, vector_imatge_xfila=vz.tolist(), graus_a_la_dreta_de_la_vertical=ang_vertical,
               vector_gradient_X=vg.tolist(), angle_gradient_vs_zenit_deg=ang_grad_zenit,
               vector_imatge_llenc_V42=vz42.tolist(),
               angle_final_vs_V42_deg=math.degrees(math.acos(float(np.clip(vz @ vz42, -1, 1)))),
               passa=bool(ang_grad_zenit < 1.0 and abs(zen['r1'] - zen['r4']) < 0.5)),
    E_centre_sol=E_sol, E_centre_lluna=E_lluna,
    eix_zenit=eix, segons=round(time.time() - T0, 1))
ed.json_dump(out, ed.RES / 'E1_MASSA_AIRE_FINAL.json')
print(f"a) |dX| màx {out['prova_a_contra_llenc_V42']['max_abs_dX']:.2e}; spline {err_spline:.1e}; zenit PA {zen} "
      f"({ang_vertical:+.2f}° de la vertical), gradient a {ang_grad_zenit:.2f}°; E☉ {E_sol:.6f}; E lluna {E_lluna:.4f}")
print(f'fet ({time.time() - T0:.0f} s)')
