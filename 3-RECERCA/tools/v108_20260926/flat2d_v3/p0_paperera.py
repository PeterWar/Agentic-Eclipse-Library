"""p0_paperera (V108, flat2d_v3) · Envia a la Paperera els intermedis PROPIS de la variant flat2d_v3 que ja no calen, amb manifest i SHA-256.
Només accepta camins dins de 4-RESULTATS/v108_20260926/flat2d_v3/ o de 4-RESULTATS/v108_20260926/cadena/flat2d_v3/ (els de la tasca).
Mou (no esborra): ~/.Trash/Eclipse_V108_flat2d_v3_intermedis_20260927/<camí relatiu>. Es recuperen movent-los de tornada.
Manifest (una línia JSON per fitxer: quan, de, a, sha256, bytes, motiu): 4-RESULTATS/v108_20260926/flat2d_v3/MOVIMENTS_PAPERERA_FLAT2D_V3.jsonl
Ús: p0_paperera.py "<motiu>" <camí> [<camí> …]   (els directoris s'hi envien sencers, fitxer a fitxer al manifest)"""
import sys, json, hashlib, shutil, time, os
from pathlib import Path
A = Path(__file__).resolve().parents[4]
PERMES = [A / '4-RESULTATS/v108_20260926/flat2d_v3', A / '4-RESULTATS/v108_20260926/cadena/flat2d_v3']
DEST = Path.home() / '.Trash/Eclipse_V108_flat2d_v3_intermedis_20260927'; MAN = A / '4-RESULTATS/v108_20260926/flat2d_v3/MOVIMENTS_PAPERERA_FLAT2D_V3.jsonl'
motiu = sys.argv[1]; camins = [Path(p) if Path(p).is_absolute() else A / p for p in sys.argv[2:]]
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
tot = 0
for c in camins:
    c = Path(os.path.abspath(c))
    assert any(str(c).startswith(str(q) + '/') or (c == q and q.name == 'flat2d_v3' and q.parent.name == 'cadena') for q in PERMES), f'fora de la carpeta de la tasca: {c}'
    if not c.exists() and not c.is_symlink(): print('no hi és', c); continue
    fitxers = [c] if (c.is_file() or c.is_symlink()) else sorted(p for p in c.rglob('*') if p.is_file() or p.is_symlink())
    desti = DEST / c.relative_to(A / '4-RESULTATS/v108_20260926'); desti.parent.mkdir(parents=True, exist_ok=True)
    if desti.exists(): desti = desti.with_name(desti.name + '_' + time.strftime('%H%M%S'))     # ja n'hi ha un amb el mateix nom a la Paperera: no el trepitgis
    files_rows = []
    for f in fitxers:
        rel = f.relative_to(A); a_ = desti if f == c else desti / f.relative_to(c)
        files_rows.append(dict(quan=time.strftime('%Y-%m-%dT%H:%M:%S'), de=str(rel), a=str(a_), sha256=None if f.is_symlink() else sha(f), bytes=0 if f.is_symlink() else f.stat().st_size,
                               enllac=str(os.readlink(f)) if f.is_symlink() else None, motiu=motiu))
    assert not desti.exists(), f'ja existeix a la Paperera: {desti}'
    shutil.move(str(c), str(desti))
    with open(MAN, 'a') as fm:
        for r in files_rows: fm.write(json.dumps(r, ensure_ascii=False) + '\n')
    b = sum(r['bytes'] for r in files_rows); tot += b; print(f'→ Paperera {c.relative_to(A)} ({len(files_rows)} fitxers, {b/1e9:.2f} GB)', flush=True)
print(f'TOTAL {tot/1e9:.2f} GB · manifest {MAN.relative_to(A)}')
