"""Publish the measured state, preserve prior authority and release own claim."""
from native_common import *
from photoshop_api import jsx
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import ast,subprocess,os
HERE=Path(__file__).resolve().parent;IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');D=OUT/'full_sampler_delta';now=datetime.now(timezone.utc).isoformat()
def rec(p):
    p=Path(p)
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def write_json(p,a):p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
pres=json.loads((OUT/'Z0_preservation.json').read_text());canon_before=pres['canonical_before'];pub=json.loads((D/'E3_publish.json').read_text())
for a in canon_before+pres['originals']+pres['camera_raw_preferences_exact']:assert rec(a['path'])['sha256']==a['sha256'],('Changed',a['path'])
assert rec(pub['path'])['sha256']==pub['sha256']
state=jsx('var a=[];for(var i=0;i<app.documents.length;i++){var d=app.documents[i];a.push(d.id+"|"+d.name+"|"+d.saved);}a.join("\\n");');assert state==json.loads((D/'E3_open_documents.json').read_text())['state']
assert all(v in state.splitlines() for v in pres['live_documents'].splitlines())
save('Z1_after_delivery_preservation.json',dict(PASS=True,created=now,publication=pub,originals=pres['originals'],camera_raw_preferences=pres['camera_raw_preferences_exact'],live_documents=state,scope='Original V46/V47/V48 and CameraRaw XMP rehashed after V49 delivery; original live saved states unchanged; new V49 saved and open for the user. No own scratch document remains.'))
handoff=ROOT/'.coordination/HANDOFF_2026-09-11_EARTHSHINE_V49_GRAELLA_NATIVA.md';assert not handoff.exists();report=OUT/'RESULTAT.md';plan=HERE/'REPRESA.md'
text=f'''# Handoff — V49, graella verda nativa — {now}

**Producte revisable:** `{pub['path']}`, SHA `{pub['sha256']}`,26capes,10551×7506RGB16. Photoshop i recomposició PASS, màxim3DN16;25capesV48 preservades, només s’oculta la fontV48 i s’afegeix la nova. **Millora modesta; halo i recuperació completa del llimb continuen oberts. Goal actiu.**

Informe `{report}`. Represa acotada `{plan}`. Manifest `{HERE/'delivery_manifest.json'}`. Downloads és codi; Desktop són actius. Sense Git, maquinari ni agents nous. Pere autoritza continuar sense confirmacions freqüents; els canvis vius deV48 eren només inspecció.

## Evidència nova

- El remapat anterior interpolava dos subplans verds i després els promitjava: suavitzava fins i tot mostres verdes existents. Nou interpolador positiu sobre la graella verda completa, sense prendre altres colors; mateixes calibracions, registre i validesa.67RAWVixen regenerats i SHAverificats;21Sony conservats com a referència separada.
- A1:17sectors qualificats de2976, sigma descriptiva1,3254→1,1834px versus1,0121nativa;10,82% de reducció aparellada. No és una PSF única. Variància condicional≈1,99×, perquè s’ha retirat una mitjana. No hi ha guany gratuït deS/N.
- B0: compositor antic reproduït exactament;25/42captures disjuntes per jutge temporal. B1: Sony/LROC i temporal mixtos; cap nova corroboració global2–8px ni de tota la franja. ALPHA històric congelat, no nova estimació de covariància.
- Primera transferència només8–16px: gairebé no alterava la franja. V49 aplica la diferència completa mesurada entre els dos apilats abans de la mateixa receptaCameraRawV48 i la mateixa corba tonal global. Cap nou degradat, màscara ni geometria. No es coneixen amb certesa tots els sliders històrics dePere; es conserva la recepta deV48.
- Fotografia: mediana449–454 aproximadament1,285% més fosca; nucli amb canvi medià zero.50/50condicions anteriors de retenció passen, sense descobertes noves; no són50deteccions independents. Màscara zero/context exterior/alfa exactes; crominància nativa màxim2DN16. Luminància local de protuberàncies no és absolutament idèntica: límits a E2; canals originals preservats.

## Represa

Continua la qualificació de resposta per captura al CFA natiu i la separació de llum solar dispersada i radiància lunar; sector i parell d’èpoques acotats abans de qualsevol expansió. Les67fonts i punts natius ja estan desats, no reapilar-les de nou per començar. No traslladar els sigmes mesurats sobre altres remapats a aquest operador. No reprendre inversions delHDRestàtic ni retalls geomètrics que creen anells negres. La màscara heretada és l’encaix fotogràficV44, no només ocultació física.

PreservacióZ0/Z1:93fonts congelades, originalsV46Detall/V47/V48 i3XMP exactes. Documents originals79/140/1297sense desar i1275desat, inalterats. V49 publicada, oberta i desada per aPere. Còpies de treball natives tancades, cap procés de càlcul propi alrelease. Cap afirmació de llimb complet, d’equivalènciaDHS o de nova textura no corroborada.
'''
handoff.write_text(text)
entry=f'> **11-09-2026 · Earthshine V49 revisable; graella verda nativa.** 67RAWVixen regenerats sense la mitjana de dos verds interpolats; 21Sony com a jutge separat. Vora font≈10,8% més estreta en17sectors qualificats; fotografia449–454≈1,3% més fosca. Mateixa receptaCameraRawV48 i màscara,26capes/25anteriors preservades; Photoshop/readback3DN16 i retenció50/50. Millora modesta: halo i detall de tot el llimb continuen oberts; goal actiu. Represa `{handoff}`; informe `{report}`.\n\n'
canon=[ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ACTIVE.json',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',IA/'Coordinació/HANDOFF_VIGENT.md',ROOT/'research/README.md']
oldprefix='> **11-09-2026 · V48 vigent; model per captura i muntatge diagnosticats.**'
for p in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',ROOT/'research/README.md']:
    s=p.read_text();assert s.startswith(oldprefix),(p,s[:100]);p.write_text(entry+s.split('\n\n',1)[1])
