"""r1 (V97) · Entrades: els apilats per tren i apuntament, la fusió V42, les fonts V29 i la calibració, clonats des de la Paperera (lot 10b del 24-09)
a 4-RESULTATS/v97_refundacio_20260924/entrades/ amb la mateixa ruta relativa que tenien a v85_regeneracio_20260922/.
- Còpia APFS (`cp -c`, clonefile): no ocupa espai nou i NO mou ni toca la Paperera.
- Cada fitxer es verifica amb el SHA-256 del manifest MOVIMENTS_lot10b (si no quadra, s'atura).
Escriu ENTRADES.json (ruta, bytes, sha256, origen). Ús: r1_entrades.py [patró …] (per defecte, els grups de GRUPS)."""
import sys, json, hashlib, subprocess
from pathlib import Path
ARREL = Path(__file__).resolve().parents[3]
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
M = ARREL / '2-ARXIU/reconstruccio_compactacio_20260915/neteja_20260916/MOVIMENTS_lot10b_resultats_intermedis.jsonl'
V85 = ARREL / '4-RESULTATS/v85_regeneracio_20260922'
DST = ARREL / '4-RESULTATS/v97_refundacio_20260924/entrades'
GRUPS = sys.argv[1:] or ['b2_vixen/', 'b2_sony_A/', 'b2_sony_B/', 'b3_baseline/', 'sources_v29/', 'calibration_VIXEN/', 'calibration_SONYTOT/']
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
fets = []
for l in open(M):
    r = json.loads(l)
    if r.get('event') != 'intent' or 'path' not in r: continue
    p = Path(r['path'])
    try: rel = p.relative_to(V85)
    except ValueError:
        try: rel = Path(str(p).split('/4-RESULTATS/v85_regeneracio_20260922/', 1)[1])
        except IndexError: continue
    if not any(str(rel).startswith(g) for g in GRUPS): continue
    src = Path(r['dest']); dst = DST / rel
    if dst.exists():
        assert dst.stat().st_size == r['bytes'], dst
    else:
        assert src.exists(), f'no és a la Paperera: {src}'
        dst.parent.mkdir(parents=True, exist_ok=True); subprocess.run(['cp', '-c', str(src), str(dst)], check=True)
    h = sha(dst); assert h == r['sha256'], f'SHA no quadra: {rel}'
    fets.append(dict(ruta=str(rel), bytes=r['bytes'], sha256=h, origen='Paperera lot10b (' + str(p.relative_to(ARREL)) + ')'))
    print('OK', rel, flush=True)
prev = json.loads((DST / 'ENTRADES.json').read_text()) if (DST / 'ENTRADES.json').exists() else []
tot = {e['ruta']: e for e in prev}; tot.update({e['ruta']: e for e in fets})
(DST / 'ENTRADES.json').write_text(json.dumps(sorted(tot.values(), key=lambda e: e['ruta']), ensure_ascii=False, indent=1) + '\n')
print(f'{len(fets)} fitxers verificats; {sum(e["bytes"] for e in fets)/1e9:.1f} GB')
