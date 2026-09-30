"""Close this diagnostic round, preserve delivery and release only our claim."""
from a4_sources import *

def main():
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();lock=R/'.coordination/claim.lock/owner.json';claim=json.loads(lock.read_text());assert claim['claim_id']==CID
 handoff=R/'.coordination/HANDOFF_2026-09-22_V85_R02.md'
 for scope in ['.coordination/HANDOFF_2026-09-22_V85_R02.md','IA/ESTAT_ACTUAL.md']:
  if scope not in claim['scope']:claim['scope'].append(scope)
 save(lock,claim)
 assert json.loads((O/'R02_NATIVE_PRESERVATION.json').read_text())['R02_changes_to_native_PSB'] is False
 assert all(r['valid_samples']==0 for r in json.loads((O/'SONY_INNER_SUPPORT_R02.json').read_text())['root_verified_weights'])
 p=O/'R02_DIAGNOSTIC_STATE.md';s=p.read_text();old='Resta una comprovació geomètrica acotada: si Sony ofereix una observació independent neta del veí interior del component1. Només després d’això es pot formular amb precisió què falta per validar-ne la radiància. Estat viu `WORKING_STATE_R02.json`.'
 # Previous text uses straight apostrophes, so replace the final paragraph by anchor.
 anchor='Resta una comprovació geomètrica acotada:';assert anchor in s;s=s[:s.index(anchor)]+'''La comprovació Sony també és negativa: els 21 fotogrames admesos no ofereixen cap mostra neta al veí interior dels 80 triplets. Root ha comprovat denominadors RGB i count zero sense carregar radiància; la geometria independent situa Sony A per sota de D2 i B dins del limbe modelat. `SONY_INNER_SUPPORT_R02.json`.

No s'ha trobat una correcció que resolgui tot el llimb conservant el detall amb evidència suficient. Falta una observació independent adequada o un model de resposta al limbe/PSF/registre validat fora d'aquesta mateixa marca. Això no prova impossibilitat absoluta; és el límit de les dades i mètodes comprovats. La diagnosi R02 queda tancada, la petició completa continua oberta i no es declara goal complet.

Cap càlcul propi pendent; agents acabats. Claim alliberat al tancament. Estat `WORKING_STATE_R02.json`; traspàs `.coordination/HANDOFF_2026-09-22_V85_R02.md`. El rebut de preservació nativa s'ha verificat per SHA de les dues PSB.
''';p.write_text(s)
 state=json.loads((O/'WORKING_STATE_R02.json').read_text());state.update(utc=now,status='ROUND_COMPLETE_NO_CANDIDATE_PROMOTED_GOAL_INCOMPLETE',claim=CID+' RELEASED',active=None,next=['Only resume mutation with a new justified causal hypothesis or independently validated limb response; preserve frozen holdouts and all negative results','Do not repeat rejected padding/domain sweeps or silently mask lost support'],goal_complete=False,unresolved_condition='No verified correction for the residual inner limb; component1 interior has no clean Vixen/Sony observation or usable Brno triplet. An independently validated response model or new independent evidence is required for a stronger restoration claim.',goal_block_audit={'first_documented_goal_turn_with_this_complete_coverage_result':True,'consecutive_qualifying_turns_observed':1,'status_not_marked_blocked':'Tool requires at least three consecutive goal turns with same blocking condition; this round also made meaningful progress.'});state['completed']+=['Sony independent support audit: no clean inner coverage','native V84/V85 SHA unchanged','independent review of inner Brno method'];save(O/'WORKING_STATE_R02.json',state)
 refs=['PHYSICAL_T_R02_DECISION.json','SOLAR_R02_DECISION.json','MOMENT_R02_DECISION.json','PRES4_R02_DECISION.json','MOMENT_R02_BOUNDARY_QA.json','BRNO_MOMENT_R02_QA.json','BRNO_PRES4_R02_QA.json','inner_brno_pres4_R02/QA.json','inner_brno_pres4_R02/GEOMETRIC_COVERAGE.json','marks246_pres4_R02/SUPPORT_LOSS.json','bias_component_R02/RECEIPT.json','bias_component_R02/DECOMPOSITION.json','TEMPORAL_CALIBRATION_R02.json','SONY_INNER_SUPPORT_R02.json','R02_NATIVE_PRESERVATION.json','SKILL_R02_QA.json','R02_DIAGNOSTIC_STATE.md']
 save(O/'R02_RECEIPT_MANIFEST.json',{'utc':now,'files':[{'path':q,'sha256':sha(O/q)} for q in refs],'native_delivery':'R01 unchanged','all_artifacts_resolved':False,'goal_complete':False})
 handoff.write_text('''# V85 R02 — traspàs de diagnosi

Llegir primer `4-RESULTATS/v85_regeneracio_20260922/R02_DIAGNOSTIC_STATE.md` i `WORKING_STATE_R02.json`. Codi nou a73–a82; fases anteriors a41–a72 al mateix directori `3-RECERCA/tools/v85_regeneracio_20260922`.

`1-PHOTOSHOP/V85.psb` continua sent R01: 17 capes/16 ràsters regenerats, verd de presentació corregit, Lluna nativa exacta, Photoshop OBRE, límits de transferència declarats. V84 i V85 rehashades intactes en `R02_NATIVE_PRESERVATION.json`. Cap candidat R02 s'ha incorporat.

R02 descarta domini físic, disc solar, moments quadràtics i pre-S4 com a paquet de substitució. Ha identificat la sensibilitat B(D) de l'arc superior i verificat que no hi ha observació neta Vixen/Sony ni triplet Brno usable al seu veí interior. No confondre aquesta sensibilitat amb demostració que B(D) sigui errònia. Pre-S4 perd2.880píxels efectius i tots80triplets h4 de component1; no és una cura.

Skills i nota de memòria rectificades. `SKILL_R02_QA.json` és la comprovació vigent; R01 `SKILL_FINAL_QA.json` es conserva històric. No reconstrucció RAW→PSB completa declarada, no corona oculta recuperada, no PSF mesurada en la comparació Brno. Els Pearson locals són descriptius i les mostres estan correlacionades.

No repetir una variant rebutjada ni ajustar amb els sis numeradors reservats. Una continuació científica necessita una hipòtesi nova i validable de resposta al limbe/PSF/registre o nova evidència independent. L'encàrrec de tot arreglat continua incomplet; el goal no s'ha marcat complet ni pausat. Cap procés propi pendent, agents acabats, claim RELEASED. Reprendre amb claim propi abans de mutar.
''')
 status=R/'IA/ESTAT_ACTUAL.md';oldstatus=status.read_text();(O/'R02_lessons/IA_STATUS_before_R02_checkpoint.md').write_text(oldstatus);status.write_text('''# Nota V85 R02 — 22-09-2026

R02 ha acabat la diagnosi sense promoure cap candidat. La V85 lliurada R01 continua intacta; no queda acreditat tot el llimb resolt. Candidats i límits a `4-RESULTATS/v85_regeneracio_20260922/R02_DIAGNOSTIC_STATE.md`; traspàs `.coordination/HANDOFF_2026-09-22_V85_R02.md`. Skills/memòria rectificades, originals protegits. L'encàrrec complet continua obert.

'''+oldstatus)
 with (R/'.coordination/CODEX_STATUS.md').open('a') as f:f.write('\n'+now+' · V85 R02 RELEASED; serial_writes: RELEASED; owner: null; released_utc: '+now+'. Claim '+CID+'. R02 no candidate promoted; native V84/V85 hashes unchanged. Physical/solar/moment/preS4 negatives preserved, B(D) source mechanism traced, no clean independent coverage at component1 inner samples. Skills/index/memory corrected. Goal incomplete; no global artifact PASS. Handoff .coordination/HANDOFF_2026-09-22_V85_R02.md; receipt 4-RESULTATS/v85_regeneracio_20260922/R02_RECEIPT_MANIFEST.json. No owned calculations pending; helpers finished.\n')
 assert json.loads(lock.read_text())['claim_id']==CID;lock.unlink();lock.parent.rmdir();print('R02_CHECKPOINT_AND_RELEASE_COMPLETE')

if __name__=='__main__':guard();main()
