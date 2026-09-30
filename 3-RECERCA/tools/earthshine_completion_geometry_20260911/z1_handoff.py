"""Record the bounded geometry result and release this writer claim."""
from geometry_common import *
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
    if len(s)==2 and int(s[0]) not in [os.getpid(),os.getppid()] and 'python' in s[1].lower() and 'earthshine_completion_geometry_20260911/' in s[1] and '.py' in s[1]:other.append(line)
assert not other,other
handoff=ROOT/'.coordination/HANDOFF_2026-09-11_EARTHSHINE_GEOMETRIA_COMPLETAT.md';assert not handoff.exists();report=OUT/'RESULTAT.md';manifest=HERE/'delivery_manifest.json';restart=HERE/'REPRESA.md'
body=f'''# Handoff — geometria del completat — {now}

**V49 vigent i preservada. Assaig de geometria acabat; cap nova font o PSB. Goal global actiu.** No s’ha invocat Photoshop ni alterat Camera Raw. Pere autoritza continuar autònomament amb passos mesurats i sense confirmacions repetides. La millora fotogràfica del llimb complet continua oberta.

Informe `{report}`. Represa `{restart}`. Manifest `{manifest}`. Producte `{pres['publication']['path']}`, SHA `{pres['publication']['sha256']}`. Downloads és codi i Desktop són actius. Sense Git, maquinari, agents nous ni generació de textures.

## Evidència que no cal repetir

- Component ampla congelada: p=0,01406309541811233, gaussiana addicional de 12 px, nucli estret retingut. El resultat temporal positiu anterior continua qualificat dins del seu abast; no s’ha refet l’ajust de p.
- A0/A1: referència solar amb 33 curts, excloent els 16 objectius. Registre a 470–650 px amb translació, guany i offset; 15/16 curts coherents entre meitats angulars. 2985 falla (0,419 px). Dels llargs, 2980 passa, 2978 falla (0,489 px), 2983 té suport insuficient. **2983 no té una posició estimada**, no un zero validat. El registrador exigeix almenys 1000 mostres per ajust.
- B0/B1: fase lunar mesurada en verds nadius, amb integració del píxel, component ampla fixada i perfil local de nucli/fons. Només r≥450 px; 435–449 reservat. Una fase angular comuna s’ajusta en 12 curts. Les quatre preses reservades 2967/2985/2997/3003 tenen RMS de predicció 0,545/0,339/0,371/0,520 px. **0/4 passen 0,25 px.** No hi ha un vincle solar-lunar prou precís per assignar automàticament geometria als llargs censurats.
- C0: base, registre solar, fase lunar per presa i fase+amplada. Les quatre variants tenen 24/36 comprovacions positives; **totes les 12 de 435–449 fallen**. Amb la màscara de 2983, la fase mesurada redueix P95 de 133,31 a 53,12 G a 3003, però empitjora 2967 de 40,38 a 94,54 G. Afegir amplada mediana gairebé no canvia res. Límits 5/25 G i 80% de suport intactes. No es promou cap d’aquestes geometries a una font.
- D0: figura inspeccionada i informe. La base reprodueix la ronda anterior amb diferència de correcció <0,008 G per la precisió de l’interpolador auxiliar; conclusions idèntiques.

## Continuació acotada

No repetir desplaçaments globals, el·lipses lliures o ajustos de fase comuns per resoldre aquest residu. Una resposta intermèdia entre nucli≈1 px i ala de 12 px és una hipòtesi nova que es pot comprovar amb diversitat temporal i control angular. La validació ampla anterior a 426–445 no resol per si sola la resposta més propera a la vora. Declarar models i controls abans de provar; no qualificar dades reutilitzades com a verges. Una altra via exigeix suport observat millor per al model solar pròxim, no una continuació més flexible triada pels mateixos errors.

La fase ajustada en un perfil local no és una mesura pura de la topografia: pot confondre protuberància, ales òptiques i fons. La nova prova de completat és withholding espacial dins de cada presa; no valida llargs sense geometria observable. Cap atribució única de l’error demostrada. Cap píxel completat és textura lunar recuperada. Preservar el detall real, les protuberàncies i l’estètica Camera Raw; cap degradat manual.

Z0 ha verificat 83 arrays congelats (67 quincunx i 16 natius), 7 inputs diagnòstics anteriors, originals V46/V47/V48, V49 i 3 XMP. Cap consulta o alteració de documents vius. Càlculs finalitzats; només aquest registrador tanca ara el claim. Handoff explícit, zero processos propis de càlcul o documents de treball. Objectiu encara actiu; no nova porta Photoshop ni equivalència DHS acreditada.
'''
handoff.write_text(body)
entry=f'> **11-09-2026 · V49 vigent; geometria del completat no qualificada.** Registre solar i fase lunar contrastats per separat: la geometria mesurada ajuda una zona tardana però empitjora la primerenca; les 12 comprovacions de 435–449 px continuen fallant. Cap nova font/PSB ni canvi de Camera Raw. Component ampla anterior congelada; goal actiu. Represa `{handoff}`; informe `{report}`.\n\n'
oldprefix='> **11-09-2026 · V49 vigent; candidat de dispersió ampla.**'
for path in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',ROOT/'research/README.md']:
    s=path.read_text();assert s.startswith(oldprefix),(path,s[:100]);path.write_text(entry+s.split('\n\n',1)[1])
