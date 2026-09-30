"""Keep the full V85 objective intact; record completion and blocker evidence."""
from pathlib import Path
import datetime
import hashlib
import json
import sys

R = Path(__file__).resolve().parents[3]
O = R / '4-RESULTATS/v85_regeneracio_20260922'
CID = 'CODEX_V85_REGENERACIO_20260922'

def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def guard():
    owner = json.loads((R / '.coordination/claim.lock/owner.json').read_text())
    assert owner['claim_id'] == CID and owner['round'] == 'R04'

def prepare():
    assert not (O / 'R04_COMPLETION_AUDIT.json').exists()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipts = {
        name: json.loads((O / name).read_text())
        for name in ['REBUT.json', 'PHOTOSHOP_GATE.json', 'NATIVE_INTEGRITY.json',
                     'FINAL_NATIVE_VISUAL_QA.json', 'SCIENTIFIC_DECISION.json',
                     'SKILL_R03_QA.json', 'R04_NATIVE_PRESERVATION.json']
    }
    for row in receipts['SKILL_R03_QA.json']['reference_changes']:
        assert sha(Path(row['path'])) == row['after']
    for row in receipts['SKILL_R03_QA.json']['skills']:
        assert sha(R / row['canonical']) == row['sha256']
    memory_updates = json.loads((O / 'R03_lessons/UPDATE_RECEIPT.json').read_text())
    for key in ['memory_note', 'camera_diagnostic_memory_note']:
        assert Path(memory_updates[key]).is_file()
    assert all(row['unchanged'] for row in receipts['R04_NATIVE_PRESERVATION.json']['files'])
    assert not receipts['SCIENTIFIC_DECISION.json']['all_artifacts_resolved']
    requirements = [
        {'id': 'V85_FROM_V84', 'status': 'PROVEN_WITHIN_NATIVE_SCOPE',
         'evidence': ['REBUT.json', 'PHOTOSHOP_GATE.json', 'R04_NATIVE_PRESERVATION.json'],
         'finding': 'Native V85 42 layers opens at10551x7506 RGB16; latest user V84 and V85 bytes verified unchanged.'},
        {'id': 'GREEN_MARK_FIRST', 'status': 'PROVEN_PRESENTATION_CORRECTION',
         'evidence': ['FINAL_NATIVE_VISUAL_QA.json', 'HIGHLIGHT_NATIVE_MEASUREMENTS.json', 'RESULTAT.md'],
         'finding': 'Marked red clipping71.8248percent to0 among22857pixels; correction common to RGB before final adjustments. No raw green-radiance correction claimed.'},
        {'id': 'ALL_CORONAL_FILTERS_REGENERATED', 'status': 'PROVEN_CONSTRUCTION',
         'evidence': ['filters_selected/MANIFEST.json', 'NATIVE_INTEGRITY.json', 'REBUT.json'],
         'finding': '17 filter layers consume16 regenerated distinct rasters including hidden layers; frozen geometry and editorial input reuse declared, not full RAW-to-PSB determinism.'},
        {'id': 'ALL_MOON_EXCLUDED', 'status': 'PROVEN',
         'evidence': ['NATIVE_INTEGRITY.json'],
         'finding': 'All17filter masks zero over653168lunar pixels; output Moon composite exact.'},
        {'id': 'MOVING_LIMB_CONTAMINATION_RESOLVED_ESPECIALLY_WOW', 'status': 'NOT_ACHIEVED',
         'evidence': ['SCIENTIFIC_DECISION.json', 'R02_DIAGNOSTIC_STATE.md', 'R03_DIAGNOSTIC_STATE.md',
                      'marks246_pres4_R02/WOW_comparison.png', 'camera_channels_R03/DECISION.json'],
         'finding': 'Residual marked arcs and source contrast remain. No complete source correction accepted. Candidate failures include observable regressions and support loss, not only hidden-signal oracle failure.'},
        {'id': 'SIMILAR_OR_PREFERABLY_SUPERIOR_TO_V84', 'status': 'PARTIALLY_PROVEN_NOT_GLOBAL',
         'evidence': ['RESULTAT.md', 'SCIENTIFIC_DECISION.json', 'PRES4_R02_DECISION.json', 'early_epoch_R03/DECISION.json'],
         'finding': 'Scoped improvements coexist with transfer and external morphology regressions; full requested quality cannot be certified.'},
        {'id': 'PRESERVE_ORIGINALS_AND_MANUAL_MOON', 'status': 'PROVEN_WITHIN_DECLARED_CHANGES',
         'evidence': ['R04_NATIVE_PRESERVATION.json', 'NATIVE_INTEGRITY.json', 'FINAL_NATIVE_VISUAL_QA.json'],
         'finding': 'V84 unchanged,140unplanned original channels exact, Moon653168pixels exact, native newRGB tolerance1DN16; no FOV change.'},
        {'id': 'UPDATE_SKILLS_AND_PROJECT_MEMORY', 'status': 'PROVEN_DOCUMENTATION',
         'evidence': ['SKILL_R03_QA.json', 'R03_lessons/UPDATE_RECEIPT.json', 'IA/Skills/README.md'],
         'finding': 'Canonical and checked consumer references match current hashes; authorized memory update notes exist. Full repair remains expressly unachieved.'}
    ]
    evidence = []
    for n in ['SONY_INNER_SUPPORT_R02.json', 'inner_brno_pres4_R02/GEOMETRIC_COVERAGE.json',
              'GEOMETRY_PSF_R03.json', 'F4_PAIR_COVERAGE_R03.json',
              'early_epoch_R03/DECISION.json', 'camera_channels_R03/DECISION.json',
              'PRES4_R02_DECISION.json', 'WORKING_STATE_R02.json', 'WORKING_STATE_R03.json',
              'R04_NATIVE_PRESERVATION.json']:
        evidence.append({'path': n, 'sha256': sha(O / n)})
    audit = {
        'utc': now, 'full_goal_complete': False, 'requirements': requirements,
        'previous_goal_turn': {'round': 'R03', 'classification': 'PROGRESS',
                               'evidence': 'New early-epoch and channel hypotheses tested; geometry/PSF assumptions corrected'},
        'blocking_condition': 'Residual inner-limb radiance is not separated from instrumental/geometry response; no qualified clean independent observation or validated early-short-epoch local forward response exists for component 1.',
        'same_condition_consecutive_turns': ['R02', 'R03', 'R04'],
        'count': 3,
        'not_a_permission_or_runtime_blocker': True,
        'not_just_hidden_injection_failure': True,
        'candidate_changes_rejected_for_observable_reasons': [
            'preS4 loses all80component1triplets and worsens bilateral Brno',
            'q16 radiance introduces negative G',
            'early6 does not change upper-arc contrast and worsens other components',
            'cameraG retains the upper depression before the color matrix'],
        'remaining_diagnostics_scope': {
            'relative_F4_early_pairs': 'Can assess relative ordering only; cannot identify absolute interior radiance or validate a corrective source. Not executed as a restoration route.',
            'observable_only_injection': 'Can separate visible retention from unknown continuation; does not correct the real marked source contamination. Existing failures retained.'},
        'resume_requires': [
            'An independently registered clean observation covering the inner marked arc at adequate resolution',
            'Or an independently validated forward response for early short frames including local PSF/wings, pixel response and physical occultation geometry, with uncertainty and excluded-sample validation'],
        'scope_limit': 'This is the current limit of investigated data and validated models, not proof of mathematical or observational impossibility.',
        'evidence': evidence,
        'independent_reviews': ['qa_regeneration requirement audit', 'filter_sources next-action challenge', 'limb_diagnosis relative-geometry feasibility'],
        'goal_status_request': 'blocked',
        'status_tool_called': False
    }
    save(O / 'R04_COMPLETION_AUDIT.json', audit)
    print('R04_COMPLETION_NOT_PROVEN_BLOCK_AUDIT_READY')

