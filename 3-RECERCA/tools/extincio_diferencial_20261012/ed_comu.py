"""ed_comu · Mòdul comú de la comparació «extinció diferencial» (12-10-2026).

Encàrrec: un costat a costat perquè Pere decideixi si la imatge publicada s'ha de corregir de l'extinció diferencial.
Dos pisos, tots dos amb el llenç SENCER:
  pis 1 (física, el pis on neix el defecte): el compost lineal fusion_total_v42 (cau b3, NOMÉS LECTURA), sense i amb
        E(x, y) = 10^(0,4·k·(X(x, y) − X☉)) aplicat en llum lineal DESPRÉS de restar el pla del cel de la v2 (el cel és llum
        de l'atmosfera i no es corregeix);
  pis 2 (APROXIMACIÓ VISUAL): la imatge fusionada de la V125-FINAL.psb (psd-tools, NOMÉS LECTURA; mai el Photoshop),
        passada a Adobe RGB lineal, amb el seu cel estimat i intacte, la part de corona multiplicada per E (el mateix guany
        a R, G i B: el to no canvia) i tornada a codificar amb el mateix perfil.

Importar-lo no escriu res ni llegeix cap fitxer gros.
Rutes: respecte de 4-Photoshop (ARREL), com mana AGENTS.md. Cap intèrpret anomenat: el guió de crida el detecta."""
import hashlib
import io
import json
import math
import sys
from pathlib import Path

import numpy as np

ARREL = Path(__file__).resolve().parents[3]                       # …/4-Photoshop
EINES = Path(__file__).resolve().parent
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/msb_calibrat_20261011'))
import msb_comu as mc          # noqa: E402  (geometria del llenç V42, massa d'aire, matriu del color, cau)

SORT = ARREL / 'Sortides/extincio_diferencial_20261012'           # el que mira Pere
RES = ARREL / '3-RECERCA/resultats/extincio_diferencial_20261012'  # dades i proves
PSB = ARREL / '1-PHOTOSHOP/V125-FINAL.psb'
SHA_PSB_ESTAT = 'bfa9daeef208f61c55bc736e6a71e01754edb4cab5f8fe2f747ed23281645797'   # ESTAT.md (03-10)
GEOF = ARREL / '3-RECERCA/resultats/comparacio_sdo_lasco_20261001/GEOMETRIA_FINAL.json'
CEL_CANALS = ARREL / '3-RECERCA/resultats/msb_calibrat_20261011/v2/comparacions/banda/CEL_CANALS_v2.json'
GRAELLA_V42 = mc.MAPA / 'massa_aire_graella.npz'
GRAELLA_FINAL = RES / 'massa_aire_graella_final.npz'

K = 0.40                       # mag per massa d'aire (nota 78: 0,402 ± 0,036; msb_comu.K_EXT)
GAMMA = 563.0 / 256.0          # corba de to d'Adobe RGB (1998): potència pura 2,19921875 (rTRC = gTRC = bTRC del perfil)
HF, WF = 5021, 7933            # marc de la final (V121/V123/V125)

GEO = json.load(open(GEOF))
LLUNA_F = (float(GEO['lluna_px'][0]), float(GEO['lluna_px'][1]))   # la Lluna de C2 a la final (la de Pere)
R_LLUNA_F = float(GEO['R_lluna_px'])


def geo_final():
    """La geometria pròpia de la final (GEOMETRIA_FINAL.json, la de comparacio_sdo_lasco_20261001): centre del Sol per efemèride,
    R☉ en px i nord i est solars afins (90,43° entre ells)."""
    c = GEO['sol_px_efemeride']
    return mc.Geo(c[0], c[1], GEO['R_sol_px'], GEO['nord_solar'], GEO['est_solar'])


def sha256(ruta, bloc=1 << 24):
    h = hashlib.sha256()
    with open(ruta, 'rb') as fh:
        for b in iter(lambda: fh.read(bloc), b''):
            h.update(b)
    return h.hexdigest()


def rel(p):
    """Ruta respecte de 4-Photoshop (per als rebuts)."""
    try:
        return str(Path(p).resolve().relative_to(ARREL))
    except ValueError:
        return str(p)


