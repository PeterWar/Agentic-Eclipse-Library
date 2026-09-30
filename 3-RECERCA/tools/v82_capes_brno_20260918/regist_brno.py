"""Registre de les 4 imatges publicades de Brno (Druckmüller, Habbal, Široký; 12-08-2026, Pico Trigaza)
al llenç del projecte Photoshop (V81.psb, 10551×7506).

Punt de partida (cadena declarada, sense cap píxel ajustat encara):
  Brno (píxels del PNG) → llenç de l'auditoria del 27-08 (F1.2: Sol al centre, nord amunt, R☉ 440,603 px)
  amb el registre fi `registre2.json` (research/114) → llenç V23/Photoshop amb la matriu `M_llenc_a_v23`
  (geometria_v27.json: gir 46,587°, escala 1).
Després es refina contra la capa base de V81 (00 Base corba) amb correlació d'estructura per anells
(mediana i MAD azimutals fora; banda d'harmònics m 13–80 com al 114), s'escombra el gir sencer (−180…180°)
per no repetir l'error dels 138,5° de la V25/V26, i es fa un CONTROL: l'optimitzador ha de tornar al mateix
òptim des d'un punt de partida desplaçat conegut.

Convenció d'angles: marc d'imatge (x a la dreta, y avall); R(a) = [[cos,−sin],[sin,cos]] porta l'angle φ a φ+a
(a pantalla, a>0 gira en sentit HORARI). `mostreja(..., ang0=gir)` del 114 mostreja Brno a l'angle θ+gir on el
nostre llenç és a θ ⇒ Brno → nostre és R(−gir).
"""
import json, sys, time, numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
from scipy.optimize import minimize

ROOT = '/Users/USUARI/Desktop/Eclipse 2026'
S = '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/49e1d801-8306-4d45-9cae-a03da6b42a8d/scratchpad'
BRNO = ROOT + '/3-RECERCA/druckmuller_fotos_finals'
GEO = json.load(open(ROOT + '/3-RECERCA/tools/estudi_druckmuller/geometria.json'))
REG = json.load(open(ROOT + '/3-RECERCA/tools/auditoria_estructura/registre2.json'))
G27 = json.load(open(ROOT + '/3-RECERCA/tools/v25_lineal/cau_v25/geometria_v27.json'))
M = np.asarray(G27['M_llenc_a_v23'], np.float64)              # 2×3, llenç auditoria → llenç V23
RS_AUD = 440.60304883027544                                    # R☉ px del llenç F1.2 (tots els runs)
SUN_AUD = np.array([8096 / 2.0, 8960 / 2.0])
SUN_V = M @ np.array([SUN_AUD[0], SUN_AUD[1], 1.0])           # Sol al llenç V (5361,79, 3775,04)
ESC_M = float(np.hypot(M[0, 0], M[1, 0]))                      # 1,0
RS_V = RS_AUD * ESC_M
ALPHA_M = float(np.arctan2(M[1, 0], M[0, 0]))                  # +46,587° (sentit estàndard del marc d'imatge)
NTH = 2880
RMAX = {'TSE2026_Trigaza_800mm.png': 3.0, 'TSE_2026_530mm_DHS.png': 4.2,
        'TSE_2026_400mm_DHS.png': 5.5, 'TSE_2026_200mm_DHS.png': 7.5}
BANDES = {'baixa': (3, 12), 'jutge114': (13, 80), 'fina': (30, 200)}
PERTORBA = np.array([8.0, -5.0, np.log(1.03), np.deg2rad(1.2)])   # control: punt de partida desplaçat

def R(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s], [s, c]])

def carrega_brno(nom):
    g = GEO[nom]; f0, f1, c0, c1 = g['marc']
    im = np.asarray(Image.open(f'{BRNO}/{nom}').convert('RGB'), np.float32) / 255.0
    lum = (im[..., 0] + 2 * im[..., 1] + im[..., 2]) / 4.0
    valid = np.zeros(lum.shape, bool); valid[f0:f1, c0:c1] = True
    # peu de foto: files planes al capdavall del contingut (com carrega_brno del 114)
    sd = lum[f0:f1, c0:c1].std(axis=1); pla = sd < 0.02 * sd.max(); tall = f1 - f0
    while tall > 0 and pla[tall - 1]: tall -= 1
    valid[f0 + tall:f1, c0:c1] = False
    # disc lunar pintat (centre en coordenades del retall) + guarda
    yy, xx = np.mgrid[0:lum.shape[0], 0:lum.shape[1]]
    valid &= np.hypot(xx - (g['cx'] + c0), yy - (g['cy'] + f0)) > g['R_lluna_px'] + 4
    lum = np.where(valid, lum, np.nan).astype(np.float32)
    r = REG[nom]; csun = np.array([r['cx'] + c0, r['cy'] + f0])   # Sol al PNG sencer
    return lum, csun, r['R_sol_px'], np.deg2rad(r['gir_deg']), (f1 - f0 - tall)

