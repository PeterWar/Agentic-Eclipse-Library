from pathlib import Path
import json,hashlib,datetime,os
R=Path.cwd();T=R/'research/tools/v62_prominencies_20260913';O=R/'output/v62_prominencies_20260913';IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA')
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write_new(p,x):
 assert not p.exists(),p;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V62_V61_PROMINENCES_20260913'
pub=json.loads((O/'E1_publish.json').read_text());qa=json.loads((O/'E0_integrity.json').read_text());rb=json.loads((O/'E3_final_readback.json').read_text());ui=json.loads((O/'E4_UI.json').read_text())
gate=(O/'E1_photoshop_gate.txt').read_text().strip();reader=(O/'E1_second_reader.txt').read_text().strip();opened=(O/'E2_final_open.log').read_text()
assert qa['PASS'] and rb['PASS'] and ui['native_document_state_confirmed'] and gate.startswith('OBRE ') and '10551x7506' in reader
assert 'FINAL_OPEN_COMPLETE' in opened and 'saved=true' in opened
now=datetime.datetime.now(datetime.timezone.utc).isoformat();handoff=R/'.coordination/HANDOFF_2026-09-13_CODEX_CAPES_TOTALS_V62.md';report=O/'RESULTAT.md';manifest=T/'delivery_manifest.json'
body=(T/'RESULTAT_template.md').read_text()
for k,v in dict(PRODUCT=pub['path'],SHA=pub['sha256'],BYTES=str(pub['bytes']),CHECKS=str(len(qa['channel_checks'])),GATE=gate,READER=reader,READBACK=str(rb['max_DN16'])).items():body=body.replace('@'+k+'@',v)
assert '@PRODUCT@' not in body
for p in [report,handoff]:assert not p.exists(),p;p.write_text(body)
m={**pub,'canvas':[10551,7506],'depth':16,'profile':'Adobe RGB (1998)','report':str(report),'handoff':str(handoff),'manifest':str(manifest),'qa':str(O/'E0_integrity.json'),'readback':rb,'open_document':opened,'UI_observation':ui,'artifact_free':False,'status':'V62_COLOUR_AND_PROMINENCE_COMPOSITING_DELIVERED_FINE_LIMB_NW_PENDING','top_level_items':24,'embedded_editable_original_interiors':7,'embedded_added_correction_layers':1,'source_Pere_V61':json.loads((O/'A0_sources.json').read_text())['sha256'],'source_Pere_Moon_mask_exact':True,'geometry_exact_to_Pere_V61':True,'colour_external_validation':json.loads((O/'C1_colour_validation.json').read_text()),'limits':['Fine blue contour not completely corrected','NW local alignment remains unvalidated','Photographic black-matte separation is not a new physical radiance estimate','No new astronomical resolution claim','CUA window observation unavailable because Mac was locked; native Photoshop readback verified'],'preview':str(O/'vistes/V62_full.png')}
write_new(manifest,m)
prefix=f'> **13-09-2026 · Capes Totals V62: vermell ample i pedestal negre corregits; filet fi/NW pendents.** Font: V61 simplificada per Pere, 24 capes, SHA 63d4c0dc…; supressions i màscara lunar de Pere exactes. El gaussià de color sigma 24 escampava el vermell sobre la corona: correcció de l\'estimador, luminància de pantalla preservada, Sony reservada millora els errors R/B als dos costats. Interiors visibles segons la màscara de Pere, pedestal uniforme de selecció normalitzat; set originals editables exactes + divisor i màscara de grup. Recomposició nativa de la fotografia sobre negre 0 DN16; matriu V61 exacta, cap nou gir/escala. Pedestal angular superior retirat, però filet clar fi i discrepància local NW NO resolts. 150 comprovacions de canals; Photoshop 24 capes, reobertura de tot el llenç {rb["max_DN16"]} DN16. Producte `{pub["path"]}`, SHA `{pub["sha256"]}`. Represa `{handoff}`; informe `{report}`. Cap tria de mescla pendent: Pere ja l\'ha indicada. Les entrades següents són història.\n\n'
history={r['path']:r['after_sha256'] for r in json.loads((R/'output/v61_interiors_limbe_20260913/E3_authorities.json').read_text())['rows']}
paths=[R/'AGENTS.md',R/'CLAUDE.md',IA/'README.md',IA/'ESTAT_ACTUAL.md',IA/'MAPA_RUTES_I_OUTPUTS.md',IA/'Coordinació/HANDOFF_VIGENT.md',IA/'ACTIVE.json']
# Validate every authority before beginning the first write.
old_bytes={str(p):p.read_bytes() for p in paths}
for p in paths:assert hashlib.sha256(old_bytes[str(p)]).hexdigest()==history[str(p)],p
(O/'receipts').mkdir(exist_ok=True);receipts=[]
for i,p in enumerate(paths[:-1]):
 old=old_bytes[str(p)];snap=O/'receipts'/f'E5_before_{i}_{p.name}';assert not snap.exists();snap.write_bytes(old)
 tmp=p.with_name(p.name+'.V62.tmp');assert not tmp.exists();tmp.write_bytes(prefix.encode()+old);assert p.read_bytes()==old;os.replace(tmp,p)
 receipts.append(dict(path=str(p),snapshot=str(snap),before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=sha(p),old_content_exact_suffix=p.read_bytes().endswith(old)))
