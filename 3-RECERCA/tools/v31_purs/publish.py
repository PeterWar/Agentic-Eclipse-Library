"""Publish the verified comparison under a new name, preserving open unsaved originals."""
from common import *
import shutil,datetime
CT=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA')
FINAL=CT/'V31_FiltresPurs.psb';BACKUP=CT/'V31_abans_filtres_purs_20260906.psb'
PUBLISHED_VIEWS=IA/'output/v31_purs_20260906'
HANDOFF=ROOT/'.coordination/HANDOFF_2026-09-06_V31_FILTRES_PURS.md'
REPORT=ROOT/'research/142_V31_FILTRES_PURS_20260906.md'
MANIFEST=D/'delivery_manifest.json'
EXPECTED='bbbb2b93a49a0e09226b89467754f6364d1c6b929bc147bd34387a1c66d7affe'
def exclusive_copy(src,dst):
 assert not dst.exists(),str(dst)
 with open(src,'rb') as f,open(dst,'xb') as g:shutil.copyfileobj(f,g,8<<20)
 shutil.copystat(src,dst)
def atomic_text(p,s):
 q=p.with_name(p.name+'.codex_v31_tmp');assert not q.exists();q.write_text(s);os.replace(q,p)
def main():
 claim=json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text());assert claim['claim_id']=='CODEX_V31_FILTRES_PURS_20260906' and claim['owner']=='Codex'
 verify=json.loads((D/'receipts/psb_verification.json').read_text());gate=json.loads((D/'receipts/photoshop_gate.json').read_text());assert verify['PASS'] and gate['result']=='OBRE 10551 px x 7506 px · 40 capes' and gate['restored']
 assert json.loads((D/'receipts/injection.json').read_text())['PASS_positive_matched_response']
 assert sha(CT/'V31.psb')==EXPECTED and sha(D/'sources/V31_abans.psb')==EXPECTED
 assert sha(D/'staging/V31.psb')==verify['sha256']
 before=[ROOT/'AGENTS.md',ROOT/'CLAUDE.md',ROOT/'research/README.md',IA/'ACTIVE.json',IA/'README.md',IA/'ESTAT_ACTUAL.md',IA/'MAPA_RUTES_I_OUTPUTS.md',IA/'Coordinació/HANDOFF_VIGENT.md']
 snaps=[]
 for p in before:
  dst=D/'docs_before'/('IA_'+p.name if p.is_relative_to(IA) else 'ROOT_'+p.name)
  assert p.is_file() and not p.is_symlink();exclusive_copy(p,dst);snaps.append({'original':str(p),'snapshot':str(dst),'sha256':sha(dst)})
 exclusive_copy(CT/'V31.psb',BACKUP);assert sha(BACKUP)==EXPECTED
 temp=CT/'V31_FiltresPurs_20260906_verificat.tmp.psb';exclusive_copy(D/'staging/V31.psb',temp);assert sha(temp)==verify['sha256'];assert not FINAL.exists();os.rename(temp,FINAL)
 assert sha(CT/'V31.psb')==EXPECTED
 shutil.copytree(OUT,PUBLISHED_VIEWS,dirs_exist_ok=False)
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 manifest={'version':'V31_FiltresPurs','published_utc':now,'path':str(FINAL),'sha256':verify['sha256'],'bytes':verify['bytes'],'size':[W,H],'depth':16,'layers':40,'container_PASS':True,'scientific_status':'VERIFIED_COMPARISON_WITH_VISIBLE_LIMITATIONS','artifact_free':False,'preserved_original_path':str(CT/'V31.psb'),'preserved_original_sha256':EXPECTED,'backup':{'path':str(BACKUP),'sha256':EXPECTED,'scope':'saved disk version; not the unsaved Photoshop changes'},'filename_reason':'Photoshop V31.psb was open with saved=false; publish under new name to protect user work','original_layers_preserved_exactly':30,'new_independent_views':10,'default':'all new views OFF; original30 visibility and merged pixels unchanged','source':'corrected linear G, global Sony-to-Vixen gain0.3411462604999542','FOV':'unchanged native10551x7506','RAW_recalibration':False,'photoshop_gate':gate,'output':str(PUBLISHED_VIEWS),'report':str(REPORT),'handoff':str(HANDOFF),'receipts':str(D/'receipts'),'source_code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in D.glob('*') if p.suffix in ['.py','.cpp']},'documentation_snapshots':snaps,'limits':['No guarantee of all solar arcs eliminated; visible limitations documented.','Pure filters use intrinsic published operations plus declared numerical boundary handling; no added H1/tanh/external high-pass/denoise/circular fade.','FNRGF domain-only array, missing angular sectors not invented.','NAFE-VN and RLMF deferred for unverifiable specifications; SiRGraF lacks required temporal input; full Corona ACHF not reproduced.','G monochrome scientific views; pure float arrays retained before display LUT.']}
 savejson(MANIFEST,manifest)
 guide=f'''# V31 — filtres independents

[Obrir V31_FiltresPurs.psb](<{FINAL}>)

40 capes, RGB16, 10551 × 7506. Les 30 originals són intactes. Les 10 noves estan apagades: activa **una sola capa P01–P09 o C01** per comparar. Són Normal al 100%; no cal combinar-les amb els filtres anteriors. Les vistes noves són monocromes, calculades del mateix canal G lineal corregit.

P01 NRGF; P02 RHEF; P03 MGN; P04 WOW; P05 WOW bilateral; P06 NAFE; P07/P08 precursor ACHF16/32; P09 SWAP com a pilot. C01 és un nou passa-alt lineal de control. El passa-alt i els tangencials clàssics anteriors es conserven exactament.

**No tots donen una corona neta.** RHEF pot crear anells; NRGF/RHEF encara mostren arcs exteriors; MGN/WOW/NAFE amplifiquen soroll; el precursor ACHF respon fortament al limbe i mostra poc detall exterior amb aquesta escala global. Aquestes limitacions no s'han amagat amb retalls circulars ni suavitzats.

FNRGF no es força al PSB: en part del camp falten sectors angulars necessaris. NAFE-VN/RLMF no tenen encara una especificació reproduïble verificada; SiRGraF necessita dades temporals que no tenim. [Inventari, fonts i proves](<{REPORT}>).

Photoshop ha obert les 40 capes. Píxels, màscares, geometria i recursos comprovats; l'avaluació visual final continua oberta. SHA-256: `{verify['sha256']}`.

La V31 anterior estava oberta amb canvis sense desar. S'ha preservat el seu fitxer i el document obert; per això la nova porta el nom V31_FiltresPurs.psb. [Backup del V31 desat](<{BACKUP}>).

[Manifest i rebuts](<{MANIFEST}>). Vistes completes: P*_full.png; comparacions a mida nativa: QA_100_1/2/3.png. Els resultats científics float32, abans de la LUT de pantalla, són a `{C}`.
'''
 (OUT/'LLEGEIX-ME.md').write_text(guide);(PUBLISHED_VIEWS/'LLEGEIX-ME.md').write_text(guide)
 summary=f'''V31 comparativa de filtres independents és el lliurable actual: `{FINAL}`.
10551 × 7506, RGB16, 40 capes; {verify['bytes']:,} bytes.
SHA-256 `{verify['sha256']}`.

Les 30 capes anteriors i el compost inicial són exactes; s'afegeixen 10 vistes Normal100%, apagades. Base comuna G corregida i match global Sony→Vixen0,3411462604999542. NRGF, RHEF, MGN, WOW/bilateral, NAFE, precursor ACHF16/32, SWAP pilot i control passa-alt. Cap H1/tanh/suavitzat extern ni retall circular als mètodes nous; operacions intrínseques i discretització documentades.

És una comparació amb limitacions visibles, no una correcció certificada de tots els arcs. RHEF pot crear bandes; hi ha arcs de la base, soroll exterior i resposta forta d'ACHF al limbe. FNRGF queda com a array de domini vàlid; no s'inventen sectors. Inventari i exclusions justificats a `{REPORT}`.

Photoshop real: {gate['result']}. Les 30 capes originals i tots els nous RGB/màscares verificats. Els documents V31.psb/V30.psb estaven oberts amb canvis sense desar i no s'han substituït. Backup de disc: `{BACKUP}`.

Handoff: `{HANDOFF}`. Manifest: `{MANIFEST}`. Guia i vistes: `{PUBLISHED_VIEWS}`. No hi ha tasca automàtica nova; l'avaluació visual de Pere resta oberta.
'''
 handoff='# Handoff vigent — V31 filtres independents — 06-09-2026\n\n'+summary+'\nRepresa: AGENTS.md, bloc inicial de CLAUDE.md, IA/ACTIVE.json i research/142. Les peticions actuals autoritzen la comparació independent; no universalitzar H1 o altres components de la cadena fotogràfica sobre els filtres purs. Les retallades circulars probablement fan més mal que bé. No assumir que un PASS numèric o Photoshop elimina artefactes visuals.\n'
 HANDOFF.write_text(handoff);atomic_text(IA/'Coordinació/HANDOFF_VIGENT.md',handoff)
 old=(IA/'ESTAT_ACTUAL.md').read_text();atomic_text(IA/'ESTAT_ACTUAL.md','# Estat actual — V31 comparativa\n\n'+summary+'\n## Històric 05-09-2026\n\n'+old)
 for p in [IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md']:
  old=p.read_text();block='# Actualització vigent 06-09-2026 — V31 comparativa\n\n'+summary+'\nLes referències a la V31 del05-09 més avall són històriques. Les normes generals i rutes de RAW continuen vigents.\n\n---\n\n';atomic_text(p,block+old)
 active=json.loads((IA/'ACTIVE.json').read_text());previous=active['current_product']
 active.update(updated=now,phase='post-eclipse-V31-pure-filter-comparison',formal_worktree_handoff=str(HANDOFF))
 active['paths'].update(current_technical_editable=str(FINAL),current_delivery_manifest=str(MANIFEST),current_visual_output=str(PUBLISHED_VIEWS))
 active['current_product']={'path':str(FINAL),'sha256':verify['sha256'],'bytes':verify['bytes'],'size':[W,H],'depth':16,'layers':40,'published_utc':now,'PASS':True,'PASS_scope':'container and implementation checks, not artifact-free visual enhancement','artifact_free':False,'source':previous,'verification':str(D/'receipts/psb_verification.json'),'photoshop':gate['result'],'visual_acceptance':'comparison delivered with visible limitations; Pere judgement pending','preservation':'all30 prior layer records/pixels/masks/visibility exact; ten independent hidden Normal100 views added','limitations':manifest['limits'],'manifest':str(MANIFEST)}
 active['processing_authority'].update(type='independent-scientific-filter-comparison-plus-preserved-photo',source=manifest['source'],fov_status='same10551x7506',raw_calibration_reexecuted=False)
 active['visual_task']={'status':'DELIVERED_COMPARISON_WITH_LIMITATIONS','target':str(FINAL),'original30':'unchanged including classic controls','new10':'independent Normal100 views OFF','next_action':'No automatic task; follow-up requires current authority and a new claim'}
 active['history']={'previous_active_snapshot':str(D/'docs_before/IA_ACTIVE.json'),'previous_active_sha256':sha(D/'docs_before/IA_ACTIVE.json'),'meaning':'previous V31 and open unsaved documents preserved; this V31 comparison published under a new filename'}
 atomic_text(IA/'ACTIVE.json',json.dumps(active,ensure_ascii=False,indent=2)+'\n')
 p=ROOT/'CLAUDE.md';old=p.read_text();old=old.replace('Última actualització efectiva: 05 de setembre de 2026 (V31).','Última actualització efectiva: 06 de setembre de 2026 (V31 comparativa).',1);needle='## 1. Punt de represa\n\n';assert needle in old;old=old.replace(needle,needle+summary+'\n### Història de la V31 anterior (05-09-2026)\n\n',1);atomic_text(p,old)
 p=ROOT/'AGENTS.md';old=p.read_text();old=old.replace('.coordination/HANDOFF_2026-09-05_V31.md','.coordination/HANDOFF_2026-09-06_V31_FILTRES_PURS.md',1);start=old.index('** (V31:');end=old.index('Els handoffs anteriors',start);old=old[:start]+'** (V31 comparativa: 30 capes originals intactes + 10 vistes independents, sense mescles; limitacions visuals declarades; nou nom per preservar la V31 oberta sense desar). '+old[end:];old=old.replace('bloc inicial deCLAUDE i research/139','bloc inicial deCLAUDE i research/142',1);atomic_text(p,old)
 p=ROOT/'research/README.md';old=p.read_text();atomic_text(p,'- [142 — V31: filtres independents, inventari i límits](142_V31_FILTRES_PURS_20260906.md) — 06-09-2026.\n\n'+old)
 with open(ROOT/'.coordination/CODEX_STATUS.md','a') as f:f.write('\n\n## '+now+' — V31_FiltresPurs publicat\n\n'+summary+'\nClaim encara retingut fins a comprovació final i RELEASED.\n')
 # Verify the published artifact and critical authority pointers after all writes.
 assert sha(FINAL)==verify['sha256'] and sha(BACKUP)==EXPECTED and sha(CT/'V31.psb')==EXPECTED
 assert json.loads((IA/'ACTIVE.json').read_text())['current_product']['path']==str(FINAL)
 savejson(D/'receipts/publication.json',{'PASS':True,'final':str(FINAL),'sha256':verify['sha256'],'backup_sha256':EXPECTED,'old_V31_disk_unchanged':True,'open_unsaved_documents_untouched':True,'authority_updated':True,'published_utc':now})
 log('publication and authority verified')
if __name__=='__main__':main()
