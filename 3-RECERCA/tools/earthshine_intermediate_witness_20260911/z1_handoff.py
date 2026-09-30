"""Record native-operator evidence, preserve V49 and release this writer."""
from intermediate_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import ast,os,subprocess
IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');now=datetime.now(timezone.utc).isoformat();pres=json.loads((OUT/'Z0_preservation.json').read_text());summary=json.loads((OUT/'F0_summary.json').read_text());assert pres['PASS'] and summary['final_crossgreen_numeric_PASS']
def rec(path):
    path=Path(path)
    with path.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(path),bytes=path.stat().st_size,sha256=h)
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
for r in pres['canonical_before']+[pres['claude_status']]:assert rec(r['path'])['sha256']==r['sha256'],r['path']
other=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
    s=line.strip().split(None,1)
    if len(s)==2 and int(s[0]) not in [os.getpid(),os.getppid()] and 'python' in s[1].lower() and 'earthshine_intermediate_witness_20260911/' in s[1] and '.py' in s[1]:other.append(line)
assert not other,other
handoff=ROOT/'.coordination/HANDOFF_2026-09-12_EARTHSHINE_OPERADOR_NATIU_I_ALA_INTERMEDIA.md';assert not handoff.exists();report=OUT/'RESULTAT.md';restart=HERE/'REPRESA.md';manifest=HERE/'delivery_manifest.json'
body=f'''# Handoff — operador natiu i resposta intermèdia — {now}

**V49 vigent i preservada. Operador verificat numèricament; correcció fotogràfica nova encara no qualificada. Goal global actiu.** No s’ha invocat Photoshop ni alterat Camera Raw. Pere autoritza continuar autònomament en passos mesurats. Cap equivalència amb DHS ni recuperació de tot el llimb acreditada.

Informe `{report}`. Represa `{restart}`. Manifest `{manifest}`. Producte `{pres['publication']['path']}`, SHA `{pres['publication']['sha256']}`. Codi a Downloads; actius a Desktop. Sense Git, maquinari, agents nous o generació de textures.

## Resultats que no cal repetir

- p12=0,01406309541811233 es manté congelat. Hipòtesi declarada: component addicional de 4 px. Vuit RAW entrenen, dotze són comprovacions retrospectives, vuit nous per a aquest ajust proven C2/C3: 2960/2962/2964/2966 i 3012/3016/3020/3024. No són dades verges respecte de tot el projecte.
- A0/B0: testimoni aproximat f4=0,0248282; totes les sis èpoques milloren, però dues no superen el 5% predeclarat. A1/B1: cascada física H12(H4(X)), p4=0,0257283; X reté el nucli estret. Meitats 0,0254048/0,0258031. Millores per èpoques 1/4/6/7/C2/C3: 4,26/9,27/8,31/34,15/1,50/12,45%. Gate global FAIL; no promoció.
- **C0 identifica un error numèric:** amb una escena coneguda, aplicar els termes de la correcció a predictors interpolats deixa RMS 5,67/5,74 G al contorn (límit 2 G). Convolucionar directament sobre la graella verda u,v de pas √2, amb sigma/√2, dona RMS≈0,00093 G. Textures conegudes de 8/16/32 px conservades en dues fases. Fantomes només de validació, mai font lunar.
- D0 reconstrueix 28 camps natius complets amb calibració existent. **{summary['exact_native_samples']} mostres** congelades coincideixen exactament en radiància, variància, qualitat, validesa i coordenades; 28 SHA de RAW iguals. Caches `D0_native_field_*.npz` reutilitzables, sense interpolar radiància. No repetir la lectura/calibració.
- D1/E0 controla la predicció del propi soroll: cada verd usa termes òptics de l’altre verd. Dues files per cel·la es mantenen separades fins al score. p4=0,02714295880522035; meitats 0,0260299/0,0276471. Millores 1/4/6/7/C2/C3: 3,26/5,29/5,53/24,46/0,53/7,98%. 71/72 sectors no empitjoren més d’un 2%, però només 4/6 èpoques superen 5%; gate global FAIL. El senyal intermedi no desapareix amb aquest control, però no és suficient per publicar la correcció.
- C1 valida numèricament el verd oposat al p4 anterior. **C2 repeteix al p4 final:** 8/8 PASS, RMS 0,119520/0,149805 G, textures i GL4/GL6 dins dels límits. És qualificació aritmètica, no de la PSF real. Resta de la sèrie E0 ≤0,021906 G; no confondre-la amb error físic.
- F0 és l’informe/figura inspeccionada. Les comparacions interpolat/natiu/crossgreen canvien suport i estadístic: no són una diferència fotogràfica aparellada. Cada percentatge usa el seu propi control zero.

## Continuació concreta

Conservar l’operador natiu i els camps D0. No repetir la correcció intermèdia sobre predictors interpolats. No rebaixar els gates fallats ni barrejar preses llargues sense qualificar amb curtes corregides. Cal resoldre resposta del nucli/ales i completat temporal de les zones censurades abans de construir una nova font o PSB.

Pista física nova F1: el projecte identifica un Vixen VSD90SS; el fabricant declara obertura nominal de 90 mm i focal nominal de 495 mm (`https://www.vixen.co.jp/product/26131_4/`). Provar la difracció de la pupil·la amb l’escala angular **mesurada** de la cadena i un interval espectral declarat pot ser més informatiu que afegir gaussianes lliures. Cal verificar la configuració òptica efectiva; cap Airy s’ha calculat ni aplicat. No ajustar longitud d’ona o geometria per fer desaparèixer el halo dels mateixos targets.

La Lluna conserva radiància desconeguda per cel·la; no forçar-la a zero. Els verds separen fotons però comparteixen calibració/FPN i no substitueixen el jutge entre telescopis. Mantenir els límits de reutilització de dades i de model de llum oculta. No nous retocs manuals del contorn ni modificació de l’estètica de Pere. Una nova font necessita corroboració de textura i, si arriba a PSB, porta Photoshop i recomposició.

Z0 verifica 56 arrays congelats, 28 RAW, originals V46/V47/V48, V49 i 3 XMP. Autoritat preservada abans d’actualitzar. Cap consulta o alteració de documents vius; cap document de treball creat. Tots els càlculs finalitzats. Només aquest registrador tanca el claim amb handoff explícit i zero processos propis de càlcul.
'''
handoff.write_text(body)
entry=f'> **12-09-2026 · V49 vigent; resposta intermèdia i operador natiu.** La correcció sobre predictors interpolats falla la prova numèrica del contorn; el càlcul sobre verds nadius la supera. 28 camps RAW exactes preparats. Component de 4 px contrastada entre verds: 4/6 èpoques superen el gate, encara sense font/PSB nou ni canvi de Camera Raw. Goal actiu. Represa `{handoff}`; informe `{report}`.\n\n'
oldprefix='> **11-09-2026 · V49 vigent; geometria del completat no qualificada.**'
for path in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',ROOT/'research/README.md']:
    text=path.read_text();assert text.startswith(oldprefix),(path,text[:100]);path.write_text(entry+text.split('\n\n',1)[1])