p=paths[-1];old=old_bytes[str(p)];snap=O/'receipts/E5_before_ACTIVE.json';assert not snap.exists();snap.write_bytes(old);a=json.loads(old)
earth_keys=[k for k in a if 'earthshine' in k and k!='general_earthshine_mask_override'];earth={k:json.dumps(a[k],sort_keys=True) for k in earth_keys}
a['previous_general_product_V61_delivery']=a['current_product'];a['previous_general_product_V61_Pere']=json.loads((O/'A0_sources.json').read_text())
a['current_product']=m;a['updated']=now;a['phase']='post-eclipse-general-V62-colour-compositing-fine-limb-NW-pending';a['formal_worktree_handoff']=str(handoff)
a['paths']['current_technical_editable']=pub['path'];a['paths']['current_delivery_manifest']=str(manifest);a['paths']['current_visual_output']=str(O/'vistes')
a['general_integration_task']=dict(status=m['status'],handoff=str(handoff),report=str(report),pending='Fine blue contour and NW local discrepancy. Pere already chose the prominence blend with the V61 mask.')
a['historical_visual_task_before_V62']=a['visual_task'];a['visual_task']=dict(status=m['status'],target=pub['path'],next_action='Visual judgement by Pere; source investigation of the residual fine limb and NW temporal/photometric discrepancy. No additional user blend choice required.')
assert all(json.dumps(a[k],sort_keys=True)==v for k,v in earth.items())
tmp=p.with_name(p.name+'.V62.tmp');assert not tmp.exists();tmp.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');assert p.read_bytes()==old;os.replace(tmp,p)
receipts.append(dict(path=str(p),snapshot=str(snap),before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=sha(p)))
write_new(O/'E5_authorities.json',dict(time=now,rows=receipts,CLAUDE_STATUS_untouched=True,independent_earthshine_authority_unchanged=True))
with (R/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n## {now} · V62 PARTIAL CORRECTIONS DELIVERED · CLAIM HELD\nV61 de Pere (24 capes) exacta preservada. Color q24 corregit amb Sony reservada; selecció de Pere aplicada a les interiors, set originals exactes, recomposició sobre negre 0 DN16 i matriu exacta. Filet fi i NW encara oberts; no absència global d\'artefactes. Photoshop OBRE; 150 canals; readback complet {rb["max_DN16"]} DN16. Producte {pub["path"]}. Handoff {handoff}.\n')
print('DOCUMENTED',handoff,flush=True)
