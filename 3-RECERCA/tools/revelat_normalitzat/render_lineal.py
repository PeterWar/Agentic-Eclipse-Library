"""Renderer lineal offline per a CapesTotals V4 (Opcio B+ aprovada per Pere 21-08-2026).

Per que no ACR: el revelat scriptat d'ACR a Photoshop 27.9.1 obre SEMPRE a 8 bits
(provat: prefs de workflow DNG.xmp a 16 bits, reinici de PS, smart object, i
descriptors cameraRawOptions rebutjats amb error 8800). Pere ho ha pogut constatar.
Via aprovada: revelat offline determinista.

Pipeline (identic per a les 12 capes):
  1. Lectura LinearRaw amb rawpy (mateix motor que apila_hdr4_vixen.py):
     - 01..09: els DNG d'apilats HDR4 (LinearRaw, negre 512, blanc 13995).
     - 10..12: CR3 convertits a DNG lineal amb Adobe DNG Converter 18.5 (-c -l -p1),
       la mateixa eina que va reescriure els 9 apilats (negre 2398, blanc 65535,
       crop 10,10 + 6960x4640).
  2. lineal = (x - negre) / (blanc - negre), retallat a >= 0. Saturacio = 1.
  3. WB: x camera_whitebalance (As Shot; IDENTIC als 12 fitxers: 1.943359 1 1.659181,
     neutral 0.514573 1 0.602707, Dia 5200 K).
  4. Escala: x t_ref / t, t_ref = 1/15 s (capa 07, EXIF APEX). t de l'EXIF APEX de
     cada fitxer; capa 01 = 10,08 s fotometric (decisio §8.3, research/76).
     BaselineExposure (0,26 als 12) NO s'aplica: escala pura declarada.
  5. Color: ForwardMatrix2 (il.luminant D65) -> XYZ D50 -> Bradford D65 ->
     Display P3 lineal -> retall [0,1] -> TRC sRGB -> u16 (rint) -> TIFF 16 bits
     amb l'ICC Display P3 pinat (SHA 7e1c7ec5..., el dels PSB del projecte).

El clip de les capes escalades amunt (12..08) es l'esperat a la proposta:
les perles/cromosfera clippen a blanc pero queden detectables i protegides (P3/P4).
"""
from __future__ import annotations
import json, math, os, subprocess, sys, time
from pathlib import Path
import numpy as np
import rawpy
import tifffile

