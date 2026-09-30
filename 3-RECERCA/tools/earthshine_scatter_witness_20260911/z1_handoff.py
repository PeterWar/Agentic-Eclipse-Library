"""Record measured scatter progress and release the single-writer claim."""
from scatter_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import ast,os,subprocess
IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');now=datetime.now(timezone.utc).isoformat();pres=json.loads((OUT/'Z0_preservation.json').read_text());assert pres['PASS']
def rec(path):
    path=Path(path)
    with path.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(path),bytes=path.stat().st_size,sha256=h)
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
for r in pres['canonical_before']+[pres['claude_status']]:assert rec(r['path'])['sha256']==r['sha256'],r['path']
other=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
    s=line.strip().split(None,1)
    if len(s)==2 and int(s[0]) not in [os.getpid(),os.getppid()] and 'python' in s[1].lower() and 'earthshine_scatter_witness_20260911/' in s[1] and '.py' in s[1]:other.append(line)
assert not other,other
handoff=ROOT/'.coordination/HANDOFF_2026-09-11_EARTHSHINE_DISPERSIO_AMPLA.md';assert not handoff.exists();report=OUT/'RESULTAT.md';manifest=HERE/'delivery_manifest.json';restart=HERE/'REPRESA.md'
text=f'''# Handoff — candidat de dispersió ampla — {now}

**V49 vigent i preservada. Candidat òptic positiu; completat de saturació encara no qualificat. No V50. Goal global actiu.** No s’ha invocat Photoshop ni alterat CameraRaw. Pere autoritza continuar autònomament en passos mesurats, sense confirmacions repetides; mantenir l’abast real de recuperar el llimb, no redefinir-lo com un PASS numèric.

Informe `{report}`. Represa exacta `{restart}`. Manifest `{manifest}`. Producte `{pres['publication']['path']}`, SHA `{pres['publication']['sha256']}`. Downloads és codi i Desktop són actius. Sense Git, maquinari, agents nous ni generació de textura artificial.

## Evidència nova que no cal repetir

- A0/B0:8curts de2èpoques entrenen;12curts d’altres4èpoques reservats. Dades natives agregades en cel·les5px només com a estadístic. Nuisance lunar per cel·la i pla per captura; els plans reservats es calibren només a415–423, mentre426–445 és prova. Predictor ampli real positiu, gir90°nul. El coeficient testimoni12px≈0,01404 i24px=0.
- B1: modelY=((1−p)I+pG12)X, amb nucli estret retingut enX; p=0,01406309541811233. És condicional al model, no PSF única. Millores22,76/21,72/31,65/53,25% d’error en les4èpoques i47/48sectors no empitjoren més de2%. No és percentatge de detall recuperat.
- Inversa amb4termes Neumann; resta numèrica<0,000801G. C0injecció8/8PASS en2fases natives:baselineRMS0,539/0,545G, GL4vs6<0,042G, error de textures8/16/32px<0,001%. Fantomes mai incorporats a imatges científiques.
- D0/D1:camp auxiliar55preses exclou12targets;12/36gates. No promogut. La vora observada contaminada no és radiància lunar latent neta; tornar-la a convolucionar pot recomptar llum dispersada. També queden forats de suport solar.
- D2:51preses exclouen16targets;4nous targets2967/2985/2997/3003 amb màscares reals de2978/2980/2983. Lunar auxiliar només nivell profund mesurat; corona auxiliar continuada suaument com a màxim8px des de dades.100%suport i24/36PASS, però totes12les comprovacions435–449fallen(medianaabs5,7–11,9G/P95abs38,5–134,5G versus límits5/25G). No aplicar aquest completat ni la seva continuació a una font fotogràfica.
- E1 guarda mapes reals de l’error per a2967i3003. Amb la màscara2983, el pitjor residu primerenc és a172,5°(mediana−43,4G/P95abs189,3); el tardà a22,5°(mediana+186,0G/P95abs331,3). No són només un offset global. MapesNPZ i sectorsJSON: punt de diagnòstic següent, sense fit nou.

## Continuació concreta

Congelar el candidat de dispersió i estudiar la geometria/llum del completat per fotograma a partir d’E1. Cal discriminar errors d’ocultació, registre i model solar local amb dades no saturades; les desigualtats de censura poden aportar informació, però no convertir el màxim no saturat en vora física. Reservar nous targets abans de qualsevol ajust. La nova física ampla redueix una incertesa del model anterior; no cal tornar a cercar sigmes o coeficients globals sobre els mateixos jutges.

No promoure fonts llargues sense corregir barrejades amb curtes corregides, ni degradats manuals. El model de completat només pot estimar llum que entra al nucli ampli: cap píxel completat és textura lunar recuperada. Encara no hi ha una font67captures corregida ni una nova porta Photoshop; mantenir el jutge entre trens abans de publicar.

Z0verifica87inputs congelats(67quincunx+20mostresnatives), originalsV46/V47/V48, V49 i3XMP. No RAWreapilat ni estat viu de documents consultat/alterat. Tots els càlculs acabats, cap document de treball creat. Només aquest registrador finalitza el claim amb handoff explícit. Goal actiu, llimb complet i equivalènciaDHS no acreditats.
'''
handoff.write_text(text)
entry=f'> **11-09-2026 · V49 vigent; candidat de dispersió ampla.** Model amb fracció condicionada≈1,406% i eixamplament addicional12px: predicció temporal reservada i injecció nativa positives. El completat de saturació encara falla435–449px; cap nova font/PSB ni canvi de CameraRaw. Goal actiu. Represa `{handoff}`; informe `{report}`.\n\n'
oldprefix='> **11-09-2026 · V49 vigent; diagnòstic natiu del llimb.**'
for path in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',ROOT/'research/README.md']:
    s=path.read_text();assert s.startswith(oldprefix),(path,s[:100]);path.write_text(entry+s.split('\n\n',1)[1])