(IA/'Coordinació/HANDOFF_VIGENT.md').write_text(text)
p=IA/'ACTIVE.json';a=json.loads(p.read_text());a['updated']=now;a['phase']='post-eclipse-earthshine-V49-native-green-lattice-partial-improvement';a['formal_worktree_handoff']=str(handoff)
a['previous_earthshine_product_V48']=a['current_earthshine_product'];a['current_earthshine_product']=dict(pub,report=str(report),handoff=str(handoff),code=str(HERE))
a['paths']['current_earthshine_editable']=pub['path'];a['paths']['current_earthshine_manifest']=str(HERE/'delivery_manifest.json');a['paths']['current_earthshine_visual_output']=str(IA/'output/earthshine_native_psf_20260911/full_sampler_delta/vistes')
a['earthshine_task']=dict(status='V49_DELIVERED_PARTIAL_IMPROVEMENT; GLOBAL_DETAIL_GOAL_ACTIVE',completed='67 native green-lattice sources, temporal and cross-sensor checks, same-CR reversible V49, Photoshop and retention gates',next_action='Native-CFA per-capture response qualification on a bounded temporal/sector pilot; see REPRESA.md; no global fixed PSF or hand mask correction',handoff=str(handoff))
a['earthshine_v49_source']=dict(candidate=str(OUT/'B0_new_all.npz'),native_inventory=str(OUT/'A2_all_native.json'),source_frames=67,reference_frames=21,judge=str(OUT/'B1_independent_detail.json'),retention=str(D/'C5_retention.json'),native_profile=str(OUT/'A1_native_profiles.json'),mask_and_geometry_unchanged=True,all_limb_scientific_PASS=False,report=str(report))
write_json(p,a)
link=IA/'output/earthshine_native_psf_20260911';assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
files=[p for directory in [HERE,OUT] for p in sorted(directory.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
with ThreadPoolExecutor(max_workers=3) as pool:inventory=list(pool.map(rec,files))
write_json(HERE/'delivery_manifest.json',dict(created=now,status='V49_DELIVERED_PARTIAL_IMPROVEMENT; GLOBAL_GOAL_ACTIVE',publication=pub,files=inventory,canonical_before=canon_before,canonical_after=[rec(p) for p in canon],handoff=rec(handoff),prior_manifest=pres['prior_manifest'],inputs=pres['consumed_sources_exact'],raw67_checked=pres['raw67_verified_during_render'],scope='Native green interpolation correction and same-CR photographic delta. No new mask; complete halo removal and all-limb recovery not achieved.'))
other=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
    f=line.strip().split(None,1)
    if len(f)==2 and int(f[0]) not in [os.getpid(),os.getppid()] and 'python' in f[1].lower() and 'earthshine_native_psf_20260911/' in f[1] and '.py' in f[1]:other.append(line)
assert not other,other
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} — RELEASED — EARTHSHINE V49, MILLORA PARCIAL\n\nClaim {CLAIM}. PROGRÉS:67RAW regenerats sobre la graella verda completa, perfil font10,82% més estret en17sectors qualificats; variància≈1,99×. Nova V49 revisable,26capes i25fonts originals preservades; mateixa màscara, receptaCameraRawV48 i corba global. Franja fotogràfica449–454≈1,285% més fosca; retenen50/50condicions antigues, sense noves deteccions. Sony/temporal mixtos: halo i recuperació global continuen oberts.\n\nHandoff explícit {handoff}; informe {report}; manifest {HERE/"delivery_manifest.json"}. Photoshop26capes, readback3DN16, context/alfa exactes, crominància2DN16. OriginalsV46/V47/V48 iXMP rehash després de publicació; documents originals intactes. V49 desada i oberta per aPere, cap còpia de treball pròpia oberta. Zero processos de càlcul; només aquest registrador acaba ara. Objectiu global actiu. Allibero owner propi i directori buit.\n')
claim=ROOT/'.coordination/claim.lock';assert json.loads((claim/'owner.json').read_text())['claim_id']==CLAIM
(claim/'owner.json').unlink();claim.rmdir();print('RELEASED',len(inventory),'files; V49 delivered; full-limb goal active',flush=True)
