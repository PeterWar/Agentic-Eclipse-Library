"""Record diagnostic failures and the user-requested visible checkpoint; release."""
from diffraction_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import ast,os,subprocess
IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');now=datetime.now(timezone.utc).isoformat()
pres=json.loads((OUT/'Z0_preservation.json').read_text());summary=json.loads((OUT/'F0_summary.json').read_text());review=json.loads((OUT/'R1_visible_review.json').read_text());live=json.loads((OUT/'R2_open_documents_after.json').read_text())
assert pres['PASS'] and summary['profile_model_adequacy_FAIL'] and live['original_document_records_unchanged']
def rec(path):
    path=Path(path)
    with path.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(path),bytes=path.stat().st_size,sha256=h)
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
for r in pres['canonical_before']+[pres['claude_status']]:assert rec(r['path'])['sha256']==r['sha256'],r['path']
for r in review['copies']:assert rec(r['review_copy'])['sha256']==r['sha256']
other=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
    pair=line.strip().split(None,1)
    if len(pair)==2 and int(pair[0]) not in [os.getpid(),os.getppid()] and 'python' in pair[1].lower() and 'earthshine_diffraction_20260912/' in pair[1] and '.py' in pair[1]:other.append(line)
assert not other,other
handoff=ROOT/'.coordination/HANDOFF_2026-09-12_EARTHSHINE_REVISIO_VISIBLE_I_DIFRACCIO.md';assert not handoff.exists()
report=OUT/'RESULTAT.md';restart=HERE/'REPRESA.md';manifest=HERE/'delivery_manifest.json'
body=f'''# Handoff — revisió visible de Pere i diagnòstic de difracció — {now}

**ATURADA DEMANADA PER PERE AL PUNT VISIBLE.** Missatge: «para quan tinguis el pròxim resultat visible per ensenyar al photoshop, vull veure com vas si us plau». La V49 és l’últim resultat fotogràfic; les proves posteriors no han produït cap millora visual qualificada. S’ha dit expressament a Pere. No presentar les còpies de revisió com una V50 o una correcció nova. No reprendre la recerca sense una nova indicació de Pere. L’objectiu global continua incomplet; no s’ha marcat complet ni bloquejat.

## Què queda obert a Photoshop

- Document1596 `REVISIO_V49_sense_modificar.psb`, primer pla, ordre native Actual Pixels executada.
- Document1593 `REVISIO_V48_sense_modificar.psb`, referència disponible en una altra pestanya.
- Fitxers a `{OUT}`. Còpies byte a byte dels productes guardats V48/V49, amb els mateixos SHA. Porta Photoshop: `OBRE 10551 px x 7506 px · 25 capes` i `OBRE 10551 px x 7506 px · 26 capes`; segon lector ImageMagick RGB16, dimensions correctes. Vista sencera i lunar del readback V49 inspeccionades.
- Quatre documents previs conservats: IDs79 V45_Fonts,140 V46_Detall,1275 V47 i1297 V48. Els estats saved/path/dimensions/ID coincideixen abans/després. No se n’ha guardat ni tancat cap. Això no és un hash dels píxels vius sense desar.
- Les dues còpies obertes es lliuren a Pere per inspecció: no són documents temporals pendents de tancar. Cap procés propi de càlcul queda corrent. R0/R1/R2 contenen els rebuts. El CUA va quedar pendent de permisos; no s’ha insistit ni n’ha depès l’obertura, feta per l’API nativa ja disponible.

Producte V49 `{pres['publication']['path']}`, SHA `{pres['publication']['sha256']}`. Camera Raw i originals intactes. Informe `{report}`, represa `{restart}`, manifest `{manifest}`.

## Resultats que no cal repetir

1. Vixen VSD90SS: pupil·la nominal90mm i escala mesurada2,1494813525884373arcsec/píxel. Banda declarada500/550/600nm, no resposta espectral Canon mesurada. Airy ideal a550nm: energia fora4/12px 2,9425%/0,9978%; cascada anterior4/12:2,9537%/0,8839%. Motiva una hipòtesi, no identifica PSF. **No sumar Airy i les gaussianes automàticament:** possible doble recompte.
2. A1: inversió directa sobre presa mostrejada RMS4,17–5,28G FAIL. Suavitzada sigma2 passa només contra un objectiu també suavitzat. A2 demostra que falla respecte de la imatge completa (centenarsG). No promoure aquell PASS limitat.
3. A2/A3:21camps D0 sense cap píxel censurat, fases reals i pesos congelats. La mitjana de preses invertides redueix l’error però no passa totes les meitats/espectres. Prior blanc alias-aware tampoc. És qualificació numèrica, no l’exclusió admissible dels altres RAW en un producte final.
4. A4: resol quatre aliases Fourier conjuntament, sense prior de textura.36/36 PASS en escena sintètica comuna, registre exacte, sigma0,97 i frontera periòdica; RMS màxim0,008873G. Condicionament4,92/15,11/6,91; amplificació de variància d’alguns coeficients fins24 a l’inici.
5. **A5 refusa l’aplicació directa:** error simulat0,01px u/v produeix RMS28,38/54,99/37,35G; variaciósigma RMS0,05px:38,99/80,59/30,64G; variació1% de la protuberància sintètica:5,29/28,03/7,03G. No són errors mesurats de les fotos. La mateixa escena i PSF al llarg de la totalitat és una hipòtesi inadequada per invertir el stack.
6. B0/B1: perfils reals12sectors de21preses, bins0,5px; ajust a distància<=−27 o>=−3, reserva−25..−6. Model gaussià contra gaussià+Airy, mateix nombre de paràmetres. Cinc preses èpoques2/5 entrenen residu lunar;16validen sis èpoques.550nm: reduccions52,46/20,31/−1,30/30,32/40,18/−1,47%;4/6gates i50/72sectors.500/600 també fallen.
7. **B2/inspecció visual invaliden la lectura física dels percentatges B0/B1.** L’exterior lineal no reprodueix el pic de cromosfera i la caiguda radial. El fit compensa amb un pendent lunar que les dades no sostenen.103/252Airy tenen chi2mitjà>5;71/252discrepen>3sigmes condicionals del pendent profund;13tocant límits. ExempleC2 572A2960sector6: el predictor dins la Lluna puja a desenes de milersG davant pocs milers observats. Flags retrospectius, no nous gates predeclarats. No usar aquestes restes, shifts o sigma com a font, geometria o mesura de seeing. Cap evidència favorable de recuperació nova.

Les figures són diagnòstiques; els fantomes mai entren a una font lunar. La banda dels últims6px, la censura dels llargs i la corroboració entre telescopis continuen obertes. Si Pere autoritza reprendre, conservar D0 i l’operador natiu, fer un model directe amb llum solar temporal pròpia de cada presa i nucli comprovat, abans d’estimar una radiància lunar comuna. No arreglar el perfil forçant a mà el pendent lunar ni afegir una màscara. No repetir aquest paquet de proves.

Z0 preserva46inputs consumits,28RAW, originals V46/V47/V48, V49 i3XMP;8autoritats congelades abans d’actualitzar. Handoff explícit, zero processos propis, dues còpies de revisió deixades obertes deliberadament a Pere. La recerca s’atura al punt visible demanat.
'''
handoff.write_text(body)
entry=f'> **12-09-2026 · Revisió V48/V49 oberta; aturada demanada per Pere.** V49 segueix sent l’últim producte. Còpies exactes V48/V49 obertes a Photoshop per revisar, sense guardar originals. Difracció i inversió conjunta: aritmètica qualificada però sensibilitat falla; perfils solars lineals inadequats, cap font nova. No reprendre recerca sense nova indicació de Pere. Represa `{handoff}`; informe `{report}`.\n\n'
oldprefix='> **12-09-2026 · V49 vigent; resposta intermèdia i operador natiu.**'
for path in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',ROOT/'research/README.md']:
    text=path.read_text();assert text.startswith(oldprefix),(path,text[:100]);path.write_text(entry+text.split('\n\n',1)[1])