def finish():
    tool = json.loads((O / 'R04_GOAL_STATUS.json').read_text())
    assert tool['status'] == 'blocked'
    assert not (O / 'WORKING_STATE_R04.json').exists()
    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.isoformat()
    audit = json.loads((O / 'R04_COMPLETION_AUDIT.json').read_text())
    audit['status_tool_called'] = True
    audit['goal_status'] = 'blocked'
    save(O / 'R04_COMPLETION_AUDIT.json', audit)
    state = {'utc': stamp, 'round': 'R04', 'goal_status': 'blocked', 'goal_complete': False,
             'delivery_still': '1-PHOTOSHOP/V85.psb (R01 bounded)',
             'no_new_PSB': True, 'serial_writes': 'RELEASED', 'owner': None, 'released_utc': stamp,
             'active_calculations': [], 'helpers_finished': True,
             'blocking_condition': audit['blocking_condition'], 'resume_requires': audit['resume_requires'],
             'goal_block_audit': {'consecutive_turns': ['R02', 'R03', 'R04'], 'threshold_met': True,
                                  'scope': 'No qualified correction currently actionable; not difficulty or an unpassed hidden-data oracle alone'}}
    save(O / 'WORKING_STATE_R04.json', state)
    report = '''# V85 — auditoria final de l'encàrrec

**V85 existeix i és llegible, però l'objectiu íntegre queda bloquejat perquè la contaminació del limbe no està resolta amb una correcció validada.** El lliurament continua sent R01. No s'ha modificat cap PSB durant R02–R04.

| Punt de l'encàrrec | Resultat verificat |
|---|---|
| Nova V85 des de V84 | 42 capes, 10551×7506 RGB16; Photoshop OBRE |
| Verd marcat | Correcció de presentació: retall vermell 71,82 % → 0 % als 22.857 píxels marcats |
| Tots els filtres | 17 capes, 16 ràsters regenerats, inclosos els ocults |
| Exclusió lunar | 17 màscares negres als 653.168 píxels lunars |
| Preservació |V84 intacta; compost lunar exacte; 140 canals originals no previstos per canviar exactes |
| Limbe corregit, especialment WOW |**No assolit**: resten arcs i resposta de vora no identificada |
| Qualitat global similar o superior |Millores parcials; superioritat global no demostrada |
| Skills i memòria |Actualitzades amb causes comprovades, límits i proves negatives |

El mateix impediment s'ha comprovat a R02, R03 i R04. Al veí interior dels 80 triplets de l'arc superior no hi ha una observació neta alternativa qualificada: Vixen aporta resposta de vora, Sony no té pes net i Brno no cobreix triplets complets. Les PSF existents i el contorn aparent F4 no determinen independentment la resposta dels primers fotogrames curts. La depressió persisteix al verd de càmera abans de la matriu RGB.

El resultat no depèn només de les proves sintètiques: eliminar S4 perd suport; altres variants empitjoren Brno o introdueixen senyal invàlid. Les injeccions sota la Lluna combinen retenció i continuació desconeguda; les seves fallades no equivalen directament a pèrdua del detall visible.

La prova relativa entre contorns F4 podria estudiar ordenacions entre fotogrames, però no fixaria la radiància correcta ni validaria per si sola una nova font. No s'ha executat com si pogués desbloquejar aquesta mancança. Tampoc s'ha ocultat la franja eliminant suport o rebaixant filtres.

Per reprendre una correcció fonamentada cal una observació independent neta de l'arc interior, o un model de resposta local dels curts validat independentment —PSF, ales, resposta del píxel i geometria física— amb incerteses comprovades. Això descriu el límit actual dels materials i models investigats, no una impossibilitat absoluta.

Auditoria per requisit: `R04_COMPLETION_AUDIT.json`. Hashes natius acabats de recalcular: `R04_NATIVE_PRESERVATION.json`. Estat: `WORKING_STATE_R04.json`. No queda cap procés propi en execució.
'''
    (O / 'R04_FINAL_STATUS.md').write_text(report)
    handoff = '''# Traspàs V85 R04 — objectiu bloquejat, no complet

Lliurament vigent `1-PHOTOSHOP/V85.psb`, R01. Entrada curta: `4-RESULTATS/v85_regeneracio_20260922/R04_FINAL_STATUS.md`; contracte de represa i comprovació per requisit a `R04_COMPLETION_AUDIT.json`. R02–R04 no han canviat el PSB. La integritat actual s'ha verificat recalculant completament els SHA de V84 i V85.

Falta separar la radiància interior de la resposta instrumental/geometria. No repetir les variants de domini, farciment, S4, època o matriu ja rebutjades. Conservar negatius i numeradors reservats. Cap FOV, RAW, calibrador, encaix, màscara manual o Camera Raw modificat. No declarar acabat perquè Photoshop obre ni perquè hi ha 17 filtres nous.

Goal `blocked` després de revalidar la mateixa condició als torns R02/R03/R04. Una represa expressa inicia una auditoria nova del bloqueig. Cap procés propi pendent, agents acabats. `serial_writes: RELEASED`, `owner: null`; adquirir un claim nou abans de qualsevol mutació.
'''
    (R / '.coordination/HANDOFF_2026-09-22_V85_R04.md').write_text(handoff)
    status_path = R / 'IA/ESTAT_ACTUAL.md'
    (O / 'ESTAT_ACTUAL_before_R04.md').write_bytes(status_path.read_bytes())
    prefix = '''# V85 R04 — objectiu bloquejat, 22-09-2026

V85 R01 conserva els 17 filtres regenerats, el verd de presentació corregit i la Lluna exacta. **La contaminació íntegra del limbe continua sense correcció validada.** La mateixa mancança d'observació/resposta independent s'ha revalidat durant tres torns; goal `blocked`, no complet. V84 i V85 verificades de nou per SHA. Cap procés pendent. Auditoria i criteris per reprendre: `4-RESULTATS/v85_regeneracio_20260922/R04_FINAL_STATUS.md`; traspàs `.coordination/HANDOFF_2026-09-22_V85_R04.md`.

'''
    status_path.write_text(prefix + status_path.read_text())
    note = Path('/Users/USUARI/.codex/memories/extensions/ad_hoc/notes') / (now.strftime('%Y-%m-%dT%H-%M-%SZ') + '-eclipse-v85-final-status.md')
    assert not note.exists()
    note.write_text('''# V85: estat final parcial i impediment obert

Actualització autoritzada per Pere dins l'encàrrec V85; projecte canònic Desktop/Eclipse 2026.
V85 R01: 17 capes de filtres regenerades, verd de presentació corregit i 653.168 píxels lunars exactes. V84 preservada. No donar tot el limbe per resolt: els pilots R02/R03 no s'han promogut. R04 revalida els SHA i marca el goal blocked després de tres torns amb la mateixa manca d'ancoratge independent de radiància/resposta al component 1.
Per reprendre: observació neta adequada o resposta local primerenca/PSF/geometria validada independentment. No és una impossibilitat absoluta ni un bloqueig de permisos. No repetir variants negatives ni assimilar fallades d'injecció oculta a pèrdua equivalent de detall visible.
Entrada: 4-RESULTATS/v85_regeneracio_20260922/R04_FINAL_STATUS.md i R04_COMPLETION_AUDIT.json. Skills vigents: SKILL_R03_QA.json. Originals i negatius preservats.
''')
    files = ['R04_COMPLETION_AUDIT.json', 'R04_GOAL_STATUS.json', 'R04_NATIVE_PRESERVATION.json',
             'WORKING_STATE_R04.json', 'R04_FINAL_STATUS.md']
    manifest = {'utc': stamp, 'goal_status': 'blocked', 'goal_complete': False,
                'files': [{'path': str((O / n).relative_to(R)), 'sha256': sha(O / n)} for n in files],
                'memory_note': str(note), 'memory_note_sha256': sha(note),
                'serial_writes': 'RELEASED', 'owner': None, 'released_utc': stamp}
    for name in ['.coordination/HANDOFF_2026-09-22_V85_R04.md', 'IA/ESTAT_ACTUAL.md',
                 '3-RECERCA/tools/v85_regeneracio_20260922/a91_completion_block_audit.py']:
        manifest['files'].append({'path': name, 'sha256': sha(R / name)})
    save(O / 'R04_RECEIPT_MANIFEST.json', manifest)
    with (R / '.coordination/CODEX_STATUS.md').open('a') as f:
        f.write('\n' + stamp + ' · V85 R04 RELEASED; serial_writes: RELEASED; owner: null; released_utc: ' + stamp + '. Goal blocked after three consecutive verified turnsR02/R03/R04 with the same missing independent inner-limb response/observation. Native V84/V85 fullSHA unchanged.17filters/green/Moon complete in stated scopes; complete limb correction and global quality unproven. No pending processes/helpers. Handoff .coordination/HANDOFF_2026-09-22_V85_R04.md; receipt 4-RESULTATS/v85_regeneracio_20260922/R04_RECEIPT_MANIFEST.json.\n')
    guard()
    (R / '.coordination/claim.lock/owner.json').unlink()
    (R / '.coordination/claim.lock').rmdir()
    print('R04_RELEASED_GOAL_BLOCKED_NOT_COMPLETE')

if __name__ == '__main__':
    guard()
    {'prepare': prepare, 'finish': finish}[sys.argv[1]]()