def json_dump(obj, ruta):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, 'w') as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))


# ------------------------------------------------------------------------------------------------ massa d'aire i E
def altures(geo, x, y, data=mc.DATE_OBS, refractat=True):
    """Altura aparent (graus) de punts d'una imatge amb geometria solar `geo`, exacta amb astropy. Mateixa recepta que
    msb_comu.altures_astropy (gnòmica: separació = atan(r·tan R☉); PA celeste = PA solar + P; refracció de zp.py)."""
    import astropy.units as u
    from astropy.coordinates import AltAz, EarthLocation, get_body
    from astropy.time import Time
    loc = EarthLocation(lat=mc.LLOC['lat'] * u.deg, lon=mc.LLOC['lon'] * u.deg, height=mc.LLOC['alt_m'] * u.m)
    t = Time(data, scale='utc')
    sol = get_body('sun', t, loc)
    r, pa = geo.polar(x, y)
    sep = np.degrees(np.arctan(np.asarray(r) * math.tan(math.radians(mc.RSOL_ARCSEC / 3600.0))))
    p = sol.directional_offset_by((np.asarray(pa) + mc.P_DEG) * u.deg, sep * u.deg)
    if refractat:
        fr = AltAz(obstime=t, location=loc, pressure=mc.REFRACCIO['pressure_hPa'] * u.hPa,
                   temperature=mc.REFRACCIO['temperature_C'] * u.deg_C, relative_humidity=mc.REFRACCIO['relative_humidity'],
                   obswl=mc.REFRACCIO['obswl_um'] * u.micron)
    else:
        fr = AltAz(obstime=t, location=loc, pressure=0 * u.hPa)
    return p.transform_to(fr).alt.deg


def factor_E(X, X_sol, k=K):
    """E = 10^(0,4·k·(X − X☉)): > 1 cap a l'horitzó (hi arriba menys llum), < 1 cap al zenit. E = 1 al centre del Sol."""
    return 10.0 ** (0.4 * k * (np.asarray(X, np.float64) - X_sol))


class Spline:
    """Altura per píxel a partir d'una graella exacta d'astropy (spline bicúbica, com msb_comu.MassaAire)."""

    def __init__(s, fitxer):
        from scipy.interpolate import RectBivariateSpline
        d = np.load(fitxer)
        s.files, s.cols, s.alt = d['files'], d['cols'], d['alt']
        s.sp = RectBivariateSpline(s.files, s.cols, s.alt, kx=3, ky=3)
        s.h_sol = float(d['h_sol'])
        s.X_sol = float(mc.kasten_young(s.h_sol))

    def X_graella(s, ys, xs):
        return mc.kasten_young(s.sp(np.asarray(ys, np.float64), np.asarray(xs, np.float64), grid=True))

    def X_punts(s, x, y):
        return mc.kasten_young(s.sp.ev(np.asarray(y, np.float64), np.asarray(x, np.float64)))


# ------------------------------------------------------------------------------------------------ cel del pis 1 (v2)
def cel_F_v42(x, y):
    """Cel del compost lineal en l'espai del compost (sRGB lineal × guany CIENCIA), per canal, a (x, fila) del llenç V42.
    Font: el pla per canal de la v2 (CEL_CANALS_v2.json: constant + pla a r ≥ 8 R☉ en canals natius de la càmera; el verd
    és exactament el b_new de CEL_v2.json) passat a l'espai del compost amb la inversa exacta de la matriu de color:
    F = A⁻¹ · cam. Retorna (..., 3) en ADU/s."""
    c = json.load(open(CEL_CANALS))['cel']
    u = (np.asarray(x, np.float64) - mc.SOL_XY[0]) / mc.RSOL_PX
    v = (np.asarray(y, np.float64) - mc.SOL_XY[1]) / mc.RSOL_PX
    cam = np.stack([c[n]['c0'] + c[n]['gu'] * u + c[n]['gv'] * v for n in ('R', 'G', 'B')], axis=-1)
    Ainv = np.linalg.inv(mc.matriu_inversa())
    return np.einsum('ij,...j->...i', Ainv, cam)


