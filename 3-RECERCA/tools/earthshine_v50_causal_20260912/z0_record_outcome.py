"""Record honest incomplete outcome, preserve sources, refresh restart pointers.
No V50 promotion and no Photoshop or original photographic modifications.
"""
from common50 import *
import datetime,shutil,subprocess
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');source=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V49.psb');expected='fc22af4660c7ac7aeb10a1433f1c159a91968fed70646c4b9200bb5bf7748366'
assert sha(source)==expected,'User reference changed; preserve and re-assimilate'
authorities=json.loads((OUT/'A0_authorities.json').read_text());backup=OUT/'Z0_authorities_before';backup.mkdir(exist_ok=False)
for i,row in enumerate(authorities):
 p=Path(row['path']);assert sha(p)==row['sha256'],str(p);shutil.copy2(p,backup/f'{i:02d}_{p.name}')
handoff=ROOT/'.coordination/HANDOFF_2026-09-12_V50_CAUSES_I_PROVES_REFUSADES.md';report=OUT/'RESULTAT_V50_ENCARA_NO_VALIDADA.md';manifest=HERE/'delivery_manifest.json';assert not handoff.exists() and not report.exists() and not manifest.exists()
body=f'''# V50: resultat encara no aconseguit

{stamp}

La V50 sol·licitada **no s'ha creat ni validat**. Les proves de correcció encara introdueixen una costura visible. La V49 revisada de Pere conserva exactament SHA-256 `{expected}`; el seu revelat i totes les capes originals continuen desats igual. En aquesta represa no s'ha obert, guardat, filtrat ni tancat cap document Photoshop. Els arrays i PNG nous són diagnòstics, no versions fotogràfiques acceptades.

## Què ha quedat aclarit

1. L'antic resultat favorable A1/A2 tenia un nul identitat que millorava la seva MSE un29,85% sense corregir la imatge. Aquella interpretació queda retirada. I3 utilitza unitats comunes, suport estricte i un nul girat real; millora coherència temporal, però la seva previsualització encara falla.
2. Uns offsets ajustats només a la corona havien entrat a la branca lunar. Retirar-los millora el biaix entre exposicions pròximes, però no elimina l'halo principal.
3. El pes fotogràfic additiu V44 s'havia reutilitzat com una alfa NORMAL sobre un HDR amb llum solar. No era cobertura física lunar; la reutilització fa visible llum solar com si fos Lluna.
4. La capa anomenada09 d'Earthshine és, en realitat, un compost12+11+10+09 amb màscares aplicades. L6 el reprodueix amb la capa12 moguda−3px respecte de CapesTotalsV42: nucli lunar exacte i la major part de la resta dins1–3DN16. Queden excepcions importants a algunes protuberàncies, de manera que no és un reemplaçament universal exacte.
5. Les vores aparentment més petites i regulars dels RGB originals no determinen per si soles el radi lunar intrínsec. Els instants i desplaçaments són diferents; no moure tota la Lluna ni les protuberàncies segons una sola derivada fotogràfica.

## Proves finals i rebuig

M0 regenera quatre RAW en canals de càmera independents, sense offsets/camps coronals ni terra de brillantor. M1 prova una desmescla mínima de color: ajustar dos canals i predir el tercer, amb llimb i altra època reservats. Falla: residuals35–45vegades la referència interior i molts coeficients lunars negatius. No promoguda.

N1 conserva el RGB de Pere i la cobertura geomètrica K0, amb la fotografia solar10 original sense màscara a sota. Redueix l'anell negre en bona part del contorn, però canvia l'aspecte solar i continua fallant a l'esquerra.

N2 conserva el context solar real de V49 mitjançant LIGHTEN amb l'original10. **Rebutjada visualment per root i per un revisor independent:** franja marró contínua dalt, doble contorn marró baix, línia fosca prop de la protuberància esquerra i vora clara fina a la dreta. Per tant, no compleix l'encàrrec. No s'ha executat la porta Photoshop perquè cap candidat visual ha arribat a qualificació.

![N2 dalt: V49 a l'esquerra, prova rebutjada a la dreta]({OUT/'N2_top.png'})

![N2 baix: V49 a l'esquerra, prova rebutjada a la dreta]({OUT/'N2_bottom.png'})

## Límit i represa

Hi ha ara una causa de composició demostrada, però encara falta una font lunar neta fins a l'últim píxel i una unió amb la corona que sigui compatible entre instants i revelats. Les proves actuals no justifiquen ni una màscara retocada per amagar residus, ni un radi nou, ni una afirmació que les dades siguin irrecuperables en general.

La continuació autònoma de Pere continua autoritzada. No hi ha una espera de permís. Per reprendre cal una hipòtesi nova i una validació que resolgui aquesta unió; no repetir les PSF, desmescla global o variants de màscara ja refusades. Les dades i els punts de reinici queden conservats. L'objectiu continua incomplet i no es marca aconseguit.

Informe causal detallat: [CAUSES_CONFIRMADES_I_LIMITS.md]({OUT/'CAUSES_CONFIRMADES_I_LIMITS.md'}). Codi: `{HERE}`. Rebuts: `{OUT}`. Manifest: `{manifest}`. Represa: `{handoff}`.
'''
report.write_text(body)
handoff.write_text(f'''# Represa V50 causal — resultat no validat

{stamp}

Autorització de Pere vigent: acabar V50 autònomament, preservar V49 revisada i el seu Camera Raw, corregir a l'origen, cap halo/artefacte nou. No cal un altreok per a una continuació dins l'abast. **Aquest handoff no afirma que la tasca estigui acabada.**

Font `{source}`; SHA `{expected}`. No V50 produïda. Codi i únic espai nou `{HERE}` i `{OUT}`. Arrel senseGit. Llegir CLAUDE i IA segonsAGENTS; adquirir SERIAL_WRITES nou abans d'escriure. Aquest claim és `{CLAIM}` i s'allibera explícitament al diari després dels rebuts.

Llegir primer `{report}` i `{OUT/'CAUSES_CONFIRMADES_I_LIMITS.md'}`. Manifest `{manifest}`. L'antic handoff `{ROOT/'.coordination/HANDOFF_2026-09-12_V50_NO_VALIDADA.md'}` conserva la història, però la seva interpretació favorable A1/A2 queda retirada pel nul identitat d'aquesta represa.

## Punts de reinici útils

- H0/H1: retirar els offsets coronals és correcte com a ablació de calibració, no cura de l'halo. Congela pesos, no els dona per revalidats.
- I1/I3: transferència exterior positiva, cinc frames d'ajust i setze reservats, suport de cel·les estrictament interior. I4 és la seva previsualització rebutjada; no transferir-la als llargs ni a píxels exteriors sense prova.
- L4_original_12/11/10/09.npz: RGB, alfa i màscara de CapesTotalsV42 exactes a la ROI1400. L6 reconstrucció de l'09 actual, amb12 a−3px en x. No ignorar residus de protuberàncies de fins26kDN16.
- N0: resposta aparent dels RGB sense màscara. No és geometria lunar intrínseca ni una ordre de traslladar capes.
- M0_camera_*.npz: quatre RAW regenerats en espai càmera, sense offsets/phi, validesa per canal. M1 dos colors globals falla fort; tercers canals no són tres experiments independents.
- N1/N2: assaig acotat proposat per auditoria independent. Restituir10 sense màscara elimina part del forat però N2 encara presenta costura marró/fosca. Rebuig independent confirmat. Cap candidatPSB.

Només reprendre amb una hipòtesi de composició física entre instants que es pugui falsar amb dades reservades, mantenint la resposta de Pere. No convertir la manca d'una solució actual en una prova d'impossibilitat ni en una nova demanda rutinària de confirmació.

## Preservació

Tots els originals fotogràfics oberts només en lectura. V49 revalidada pel hash anterior. Zero documents Photoshop creats/modificats en aquesta represa; només inventari inicial amb zero documents. Cap Camera Raw executat. Agents auxiliars només lectura. L'estat final de processos i l'alliberament queden a CODEX_STATUS.md i Z1_release.json.
''')
header=f'> **12-09-2026 · Represa V50 causal: encara no validada.** Identificats pes additiuV44 reutilitzat com alfaNORMAL i capa09 com a compost12+11+10+09 amb màscares. L6 reprodueix gran part del RGB dins1–3DN16; protuberàncies amb excepcions. N1/N2 retiren part del forat però deixen costura marró/fosca: rebutjades per dues revisions. M1 desmescla de color falla. Retirada la interpretació favorable de l\'anticA1/A2: nul identitat millorava29,85%. V49 SHA `{expected}` exacta; capV50 ni correcció promoguda. Represa `{handoff}`; informe `{report}`. Autorització autònoma vigent, resultat incomplet.\n\n'
for row in authorities:
 p=Path(row['path'])
 if p.suffix=='.md':p.write_text(header+p.read_text())