PY = sys.executable
APILATS = Path(os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Vixen/HDR4/apilats'))
BASE = Path(os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Vixen/HDR4/revelat_v4'))
WORK, OUT, RECEIPTS = BASE / 'work', BASE / 'out', BASE / 'receipts'
DNGC = Path('/Applications/Adobe DNG Converter.app/Contents/MacOS/Adobe DNG Converter')
W, H = 6960, 4640

LAYERS = {  # prefix -> fitxer font
    '12': '12_1-3200s_572A2956.CR3', '11': '11_1-500s_572A2968.CR3',
    '10': '10_1-125s_572A2969.CR3',
    '09': '09_1-60s_572A2975_apilat2.dng', '08': '08_1-30s_572A2970_apilat4.dng',
    '07': '07_1-15s_572A2976_apilat2.dng', '06': '06_1-8s_572A2971_apilat4.dng',
    '05': '05_1-4s_572A2977_apilat2.dng', '04': '04_1-2s_572A2972_apilat4.dng',
    '03': '03_1s_572A2978_apilat2.dng', '02': '02_2s_572A2979_apilat3.dng',
    '01': '01_10.3s_572A2982_apilat3.dng',
}
REF = '07'
OVERRIDE_T = {'01': 10.08}  # decisio §8.3

# Bradford D50 -> D65
M_BRAD = np.array([[0.9555766, -0.0230393, 0.0631636],
                   [-0.0282895, 1.0099416, 0.0210077],
                   [0.0122982, -0.0204830, 1.3299098]])
# Display P3 (D65) primaries -> XYZ
M_P3_TO_XYZ = np.array([[0.48657095, 0.26566769, 0.19821729],
                        [0.22897456, 0.69173852, 0.07928691],
                        [0.00000000, 0.04511338, 1.04394437]])
M_XYZ_TO_P3 = np.linalg.inv(M_P3_TO_XYZ)

def sha256(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()

def exif_time_s(path: Path) -> float:
    r = subprocess.run(['exiftool', '-n', '-ShutterSpeedValue', '-s3', str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip().splitlines()[0])

def srgb_trc(lin):
    return np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * np.power(lin, 1 / 2.4) - 0.055)

def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def converteix_cr3(prefix: str) -> Path:
    """CR3 -> DNG lineal amb el DNG Converter 18.5 (una sola vegada; fail-closed)."""
    src = APILATS / LAYERS[prefix]
    dst = WORK / f'lineal_{src.stem}.dng'
    if dst.exists():
        return dst
    tmp_cr3 = WORK / src.name
    if not tmp_cr3.exists():
        import shutil
        shutil.copy2(src, tmp_cr3)
    r = subprocess.run([str(DNGC), '-c', '-l', '-p1', '-d', str(WORK), '-o', dst.name, str(tmp_cr3)],
                       capture_output=True, text=True, timeout=280)
    if not dst.exists():
        raise RuntimeError(f'DNG Converter ha fallat per {prefix}: {r.stdout} {r.stderr}')
    with rawpy.imread(str(dst)) as raw:
        s = raw.sizes
        assert (s.crop_width, s.crop_height) == (W, H), (s.crop_width, s.crop_height)
    return dst

def dng_font(prefix: str) -> Path:
    if LAYERS[prefix].endswith('.CR3'):
        return converteix_cr3(prefix)
    return APILATS / LAYERS[prefix]

def llegeix_lineal(path: Path):
    """RGB float64 lineal (saturacio = 1) amb WB As Shot aplicat, 6960x4640."""
    with rawpy.imread(str(path)) as raw:
        s = raw.sizes
        x = raw.raw_image[..., :3].astype(np.float64)
        if (s.crop_width, s.crop_height) == (W, H) and (s.crop_left_margin or s.crop_top_margin):
            x = x[s.crop_top_margin:s.crop_top_margin + s.crop_height,
                  s.crop_left_margin:s.crop_left_margin + s.crop_width, :]
        assert x.shape == (H, W, 3), x.shape
        black = np.array(raw.black_level_per_channel[:3], np.float64)
        white = float(raw.white_level)
        wb = np.array(raw.camera_whitebalance[:3], np.float64)
    lin = (x - black) / (white - black)
    np.maximum(lin, 0.0, out=lin)
    lin *= (wb / wb[1])
    return lin

def forward_matrix_2(path: Path) -> np.ndarray:
    """ForwardMatrix2 (D65) del DNG root; per als CR3 convertits, del DNG convertit."""
    with tifffile.TiffFile(str(path)) as t:
        v = t.pages[0].tags['ForwardMatrix2'].value
    m = np.array([a / b for a, b in np.asarray(v).reshape(9, 2)], np.float64).reshape(3, 3)
    return m

def render(prefix: str, escala: float, out_tif: Path, icc: bytes) -> dict:
    src = dng_font(prefix)
    lin = llegeix_lineal(src) * escala
    fm2 = forward_matrix_2(src)
    xyz50 = lin @ fm2.T
    xyz65 = xyz50 @ M_BRAD.T
    p3 = xyz65 @ M_XYZ_TO_P3.T
    np.clip(p3, 0.0, 1.0, out=p3)
    n_clip_hi = int((xyz65 @ M_XYZ_TO_P3.T > 1.0).any(axis=2).sum())
    coded = srgb_trc(p3)
    u16 = np.rint(coded * 65535.0).astype(np.uint16)
    tifffile.imwrite(str(out_tif), u16, photometric='rgb', compression='zlib',
                     extratags=[(33432, 'B', len(icc), icc, False)])
    return {'source_dng': {'path': str(src), 'sha256': sha256(src)},
            'out': {'path': str(out_tif), 'sha256': sha256(out_tif)},
            'pixels_clipped_white': n_clip_hi}

def icc_p3() -> bytes:
    """ICC Display P3 pinat: s'extreu del PSB font (SHA 7e1c7ec5...)."""
    cache = WORK / 'display_p3.icc'
    if cache.exists():
        data = cache.read_bytes()
    else:
        from psd_tools import PSDImage
        from psd_tools.psd.image_resources import Resource
        psd = PSDImage.open('/Users/USUARI/Downloads/Corretgint2.psb')
        data = psd.image_resources.get_data(Resource.ICC_PROFILE)
        cache.write_bytes(data)
    import hashlib
    assert hashlib.sha256(data).hexdigest() == \
        '7e1c7ec53e8ea35fed3e169dee62115ac045f26c7bc256fab16a5c26c29eacbd'
    return data

def receipt(prefix, t_s, t_ref, escala, rec, kind):
    return {
        'RENDER_RECEIPT': 'v2-offline',
        'kind': kind, 'prefix': prefix,
        'source_original': {'path': str(APILATS / LAYERS[prefix]),
                            'sha256': sha256(APILATS / LAYERS[prefix])},
        'exposure_s_exif_apex': exif_time_s(APILATS / LAYERS[prefix]),
        'exposure_s_used': t_s, 'exposure_override': OVERRIDE_T.get(prefix),
        't_ref_s': t_ref, 'scale': escala, 'ev_equivalent': round(math.log2(escala), 4),
        'pipeline': 'LinearRaw -> (x-negre)/(blanc-negre) -> WB As Shot -> x t_ref/t '
                    '-> ForwardMatrix2 D65 -> XYZ D50 -> Bradford D65 -> Display P3 '
                    'lineal -> clip [0,1] -> TRC sRGB -> u16 rint -> TIFF zlib',
        'baseline_exposure': '0,26 present als 12 DNG i NO aplicat (escala pura declarada)',
        'wb': 'As Shot identic als 12 fitxers (neutral 0.514573 1 0.602707, Dia 5200 K)',
        'geometry': 'intacta: cap remostreig, cap translacio; crop del DNG respectat',
        'tool': {'name': 'render_lineal v1', 'python': PY, 'rawpy': rawpy.__version__,
                 'tifffile': tifffile.__version__, 'dng_converter': '18.5 (-c -l -p1) pels CR3'},
        'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'render': rec,
    }

def main():
    ap = sys.argv[1] if len(sys.argv) > 1 else 'render-all'
    for d in (WORK, OUT, RECEIPTS):
        d.mkdir(parents=True, exist_ok=True)
    icc = icc_p3()
    t_ref = exif_time_s(APILATS / LAYERS[REF])
    print(f't_ref = {t_ref:.9f} s (07 EXIF APEX)')
    if ap == 'probe':
        for tag, esc in (('p0', 1.0), ('p1', 2.0)):
            out = OUT / f'probe_07_{tag}.tif'
            out.unlink(missing_ok=True)
            rec = render(REF, esc, out, icc)
            (RECEIPTS / f'probe_07_{tag}.receipt.json').write_text(json.dumps(
                receipt(REF, t_ref, t_ref, esc, rec, 'probe_escala'), indent=1, ensure_ascii=False))
            print(f'probe {tag}: {rec["out"]["sha256"][:16]}… clip={rec["pixels_clipped_white"]}')
        return
    if ap == 'render-all':
        for prefix in ['12', '11', '10', '09', '08', '07', '06', '05', '04', '03', '02', '01']:
            t = OVERRIDE_T.get(prefix, exif_time_s(APILATS / LAYERS[prefix]))
            esc = t_ref / t
            out = OUT / f'v4_{prefix}.tif'
            out.unlink(missing_ok=True)
            t0 = time.time()
            rec = render(prefix, esc, out, icc)
            (RECEIPTS / f'v4_{prefix}.receipt.json').write_text(json.dumps(
                receipt(prefix, t, t_ref, esc, rec, 'render_v4'), indent=1, ensure_ascii=False))
            print(f'{prefix}: t={t:.6f} escala=x{esc:.4f} ({math.log2(esc):+.2f} EV) '
                  f'clip={rec["pixels_clipped_white"]:,} px  ({time.time()-t0:.0f} s)', flush=True)
        return
    raise SystemExit(f'ordre desconeguda: {ap}')

if __name__ == '__main__':
    main()
