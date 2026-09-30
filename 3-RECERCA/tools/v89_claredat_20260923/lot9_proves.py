"""lot9 · Manifest de retirada (protocol retira.py de la neteja del 16-09) de les proves A–E de la vora esquerra (23-09-2026, vespre).
Autorització de Pere (23-09, resposta «Retira-les totes (A–E)»): es retiren els PSB de les proves i els seus intermedis (ràsters de filtres,
canals codificats); es queden els rebuts JSON, els MD, els logs, les vistes natives (TIF), les làmines i el codi. La prova A no hi entra mentre
Pere la tingui oberta a Photoshop (s'afegirà en un lot a part quan la tanqui).
Ús: python lot9_proves.py  → 2-ARXIU/reconstruccio_compactacio_20260915/neteja_20260916/lot9_proves_v89_20260923.json"""
import os, sys, json, hashlib, datetime
from pathlib import Path
ARREL = Path(__file__).resolve().parents[3]; NET = ARREL / '2-ARXIU/reconstruccio_compactacio_20260915/neteja_20260916'; P = ARREL / '4-RESULTATS/v89_proves_20260923'
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
fitxers = [P / f'V89_prova_{k}.psb' for k in 'BCDE'] + sorted((P / 'filtres').glob('*.npy')) + sorted((P / 'filtres_finals').glob('*.npy')) + sorted((P / 'canals_psb').glob('*.bin')) \
          + sorted((P / 'C/filtres').glob('*.npy')) + sorted((P / 'C/filtres_finals').glob('*.npy'))
items = []
for f in fitxers:
    st = os.lstat(f); items.append(dict(path=str(f), sha256=sha(f), bytes=st.st_size, dev=st.st_dev, ino=st.st_ino, mtime_ns=st.st_mtime_ns, keeper=None,
        reason="prova de la vora esquerra (23-09) descartada per Pere: només aporta l'opció «claridad»; lliçons a DIAGNOSI.md i PROVES.md, vistes i làmines conservades; regenerable amb 3-RECERCA/tools/v89_proves_20260923",
        regla='proves_v89_vora_esquerra'))
lot = dict(lot='lot9_proves_v89_20260923', created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
           criteri="Proves A–E de la vora esquerra (V89) descartades per Pere el 23-09 vespre («les úniques que aporten alguna cosa és l'opció claridad»; «Retira-les totes (A–E)»). Es retiren PSB i intermedis; es conserven rebuts, MD, logs, vistes natives, làmines i codi. V89_prova_A.psb en queda fora mentre sigui oberta a Photoshop.",
           items=items)
out = NET / 'lot9_proves_v89_20260923.json'; assert not out.exists(); out.write_text(json.dumps(lot, ensure_ascii=False, indent=1) + '\n')
print(json.dumps(dict(fitxers=len(items), GiB=round(sum(i['bytes'] for i in items) / 2**30, 2)), ensure_ascii=False))
