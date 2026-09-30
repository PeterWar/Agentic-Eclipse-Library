from pathlib import Path
import json,hashlib,datetime,os,re
R=Path.cwd();T=R/'research/tools/v63_encaix_contorn_20260913';O=R/'output/v63_encaix_contorn_20260913';P=R/'output/v62_prominencies_20260913';IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA')
def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write_new(p,x):
    assert not p.exists(),p;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V63_INNER_ALIGNMENT_LUNAR_CONTOUR_20260913'
pub=json.loads((O/'E0_publish.json').read_text());qa=json.loads((O/'D1_integrity.json').read_text());rb=json.loads((O/'E3_final_readback.json').read_text());fg=json.loads((O/'C1_foreground_checks.json').read_text())
originals=json.loads((O/'E4_external_originals.json').read_text());assert all(x['exact'] for x in originals)
gate=(O/'E1_photoshop_gate.txt').read_text().strip();reader=(O/'E1_second_reader.txt').read_text().strip();opened=(O/'E2_final_open.log').read_text()
assert qa['PASS'] and rb['PASS'] and fg['PASS'] and gate.startswith('OBRE ') and '10551x7506' in reader
assert 'FINAL_OPEN_COMPLETE' in opened and 'saved=true' in opened and 'interiors above Moon=true' in opened
now=datetime.datetime.now(datetime.timezone.utc).isoformat();handoff=R/'.coordination/HANDOFF_2026-09-13_CODEX_CAPES_TOTALS_V63.md';report=O/'RESULTAT.md';manifest=T/'delivery_manifest.json'
ui=dict(time=now,verified=False,native_document_state_confirmed=True,native_evidence=str(O/'E2_final_open.log'),native_full_canvas_readback=str(O/'E3_final_readback.json'),CUA_result='The Mac is locked and automatic unlock could not unlock it. Ask the user to unlock the Mac manually before continuing.',visual_QA='All ten marked sectors, 360-degree limb and full canvas reviewed from native TIFF exports.',scope='Auxiliary foreground-window screenshot unavailable; no successful screenshot claimed.')
write_new(O/'E4_UI.json',ui)
body=(T/'RESULTAT_template.md').read_text()
fields=dict(PRODUCT=pub['path'],SHA=pub['sha256'],BYTES=str(pub['bytes']),CHECKS=str(len(qa['channel_checks'])),GATE=gate,READER=reader,READBACK=str(rb['max_DN16']),EXTERIOR=str(rb['outside_lunar_ROI_RGB_max_DN16']),UI='CUA no ha pogut observar la finestra perquè el Mac estava bloquejat. Reobertura i estat desat confirmats per Photoshop; cap captura GUI reeixida declarada')
for k,v in fields.items():body=body.replace('@'+k+'@',v)
assert not re.search(r'@[A-Z]+@',body)
for p in [report,handoff]:assert not p.exists(),p;p.write_text(body)
status='V63_COMPOSITING_AND_LUNAR_COVERAGE_DELIVERED_FINE_TRANSITION_AND_ABSOLUTE_REGISTRATION_NOT_FULLY_RESOLVED'
m={**pub,'canvas':[10551,7506],'depth':16,'profile':'Adobe RGB (1998)','report':str(report),'handoff':str(handoff),'manifest':str(manifest),'qa':str(O/'D1_integrity.json'),'readback':rb,'open_document':opened,'UI_observation':ui,'artifact_free':False,'status':status,'top_level_items':24,'embedded_editable_original_interiors':7,'embedded_correction_layers':1,'source_V62':json.loads((O/'A0_input.json').read_text()),'Pere_accepted_V62_colour_preserved_exact':True,'original_RGB_exact':True,'original_source_alpha_exact':True,'source_transform_exact':qa['source_transform'],'root_user_selection_exact':True,'lunar_mask_restored_pixels':347,'remaining_Pere_lunar_mask_edits_preserved':3286,'base_mask_validity_pixels':1895,'foreground_above_Moon':True,'foreground_validation':fg,'external_originals':originals,'limits':['Fine limb transition remains visible in some sectors','No new absolute astronomical registration or new scale/rotation demonstrated','Photographic opacity/support correction is not a new physical radiance or resolution estimate','Native CUA window screenshot unavailable because Mac locked'],'preview':str(O/'vistes/V63_full_canvas.png'),'visual_review':str(T/'D2_VISUAL_REVIEW.md')}
write_new(manifest,m)
prefix=f'> **13-09-2026 · Capes Totals V63: encaix fotogràfic i cobertura del contorn revisats.** Pere ha acceptat el color V62 sense reflex vermell; RGB exacte. Interiors 06–12 sobre Earthshine: evita retallar de nou perles i peu superior; selecció i matriu exactes, set originals + Divide intactes. Validesa del denominador C2 corregeix opacitat falsa al fons lunar; 1.411.784 píxels de primer pla natiu, RGBA 0 DN16. Retirada protecció antiga ampla dels sis filtres només dins la selecció de Pere; base amb RGB vàlid i 347 forats de màscara lunar restaurats (altres 3.286 edicions exactes). Transparència lunar 1.465→0. {len(qa["channel_checks"])} comprovacions; Photoshop 24 capes, readback complet {rb["max_DN16"]} DN16. Franja blanca oest i pedestal superior reduïts; transició fina residual i registre astronòmic absolut NO declarats resolts. Producte `{pub["path"]}`, SHA `{pub["sha256"]}`. Represa `{handoff}`; informe `{report}`. No restaurar capes suprimides per Pere ni exigir nova tria de mescla. Les entrades següents són història.\n\n'
history={r['path']:r['after_sha256'] for r in json.loads((P/'E5_authorities.json').read_text())['rows']}
paths=[R/'AGENTS.md',R/'CLAUDE.md',IA/'README.md',IA/'ESTAT_ACTUAL.md',IA/'MAPA_RUTES_I_OUTPUTS.md',IA/'Coordinació/HANDOFF_VIGENT.md',IA/'ACTIVE.json']
old_bytes={str(p):p.read_bytes() for p in paths}
for p in paths:assert hashlib.sha256(old_bytes[str(p)]).hexdigest()==history[str(p)],p
(O/'receipts').mkdir(exist_ok=True);receipts=[]
for i,p in enumerate(paths[:-1]):
    old=old_bytes[str(p)];snap=O/'receipts'/f'E5_before_{i}_{p.name}';assert not snap.exists();snap.write_bytes(old)
    tmp=p.with_name(p.name+'.V63.tmp');assert not tmp.exists();tmp.write_bytes(prefix.encode()+old);assert p.read_bytes()==old;os.replace(tmp,p)
    receipts.append(dict(path=str(p),snapshot=str(snap),before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=sha(p),old_content_exact_suffix=p.read_bytes().endswith(old)))
