"""Record bounded diagnostic progress and release own serial-writer claim."""
from native_forward_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import os,subprocess,ast
HERE=Path(__file__).resolve().parent;IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');now=datetime.now(timezone.utc).isoformat();pres=json.loads((OUT/'Z0_preservation.json').read_text());assert pres['PASS']
def rec(p):
    p=Path(p)
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def write(p,a):p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
for r in pres['canonical_before']+[pres['claude_status']]:assert rec(r['path'])['sha256']==r['sha256'],('AUTHORITY_CHANGED',r['path'])
other=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
    s=line.strip().split(None,1)
    if len(s)==2 and int(s[0]) not in [os.getpid(),os.getppid()] and 'python' in s[1].lower() and 'earthshine_native_forward_20260911/' in s[1] and '.py' in s[1]:other.append(line)
assert not other,other
handoff=ROOT/'.coordination/HANDOFF_2026-09-11_EARTHSHINE_MODEL_NATIU.md';assert not handoff.exists();report=OUT/'RESULTAT.md';manifest=HERE/'delivery_manifest.json';restart=HERE/'REPRESA.md'
text=f'''# Handoff — model natiu del llimb — {now}

**V49 continua vigent i immutable. No V50; goal global actiu.** Aquesta ronda qualifica un operador físic natiu i identifica sensibilitat a la geometria, però no promou cap camp latent ni canvi de registre a la fotografia. Pere autoritza continuar en passos mesurats sense confirmacions repetides; els seus canvis vius de V48 eren només inspecció. Originals i estètica Camera Raw preservats.

Informe `{report}`. Represa exacta `{restart}`. Codi `{HERE}`. Manifest `{manifest}`. Producte `{pres['publication']['path']}`, SHA `{pres['publication']['sha256']}`; la porta Photoshop és la de V49 anterior, no una porta nova d’aquesta ronda. Downloads és codi; Desktop són actius. Sense Git, maquinari, delegació o generació de textura artificial.

## Evidència i límits

- A0: integració positiva sobre CFA natiu, píxel integrat analíticament sota nucli gaussià i cel·les partides per ocultació. Constant/pla/adjunt/refinament PASS. Diferència màxima de quadratura <0,108 G davant un salt 500→100.000 G; no qualifica la PSF física.
- B0/B1: 12 preses primerenques/tardanes, 8 entrenen i 4 reservades; fonts M/C separades, Sol mòbil contra control estàtic. B1 mòbil convergeix sense negatius lunars; estàtic convergit a **B2_static_refined**. Encara falla la predicció dels últims píxels; no hi ha recuperació fotogràfica validada.
- V44 afinava registre per textura només en preses>=1 s; el contorn era una mediana de curtes sense retirar translacions residuals. C0 mesura posicions nadiues fora de la dreta; hi ha residus d’aproximadament1 píxel, però no són una correcció global demostrada.
- C1/C2: 6 curts ajusten, 2976/2994 reservats a la dreta. Translació de l’operador mesurada en altres sectors: error449–454 baixa48,352→1,981 i60,130→35,922 (95,9% i40,3%). **Percentatge d’error del model, no de detall recuperat.** Lluna latent mediana3694→1473 G. Regressió2994 en445–449. Afegir amplada per presa baixa a522 G i necessita molts negatius sense restriccions; no promogut. Tots tres tenen convergència numèrica.
- C3: model afí refusat amb199parelles en nous sectors intercalats; a la dreta RMS0,340→0,406 píxels. No atribuir el resultat a refracció atmosfèrica ni deformar el PSB.
- D0: textura interior creuada amb3presesSonyA, meitats angulars i control conegut.0/16registres compleixen els acords exigits, tot i control d’equivariança PASS. No aplicar-ne vectors. Subplans verds Sony1/2 no són meitats temporals.
- E0: figura científica revisada i resultats guardats. No s’ha invocat Photoshop. Z0:34inputs natius consumits, originalsV46/V47/V48, V49 i3XMP rehash exactes; cap RAW reapilat en aquest pas.

## Continuació sense repetir assaigs

El límit segueix sent separar el senyal lunar real de la dispersió solar i de la incertesa geomètrica. Una nova hipòtesi ha de representar-los conjuntament i declarar prediccions noves/refutables abans d’ajustar. Les ales òptiques àmplies no s’han inferit conjuntament; els sigmes de perfil continuen sent descriptius. No repetir PSF uniforme, translacions de vora lluminosa, inversió del HDR estàtic ni deformació afí contra els mateixos jutges. Injecció de textura i jutge entre trens pendents abans de substituir cap font fotogràfica.

Matrius i mostres ja desades; no reapilar88RAW per reprendre. Respectar el canvi de coordenades comú a Lluna i Sol: `solar_center_in_lunar_grid` antic incorpora `native.shift`; C1 retira aquesta suma del moviment relatiu quan registra amb `xy−pose`. No moure fonts per corregir una fórmula. La màscara V49 heretada és un encaix fotogràfic, no només ocultació física.

Tots els processos de càlcul acabats; cap document de treball propi creat. Handoff explícit, només el registrador tanca ara el seu claim. Goal actiu, sense afirmació de llimb complet ni d’equivalència DHS.
'''
handoff.write_text(text)
entry=f'> **11-09-2026 · V49 vigent; diagnòstic natiu del llimb.** Operador CFA positiu qualificat numèricament. Translació mesurada fora de la dreta redueix error local en dues preses reservades95,9%/40,3%, però no acredita detall recuperat ni una correcció global. Model afí i registre de curtes per textura refusats; cap PSB nou ni canvi de Camera Raw. Goal actiu. Represa `{handoff}`; informe `{report}`.\n\n'
oldprefix='> **11-09-2026 · Earthshine V49 revisable; graella verda nativa.**'
for p in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',ROOT/'research/README.md']:
    s=p.read_text();assert s.startswith(oldprefix),(p,s[:100]);p.write_text(entry+s.split('\n\n',1)[1])
