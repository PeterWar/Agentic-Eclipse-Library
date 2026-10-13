"""c11 · Capes del mosaic final + LASCO C2 per a l'APOD (a partir del M1 de c5, mateix to i mateix color).
Canvis respecte del M1:
  1. el sector del braç de l'ocultador (PA 290–352°) ja no es posa en negre: el vinyetatge oficial del C2 (c2vig_final, SolarSoft)
     ja en corregeix l'ombra; a 3,5–5,5 R☉ el perfil d'angle corregit passa pel sector sense graó (vistes/apod_lasco/perfil_pa_c2.png);
  2. les taques fosques del detector (puntets negres, 2–5 px, ja a la dada crua de nivell 0,5) es substitueixen per la mediana local
     de la mateixa imatge; les brillants (estrelles i raigs còsmics) es deixen;
  3. 300 px per R☉ (3960 px, ±6,6 R☉) i sense rètols: els rètols van a una capa a part (c12).
La final no es gira ni es retoca: és el JPG sRGB enviat a l'APOD el 30-09, només reduït. Desa les capes (PNG RGBA) a apod_lasco/capes."""
import sys, json, os
import numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *
from lasco_vista import VistaLasco
Image.MAX_IMAGE_PIXELS = None
SRGB = ARREL / 'publicacions/APOD/enviament_20260930/Eclipse_2026-08-12_Pere_Guerra_Serra.jpg'
OUT = RES / 'apod_lasco'; CAP = OUT / 'capes'; CAP.mkdir(parents=True, exist_ok=True)
RPX = 300.0; S = 3960; RT = 3.5            # px per R☉, costat, radi de la costura (R☉)
C2COL = np.array([1.0, 0.60, 0.28])        # el mateix taronja del M1
PIL2 = (290.0, 352.0)                      # sector del braç (només per a la capa «abans»)

# ------------------------------------------------ taques fosques del detector (a la imatge nativa, ja amb vinyetatge)
TAQUES = {}
def repara_taques(d, g, k=7.0, mida_max=60):
    yy, xx = np.mgrid[0:d.shape[0], 0:d.shape[1]].astype(np.float64); r, pa = g.polar(xx, yy)
    zona = (r > 2.0) & (r < 6.6) & (d > 0)
    l = np.log10(np.clip(d, 1e-3, None)); m = nd.median_filter(l, 11); res = l - m
    rb = np.clip((r / 0.25).astype(int), 0, 40); sig = np.full(41, np.nan)
    for i in range(41):
        v = res[zona & (rb == i)]
        if v.size > 50: sig[i] = 1.4826 * np.median(np.abs(v))
    sig = np.where(np.isfinite(sig), sig, np.nanmax(sig))
    flag = zona & (res < -k * sig[rb])
    lab, n = nd.label(flag); mides = nd.sum(flag, lab, range(1, n + 1))
    flag = np.isin(lab, 1 + np.nonzero(mides <= mida_max)[0])
    flag = nd.binary_dilation(flag, iterations=1) & zona
    lab, n = nd.label(flag)
    cs = nd.center_of_mass(flag, lab, range(1, n + 1))
    TAQUES.update(n=int(n), px=int(flag.sum()), k_sigma=k, finestra_mediana=11,
                  llista=[dict(x=round(c[1], 1), y=round(c[0], 1), r=round(float(r[int(c[0]), int(c[1])]), 2),
                               pa=round(float(pa[int(c[0]), int(c[1])]), 1)) for c in cs])
    out = d.copy(); out[flag] = (10 ** m[flag]).astype(out.dtype)
    TAQUES['_mask'] = flag
    return out

gF = geo_final('efemeride')
fin = Image.open(SRGB); ICC = fin.info.get('icc_profile'); fin = fin.convert('RGB'); W, H = fin.size
gO = Geo('apod', S / 2 - 0.5, S / 2 - 0.5, RPX, gF.n, gF.e, '', '')
yy, xx = np.mgrid[0:S, 0:S].astype(np.float64); rO, paO = gO.polar(xx, yy)

# ------------------------------------------------ eclipsi: la final reduïda (sense gir), al marc del mosaic
f = gF.R / RPX
fa = np.asarray(fin.resize((round(W / f), round(H / f)), Image.LANCZOS)).astype(np.float32) / 255
gFf = Geo('f', (gF.cx + 0.5) / f - 0.5, (gF.cy + 0.5) / f - 0.5, gF.R / f, gF.n, gF.e, '', '')
fx, fy = gFf.px(rO, paO)
finO = np.dstack([nd.map_coordinates(fa[..., c], [fy, fx], order=1, mode='constant', cval=np.nan) for c in range(3)])
dins = np.isfinite(finO[..., 0])
rpx = rO * RPX
a_disc = np.clip(RT * RPX - rpx + 0.5, 0, 1) * dins           # vora antialiàsing d'1 px