(IA/'Coordinació/HANDOFF_VIGENT.md').write_text(body)
path=IA/'ACTIVE.json';v=json.loads(path.read_text());v['updated']=now;v['phase']='post-eclipse-V49-visible-review-user-requested-stop';v['formal_worktree_handoff']=str(handoff);v['paths']['latest_earthshine_diagnostic_manifest']=str(manifest)
v['earthshine_task']=dict(status='USER_REQUESTED_STOP_AT_VISIBLE_CHECKPOINT; V49_PRESERVED; GLOBAL_OBJECTIVE_INCOMPLETE',completed='Exact V48/V49 review copies opened in Photoshop; native sampling/diffraction diagnostic recorded, no new correction qualified',next_action='Wait for Pere visual review or explicit instruction before further research',handoff=str(handoff),visible_review=str(OUT/'R2_review_opened.json'))
v['earthshine_diffraction']=dict(status='DIAGNOSTIC_FINISHED; NO_NEW_PHOTOGRAPHIC_SOURCE; USER_VISUAL_CHECKPOINT',report=str(report),code=str(HERE),manifest=str(manifest),native_joint_numeric_PASS=True,joint_stress_PASS=False,profile_model_adequacy_PASS=False,new_PSB_version=False,all_limb_recovery_PASS=False,review_copies=review['copies'])
write(path,v)
link=IA/'output/earthshine_diffraction_20260912';assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)
for path in HERE.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
assert rec(ROOT/'.coordination/CLAUDE_STATUS.md')['sha256']==pres['claude_status']['sha256']
files=[p for folder in [HERE,OUT] for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
with ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(rec,files))
write(manifest,dict(created=now,status='USER_REQUESTED_VISIBLE_CHECKPOINT_STOP; V49_PRESERVED; GLOBAL_OBJECTIVE_INCOMPLETE',publication=pres['publication'],files=records,canonical_before=pres['canonical_before'],canonical_after=[rec(r['path']) for r in pres['canonical_before']],handoff=rec(handoff),prior_manifest=pres['prior_manifest'],verified_inputs=pres['verified_inputs'],verified_RAWs=pres['verified_RAWs'],review_copies=review['copies'],open_review_documents=live,scope='Diagnostic pupil/sampling hypotheses, rejected sensitivity and inadequate solar-profile model. No new photographic correction. Two byte-exact review copies deliberately opened for Pere; all four original live documents remain unchanged in recorded state.'))
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} — RELEASED — REVISIÓ V48/V49 VISIBLE, ATURADA DEMANADA PER PERE\n\nClaim {CLAIM}. A4numèric36/36PASS, però A5sensibilitatFAIL. B0/B1reduccions4/6èpoques no acceptades com evidència física: B2iinspecció revelen model exterior lineal inadequat i pendent lunar forçat. Cap font ni correcció nova.\n\nPere demana parar al pròxim punt visible. Còpies exactes V48/V49 obertes IDs1593/1596, V49 primer pla i ActualPixels executat. PortaOBRE25/26capes i segon lector. Quatre originals vius IDs79/140/1275/1297 conservats amb estats id/path/saved/dimensions iguals; no guardats ni tancats. CUA pendent de permisos, obertura nativa completada sense dependre’n.\n\nHandoff explícit {handoff}; informe {report}; manifest {manifest}. Goal incomplet, no marcar complet/bloquejat. No reprendre recerca sense nova indicació de Pere. Zero processos propis; les dues còpies visibles queden lliurades per inspecció. Allibero només el meu owner i el directori buit.\n')
claim=ROOT/'.coordination/claim.lock';assert json.loads((claim/'owner.json').read_text())['claim_id']==CLAIM;(claim/'owner.json').unlink();claim.rmdir()
print('RELEASED',len(records),'artifacts; visible V48/V49 checkpoint; original documents preserved; no new science claim',flush=True)