(IA/'Coordinació/HANDOFF_VIGENT.md').write_text(text)
p=IA/'ACTIVE.json';a=json.loads(p.read_text());a['updated']=now;a['phase']='post-eclipse-V49-preserved-native-forward-diagnostic';a['formal_worktree_handoff']=str(handoff);a['paths']['latest_earthshine_diagnostic_manifest']=str(manifest)
a['earthshine_task']=dict(status='V49_PRESERVED; NATIVE_FORWARD_DIAGNOSTIC; GLOBAL_GOAL_ACTIVE',completed='Native pixel operator qualified, moving/static fits, withheld pose tests, rejected affine and short-exposure texture registration',next_action='Joint treatment of geometric uncertainty and solar scatter with new declared predictions; see native-forward REPRESA.md; no repeated fixed-PSF or global-edge-shift search',handoff=str(handoff))
a['earthshine_native_forward_diagnostic']=dict(status='DIAGNOSTIC_ONLY_NO_NEW_PSB',report=str(report),code=str(HERE),manifest=str(manifest),operator=str(OUT/'A0_operator_pilot.json'),static_control=str(OUT/'B2_static_refined.json'),pose_comparison=str(OUT/'C2_pose_fits.json'),shape_validation=str(OUT/'C3_shape_validation.json'),texture_registration=str(OUT/'D0_lunar_texture_pose.json'),review=str(OUT/'E0_review.json'),new_PSB=False,all_limb_recovery_PASS=False)
write(p,a)
link=IA/'output/earthshine_native_forward_20260911';assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)
assert rec(ROOT/'.coordination/CLAUDE_STATUS.md')['sha256']==pres['claude_status']['sha256']
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
files=[p for directory in [HERE,OUT] for p in sorted(directory.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
with ThreadPoolExecutor(max_workers=3) as pool:inventory=list(pool.map(rec,files))
canonical=[rec(r['path']) for r in pres['canonical_before']]
write(manifest,dict(created=now,status='DIAGNOSTIC_PROGRESS; V49_PRESERVED; GLOBAL_GOAL_ACTIVE',publication=pres['publication'],files=inventory,canonical_before=pres['canonical_before'],canonical_after=canonical,handoff=rec(handoff),prior_manifest=pres['prior_manifest'],consumed_inputs=pres['consumed_inputs'],scope='Native numerical operator and geometry diagnostics only; no new astronomical image, RAW stack, Photoshop change or all-limb recovery claim. Recorder output is returned directly, not a mutable manifest log.'))
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} — RELEASED — MODEL NATIU DEL LLIMB, V49 PRESERVADA\n\nClaim {CLAIM}. PROGRÉS: operadorCFApositiu qualificat;12preses/2èpoques, ajusts mòbil i estàtic convergits. C2translació fora del sector redueix error449–454 de48,352→1,981 i60,130→35,922 en2preses reservades, però no és detall recuperat. C3deformacióafí refusada (RMSdreta0,340→0,406); D0texturacreuada0/16registres qualificats tot i controls de translació PASS. Cap canvi fotogràfic, Photoshop no invocat, V49 i originals/XMP exactes.34inputs consumits rehash.\n\nHandoff explícit {handoff}; informe {report}; manifest {manifest}; represa {restart}. Goal global actiu; halo i recuperació completa oberts. Zero processos de càlcul i cap document de treball propi; només aquest registrador acaba ara. Allibero només owner propi i directori buit.\n')
claim=ROOT/'.coordination/claim.lock';assert json.loads((claim/'owner.json').read_text())['claim_id']==CLAIM;(claim/'owner.json').unlink();claim.rmdir()
print('RELEASED',len(inventory),'artifacts; V49 preserved; diagnostic progress; global goal active',flush=True)