# ------------------------------------------------ LASCO C2: vista nova (taques reparades) i la del M1 (per a la capa «abans»)
# pilar=(999, 999): el sector del braç entra a l'ajust d'harmònics com qualsevol altre angle (la dada ja està corregida de vinyetatge).
# Amb el sector exclòs de l'ajust, el model l'interpolava des dels veïns i el sector quedava −0,6 a −1,7 σ (falca fosca artificial).
v_nou = VistaLasco('24038985.fts', 2.25, 6.4, mmax=3, suau_r=1.0, prepara=repara_taques, pilar=(999.0, 999.0))
v_vell = VistaLasco('24038985.fts', 2.25, 6.4, mmax=3, suau_r=1.0)
def tono(z): t = np.clip((z + 0.8) / 4.6, 0, 1) ** 1.15; return t      # lo −0,8, hi 3,8, γ 1,15 (com el M1)
z_nou = v_nou.mostra(rO, paO); z_vell = v_vell.mostra(rO, paO)
z_vell[(paO >= PIL2[0]) & (paO <= PIL2[1])] = np.nan
RMAX = 6.2   # R☉: el cercle del C2 toca les vores del CCD a 6,29 R☉ (centre a 506 px de la fila 0); més enllà, vora en serra
def capa_lasco(z, rmax=RMAX):
    ok = np.isfinite(z); t = np.where(ok, tono(np.nan_to_num(z)), 0)
    rgb = t[..., None] * C2COL; a = ok.astype(np.float32) * np.clip(rmax * RPX - rpx + 0.5, 0, 1)
    return np.dstack([rgb, a])

def desa(nom, rgba):
    im = Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA'); im.save(CAP / f'{nom}.png'); return im
L_nou = capa_lasco(z_nou); L_vell = capa_lasco(z_vell, rmax=6.4)
desa('2_lasco_c2', L_nou); desa('2b_lasco_c2_M1', L_vell)
E_disc = np.dstack([np.nan_to_num(finO), a_disc]); desa('3_eclipsi_disc', E_disc)
E_tot = np.dstack([np.nan_to_num(finO), dins.astype(np.float32)]); desa('3b_eclipsi_sencer', E_tot)

def sobre(base, capa):
    a = capa[..., 3:4]; return capa[..., :3] * a + base * (1 - a)
net = sobre(sobre(np.zeros((S, S, 3), np.float32), L_nou), E_disc)
m1 = sobre(sobre(np.zeros((S, S, 3), np.float32), L_vell), E_disc)
Image.fromarray((net * 255 + 0.5).astype(np.uint8)).save(OUT / 'net_3960.png')
Image.fromarray((m1 * 255 + 0.5).astype(np.uint8)).save(OUT / 'm1_mateix_marc_3960.png')

# ------------------------------------------------ comprovacions
# (a) el sector del braç, després del vinyetatge: perfil d'angle a 3,5–6 R☉ dins i fora del sector
zz = v_nou.Z; rr = 10 ** v_nou.lr; pa = v_nou.pa
sect = (pa >= PIL2[0]) & (pa <= PIL2[1]); veins = ((pa >= 260) & (pa < PIL2[0])) | ((pa > PIL2[1]) | (pa < 20))
comp = {}
for a, b in [(2.25, 2.8), (2.8, 3.5), (3.5, 4.5), (4.5, 5.5), (5.5, 6.3)]:
    k = (rr >= a) & (rr < b)
    comp[f'{a}-{b}'] = dict(mediana_sector_sigma=round(float(np.nanmedian(zz[k][:, sect])), 3),
                           mediana_veins_sigma=round(float(np.nanmedian(zz[k][:, veins])), 3),
                           mad_sector=round(float(1.4826 * np.nanmedian(np.abs(zz[k][:, sect] - np.nanmedian(zz[k][:, sect])))), 3),
                           mad_veins=round(float(1.4826 * np.nanmedian(np.abs(zz[k][:, veins] - np.nanmedian(zz[k][:, veins])))), 3))
# (b) nivells a banda i banda de la costura (sRGB 0–255)
def pct(m): return np.percentile(net[m] * 255, [5, 50, 95], axis=0).round(1).tolist()
cost = dict(eclipsi_3_3_a_3_45=pct((rO >= 3.3) & (rO < 3.45) & dins), lasco_3_55_a_3_7=pct((rO >= 3.55) & (rO < 3.7) & np.isfinite(z_nou)))
rebut_extra = dict(rmax_lasco_Rsol=RMAX, ajust_harmonics='tots els angles (pilar=None)')
mk = TAQUES.pop('_mask')
rebut = dict(script=Path(__file__).name, final_srgb=str(SRGB.relative_to(ARREL)), px_per_Rsol=RPX, costat=S, costura_Rsol=RT,
             lasco='24038985.fts (C2, 18:24:31 UT, nivell 0,5)', vista=dict(rmin=2.25, rmax=6.4, mmax=3, suau_r=1.0, lo=-0.8, hi=3.8, gamma=1.15,
             color=C2COL.tolist()), sector_braç_PA=PIL2, sector_braç_despres_vinyetatge=comp, taques_fosques=TAQUES, costura=cost,
             icc=bool(ICC), **rebut_extra)
json.dump(rebut, open(OUT / 'C11_CAPES.json', 'w'), indent=1, ensure_ascii=False)
if ICC: open(OUT / 'srgb.icc', 'wb').write(ICC)
print(json.dumps({k: rebut[k] for k in ('sector_braç_despres_vinyetatge', 'costura')}, indent=1, ensure_ascii=False))
print('taques', TAQUES['n'], 'px', TAQUES['px'])
