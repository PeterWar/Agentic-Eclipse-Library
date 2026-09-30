from pathlib import Path
import json,hashlib,datetime,os
R=Path.cwd();O=R/'output/v68_lroc_revisio_20260914';P=R/'output/v68_artefactes_20260914';IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');claim='CODEX_V68_LROC_REVIEW_20260914';lock=R/'.coordination/claim.lock/owner.json';owner=json.loads(lock.read_text());assert owner['claim_id']==claim
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
pub=json.loads((P/'E2_publish.json').read_text());source=json.loads((P/'A1_layers.json').read_text());assert sha(pub['path'])==pub['sha256'];assert sha('/Users/USUARI/Downloads/V67.psb')==source['sha256']
now=datetime.datetime.now(datetime.timezone.utc).isoformat();report=O/'RESULTAT.md';handoff=R/'.coordination/HANDOFF_2026-09-14_V68_TACA_LROC_REOBERTA.md'
body=f'''# Revisió de la taca taronja de V67/V68 contra la capa LROC exacta

Pere aclareix que veu l'artefacte en comparar l'earthshine amb **Compara LROC · alineada V58**. La marca assenyala una discrepància de to ampla. **La correcció fina de V68 no la resol. Es retira la conclusió anterior que la forma ampla ja quedava validada per les referències.**

S'ha llegit la capa62 exacta del PSB, bbox(4881,3280,5872,4271), i s'ha comparat amb la capa30 a la mateixa graella de Pere. Els154controls V68 certifiquen que la capa62 no havia canviat. La comparació inicial B3 de V68 emprava el cache LROC anterior a V58 i no caracteritzava aquesta discrepància ampla; els controls de bandes fines no validaven el seu to.

## Resultats confirmats

1. **Diferència visible:** la taca fosca inferior és molt més marcada al nostre revelat que a LROC. [Comparació directa](<{O/'vistes/COMPARACIO_TACA_LROC.png'}>). Cada panell usa un estirament lineal local declarat; això és inspecció, no equivalència radiomètrica entre dues imatges diferents.
2. **No és una ombra de la màscara:** als25.258píxels del rectangle marcat, alfa i màscara de la capa30 són65535. La discrepància ja és al RGB de la Lluna, abans de compondre'l amb la corona.
3. **Geometria:** ajust diagnòstic només de la referència, excloent la marca i50px al voltant, amb sectors alterns reservats. Lineal: dx+1,052px,dy−0,162px,gir+0,0306°,escala−0,0124%; log: dx+1,064,dy−0,273,+0,0152°,−0,0158%. Correlació reservada lineal0,7665→0,7697. El residual d'aproximadament1px no explica una taca de prop de150px. Cap matriu aplicada a cap PSB; no és una nova validació astromètrica absoluta.
4. **Història:** la depressió de llum ja és a la font V45 prèvia al Camera Raw i al revelat V49. La resta del vel V53 modifica el nivell i l'aspecte ample, però no és l'origen únic. DeV53 aV68 la mediana del canvi al rectangle és0DN16; els reforços de detall i el patró fi no han corregit la discrepància ampla.
5. **Abans de l'apilat:** també es distingeix en tres fotogrames calibrats Sony (DSC06987/06993,8s;06984,2s) i tres Vixen (572A2982/2983/2984,10s). El camp multiplicatiu φ del processat val exactament1 en tota la marca als sis, de manera que aquest camp no hi crea la taca. Són dos equips amb calibracions pròpies, no sis experiments estadísticament independents. Aquests fotogrames encara contenen llum solar dispersada i calibració: observar-hi la depressió **no demostra que tota la foscor sigui albedo lunar real**.

## Què queda obert

No s'ha separat causalment la contribució del senyal lunar, la llum dispersada i la resposta del revelat a aquesta escala ampla. Tampoc s'ha establert una equivalència fotomètrica entre LROC i les nostres preses. Per tant, no s'ha validat una correcció nova i no es pot aclarir la taca fins que s'assembli a LROC com a criteri únic.

El següent assaig ha de tractar aquesta escala ampla i incloure explícitament la marca reservada. Cal comprovar l'estimació del fons dispersat i la resposta de contrast, amb Vixen com a productor i Sony reservada, controls fora de la marca i retenció de les estructures. No reprendre només el filtre de4–12px ni donar93/93controls de detall com a validació de la fotometria ampla. Mantenir intacte l'encaix manual. No incorporar píxels LROC a la fotografia.

## Integritat i represa

V67 i V68 desades exactes: SHA V67`{source['sha256']}`, V68`{pub['sha256']}`. Documents Photoshop59/V67 i822/V68 oberts **amb canvis no desats de Pere**, preservats. Cap nova versió, cap canvi de píxels, geometria, màscares o visibilitats en documents de Pere durant aquesta revisió. El producte continua [V68.psb](<{pub['path']}>), amb aquesta qualificació posterior.

Codi: `research/tools/v68_lroc_revisio_20260914/`; rebuts A1referència exacta, A2història, A3registre de diagnòstic, A4sisfotogrames/campφ, A5cobertura. Les imatges de les fonts s'han aclarit o suavitzat només per veure-les. Cap estirament diagnòstic entra al PSB. DataUTC: {now}.
'''
for p in [report,handoff]:assert not p.exists();p.write_text(body)
owner['scope'].append('Qualification of V68 delivery record and canonical project pointers');lock.write_text(json.dumps(owner,indent=2)+'\n')
prefix=f'> **14-09-2026 · Revisió posterior de V68: taca taronja ampla contra LROC REOBERTA.** Pere es refereix a la diferència de to ampla, no només a la trama fina. Capa62 exacta V58 revisada; V68 no corregeix aquesta taca. **Retirada la conclusió que la forma ampla ja estava validada.** Alfa/màscara de30opacs a tota la marca; residual LROC~1px insuficient per explicar-la. Depressió ja visible abans deCameraRaw i en3Sony+3Vixen calibrats; campφ=1. La llum dispersada i la fotometria ampla encara no estan separades: presència a les fonts no prova tot l’albedo real. Cap nova correcció ni PSB; encaix manual i V67/V68 exactes. Documents59/822 dePere no desats, preservats. Informe `{report}`; represa `{handoff}`. La qualificació preval sobre la frase de corroboració ampla de sota.\n\n'
paths=[R/'AGENTS.md',R/'CLAUDE.md',IA/'README.md',IA/'ESTAT_ACTUAL.md',IA/'MAPA_RUTES_I_OUTPUTS.md',IA/'Coordinació/HANDOFF_VIGENT.md',IA/'ACTIVE.json'];expected={q['path']:q['after_sha256'] for q in json.loads((P/'E5_authorities.json').read_text())['rows']};old={str(p):p.read_bytes() for p in paths}
for p in paths:assert hashlib.sha256(old[str(p)]).hexdigest()==expected[str(p)],p
receipts=O/'receipts';receipts.mkdir(exist_ok=True);rows=[];cs=sha(R/'.coordination/CLAUDE_STATUS.md')
for i,p in enumerate(paths[:-1]):
 b=old[str(p)];snap=receipts/f'before_{i}_{p.name}';assert not snap.exists();snap.write_bytes(b);tmp=p.with_name(p.name+'.V68_lroc.tmp');assert not tmp.exists();tmp.write_bytes(prefix.encode()+b);assert p.read_bytes()==b;os.replace(tmp,p);rows.append(dict(path=str(p),before_sha256=hashlib.sha256(b).hexdigest(),after_sha256=sha(p),snapshot=str(snap)))
