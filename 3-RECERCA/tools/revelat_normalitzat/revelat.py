"""Driver del re-revelat normalitzat (CapesTotals V4, Opcio A signada).

Subordres:
  probe       revela la capa 07 a +0,00 i +1,00 EV (test de linealitat §5.1)
  render-all  revela les 12 capes amb -log2(t/t_ref) i escriu RENDER_RECEIPT

Mai toca els originals: copia a work/, hi escriu l'XMP crs (DNG: incrustat amb
exiftool; CR3: sidecar) i revela via Photoshop 2026 (JSX, displayDialogs=NO).
Verificacio externa de cada sortida: 16 bits, Display P3, 6960x4640.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, shutil, subprocess, sys, time
from pathlib import Path

APILATS = Path(os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Vixen/HDR4/apilats'))
BASE = Path(os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Vixen/HDR4/revelat_v4'))
WORK, OUT, RECEIPTS, JSXDIR = (BASE / d for d in ('work', 'out', 'receipts', 'jsx'))
PS_APP = 'Adobe Photoshop 2026'
W, H = 6960, 4640

# prefix -> (fitxer font, nom de capa al projecte)
LAYERS = {
    '12': ('12_1-3200s_572A2956.CR3', '12 · 1/3200'),
    '11': ('11_1-500s_572A2968.CR3', '11 · 1/500'),
    '10': ('10_1-125s_572A2969.CR3', '10 · 1/125'),
    '09': ('09_1-60s_572A2975_apilat2.dng', '09 · 1/60'),
    '08': ('08_1-30s_572A2970_apilat4.dng', '08 · 1/30'),
    '07': ('07_1-15s_572A2976_apilat2.dng', '07 · 1/15 (ref)'),
    '06': ('06_1-8s_572A2971_apilat4.dng', '06 · 1/8'),
    '05': ('05_1-4s_572A2977_apilat2.dng', '05 · 1/4'),
    '04': ('04_1-2s_572A2972_apilat4.dng', '04 · 1/2'),
    '03': ('03_1s_572A2978_apilat2.dng', '03 · 1 s'),
    '02': ('02_2s_572A2979_apilat3.dng', '02 · 2 s'),
    '01': ('01_10.3s_572A2982_apilat3.dng', '01 · 10,3 s'),
}
REF = '07'
OVERRIDE_T = {'01': 10.08}   # decisio §8.3: 10,08 s fotometric (research/76), no l'EXIF (10,0 al DNG; 10,37 APEX al CR3)

JSX = r'''var IN = %s;
var OUT = %s;
app.displayDialogs = DialogModes.NO;
var doc = app.open(new File(IN));
var depth = (doc.bitsPerChannel == BitsPerChannelType.SIXTEEN) ? 16 : (doc.bitsPerChannel == BitsPerChannelType.EIGHT) ? 8 : 32;
var res = ["depth=" + depth, "profile=" + doc.colorProfileName,
           "w=" + Math.round(doc.width.as("px")), "h=" + Math.round(doc.height.as("px"))];
var ok = (depth == 16) && (doc.colorProfileName == "Display P3")
      && (Math.round(doc.width.as("px")) == %d) && (Math.round(doc.height.as("px")) == %d);
if (ok) {
  var o = new TiffSaveOptions();
  o.imageCompression = TIFFEncoding.TIFFLZW;
  o.embedColorProfile = true;
  o.layers = false;
  o.alphaChannels = false;
  o.spotColors = false;
  doc.saveAs(new File(OUT), o, true, Extension.LOWERCASE);
}
doc.close(SaveOptions.DONOTSAVECHANGES);
(ok ? "OK;" : "FAIL;") + res.join(";");
'''

CRS_TAGS = {
    'Version': '18.5',
    'ProcessVersion': '15.4',
    'Exposure2012': None,          # s'omple per capa
    'Contrast2012': '0',
    'Highlights2012': '0',
    'Shadows2012': '0',
    'Whites2012': '0',
    'Blacks2012': '0',
    'Texture': '0',
    'Clarity2012': '0',
    'Dehaze': '0',
    'Vibrance': '0',
    'Saturation': '0',
    'ToneCurveName2012': 'Linear',
    'WhiteBalance': 'As Shot',
    'SharpenAmount': '0',
    'LuminanceSmoothing': '0',
    'ColorNoiseReduction': '0',
    'HasSettings': 'True',
}

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()

def exif_time_s(path: Path) -> float:
    """Temps d'exposicio APEX (s) rellegit de l'EXIF; mai un literal manual."""
    r = subprocess.run(['exiftool', '-n', '-ShutterSpeedValue', '-s3', str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip().splitlines()[0])

def as_shot_neutral(path: Path) -> str:
    r = subprocess.run(['exiftool', '-n', '-AsShotNeutral', '-s3', str(path)],
                       capture_output=True, text=True)
    return r.stdout.strip()

def js_str(s: str) -> str:
    return json.dumps(str(s))

def write_xmp(copy: Path, ev: float) -> dict:
    tags = dict(CRS_TAGS)
    tags['Exposure2012'] = f'{ev:+.2f}'
    if copy.suffix.lower() == '.dng':
        cmd = ['exiftool', '-overwrite_original']
        for k, v in tags.items():
            cmd.append(f'-XMP-crs:{k}={v}')
        cmd.append(str(copy))
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {'format': 'embedded_dng_xmp', 'tags': tags}
    # CR3: sidecar (exiftool no escriu CR3)
    attrs = ' '.join(f'crs:{k}="{v}"' for k, v in tags.items())
    xmp = f'''<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="revelat_normalitzat v1">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:crs="http://ns.adobe.com/camera-raw-settings/1.0/"
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmp:CreatorTool="revelat_normalitzat v1"
    crs:Version="17.0"
    crs:RawFileName="{copy.name}"
    {attrs}/>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>'''
    sidecar = copy.with_suffix('.xmp')
    sidecar.write_text(xmp, encoding='utf-8')
    return {'format': 'sidecar_xmp', 'path': sidecar.name, 'tags': tags}

def render_one(prefix: str, ev: float, out_tif: Path, tag: str) -> dict:
    src = APILATS / LAYERS[prefix][0]
    copy = WORK / f'v4_{prefix}_{tag}{src.suffix}'
    shutil.copy2(src, copy)
    if copy.suffix.lower() == '.dng':
        copy.with_suffix('.xmp').unlink(missing_ok=True)   # cap sidecar orfe que taparia l'incrustat
    else:
        copy.with_suffix('.xmp').unlink(missing_ok=True)
    xmp_info = write_xmp(copy, ev)
    jsx = JSXDIR / f'render_{prefix}_{tag}.jsx'
    jsx.write_text(JSX % (js_str(copy), js_str(out_tif), W, H), encoding='utf-8')
    t0 = time.time()
    r = subprocess.run(['osascript', '-e',
                        f'tell application "{PS_APP}" to do javascript (alias (POSIX file "{jsx}"))'],
                       capture_output=True, text=True, timeout=280)
    dt = time.time() - t0
    line = r.stdout.strip()
    rec = {'jsx': jsx.name, 'osascript_rc': r.returncode, 'ps_result': line,
           'seconds': round(dt, 1)}
    if r.returncode != 0:
        rec['stderr'] = r.stderr.strip()
        raise RuntimeError(f'osascript ha fallat per {prefix}: {r.stderr.strip()}')
    if not line.startswith('OK;'):
        raise RuntimeError(f'render FAIL per {prefix}: {line}')
    if not out_tif.exists():
        raise RuntimeError(f'no s\'ha escrit {out_tif}')
    rec['xmp'] = xmp_info
    rec['copy'] = {'path': copy.name, 'sha256': sha256(copy)}
    rec['out'] = {'path': str(out_tif), 'sha256': sha256(out_tif)}
    return rec

def receipt(prefix: str, ev: float, t_s: float, t_ref: float, rec: dict, kind: str) -> dict:
    src = APILATS / LAYERS[prefix][0]
    return {
        'RENDER_RECEIPT': 'v1',
        'kind': kind,
        'layer': LAYERS[prefix][1], 'prefix': prefix,
        'source': {'path': str(src), 'sha256': sha256(src)},
        'exposure_s_exif_apex': exif_time_s(src),
        'exposure_s_used': t_s,
        'exposure_override': OVERRIDE_T.get(prefix),
        't_ref_s': t_ref, 'ev_applied': round(ev, 4),
        'settings': rec['xmp']['tags'],
        'wb': 'As Shot (neutral identic als 12 fitxers: 0.514573 1 0.602707, Dia 5200 K)',
        'geometry': 'intacta: cap remostreig, cap translacio',
        'tool': {'name': 'revelat_normalitzat v1', 'photoshop': PS_APP,
                 'exiftool': subprocess.run(['exiftool', '-ver'], capture_output=True, text=True).stdout.strip()},
        'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'render': rec,
    }

def cmd_probe():
    for d in (WORK, OUT, RECEIPTS, JSXDIR):
        d.mkdir(parents=True, exist_ok=True)
    src = APILATS / LAYERS[REF][0]
    t_ref = exif_time_s(src)
    print(f't_ref (07, EXIF APEX) = {t_ref:.9f} s ; neutral = {as_shot_neutral(src)}')
    results = {}
    for tag, ev in (('p0', 0.0), ('p1', 1.0)):
        out = OUT / f'probe_07_{tag}.tif'
        out.unlink(missing_ok=True)
        rec = render_one(REF, ev, out, tag)
        receipt_path = RECEIPTS / f'probe_07_{tag}.receipt.json'
        receipt_path.write_text(json.dumps(receipt(REF, ev, t_ref, t_ref, rec, 'probe_linealitat_5.1'),
                                           indent=1, ensure_ascii=False))
        results[tag] = rec['ps_result']
        print(f'probe {tag}: {rec["ps_result"]} ({rec["seconds"]} s)')
    print('Ara executa: test_linealitat.py')

def cmd_render_all():
    for d in (WORK, OUT, RECEIPTS, JSXDIR):
        d.mkdir(parents=True, exist_ok=True)
    t_ref = exif_time_s(APILATS / LAYERS[REF][0])
    print(f't_ref = {t_ref:.9f} s (capa 07, EXIF APEX)')
    table = []
    for prefix in ['12', '11', '10', '09', '08', '07', '06', '05', '04', '03', '02', '01']:
        src = APILATS / LAYERS[prefix][0]
        t = OVERRIDE_T.get(prefix, exif_time_s(src))
        ev = -math.log2(t / t_ref)
        table.append((prefix, t, ev))
    for prefix, t, ev in table:
        print(f'{prefix}: t={t:.6f} s  EV={ev:+.3f}')
    for prefix, t, ev in table:
        tag = f'EV{ev:+.2f}'
        out = OUT / f'v4_{prefix}_{tag}.tif'
        out.unlink(missing_ok=True)
        rec = render_one(prefix, ev, out, tag)
        (RECEIPTS / f'v4_{prefix}.receipt.json').write_text(
            json.dumps(receipt(prefix, ev, t, t_ref, rec, 'render_v4'), indent=1, ensure_ascii=False))
        print(f'{prefix}: {rec["ps_result"]} ({rec["seconds"]} s)')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('probe', 'render-all'))
    a = ap.parse_args()
    {'probe': cmd_probe, 'render-all': cmd_render_all}[a.cmd]()