def anells(rmax, n=None):
    n = n or int(round(np.log(rmax / 1.15) / np.log(1.02)))
    return np.exp(np.linspace(np.log(1.15), np.log(rmax), n))

def mostreja(img, pts_x, pts_y):
    v = map_coordinates(img, [pts_y, pts_x], order=1, mode='constant', cval=np.nan)
    return v

def estructura(p):
    """Per anell: fora la mediana azimutal, dividit per la MAD; NaN → 0."""
    med = np.nanmedian(p, axis=1, keepdims=True); mad = np.nanmedian(np.abs(p - med), axis=1, keepdims=True)
    e = (p - med) / np.maximum(mad, 1e-9)
    return np.where(np.isfinite(e), e, 0.0)

def banda(e, lo, hi):
    F = np.fft.rfft(e, axis=1); m = np.arange(F.shape[1]); F[:, (m < lo) | (m > hi)] = 0
    return np.fft.irfft(F, n=e.shape[1], axis=1)

def corr_anells(a, b, ok, minfrac=0.6):
    out = []
    for i in range(a.shape[0]):
        m = ok[i]
        if m.mean() < minfrac: continue
        x, y = a[i][m], b[i][m]; x = x - x.mean(); y = y - y.mean()
        d = np.sqrt((x * x).sum() * (y * y).sum())
        if d > 0: out.append((x * y).sum() / d)
    return float(np.mean(out)) if out else np.nan, len(out)

class Registre:
    def __init__(self, nom, target):
        self.nom = nom; self.lum, self.csun, self.Rb, self.gir, self.peu = carrega_brno(nom)
        self.s0 = RS_V / self.Rb; self.a0 = ALPHA_M - self.gir
        self.radis = anells(RMAX[nom]); th = np.linspace(0, 2 * np.pi, NTH, endpoint=False)
        rr = self.radis[:, None] * RS_V
        self.PX = SUN_V[0] + rr * np.cos(th)[None, :]; self.PY = SUN_V[1] + rr * np.sin(th)[None, :]
        pv = mostreja(target, self.PX.ravel(), self.PY.ravel()).reshape(self.PX.shape)
        self.ok_v = np.isfinite(pv); self.ev = estructura(pv); self.cache = {}
    def brno_polar(self, p):
        dx, dy, lnk, dth = p; s = self.s0 * np.exp(lnk); a = self.a0 + dth
        X = self.PX - SUN_V[0] - dx; Y = self.PY - SUN_V[1] - dy
        Ri = R(-a) / s; bx = self.csun[0] + Ri[0, 0] * X + Ri[0, 1] * Y; by = self.csun[1] + Ri[1, 0] * X + Ri[1, 1] * Y
        pb = mostreja(self.lum, bx.ravel(), by.ravel()).reshape(X.shape)
        return pb
    def corr(self, p, b='jutge114'):
        pb = self.brno_polar(p); ok = self.ok_v & np.isfinite(pb); lo, hi = BANDES[b]
        key = b
        if key not in self.cache: self.cache[key] = banda(self.ev, lo, hi)
        return corr_anells(self.cache[key], banda(estructura(pb), lo, hi), ok)
    def cost(self, p, b='jutge114'):
        c, n = self.corr(p, b); return -c if np.isfinite(c) else 1.0
    def optimitza(self, p0, b='jutge114'):
        pas = np.array([3.0, 3.0, 0.01, np.deg2rad(0.3)])
        sim = np.vstack([p0] + [p0 + np.eye(4)[k] * pas[k] for k in range(4)])
        r = minimize(self.cost, p0, args=(b,), method='Nelder-Mead',
                     options=dict(initial_simplex=sim, xatol=1e-4, fatol=1e-7, maxiter=4000, maxfev=4000))
        return r.x, -r.fun
    def afi(self, p):
        """Matriu 2×3 PNG → llenç V (x' = A·[x,y,1])."""
        dx, dy, lnk, dth = p; s = self.s0 * np.exp(lnk); A = s * R(self.a0 + dth)
        t = SUN_V + np.array([dx, dy]) - A @ self.csun
        return np.hstack([A, t[:, None]]), s, self.a0 + dth

def fmt(p): return f'dx {p[0]:+.2f} dy {p[1]:+.2f} escala ×{np.exp(p[2]):.4f} gir {np.rad2deg(p[3]):+.3f}°'

