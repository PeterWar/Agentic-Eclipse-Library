"""Freeze measured findings and the new user aesthetic; preserve and release."""
from reveal_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import os,ast
IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA')
now=datetime.now(timezone.utc).isoformat()
prior_path=ROOT/'research/tools/earthshine_diffraction_20260912/delivery_manifest.json'
prior=json.loads(prior_path.read_text())
reference=json.loads((OUT/'A0_reference.json').read_text())
composition=json.loads((OUT/'A2_composition.json').read_text())
boundary=json.loads((OUT/'B3_normalized_result.json').read_text())
detail=json.loads((OUT/'C1_local_detail_result.json').read_text())
def rec(path):
    p=Path(path);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def check(path,expected):
    r=rec(path);assert r['sha256']==expected,(path,r['sha256'],expected);return r
canonical=[]
for i,r in enumerate(prior['canonical_after']):
    copy=HERE/'docs_before'/f'{i}_{Path(r["path"]).name}'
    assert sha(copy)==r['sha256'];canonical.append(check(r['path'],r['sha256']))
oldpres=json.loads((ROOT/'output/earthshine_diffraction_20260912/Z0_preservation.json').read_text())
claude=check(oldpres['claude_status']['path'],oldpres['claude_status']['sha256'])
preserved=[check(SOURCE,reference['sha256']),check(SNAP,reference['sha256']),check(OLD,reference['previous_sha256'])]
plan=json.loads((OUT/'B0_probe_plan.json').read_text())
consumed=[check(plan['original_input'],plan['input_sha256']),check(plan['historical_descriptor'],plan['historical_descriptor_sha256'])]
for p in [ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta/C0_pre_camera_raw_rgb.npy',ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta/C1_camera_raw.psd',ROOT/'output/earthshine_validation_20260911/B1_global_tone_diagnostic.json',ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy']:
    consumed.append(rec(p))
preferences=[check(r['path'],r['sha256']) for r in json.loads((OUT/'B1_preferences_before.json').read_text())['files']]
live=jsx('var r=["ACTIVE|"+app.activeDocument.id+"|"+app.displayDialogs.toString()];for(var i=0;i<app.documents.length;i++){var d=app.documents[i];var f="";try{f=d.fullName.fsName;}catch(e){}r.push(d.id+"|"+d.name+"|"+d.saved+"|"+f);}r.join("\\n");')
assert live==json.loads((OUT/'A1_documents_before.json').read_text())['state']
assert json.loads((OUT/'B2_boundary_result.json').read_text())['historical_replay_max_DN16']==0
assert max(composition['recomposition_max_DN16'],composition['old_recomposition_max_DN16'],composition['delta_prediction_max_DN16'])<3.01
processes=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
    pair=line.strip().split(None,1)
    if len(pair)==2 and int(pair[0]) not in [os.getpid(),os.getppid()] and 'python' in pair[1].lower() and 'earthshine_v49_pere_reveal_20260912/' in pair[1] and '.py' in pair[1]:processes.append(line)
assert not processes,processes
save('Z0_preservation.json',dict(PASS=True,created=now,canonical_before=canonical,claude_status=claude,preserved_references=preserved,consumed_inputs=consumed,preferences=preferences,live_document_state=live,live_document_state_exact=True,new_photographic_version=False,scope='All editing/filter calls operated on own diagnostic documents, closed without changing original document59. Source and reference copies hash-identical. No RAW processing this round. Consumed input hashes recorded; explicit before/after claims only for references, C0 input/descriptor, preferences and authority.'))
handoff=ROOT/'.coordination/HANDOFF_2026-09-12_V49_PERE_REVELAT_I_LLIMB.md'
report=OUT/'RESULTAT.md';restart=HERE/'REPRESA.md';manifest=HERE/'delivery_manifest.json'
assert not handoff.exists() and not report.exists() and not restart.exists() and not manifest.exists()
body=f'''# V49 guardada per Pere: nova referència i diagnòstic del llimb

Actualitzat {now}. Pere ha reprès explícitament el treball després del punt de revisió visible. La nova indicació substitueix l'aturada anterior. Continuació autoritzada en passos acotats, sense confirmació entre proves reversibles. Aquesta ronda fixa la nova estètica i diagnostica; **cap V50 ni correcció nova del llimb**. Objectiu global incomplet.

## Referència vigent

`{SOURCE}` · SHA `{reference['sha256']}` · {reference['bytes']} bytes · 10551×7506 RGB16 · 26 capes. Còpia exacta `{SNAP}`. La V49 anterior de SHA `{reference['previous_sha256']}` es conserva a `{OLD}`; ja no representa l'aspecte que Pere vol preservar.

Pere ha activat `00 Base corba (total) · V42` i ha aclarit la Lluna amb Camera Raw. Els píxels de `V49 · graella verda nativa · Camera Raw de Pere` són ara l'autoritat estètica. La capa V46 de contorn fosc continua oculta. `Compara LROC` i la font G de tots els epochs han quedat ocultes. La màscara i l'alfa de la font V49 són **exactament iguals** a les anteriors; el RGB ha canviat. És capa raster, sense descriptor de filtre intel·ligent: no inferir els ajustos complets del darrer Camera Raw a partir de Previous.xmp o del relat. Els tres XMP s'han preservat.

## Mesures i controls

- **A0–A2, nova aparença:** tres exports natius en el context coronal actual: V49 guardada, sense font lunar i amb la font V49 anterior. La recomposició amb el mateix alfa/màscara explica els canvis amb error màxim <3 DN16. Mediana de pantalla de la cara r<350: 5.580→8.678 DN16; franja r435–449: 9.891→16.706. Són nivells de pantalla, no radiància ni EV. La franja clara arriba majoritàriament amb el RGB de la font lunar, no amb una màscara que Pere hagi alterat. Això no identifica encara la PSF ni distingeix tota la cadena anterior.
- **B0–B3, frontera del filtre:** es canvien 1.292.946 píxels d'entrada amb màscara de sortida EXACTAMENT zero; cap píxel d'entrada visible canvia. Continuació veïna auxiliar, no terreny lunar ni font acceptable. Reproducció del Camera Raw històric: error 0 DN16 contra l'arxiu. La pertorbació enfosqueix la cara uns 4.050 DN16; després d'igualar només la mediana de la cara amb un desplaçament global diagnòstic, la franja −25..−6 canvia −28 DN16 de mediana (−0,30%) i els darrers 3 px −339 DN16 (−1,82%), amb resposta espacial desigual. **No és una cura de la vora; no aplicar el camp auxiliar ni el desplaçament global.** El resultat confirma dependència respecte de píxels amagats, no validesa d'una nova frontera física.
- **C0–C1, Textura/Claredat:** descriptor històric idèntic llevat de 100/40→0/0. Mediana de la cara pràcticament igual (desplaçament diagnòstic −22 DN16). La franja −25..−6 no s'enfosqueix (mediana +140 DN16); els últims 3 px sí (−1.803), però el perfil clar ample persisteix. La desviació del passa-alt sigma2 del centre baixa a {detail['core_highpass_std_ratio']:.3f} de la basal; és contrast fi, barreja de senyal i soroll, no una mesura de detall real perdut. **Desactivar aquests filtres no es promou com a correcció** perquè no resol la banda ampla ni respecta l'estètica.

Els controls B/C fan servir el descriptor històric conegut, no reconstrueixen els filtres nous de Pere. Cap prova demostra recuperació de textura, una PSF identificada, o una correcció robusta sota la recepta nova. Figures de diagnòstic B3/C1 i vistes A2 inspeccionades. La recomanació canònica continua vigent: corregir a l'origen, conservar màscares de validesa i no forçar una vora fosca ni sacrificar protuberàncies.

## Represa acotada

La comparació fotogràfica d'una candidata s'ha de fer amb la cara aclarida i la corona activada **d'aquesta** V49. No tornar silenciosament a V46/V48/V49 antiga ni prendre els XMP com a recepta completa. Cal separar el component de vel ja present abans dels controls locals del component que aquests accentuen. Per a la font física, conservar els camps CFA nadius i estimar la llum solar contaminant per presa/instant abans de combinar; la Lluna comuna no implica corona/protuberàncies ni seeing comuns. Definir primer un control de font amb trens/instants reservats i injecció, abans de fabricar un nou PSB.

No repetir les pistes descartades del handoff anterior: `{prior['handoff']['path']}`. La inversió conjunta és massa sensible a registre/seeing i el perfil solar exterior lineal força un pendent lunar fals. Tampoc sumar automàticament Airy i gaussianes. El llimb complet i les últimes textures encara no estan resolts. Aquesta ronda no reapila RAW ni publica una nova fotografia.

Codi `{HERE}`; evidències `{OUT}`; manifest `{manifest}`. Photoshop conserva el document59 Earthshine_V49.psb guardat, actiu, i cap altre document nostre. Originals, nova còpia i XMP verificats; zero processos propis en acabar. Handoff explícit i alliberament del claim.
'''
report.write_text(body);handoff.write_text(body)
restart.write_text(f'''# Represa curta

Pere ha reprès el treball. Nova V49 guardada SHA `{reference['sha256']}`, còpia exacta `{SNAP}`. Preservar la Lluna aclarida i la corona activada. Màscara/alfa V49 exactes; RGB nou. No es coneix tota la seqüència del Camera Raw rasteritzat.

Llegir `{handoff}`. A2 localitza la franja en la font (recomposició nativa <3 DN16). B0–B3 demostren resposta als píxels amagats però la cura és aparentment global: descartada. C0–C1 demostren contribució dels filtres als últims píxels; treure'ls no resol el vel ample i redueix contrast fi. Cap correcció promoguda, cap V50. No repetir aquestes proves ni les fallades de difracció/perfils anteriors.

Continuació: causa a la font, llum solar/PSF temporal per presa, controls independents i validació amb l'aspecte actual de Pere. No màscara fosca manual ni rebaixar globalment el seu revelat. Estudi en passos acotats; no cal nova confirmació.
''')
entry=f'> **12-09-2026 · V49 de Pere: nou revelat preservat, diagnòstic a l’origen.** Pere reprèn la feina i aclareix la Lluna amb Camera Raw en el context de corona activada. Nova autoritat estètica V49 SHA `{reference["sha256"]}`; màscara/alfa exactes, RGB nou. A2 localitza la franja en la font; controls de píxels amagats i Textura/Claredat no donen una cura acceptable. Cap V50 ni nova màscara. Continuació autoritzada en passos acotats; preservar aquesta aparença. Represa `{handoff}`; informe `{report}`.\n\n'
prefix='> **12-09-2026 · Revisió V48/V49 oberta; aturada demanada per Pere.**'
for path in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',ROOT/'research/README.md']:
    value=path.read_text();assert value.startswith(prefix);path.write_text(entry+value.split('\n\n',1)[1])
(IA/'Coordinació/HANDOFF_VIGENT.md').write_text(body)
path=IA/'ACTIVE.json';v=json.loads(path.read_text());v['updated']=now;v['phase']='post-eclipse-V49-Pere-new-reveal-source-diagnosis';v['formal_worktree_handoff']=str(handoff)
v['paths']['latest_earthshine_diagnostic_manifest']=str(manifest)
v['paths']['current_earthshine_manifest']=str(manifest)
v['paths']['current_earthshine_visual_output']=str(OUT)
v['previous_earthshine_product_V49_before_Pere_reveal']=v['current_earthshine_product']
v['previous_earthshine_user_reference_V46']=v['current_earthshine_user_reference']
v['current_earthshine_product']=dict(path=str(SOURCE),sha256=reference['sha256'],bytes=reference['bytes'],version=49,layers=26,canvas=[10551,7506],depth=16,photoshop=True,pixel_readback_max_DN16=composition['delta_prediction_max_DN16'],PASS=True,PASS_scope='Saved user reference preserved; native layer-ablation recomposition within 3 DN16, exact inherited mask/alpha. No new source-quality or all-limb scientific claim.',scientific_all_limb_PASS=False,scope='User-saved V49 with enabled corona and baked brighter Camera Raw lunar RGB. New photographic aesthetic authority; no new assistant correction.',report=str(report),handoff=str(handoff),code=str(HERE))
v['current_earthshine_user_reference']=dict(path=str(SOURCE),sha256=reference['sha256'],snapshot=str(SNAP),scope='Preserve actual brighter saved RGB, enabled corona, lunar texture and prominences. Exact latest CR sequence unknown; do not substitute historical settings.',report=str(report))
v['earthshine_task']=dict(status='USER_RESUMED; NEW_V49_AESTHETIC_FROZEN; BOUNDED_DIAGNOSIS_COMPLETE; LIMB_UNRESOLVED',completed='Preserved new saved V49; exact layer ablations, invisible-input boundary probe and historical Texture/Clarity control. No accepted correction.',next_action='Source contamination model per capture with independent reserved data; compare photographic candidate against new user V49. No confirmation needed for bounded reversible work.',handoff=str(handoff))
v['earthshine_v49_pere_reveal']=dict(report=str(report),manifest=str(manifest),snapshot=str(SNAP),mask_alpha_exact=True,historical_CR_replay_max_DN16=0,boundary_correction_accepted=False,local_detail_disabled_accepted=False,new_PSB_version=False,all_limb_recovery_PASS=False)
path.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
link=IA/'output/earthshine_v49_pere_reveal_20260912';assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
assert sha(claude['path'])==claude['sha256']
files=[p for folder in [HERE,OUT] for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
with ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(rec,files))
manifest.write_text(json.dumps(dict(created=now,status='NEW_USER_AESTHETIC_PRESERVED; DIAGNOSTIC_ONLY; LIMB_UNRESOLVED',publication=preserved[0],snapshot=preserved[1],files=records,canonical_before=canonical,canonical_after=[rec(r['path']) for r in canonical],handoff=rec(handoff),prior_manifest=rec(prior_path),preserved_references=preserved,consumed_inputs=consumed,preferences=preferences,claude_status=claude,live_document_state=live,scope='User resumed work. No new photographic correction; all comparisons use copies. Historical CR controls do not reconstruct newest baked filters. All own native documents closed.'),ensure_ascii=False,indent=2)+'\n')
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:
    f.write(f'\n\n## {now} — RELEASED — V49 DE PERE PRESERVADA I DIAGNÒSTIC ACOTAT\n\nClaim {CLAIM}. Nova V49 {reference["sha256"]}, RGB aclarit de Pere i corona activada; nova còpia exacta. Màscara/alfa exactes. A2 recomposició <3DN16. B2 CR històric replay 0DN16, frontera auxiliar descartada com cura; C1 Textura/Claredat accentuen darrers píxels però treure-les no resol banda ampla i baixa contrast fi a 0,453. Cap correcció, V50 ni RAW reapilat. Document59 actiu/guardat i tres XMP intactes.\n\nPere ha reprès explícitament; l’aturada anterior queda substituïda. Continuació autoritzada acotada, font física/temporal i comparació amb nou revelat; objectiu global incomplet. Handoff {handoff}; manifest {manifest}. Zero processos propis i documents temporals. Allibero només el meu owner i el directori buit.\n')
claim=ROOT/'.coordination/claim.lock';assert json.loads((claim/'owner.json').read_text())['claim_id']==CLAIM
(claim/'owner.json').unlink();claim.rmdir()
print('RELEASED',len(records),'artifacts; new V49 preserved; no new correction',flush=True)