a=json.loads((IA/'ACTIVE.json').read_text());a['updated']=stamp;a['phase']='post-eclipse-V50-causal-unqualified-V49-Pere-preserved';a['formal_worktree_handoff']=str(handoff);a['paths']['latest_earthshine_diagnostic_manifest']=str(manifest)
a['earthshine_v50_causal_attempt']=dict(status='NOT_ACHIEVED',report=str(report),handoff=str(handoff),manifest=str(manifest),new_PSB=False,source_correction_promoted=False,mask_or_geometry_promoted=False,original_V49_sha256=expected,old_A1_A2_favorable_interpretation_withdrawn=True,old_identity_null_apparent_improvement_percent=29.8476,composite09_lineage_identified=True,N2_visual_acceptance=False,independent_N2_visual_acceptance=False,M1_spectral_model_accepted=False,autonomous_authorization_continues=True)
(IA/'ACTIVE.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
save('Z0_preservation.json',dict(time=stamp,V49_path=str(source),V49_sha256=expected,V49_unchanged=True,photoshop_mutations_this_run=0,new_PSB=False,source_changes_promoted=False,authorities_before=authorities,authorities_after=[dict(path=row['path'],sha256=sha(row['path'])) for row in authorities]))
files=[p for root in [HERE,OUT] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=manifest]
rows=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]
manifest.write_text(json.dumps(dict(time=stamp,status='NOT_ACHIEVED',source=str(source),source_sha256=expected,report=str(report),handoff=str(handoff),files=rows,new_PSB=False),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(report=str(report),handoff=str(handoff),manifest=str(manifest),files=len(rows),source_unchanged=sha(source)==expected)),flush=True)
