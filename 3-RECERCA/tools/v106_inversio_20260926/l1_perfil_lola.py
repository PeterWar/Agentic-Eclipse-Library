"""l1 (V106, Claude, 26-09-2026) · Perfil del limbe lunar a partir de l'altimetria LOLA (LDEM_16, NASA PDS) per a una geometria d'observació.
Entrada: longitud i latitud selenogràfiques del punt sub-observador (λ0, β0, graus; Horizons «ObsSub-LON/LAT»), angle de posició del pol nord
lunar (P, graus des del nord celeste cap a l'est; Horizons «NP.ang») i distància observador–Lluna (km).
Mètode: cada punt de la malla LOLA (radi 1737,4 km + h) es projecta en perspectiva sobre el pla del cel; per a cada calaix d'angle de posició
(celeste) el limbe és el radi angular MÀXIM de tots els punts (l'envolupant = la silueta). Només es fan servir els punts a 60–120° del
punt sub-observador (la resta no pot fer silueta).
Sortida: npz amb pa (graus, celeste), rho (segons d'arc) i h_km (radi del limbe − 1737,4 km, equivalent al pla del cel).
Ús: l1_perfil_lola.py <lon0> <lat0> <P> <dist_km> <sortida.npz> [pas_graus=0.05]"""
import sys, numpy as np
from pathlib import Path
R0 = Path(__file__).resolve().parents[3]
import os
RESN = int(os.environ.get('V106_LDEM', '16')); IMG = R0 / f'4-RESULTATS/v106_inversio_20260926/lola/ldem_{RESN}.img'
lon0, lat0, P, dist = map(float, sys.argv[1:5]); OUT = Path(sys.argv[5]); PAS = float(sys.argv[6]) if len(sys.argv) > 6 else 0.05
NL, NS, RES, RREF = 180 * RESN, 360 * RESN, float(RESN), 1737.4
dem = np.memmap(IMG, dtype='<i2', mode='r', shape=(NL, NS))                                     # ×0,5 m: alçada sobre 1737,4 km
lat = 90.0 - (np.arange(NL) + 0.5) / RES; lon = (np.arange(NS) + 0.5) / RES          # graus; longitud est 0–360
s = np.array([np.cos(np.radians(lat0)) * np.cos(np.radians(lon0)), np.cos(np.radians(lat0)) * np.sin(np.radians(lon0)), np.sin(np.radians(lat0))])
z = np.array([0.0, 0.0, 1.0]); n = z - z.dot(s) * s; n /= np.linalg.norm(n)       # pol nord lunar projectat al cel
e = np.cross(n, s)                                                                    # «est lunar» al cel (vegeu el signe a sota)
nb = int(round(360 / PAS)); rho = np.full(nb, -np.inf)
clat = np.cos(np.radians(lat)); slat = np.sin(np.radians(lat))
for i0 in range(0, NL, 120):
    i1 = min(NL, i0 + 120); r = RREF + np.asarray(dem[i0:i1], np.float32) * 0.0005
    X = r * (clat[i0:i1, None] * np.cos(np.radians(lon))[None, :]); Y = r * (clat[i0:i1, None] * np.sin(np.radians(lon))[None, :]); Z = r * slat[i0:i1, None]
    ps = X * s[0] + Y * s[1] + Z * s[2]; cosang = ps / r
    m = np.abs(cosang) < 0.13                                                         # a menys de ~7,5° del limbe (una muntanya de 10 km no pot fer silueta més enllà de 6°)
    if not m.any(): continue
    px = X[m] - ps[m] * s[0]; py = Y[m] - ps[m] * s[1]; pz = Z[m] - ps[m] * s[2]
    un = px * n[0] + py * n[1] + pz * n[2]; ue = px * e[0] + py * e[1] + pz * e[2]
    ang = np.hypot(un, ue) / (dist - ps[m])                                           # radi angular (radiants), perspectiva
    phi = np.degrees(np.arctan2(ue, un))                                              # des del pol lunar projectat, cap a l'est LUNAR
    pa = (P - phi) % 360.0                                                            # l'est lunar cau a l'oest del cel: PA = P − φ (φ = 90° → PA = P − 90°)
    k = np.floor(pa / PAS).astype(int) % nb
    np.maximum.at(rho, k, ang)
rho = np.degrees(rho) * 3600.0
ok = np.isfinite(rho)
if not ok.all():
    idx = np.arange(nb); rho = np.interp(idx, idx[ok], rho[ok], period=nb)
pa_c = (np.arange(nb) + 0.5) * PAS
# radi equivalent en km al pla del cel (a la distància del centre)
h_km = np.radians(rho / 3600.0) * dist - RREF
np.savez_compressed(OUT, pa=pa_c, rho_arcsec=rho, h_km=h_km, lon0=lon0, lat0=lat0, P=P, dist_km=dist, font=str(IMG.relative_to(R0)))
print(f'perfil: {nb} calaixos · radi mitjà {rho.mean():.2f}″ · relleu h: p1 {np.percentile(h_km, 1):+.2f} km, p99 {np.percentile(h_km, 99):+.2f} km, rms {h_km.std():.2f} km')
