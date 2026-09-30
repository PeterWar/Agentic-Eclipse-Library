from pathlib import Path
import json,hashlib,datetime,os
R=Path.cwd();O=R/'output/earthshine_broad_lroc_20260914';T=R/'research/tools/earthshine_broad_lroc_20260914';IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');lock=R/'.coordination/claim.lock';owner=json.loads((lock/'owner.json').read_text());assert owner['claim_id']=='CODEX_EARTHSHINE_BROAD_LROC_20260914'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
start=json.loads((O/'A0_start.json').read_text());assert sha(R/'.coordination/CLAUDE_STATUS.md')==start['claude_status_sha256']
now=datetime.datetime.now(datetime.timezone.utc).isoformat();report=O/'RESULTAT.md';pdf=O/'ESTUDI_TACA_EARTHSHINE.pdf';handoff=R/'.coordination/HANDOFF_2026-09-14_EARTHSHINE_TACA_AMPLA_INVESTIGACIO.md'
body=f'''# Earthshine: investigació profunda de la taca ampla

Petició vigent: investigar a fons l’artefacte taronja de V67/V68 comparat amb «Compara LROC · alineada V58», i corregir-lo si cal. **No hi ha correcció nova validada ni V69.** No tractar aquesta ronda com una reparació de la taca. La sospita de contrast excessiu es reforça, però l’amplitud de correcció no queda determinada.

## Resultat i evidència nova

- LROC62 deriva del CGI Moon Kit2019, RGB8, gamma/rang ajustats, mosaic normalitzat a fase/incidència60°; projector local sense relighting d’earthshine. No és objectiu fotomètric. CacheV39 vs origenV22 dins1DN16. La referència exacta V58 continua la de la ronda anterior.
- Registre numèric de DHS400/530 fora de marca+50px; només es remostregen referències, mai el projecte. Banda normalitzada σ16-64: marcaV68 residual−1,099σ davantLROC; DHS400−0,203, DHS530−0,307. σ són unitats de banda, no significació. DHS200 comparteix400 segons fitxa primària i no compta com independent. Fitxes400/530 declaren captures reals però no tot el processament lunar específic.
- Màscara/alfa opacs; residual geomètric d’aproximadament1px no explica150px. A5 corba global V49 anterior→Pere: RMS reservat6,04DN16, mediana residual marca0. PreCR→Pere σ16: RMS43,18, mediana−15,02. El nou revelat dePere no introdueix una taca local apreciable.
- A4 reprodueix **el canal G** deV53 a0DN16 (no confondre amb comprovació RGB completa). Error S8: falta−0,5 en coordenada dels centres dels sectors. Correcció exacta prova: marca−101,5…+62,0DN16, mediana−10,8; taca gairebé igual. No promoguda. No clipping deG a la marca.
- Injeccions amb reestimació S8: gaussiàσ50 ±200DN16 a la marca té guany1,168/1,199; altres posicions0,43…0,60. Camp suau no equival a preservar senyal ample. És resposta del productor de pantalla, no albedo físic.
- B1 pilot nou d’ales64/128/256:21campsD0,5fotogrames d’ajust, radi260-390, exclusió de marca+guarda a l’ajust de coeficients. Senyal lunar comú+plans de fotograma confonen el component estàtic: només0,531% de normaσ256 retinguda, guany d’error0,0074%, coeficient0,02244±0,01627condicional; èpoques0,0877 vs0,00559. No identificat. Els16 reservats tenen predictors però **no validació predictiva completa**. El centrat dels donants hereta r<350 i inclou part de la marca: no és exclusió total del pilot. No promoure.

## Producte i fitxers

- Informe complet: [{report.name}](<{report}>); PDF8pàgines: [{pdf.name}](<{pdf}>).
- Codi: `{T}`. A2radis, A3models directes exploratoris, A4S8/injeccions, A5corba global, A6DHS, B1ales amples. `A3` admet coeficients negatius de diagnòstic: no és un inversor físic ni un productor fotogràfic.
- Dades/rebuts: `{O}`. `Z1_preservation.json` verifica V67 i V68 exactes i estat Photoshop. `COMPARACIONS_NUMERIQUES.csv` conté els números d’A6.
- Candidate `arrays/A4_centered_candidate.npz` **NO APROVAT**, no copiar-lo al PSB. `s8_operator.py` és reproducció aïllada amb opció de correcció angular; l’S8 històric roman intacte.
- Fitxer general V68 SHA8d5fbf033fa3b61b58a2f07526071b7402f4b3b2527bd0f5e436da842eea7f0a. V67 deDownloads SHA6d31fc44531040de4582bbd854553b5c1736f6c8745e054ef4e22b049a4c1e15.
- Documents Photoshop59/V67 i822/V68 continuen **no desats**, preservats. Zero documents propis creats, cap visibilitat/canal/màscara/matriu dePere modificat.

## Continuïtat

La petició de correcció resta sense completar; no es demana un altre permís per continuar una via acotada que aporti informació nova. Cal un model o una mesura que distingeixi la llum dispersa comuna del patró lunar, amb controls de senyal ample, Sony reservada i contorn preservat. No repetir només la correcció4-12px, no donar93controls de detall com a prova del to ample, no pintar una compensació fins que s’assembli aLROC/DHS, no copiar píxels externs, no desfer l’encaix manual.

No extrapolar «B1 no identifica» a una impossibilitat universal de totes les dades. No retirar totS8: recupera el vel/contorn ja rebutjat. Els mètodes antics de PSF curta i les proves deV50 són història amb els seus límits. Aquesta ronda no resol ni reobre les perles ni les estrelles.

DataUTC: {now}. Tres revisions auxiliars només lectura; codi i rebuts persistits per l’únic escriptor. El tancament i l’alliberament del claim consten a CODEX_STATUS.
'''
assert not handoff.exists();handoff.write_text(body)
prefix=f'> **14-09-2026 · Investigació profunda de la taca ampla V68: sense correcció nova validada.** LROC és una textura CGI amb fotometria no equivalent. DHS400/530 corroboren una depressió menys marcada; V68 continua pendent. El nou revelat de Pere és global. S8 altera senyal ample i té un error de mig sector; corregir-lo no cura la taca. Pilot de21camps amb ales64/128/256: component estàtic no identificat; cap PASS predictiu dels16reservats. V67/V68 i encaix manual exactes; documents59/822 no desats preservats. CapV69. Informe `{pdf}`; represa `{handoff}`. Els límits i contrafactuals consten al report.\n\n'
rows=[]
for i,q in enumerate(start['authorities']):
 p=Path(q['path']);b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==q['sha256'];snap=O/'receipts'/f'authority_before_{i}_{p.name}';assert not snap.exists();snap.write_bytes(b)
 if p.name=='ACTIVE.json':
  a=json.loads(b);a['updated']=now;a['formal_worktree_handoff']=str(handoff);a['current_product']['orange_mark_review']=dict(status='DEEP_INVESTIGATION_NO_CORRECTION_QUALIFIED',report=str(report),pdf=str(pdf),handoff=str(handoff),new_pixel_correction=False);a['general_integration_task']['pending']='Broad orange mark remains uncorrected. CGI reference photometry qualified; S8 response distortion and partial-sector error audited; broad-wing temporal pilot not identified.';a['general_integration_task']['handoff']=str(handoff);a['visual_task']=dict(status='BROAD_MARK_NOT_CORRECTED',target='/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V68.psb',next_action='A new causal broad-field hypothesis with independent validation is needed; preserve manual geometry and user unsaved documents.',handoff=str(handoff));new=(json.dumps(a,ensure_ascii=False,indent=2)+'\n').encode()
 else:new=prefix.encode()+b
 tmp=p.with_name(p.name+'.broad_review.tmp');assert not tmp.exists();tmp.write_bytes(new);assert p.read_bytes()==b;os.replace(tmp,p);rows.append(dict(path=str(p),before_sha256=q['sha256'],after_sha256=sha(p),snapshot=str(snap)))
assert sha(R/'.coordination/CLAUDE_STATUS.md')==start['claude_status_sha256']
(O/'Z2_authorities.json').write_text(json.dumps(dict(time=now,rows=rows,handoff=str(handoff),report=str(report),pdf=str(pdf),CLAUDE_STATUS_unchanged=True),indent=2)+'\n')
with (R/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n## {now} · DEEP BROAD-MARK INVESTIGATION DOCUMENTED · CLAIM HELD\nNo new correction qualified; no V69. CGI LROC photometry non-equivalent; DHS comparisons strengthen concern about excess broad contrast. S8 exact G reproduction, half-sector bug and refitted broad-signal distortion audited; angular candidate insufficient. Broad-wing21field pilot cannot identify stable amplitude; no complete16heldout prediction. V67/V68 SHA exact, user documents59/822 preserved unsaved. PDF8pages and reproducible receipts reviewed. Handoff {handoff}. Correction request remains incomplete.\n')
print(handoff,flush=True)