if __name__ == '__main__':
    t0 = time.time(); target = np.load(S + '/v81_base_lum.npy'); print('target', target.shape, f'SUN_V {SUN_V.round(2)} RS_V {RS_V:.3f} px  M: gir {np.rad2deg(ALPHA_M):.3f}° escala {ESC_M:.6f}')
    out = {}
    for nom in RMAX:
        t1 = time.time(); reg = Registre(nom, target); print(f'\n=== {nom}: R☉ Brno {reg.Rb:.2f} px → escala ×{reg.s0:.4f}; gir 114 {np.rad2deg(reg.gir):+.3f}° ⇒ gir total {np.rad2deg(reg.a0):.3f}°; peu {reg.peu} files; anells {len(reg.radis)} fins a {RMAX[nom]} R☉')
        # 1) escombrada de gir sencera (banda baixa) des de la cadena declarada
        sc = [(d, reg.corr(np.array([0, 0, 0, np.deg2rad(d)]), 'baixa')[0]) for d in range(-180, 180, 2)]
        sc.sort(key=lambda t: -t[1]); print('  escombrada gir (m 3–12): millors', [(d, round(c, 3)) for d, c in sc[:4]], '| a 0°:', round(dict(sc)[0], 3))
        # 2) escombrada fina ±4°
        sf = [(d, reg.corr(np.array([0, 0, 0, np.deg2rad(d)]))[0]) for d in np.arange(-4, 4.01, 0.25)]
        best = max(sf, key=lambda t: t[1]); print(f'  escombrada fina (m 13–80): màxim a {best[0]:+.2f}° corr {best[1]:.3f}; a 0° {dict(sf)[0.0]:.3f}')
        p0 = np.array([0, 0, 0, np.deg2rad(best[0])]); c0 = {b: reg.corr(np.zeros(4), b) for b in BANDES}
        # 3) refinament (Nelder-Mead) i control
        p1, c1 = reg.optimitza(p0); p2, c2 = reg.optimitza(p1)          # segona passada des de l'òptim
        pc, cc = reg.optimitza(p2 + PERTORBA)                            # control: torna?
        d = pc - p2; tornada = dict(dx=float(d[0]), dy=float(d[1]), escala_pct=float(100 * (np.exp(d[2]) - 1)), gir_deg=float(np.rad2deg(d[3])))
        cf = {b: reg.corr(p2, b) for b in BANDES}
        A, s, a = reg.afi(p2)
        print(f'  cadena declarada: ' + ' '.join(f'{b} {c0[b][0]:.3f}({c0[b][1]})' for b in BANDES))
        print(f'  òptim: {fmt(p2)} → ' + ' '.join(f'{b} {cf[b][0]:.3f}' for b in BANDES) + f'  [{time.time()-t1:.0f}s]')
        print(f'  control (partida +8,−5 px, ×1,03, +1,2°): torna a {fmt(pc)} · diferència {tornada}')
        out[nom] = dict(R_sol_brno_px=reg.Rb, gir_114_deg=float(np.rad2deg(reg.gir)), peu_files=int(reg.peu),
                        cadena=dict(escala=reg.s0, gir_deg=float(np.rad2deg(reg.a0)), sol_v=SUN_V.tolist(), corr={b: c0[b][0] for b in BANDES}),
                        escombrada_gir_millors=[(int(d), float(c)) for d, c in sc[:4]], escombrada_gir_a0=float(dict(sc)[0]),
                        optim=dict(dx=float(p2[0]), dy=float(p2[1]), escala=float(s), escala_rel=float(np.exp(p2[2])), gir_deg=float(np.rad2deg(a)), dgir_deg=float(np.rad2deg(p2[3])),
                                   sol_v=(SUN_V + p2[:2]).tolist(), corr={b: cf[b][0] for b in BANDES}, anells_usats={b: cf[b][1] for b in BANDES}, A_png_a_v=A.tolist()),
                        control=dict(partida=PERTORBA.tolist(), tornada=tornada, corr=float(cc)),
                        csun_png=reg.csun.tolist(), radis=[float(reg.radis[0]), float(reg.radis[-1])], NTH=NTH)
    json.dump(dict(SUN_V=SUN_V.tolist(), RS_V=RS_V, ALPHA_M_deg=float(np.rad2deg(ALPHA_M)), imatges=out, quan=time.strftime('%Y-%m-%dT%H:%M:%S')),
              open(S + '/registre_v82.json', 'w'), indent=1, ensure_ascii=False)
    print(f'\nescrit registre_v82.json ({time.time()-t0:.0f}s)')