(IA/'Coordinació/HANDOFF_VIGENT.md').write_text(body)
path=IA/'ACTIVE.json';v=json.loads(path.read_text());v['updated']=now;v['phase']='post-eclipse-V49-preserved-completion-geometry-unqualified';v['formal_worktree_handoff']=str(handoff);v['paths']['latest_earthshine_diagnostic_manifest']=str(manifest)
v['earthshine_task']=dict(status='V49_PRESERVED; GEOMETRY_COMPLETION_UNQUALIFIED; GLOBAL_GOAL_ACTIVE',completed='Solar and native lunar phases measured separately; common solar-lunar relation and geometry/width completion tested and rejected for promotion',next_action='Declare and test an intermediate optical-response hypothesis with temporal/angle controls; preserve frozen broad candidate and original appearance; no repeat of global pose-only remedies',handoff=str(handoff))
v['earthshine_completion_geometry']=dict(status='DIAGNOSTIC_FINISHED_NO_NEW_SOURCE_OR_PSB',report=str(report),code=str(HERE),manifest=str(manifest),solar_registration=str(OUT/'A1_solar_registration.json'),lunar_phase=str(OUT/'B1_reference_comparison.json'),completion=str(OUT/'C0_geometry_completion.json'),solar_short_qualified=15,solar_short_total=16,short_phase_prediction_pass=0,short_phase_prediction_total=4,completion_last_limb_pass=0,completion_last_limb_total=12,completion_PASS=False,new_PSB=False,all_limb_recovery_PASS=False)
write(path,v)
link=IA/'output/earthshine_completion_geometry_20260911';assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)
for path in HERE.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
assert rec(ROOT/'.coordination/CLAUDE_STATUS.md')['sha256']==pres['claude_status']['sha256']
files=[p for folder in [HERE,OUT] for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
with ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(rec,files))
write(manifest,dict(created=now,status='GEOMETRY_DIAGNOSIS_PROGRESS; V49_PRESERVED; GLOBAL_GOAL_ACTIVE',publication=pres['publication'],files=records,canonical_before=pres['canonical_before'],canonical_after=[rec(r['path']) for r in pres['canonical_before']],handoff=rec(handoff),prior_manifest=pres['prior_manifest'],verified_arrays=pres['verified_arrays'],previous_inputs=pres['previous_data'],additional_inputs=pres['additional_inputs'],scope='Independent outer-solar and native lunar-phase measurements; withheld completion failure persists. No new source image, PSB or Camera Raw modification. Recorder output returns directly to the tool.'))
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} — RELEASED — GEOMETRIA DEL COMPLETAT, V49 PRESERVADA\n\nClaim {CLAIM}. Assaig acotat acabat: 33 curts de referència; registre solar qualificat en 15/16 curts i 2980; 2983 sense suport. Relació solar-lunar falla 0,25 px als 4 targets. Completat amb fase mesurada: 24/36 comprovacions, totes 12 de 435–449 fallen. P95 tardà 133→53 G però primerenc 40→95 G; amplada no resol. Cap correcció promoguda. 83 arrays, 7 inputs anteriors, originals PSB i XMP verificats.\n\nHandoff explícit {handoff}; informe {report}; manifest {manifest}; represa {restart}. Goal actiu. Cap Photoshop invocat ni documents propis; zero processos de càlcul, només aquest registrador acaba ara. Allibero només el meu owner i el directori buit.\n')
claim=ROOT/'.coordination/claim.lock';assert json.loads((claim/'owner.json').read_text())['claim_id']==CLAIM;(claim/'owner.json').unlink();claim.rmdir();print('RELEASED',len(records),'artifacts; geometry rejected for promotion; V49 preserved; goal active',flush=True)