(IA/'Coordinació/HANDOFF_VIGENT.md').write_text(text)
path=IA/'ACTIVE.json';v=json.loads(path.read_text());v['updated']=now;v['phase']='post-eclipse-V49-preserved-broad-scatter-candidate';v['formal_worktree_handoff']=str(handoff);v['paths']['latest_earthshine_diagnostic_manifest']=str(manifest)
v['earthshine_task']=dict(status='V49_PRESERVED; BROAD_SCATTER_CANDIDATE; COMPLETION_UNQUALIFIED; GLOBAL_GOAL_ACTIVE',completed='Conditional broad mixture passes temporal predictions and native injections; saturation completion failure localized on new targets',next_action='Freeze broad p, diagnose per-frame occultation/solar completion from E1 maps, reserve new targets; no source promotion or manual mask fixes',handoff=str(handoff))
v['earthshine_scatter_candidate']=dict(status='PARTIALLY_QUALIFIED_NO_NEW_SOURCE_OR_PSB',report=str(report),code=str(HERE),manifest=str(manifest),model=str(OUT/'B1_physical_mixture.json'),native_injection=str(OUT/'C0_native_injection.json'),completion=str(OUT/'D2_refined_validation.json'),error_maps=str(OUT/'E1_completion_error_maps.json'),p_conditional=0.01406309541811233,incremental_sigma_px=12,temporal_PASS=True,numerical_native_injection_PASS=True,completion_PASS=False,new_PSB=False,all_limb_recovery_PASS=False)
write(path,v)
link=IA/'output/earthshine_scatter_witness_20260911';assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)
for path in HERE.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
assert rec(ROOT/'.coordination/CLAUDE_STATUS.md')['sha256']==pres['claude_status']['sha256']
files=[p for folder in [HERE,OUT] for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
with ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(rec,files))
write(manifest,dict(created=now,status='SCATTER_CANDIDATE_PROGRESS; V49_PRESERVED; GLOBAL_GOAL_ACTIVE',publication=pres['publication'],files=records,canonical_before=pres['canonical_before'],canonical_after=[rec(r['path']) for r in pres['canonical_before']],handoff=rec(handoff),prior_manifest=pres['prior_manifest'],consumed_inputs=pres['consumed_inputs'],scope='Conditional broad PSF mixture, native injection and unqualified censored-field completion. No new photographic source, PSB or Camera Raw modification. Recorder output goes directly to the tool, not a changing log.'))
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} — RELEASED — CANDIDAT DE DISPERSIÓ AMPLA, V49 PRESERVADA\n\nClaim {CLAIM}. PROGRÉS: pcondicional0,0140631/gaussianaaddicional12px, nucli estret retingut. Quatreèpoquesreservades milloren22,76/21,72/31,65/53,25%,47/48sectors no empitjoren; injecció8/8PASS, RMSbaseline<0,545G. CompletatD2suport100% però12/12gates435–449fallen; no nova font o PSB. E1localitza errorprimerenc172,5°negatiu i tardà22,5°positiu.87inputs i originals/XMP rehash exactes.\n\nHandoff explícit {handoff}; informe {report}; manifest {manifest}; represa {restart}. Goal actiu, límits globals oberts. Cap Photoshop invocat ni documents propis; zero processos de càlcul, només aquest registrador acaba ara. Allibero només el meu owner i el directori buit.\n')
claim=ROOT/'.coordination/claim.lock';assert json.loads((claim/'owner.json').read_text())['claim_id']==CLAIM;(claim/'owner.json').unlink();claim.rmdir();print('RELEASED',len(records),'artifacts; broad candidate qualified partially; V49 preserved; goal active',flush=True)