# ------------------------------------------------------------------------------------------------ la final (pis 2)
def llegeix_final():
    """La imatge fusionada (secció «Image Data») de la V125-FINAL.psb amb psd-tools, NOMÉS LECTURA. No compon capes.
    Retorna (uint16 (H, W, 3), bytes del perfil ICC)."""
    from psd_tools import PSDImage
    from psd_tools.constants import Resource
    psd = PSDImage.open(PSB)
    if (psd.width, psd.height, psd.depth) != (WF, HF, 16):
        raise SystemExit(f'La V125-FINAL no és la que toca: {psd.width}×{psd.height}, {psd.depth} bits')
    icc = psd.image_resources.get_data(Resource.ICC_PROFILE)
    m = psd.numpy()[..., :3]
    u16 = np.round(m * 65535.0).astype(np.uint16)
    if float(np.abs(u16 / 65535.0 - m).max()) > 1e-5:
        raise SystemExit('La lectura de 16 bits no és exacta')
    return u16, icc


def info_icc(icc):
    """Descripció, corba de to i fila Y (D50) del perfil."""
    import struct
    n = struct.unpack('>I', icc[128:132])[0]
    out = {}
    for i in range(n):
        sig, off, sz = struct.unpack('>4sII', icc[132 + 12 * i:144 + 12 * i])
        d = icc[off:off + sz]
        s = sig.decode('latin-1')
        if s == 'desc':
            ln = struct.unpack('>I', d[8:12])[0]
            out['desc'] = d[12:12 + ln - 1].decode('latin-1')
        elif s in ('rTRC', 'gTRC', 'bTRC'):
            cnt = struct.unpack('>I', d[8:12])[0]
            out[s] = struct.unpack('>H', d[12:14])[0] / 256.0 if cnt == 1 else f'corba de {cnt} punts'
        elif s in ('rXYZ', 'gXYZ', 'bXYZ'):
            out[s] = [struct.unpack('>i', d[8 + 4 * k:12 + 4 * k])[0] / 65536.0 for k in range(3)]
    out['Y'] = [out['rXYZ'][1], out['gXYZ'][1], out['bXYZ'][1]]
    out['sha256'] = hashlib.sha256(icc).hexdigest()
    return out


# ------------------------------------------------------------------------------------------------ vistes
def font(mida):
    from PIL import ImageFont
    for f in ('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',      # té el símbol ☉ (U+2609)
              '/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Helvetica.ttc'):
        if Path(f).is_file():
            return ImageFont.truetype(f, mida)
    return ImageFont.load_default()


