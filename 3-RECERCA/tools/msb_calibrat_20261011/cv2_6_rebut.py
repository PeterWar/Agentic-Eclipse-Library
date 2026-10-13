"""cv2_6 · Rebut de les comparacions v2 (12-10-2026): SHA-256 del codi, de les entrades i de les sortides; fonts externes llegides.
Escriu v2/comparacions/RECEIPT_comparacions_v2.json. No escriu res fora de v2/comparacions/."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2_comu as cv   # noqa: E402

mc, m2, cc1 = cv.mc, cv.m2, cv.cc1
EINES = Path(__file__).resolve().parent
codi = sorted(EINES.glob('cv2_*.py')) + [EINES / 'executa_comparacions_v2.sh', EINES / 'msb_comu.py', EINES / 'msb_comu_v2.py',
                                          EINES / 'comparacions' / 'cmp_comu.py', EINES / 'executa.sh']
sortides = sorted(p for p in cv.RES2.rglob('*') if p.is_file() and p.name != 'RECEIPT_comparacions_v2.json')
sortides += [p for p in (cv.COMPARTIR2 / 'README_EN_v2.md',) if p.is_file()]
entrades = {}
for js in cv.RES2.rglob('*.json'):
    try:
        d = json.load(open(js))
    except Exception:
        continue
    if isinstance(d, dict) and isinstance(d.get('entrades_sha256'), dict):
        entrades.update(d['entrades_sha256'])
rebut = dict(
    data=time.strftime('%Y-%m-%dT%H:%M:%S'), tasca='comparacions de la v2 del mapa MSB (K-Cor, C2, banda, figura, textos)',
    estat='PROVISIONAL. Res enviat ni publicat. Per enviar res o posar-ho a l\'article cal el sí de Pere.',
    codi={cv.rel(p): cv.sha256(p) for p in codi if p.is_file()},
    entrades=entrades,
    sortides={cv.rel(p): cv.sha256(p) for p in sortides},
    fonts_externes_llegides=[
        dict(que='Colaninno & Howard 2015, Sol. Phys. 290, 997 (text i Taula 2; l\'eq. 8 només és una imatge)',
             on='https://pmc.ncbi.nlm.nih.gov/articles/PMC4479163/ (llegida el 12-10-2026; no s\'ha desat cap fitxer)'),
        dict(que='Llebaria et al. 2021, Sol. Phys. 296, 53 (doi 10.1007/s11207-021-01800-w), versió arXiv 2011.12920',
             on='https://ar5iv.arxiv.org/html/2011.12920 (llegida el 12-10-2026; no s\'ha desat cap fitxer)'),
        dict(que='Lamy et al. 2020 (arXiv 2001.05925), §4.4 i Fig. 9', on='text ja extret per la sessió (scratchpad/rev10/lamy2020.txt)'),
        dict(que='Pàgina de calibratge de l\'NRL (c2vig_final.fts, «entire mission», juny 2005)',
             on='resum d\'un cercador; el servidor lasco-www.nrl.navy.mil no responia (ECONNREFUSED) el 12-10-2026')],
    paperera='La cau de la Paperera només s\'ha llegit (mmap de lectura); SHA de referència de B3_V42_FROZEN.',
    res_esborrat='Cap fitxer esborrat ni sobreescrit de la v1 ni del mapa v2.')
cv.json_dump(rebut, cv.RES2 / 'RECEIPT_comparacions_v2.json')
print(f"rebut: {len(rebut['codi'])} fitxers de codi, {len(entrades)} entrades, {len(rebut['sortides'])} sortides")
