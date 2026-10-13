"""Rebut d'entrades de la tasca msb_calibrat_20261011/zp_canal: sha256 de cada fitxer
llegit (RAW de les estrelles i de la corona, foscos que entren als mestres, catàlegs,
efemèride) i dels guions, amb la ruta relativa a 4-Photoshop/. Només lectura.

Els foscos es trien igual que original/vixen/mkdark.py (ExposureTime EXIF exacte
'10', '2', '1') i original/sony/darks.py (els 24 primers per nom de 8, 2 i 1 s).
Sortida: resultats/msb_calibrat_20261011/zp_canal/REBUT_ENTRADES.json
"""
import glob
import hashlib
import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "original"))
import comu  # noqa: E402

ARREL = comu.ARREL
RES = ARREL / "3-RECERCA/resultats/msb_calibrat_20261011/zp_canal"


def sha256(p, bloc=1 << 22):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(bloc)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def rel(p):
    p = Path(p).resolve()
    try:
        return str(p.relative_to(ARREL))
    except ValueError:
        return '~/' + str(p.relative_to(Path.home())) if str(p).startswith(str(Path.home())) else str(p)


def main():
    exiftool = shutil.which('exiftool')
    grups = {}
    # Vixen: estrelles (phot2/proc), corona (corona2) i fotogrames del registre i del centre (center2)
    vix = Path(comu.DADES_VIXEN_UNF)
    est = ['572A2978', '572A2979', '572A2980', '572A2981', '572A2982', '572A2983', '572A2984', '572A2996']
    cor = ['572A2970', '572A2971', '572A2977']
    grups['vixen_estrelles'] = [vix / f'{f}.CR3' for f in est]
    grups['vixen_corona'] = [vix / f'{f}.CR3' for f in cor]
    c2 = [f'572A{n}' for n in list(range(2969, 2973)) + list(range(2987, 2991)) + list(range(2999, 3003))
          + list(range(3005, 3009))]
    grups['vixen_center2'] = [vix / f'{f}.CR3' for f in c2 if (vix / f'{f}.CR3').exists()]
    # foscos R6 (mkdark.py)
    D = str(comu.DARKS_R6) + '/'
    out = subprocess.run([exiftool, '-q', '-n', '-T', '-FileName', '-ExposureTime'] + sorted(glob.glob(D + '*.CR3')),
                         capture_output=True, text=True).stdout
    rows = [ln.split('\t') for ln in out.strip().split('\n')]
    for e in ('10', '2', '1'):
        grups[f'foscos_r6_{e}s'] = [Path(D) / r[0] for r in rows if r[1] == e]
    # Sony (rèplica G): fotogrames d'estrelles i foscos (darks.py)
    son = Path(comu.DADES_300MM)
    sfr = ['DSC06984', 'DSC06985', 'DSC06987', 'DSC06988', 'DSC06991', 'DSC06993', 'DSC06996', 'DSC06999',
           'DSC06990', 'DSC06982', 'DSC06983', 'DSC06986']
    grups['sony_fotogrames'] = [son / f'{f}.ARW' for f in sfr if (son / f'{f}.ARW').exists()]
    DD = str(comu.DARKS_SONY) + '/'
    out = subprocess.run(['exiftool', '-T', '-FileName', '-ExposureTime', DD], capture_output=True, text=True).stdout
    byexp = {}
    for ln in out.strip().split('\n'):
        p = ln.split('\t')
        if len(p) < 2:
            continue
        byexp.setdefault(p[1].strip(), []).append(p[0].strip())
    for e in ('8', '2', '1'):
        grups[f'foscos_sony_{e}s'] = [Path(DD) / f for f in sorted(byexp.get(e, []))[:24]]
    grups['catalegs'] = [comu.TYC2_DEEP, comu.HIP_MAIN]
    grups['efemeride'] = [comu.EFEMERIDE]
    grups['guions'] = sorted(AQUI.glob('*.py')) + sorted(AQUI.glob('*.sh')) + sorted((AQUI / 'original').rglob('*.py'))
    tots = [p for v in grups.values() for p in v]
    with ThreadPoolExecutor(8) as ex:
        hs = dict(zip(tots, ex.map(sha256, tots)))
    rebut = dict(tasca='msb_calibrat_20261011/zp_canal', data=time.strftime('%Y-%m-%dT%H:%M:%S'),
                 nota='rutes relatives a 4-Photoshop/ (o a ~/ per a l\'efemèride)',
                 grups={k: {rel(p): hs[p] for p in v} for k, v in grups.items()},
                 recompte={k: len(v) for k, v in grups.items()})
    json.dump(rebut, open(RES / 'REBUT_ENTRADES.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(rebut['recompte'], indent=1))


if __name__ == '__main__':
    main()