def amb_rotol(img, titol, subtitol='', alt=None, fons=(28, 28, 30), color=(235, 235, 235), destacat=None):
    """Afegeix una franja de text a SOBRE de la imatge (no tapa cap píxel del llenç). img: PIL RGB."""
    from PIL import Image, ImageDraw
    w = img.width
    ft, fs = font(max(18, w // 55)), font(max(14, w // 80))
    alt = alt or int(w // 55 * 1.5 + (w // 80 * 1.5 if subtitol else 0) + w // 60)
    out = Image.new('RGB', (w, img.height + alt), fons)
    out.paste(img, (0, alt))
    d = ImageDraw.Draw(out)
    x0, y0 = w // 120, w // 200
    d.text((x0, y0), titol, font=ft, fill=destacat or color)
    if subtitol:
        d.text((x0, y0 + int(w // 55 * 1.35)), subtitol, font=fs, fill=color)
    return out


def costat_a_costat(imgs, sep=16, fons=(28, 28, 30)):
    from PIL import Image
    h = max(i.height for i in imgs)
    w = sum(i.width for i in imgs) + sep * (len(imgs) - 1)
    out = Image.new('RGB', (w, h), fons)
    x = 0
    for i in imgs:
        out.paste(i, (x, 0))
        x += i.width + sep
    return out


def srgb_a_adobe(img, icc_adobe):
    """Passa una imatge PIL en sRGB (gràfics de matplotlib) a Adobe RGB (1998) amb el perfil de la final, intent relatiu."""
    from PIL import ImageCms
    src = ImageCms.createProfile('sRGB')
    dst = ImageCms.ImageCmsProfile(io.BytesIO(icc_adobe))
    return ImageCms.profileToProfile(img.convert('RGB'), src, dst, renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                                     outputMode='RGB')


def desa_jpeg(img, ruta, icc, qualitat=92):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    img.save(ruta, quality=qualitat, subsampling=0, icc_profile=icc, optimize=True)


def redueix_float(arr, amplada):
    """Redueix un pla float (H, W) a `amplada` px d'ample amb Lanczos (PIL, mode F). Llenç sencer: només canvia la mida."""
    from PIL import Image
    h, w = arr.shape
    alt = int(round(h * amplada / w))
    return np.asarray(Image.fromarray(np.ascontiguousarray(arr, np.float32), mode='F').resize((amplada, alt), Image.LANCZOS))


def panell_factor(fons, mapa, Emap, geo, escala, PAZ, nom, ample=3000, etiqueta='E', r_fletxa=5.2, r_text=5.75):
    """Mapa de color d'un factor (E o quocient) sobre una vista en gris, amb les isolínies d'E, el zenit, l'horitzó, el limbe i
    1,5 i 4 R☉. fons, mapa i Emap: plans a la mida de la vista; geo: geometria en px del llenç; escala: px del llenç per px de la vista."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm
    hh, ww = fons.shape
    fig = plt.figure(figsize=(ample / 100, ample / 100 * hh / ww), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(fons, cmap='gray', vmin=0, vmax=1, interpolation='lanczos')
    norm = TwoSlopeNorm(vmin=0.70, vcenter=1.0, vmax=1.43)
    col = np.ma.masked_invalid(mapa)
    ax.imshow(col, cmap='RdBu_r', norm=norm, alpha=0.55, interpolation='nearest')
    nivells = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20, 1.30, 1.40, 1.60, 1.80, 2.00]
    cs = ax.contour(Emap, levels=nivells, colors='k', linewidths=2.0)
    ax.clabel(cs, fmt=lambda v: f'×{v:.2f}'.replace('.', ','), fontsize=26, inline=True, inline_spacing=12)
    t = np.linspace(0, 360, 721)
    for rr, ls in ((1.0, '-'), (1.5, '--'), (4.0, '--')):
        x, y = geo.px(np.full_like(t, rr), t)
        ax.plot(x / escala, y / escala, color='w', lw=1.4, ls=ls, alpha=0.9)
        if rr == 1.0:
            continue
        tx, ty = geo.px(rr + 0.25, PAZ + 120.0)
        ax.text(tx / escala, ty / escala, f'{rr:g} R☉'.replace('.', ','), color='w', fontsize=26, ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.15', fc='k', ec='none', alpha=0.5))
    x0, y0 = geo.cx / escala, geo.cy / escala
    for pa0, lab, c in ((PAZ, 'zenit', 'gold'), (PAZ + 180.0, 'horitzó', 'orange')):
        x1, y1 = geo.px(r_fletxa, pa0)
        ax.annotate('', xy=(x1 / escala, y1 / escala), xytext=(x0, y0), arrowprops=dict(arrowstyle='-|>', color=c, lw=5,
                                                                                         mutation_scale=45))
        x2, y2 = geo.px(r_text, pa0)
        ax.text(x2 / escala, y2 / escala, lab, color=c, fontsize=34, weight='bold', ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.2', fc='k', ec='none', alpha=0.6))
    ax.set_xlim(-0.5, ww - 0.5); ax.set_ylim(hh - 0.5, -0.5); ax.axis('off')
    cax = fig.add_axes([0.70, 0.07, 0.27, 0.025])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap='RdBu_r'), cax=cax, orientation='horizontal')
    cb.set_ticks([0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4])
    cb.set_ticklabels(['0,7', '0,8', '0,9', '1', '1,1', '1,2', '1,3', '1,4'])
    cb.ax.tick_params(labelsize=22, colors='w')
    cb.set_label(etiqueta, color='w', fontsize=24)
    fig.savefig(nom, dpi=100, facecolor='k')
    plt.close(fig)