p=paths[-1];old=old_bytes[str(p)];snap=O/'receipts/E5_before_ACTIVE.json';assert not snap.exists();snap.write_bytes(old);a=json.loads(old)
earth_keys=[k for k in a if 'earthshine' in k and k!='general_earthshine_mask_override'];earth={k:json.dumps(a[k],sort_keys=True) for k in earth_keys}
a['previous_general_product_V62_delivery']=a['current_product'];a['previous_general_product_V62_Pere_acceptance']=dict(colour='Pere explicitly confirmed that the diffuse red reflection disappeared successfully.',remaining='Beads, top prominence and whole lunar contour requested.')
a['current_product']=m;a['updated']=now;a['phase']='post-eclipse-general-V63-compositing-lunar-coverage-fine-transition-pending';a['formal_worktree_handoff']=str(handoff)
a['paths']['current_technical_editable']=pub['path'];a['paths']['current_delivery_manifest']=str(manifest);a['paths']['current_visual_output']=str(O/'vistes')
a['general_integration_task']=dict(status=status,handoff=str(handoff),report=str(report),pending='Pere visual judgement of V63; fine residual transition and absolute temporal/astronomical registration remain qualified. No additional blend choice required.')
a['historical_visual_task_before_V63']=a['visual_task'];a['visual_task']=dict(status=status,target=pub['path'],next_action='Review V63 beads/top/whole limb; any further investigation should address source support and temporal compatibility before changing geometry. Preserve accepted V62 colour and original source layers.')
a['general_earthshine_mask_override']=dict(product=pub['path'],method='Restore only 347 pixels opened by user mask edits where no coronal RGB exists; previous mask was opaque there. Other 3286 edits unchanged.',independent_Earthshine_V56_unchanged=True)
assert all(json.dumps(a[k],sort_keys=True)==v for k,v in earth.items())
tmp=p.with_name(p.name+'.V63.tmp');assert not tmp.exists();tmp.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');assert p.read_bytes()==old;os.replace(tmp,p)
receipts.append(dict(path=str(p),snapshot=str(snap),before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=sha(p)))
write_new(O/'E5_authorities.json',dict(time=now,rows=receipts,CLAUDE_STATUS_untouched=True,independent_earthshine_authority_unchanged=True))
with (R/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n## {now} · V63 COMPOSITING CORRECTIONS DELIVERED · CLAIM HELD\nV62 color accepted by Pere exact; original sources and transform exact. Foreground over Moon with valid C2 support; old broad filter protection removed only within user selection; duplicate/missing limb coverage repaired. Native foreground 0 DN16 on 1,411,784 samples; opacity defects 1465 to zero. 18 old proxy outliers in dark background explicitly qualified. {len(qa["channel_checks"])} channel checks; Photoshop OBRE24; full readback {rb["max_DN16"]} DN16. Fine transition and absolute registration remain qualified; no global artifact-free claim. Product {pub["path"]}. Handoff {handoff}.\n')
print('DOCUMENTED',handoff,flush=True)