p=paths[-1];b=old[str(p)];snap=receipts/'before_ACTIVE.json';snap.write_bytes(b);a=json.loads(b);a['updated']=now;a['formal_worktree_handoff']=str(handoff);a['current_product']['orange_mark_review']=dict(status='BROAD_TONAL_DISCREPANCY_REOPENED_NOT_CORRECTED',report=str(report),handoff=str(handoff),new_pixel_correction=False);a['general_integration_task']['pending']='Broad orange-mark discrepancy vs exact LROC reference reopened. No correction qualified; V68 remains unchanged.';a['general_integration_task']['handoff']=str(handoff);a['visual_task']=dict(status='V68_ORANGE_BROAD_DISCREPANCY_REOPENED',target=pub['path'],next_action='Separate broad lunar signal, scattered light and photographic response with held-out validation. Preserve manual geometry. See new diagnosis.',handoff=str(handoff));tmp=p.with_name(p.name+'.V68_lroc.tmp');tmp.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');assert p.read_bytes()==b;os.replace(tmp,p);rows.append(dict(path=str(p),before_sha256=hashlib.sha256(b).hexdigest(),after_sha256=sha(p),snapshot=str(snap)));assert sha(R/'.coordination/CLAUDE_STATUS.md')==cs
# Preserve the original delivery report verbatim as history; prepend the clarified finding.
reports=[P/'RESULTAT.md',Path(pub['path']).with_name('V68_dades')/'LLEGEIX-ME_V68.md']
for i,p in enumerate(reports):
 b=p.read_bytes();(receipts/f'old_report_{i}.md').write_bytes(b);p.write_bytes(prefix.encode()+b)
(O/'Z0_receipt.json').write_text(json.dumps(dict(time=now,source_V67=source['sha256'],V68=pub['sha256'],report=str(report),handoff=str(handoff),rows=rows,CLAUDE_STATUS_unchanged=True,new_photographic_product=False),ensure_ascii=False,indent=2)+'\n')
with (R/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n## {now} · V68 ORANGE BROAD DISCREPANCY REVIEWED · CLAIM HELD\nExact LROC62 differs in broad tone from Moon30; prior fine-noise diagnosis was incomplete. Mask/alpha65535 throughout mark; reference registration residual~1px does not explain broad patch. Depression present in historical preCR source and6individual calibrated frames from2trains; multiplicative phi field1. Underlying lunar signal versus scattered light/photographic tone unresolved. No new PSB or pixel changes; V67/V68 source hashes exact; both user documents preserved unsaved. Handoff {handoff}.\n')
print('DOCUMENTED',report,flush=True)