(IA/'Coordinació/HANDOFF_VIGENT.md').write_text(body)
path=IA/'ACTIVE.json';v=json.loads(path.read_text());v['updated']=now;v['phase']='post-eclipse-V49-native-operator-qualified-intermediate-response-incomplete';v['formal_worktree_handoff']=str(handoff);v['paths']['latest_earthshine_diagnostic_manifest']=str(manifest)
v['earthshine_task']=dict(status='V49_PRESERVED; NATIVE_OPERATOR_NUMERICALLY_QUALIFIED; INTERMEDIATE_TEMPORAL_GATE_INCOMPLETE; GLOBAL_GOAL_ACTIVE',completed='Native convolution removes demonstrated predictor-interpolation error;28 exact RAW fields and cross-green control complete;4of6 epoch gates pass, no source promotion',next_action='Use native fields to test independently constrained pupil diffraction at verified angular scale and declared spectrum; retain seeing core and cross-green controls, resolve censored long-exposure model before source/PSB',handoff=str(handoff))
v['earthshine_intermediate_response']=dict(status='DIAGNOSTIC_FINISHED; NO_NEW_PHOTOGRAPHIC_SOURCE',report=str(report),code=str(HERE),manifest=str(manifest),native_fields=str(OUT/'D0_native_fields.json'),crossgreen_fit=str(OUT/'E0_physical_cascade.json'),native_numeric_check=str(OUT/'C2_native_lattice_check.json'),hardware_followup=str(OUT/'F1_optical_followup.json'),p12_frozen=P12,p4_conditional=summary['p4_crossgreen'],native_fields_exact=28,epochs_pass=4,epochs_total=6,no_worse_sectors=71,sectors_total=72,numeric_PASS=True,temporal_PASS=False,new_PSB=False,all_limb_recovery_PASS=False)
write(path,v)
link=IA/'output/earthshine_intermediate_witness_20260911';assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)
for path in HERE.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
assert rec(ROOT/'.coordination/CLAUDE_STATUS.md')['sha256']==pres['claude_status']['sha256']
files=[p for folder in [HERE,OUT] for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
with ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(rec,files))
write(manifest,dict(created=now,status='NATIVE_OPERATOR_PROGRESS; INTERMEDIATE_RESPONSE_INCOMPLETE; V49_PRESERVED; GLOBAL_GOAL_ACTIVE',publication=pres['publication'],files=records,canonical_before=pres['canonical_before'],canonical_after=[rec(r['path']) for r in pres['canonical_before']],handoff=rec(handoff),prior_manifest=pres['prior_manifest'],verified_arrays=pres['verified_arrays'],verified_RAWs=pres['verified_RAWs'],previous_inputs=pres['previous_data'],additional_inputs=pres['additional_inputs'],scope='Native optical-operator validation and cross-green temporal intermediate-response test. Original calibration/pixels preserved; no new photographic source,PSB or CameraRaw modification. Recorder output returned directly.'))
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} — RELEASED — OPERADOR NATIU I RESPOSTA INTERMÈDIA, V49 PRESERVADA\n\nClaim {CLAIM}. Progrés: error numèric de predictors interpolats RMS≈5,7G identificat; operador natiu≈0,00093G i verd oposat final0,120/0,150G, textures de prova preservades.28 camps RAW exactes, {summary["exact_native_samples"]} mostres congelades idèntiques. p4 crossgreen0,027143;4/6èpoques superen5%,71/72sectors no empitjoren2%; no promoció perquè el gate temporal global falla. Pista física següent: pupil·la VSD90SS, escala real i espectre declarats, encara sense Airy calculat.56arrays,28RAW,originals PSB/XMP verificats.\n\nHandoff explícit {handoff}; informe {report}; manifest {manifest}; represa {restart}. Goal actiu. Cap Photoshop invocat ni documents propis; zero processos de càlcul, només aquest registrador acaba ara. Allibero només el meu owner i el directori buit.\n')
claim=ROOT/'.coordination/claim.lock';assert json.loads((claim/'owner.json').read_text())['claim_id']==CLAIM;(claim/'owner.json').unlink();claim.rmdir();print('RELEASED',len(records),'artifacts; native operator validated; temporal gate incomplete;V49 preserved;goal active',flush=True)
