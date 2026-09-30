"""Comú de la cadena V108 (Claude, 26-09-2026, nit): rutes, la V107 de Pere, la taula capa → etiqueta dels filtres, la quantització del Photoshop
i la lectura dels registres de capa d'un PSB. NOMÉS lectura del projecte; qui escriu són els guions que l'importen, i només a les carpetes cadena/.

La quantització del Photoshop (mesurada el 26-09 contra la V107, exacta al 100 % dels píxels de les capes 3 i 41–56):
  el Photoshop desa els canals de 16 bits amb 15 bits reals (0…32768); en desar un PSB, cada valor v del fitxer passa a
  q(v) = round(round(v·32768/65535)·65535/32768). q és idempotent (q(q(v)) = q(v)) i té 32 769 valors.
  Per tant: un ràster nou r «no canvia la capa» si q(r) és IGUAL al canal de la V107, i el canal que quedarà a la V108 nativa és q(r)."""
import sys, json, hashlib, re, struct, zlib, logging
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB, BIG_KEYS, _rf                      # noqa: E402
from psd_tools.psd.layer_and_mask import LayerRecord      # noqa: E402
from psd_tools.constants import Tag                       # noqa: E402
logging.getLogger('psd_tools').setLevel(logging.ERROR)
H, W = 7506, 10551
V107 = ARREL / '1-PHOTOSHOP/V107.psb'
SHA_V107 = '5927342e26fef8cf0dbe50a58c5ba2b12363d6c9921b18d30c5104a2da381afc'
CLAIM_ID = 'CLAUDE_V108_MARRONS_I_ZONES_NEGRES_20260926'
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native',
       47: '03', 48: '03v30', 49: '07', 50: '01', 51: '04', 52: '05', 53: '06', 54: 'P03_MGN', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
ETAPA = {41: 'E1', 42: 'E1', 43: 'E1', 44: 'E1', 45: 'E6', 46: 'E6', 47: 'E4', 48: 'E4', 49: 'E4', 50: 'E3', 51: 'E3', 52: 'E3', 53: 'E3', 54: 'E2', 55: 'E2', 56: 'E2'}
FILTRES = list(range(41, 57)); CAPES = [3] + FILTRES
LLUNA = (5375.786804312011, 3775.9774911631, 452.9785129274736)          # Lluna de presentació (cx, cy, R)
CAIXA_LLUNA = (4677, 3077, 6077, 4477)                                   # x0, y0, x1, y1 (la de la REC de la 56, V105)


def q(v):
    """Quantització del Photoshop en desar un PSB de 16 bits (vegeu la capçalera)."""
    return np.round(np.round(np.asarray(v, np.float64) * 32768 / 65535) * 65535 / 32768).astype(np.uint16)


def q_blocs(v, pas=512):
    """q() per blocs de files (menys memòria per als ràsters de llenç sencer)."""
    v = np.asarray(v); out = np.empty(v.shape, np.uint16)
    for y in range(0, v.shape[0], pas): out[y:y + pas] = q(v[y:y + pas])
    return out


def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def claim(exigeix_id=True):
    return {}  # 30-09-2026: regla de l'escriptor únic retirada per Pere
    o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text())
    assert o.get('serial_writes') == 'HELD', 'cal el claim SERIAL_WRITES viu'
    if exigeix_id: assert o.get('claim_id') == CLAIM_ID, f"el claim viu és {o.get('claim_id')}, no {CLAIM_ID}"
    return o


def rel(p):
    p = Path(p).resolve()
    try: return str(p.relative_to(ARREL))
    except ValueError: return str(p)


def enc(a):
    """Codifica un canal com el Photoshop el llegeix: compressió 3 (ZIP amb predicció horitzontal), 16 bits big-endian."""
    a = np.ascontiguousarray(a, np.uint16); d = a.copy(); d[:, 1:] = a[:, 1:] - a[:, :-1]
    return struct.pack('>H', 3) + zlib.compress(d.astype('>u2').tobytes(), 6)


def llegeix_registres(path):
    """Els registres de capa (psd_tools) i els seus bytes crus, i les posicions de la secció Lr16 d'un PSB de 16 bits."""
    with open(path, 'rb') as f:
        f.seek(26)
        for _ in range(2): n = _rf(f, 'I')[0]; f.seek(n, 1)
        lmpos = f.tell(); lmlen = _rf(f, 'Q')[0]; lmend = f.tell() + lmlen; n = _rf(f, 'Q')[0]; assert n == 0; n = _rf(f, 'I')[0]; f.seek(n, 1)
        while f.tell() + 12 <= lmend:
            sig, key = _rf(f, '4s4s'); fmt = 'Q' if key in BIG_KEYS else 'I'; lenpos = f.tell(); n = _rf(f, fmt)[0]; start = f.tell()
            if key == b'Lr16': break
            f.seek(start + (n + 3) // 4 * 4)
        assert key == b'Lr16', 'sense secció Lr16'
        count = _rf(f, 'h')[0]; recs = []
        for _ in range(abs(count)):
            pos = f.tell(); r = LayerRecord.read(f, version=2); end = f.tell(); f.seek(pos); recs.append((r, f.read(end - pos)))
    return dict(lmpos=lmpos, lmlen=lmlen, lenpos=lenpos, lrstart=start, lrlen=n, lrpadend=start + (n + 3) // 4 * 4, count=count, recs=recs)


rid = lambda r: int(r.tagged_blocks.get_data(Tag.LAYER_ID))
nom_de = lambda r: str(r.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME))


def nom_v108(nom):
    """El sufix de versió del nom de Pere passa a «V108» (el primer «V9x»/«V10x» del nom); si no n'hi ha cap, s'hi afegeix « · V108»."""
    if re.search(r'\bV(9\d|1\d\d)\b', nom): return re.sub(r'\bV(9\d|1\d\d)\b', 'V108', nom, count=1)
    return nom + ' · V108'


def renomena(r, nom):
    r.name = nom.encode('mac_roman', 'replace').decode('mac_roman')[:31]; r.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME, nom)
