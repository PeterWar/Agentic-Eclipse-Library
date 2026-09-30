from pathlib import Path
import shutil,json,hashlib,datetime
R=Path('/Users/USUARI/Desktop/Eclipse 2026');cid='CODEX_V105_LIMBE_OBSERVAT_20260926'
owner=json.loads((R/'.coordination/claim.lock/owner.json').read_text());assert owner['claim_id']==cid and owner['owner']=='Codex'
D=R/'4-RESULTATS/v105_limbe_20260926/checkpoint_01';C=R/'3-RECERCA/tools/v105_limbe_20260926/checkpoint_01';D.mkdir(exist_ok=False);C.mkdir(exist_ok=False)
roots=['eclipse_v104_diagnosi_20260926','v105_base_sources_20260926','v105_color_pilot_20260926','v105_filter_pilot_20260926','v105_qa_20260926','v105_raw_pilot_20260926','v105_root_pilots_20260926']
manifest=[];skipped=[]
for name in roots:
 for s in sorted((Path('/private/tmp')/name).rglob('*')):
  if not s.is_file():continue
  rel=s.relative_to('/private/tmp')
  if '__pycache__' in s.parts or 'native_probe' in s.parts or s.suffix in ['.psb','.bin']:
   skipped.append({'path':str(rel),'bytes':s.stat().st_size,'reason':'Rebuildable PSB/channel stage or active probe; sourceV104 unchanged, ROI/code retained.'});continue
  before=s.stat();raw=s.read_bytes();digest=hashlib.sha256(raw).hexdigest();after=s.stat()
  if before.st_mtime_ns!=after.st_mtime_ns or before.st_size!=after.st_size:
   skipped.append({'path':str(rel),'reason':'Changed during snapshot; copy in next checkpoint.'});continue
  dst=(C if s.suffix in ['.py','.jsx','.sh'] else D)/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
  assert hashlib.sha256(dst.read_bytes()).hexdigest()==digest
  manifest.append({'source':str(s),'destination':str(dst.relative_to(R)),'bytes':len(raw),'sha256':digest})
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'RESEARCH_IN_PROGRESS_NO_ACCEPTED_V105','claim_id':cid,'source_V104_sha256':'da2b0792db66e91e93a064540feaceafc25ea9cfc6e328d54d3c8980eabc60fa','files':manifest,'excluded':skipped}
(D/'MANIFEST.json').write_text(json.dumps(report,indent=2));(D/'README.md').write_text('Recerca V105 en curs. Cap resultat acceptat ni lliurat.\n\nP01 base nativa: negatiu (714 nous pixels R retallats); E3 P01 negatiu per linia clara. P04 negatiu per TRC i conversio L/G. P05 base: entrada validada, natiu pendent. P06: endpointsG/V corregits; filtres/natiu pendents. Originals i mascares manuals preservats.\n\nAquest checkpoint guarda entrades congelades, codi, imatges i negatius. Els scripts conserven les rutes originals TMP: MANIFEST.json documenta la correspondencia amb aquesta copia. Els PSB provisionals i canals recomprimibles no es dupliquen; es poden reconstruir amb V104 intacta, BASE_ROI i build_stage. No es reclama reconstruccio completa RAW a PSB.\n')
print(json.dumps({'copied':len(manifest),'excluded':len(skipped),'bytes':sum(x['bytes']for x in manifest),'manifest':str(D/'MANIFEST.json')}))
