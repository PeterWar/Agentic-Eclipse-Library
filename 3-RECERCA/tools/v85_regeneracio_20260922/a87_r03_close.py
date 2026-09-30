"""Record the bounded R03 diagnostic without promoting or editing any PSB."""
from pathlib import Path
import datetime
import hashlib
import json

R = Path(__file__).resolve().parents[3]
O = R / '4-RESULTATS/v85_regeneracio_20260922'
T = R / '3-RECERCA/tools/v85_regeneracio_20260922'
CID = 'CODEX_V85_REGENERACIO_20260922'

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    owner_path = R / '.coordination/claim.lock/owner.json'
    owner = json.loads(owner_path.read_text())
    assert owner['claim_id'] == CID and owner['round'] == 'R03'
    assert not (O / 'WORKING_STATE_R03.json').exists(), 'No-clobber closure'
    for scope in ['IA/ESTAT_ACTUAL.md', '.coordination/HANDOFF_2026-09-22_V85_R03.md']:
        if scope not in owner['scope']:
            owner['scope'].append(scope)
    save(owner_path, owner)

    lessons = O / 'R03_lessons'
    qa_path = O / 'SKILL_R03_QA.json'
    update_path = lessons / 'UPDATE_RECEIPT.json'
    for p in [qa_path, update_path]:
        backup = lessons / (p.stem + '_before_clarification.json')
        assert not backup.exists()
        backup.write_bytes(p.read_bytes())
    rel = Path('corregeix-artefactes/references/limbe_lunar_earthshine.md')
    canonical = R / '.claude/skills' / rel
    consumer = Path('/Users/USUARI/.codex/skills') / rel
    assert canonical.read_bytes() == consumer.read_bytes()
    (lessons / 'limbe_before_final_clarification.md').write_bytes(canonical.read_bytes())
    content = canonical.read_text()
    old = 'La silueta aparent (50 %) fa **453,5**:'
    new = 'La silueta aparent F4, definida pel màxim de derivada radial, fa **453,5**:'
    assert content.count(old) == 1
    content = content.replace(old, new)
    old = '- Les tres vores amb el mateix detector: F4, forat de la base, alfa lunar; han de coincidir a ±1 px.'
    new = '- El criteri històric exigia les tres vores amb el mateix detector i coincidència a ±1 px. R03 comprova que F4, forat de la base i alfa lunar no es van mesurar amb el mateix detector; aquesta comparació no és una coincidència física verificada.'
    assert content.count(old) == 1
    content = content.replace(old, new)
    canonical.write_text(content)
    consumer.write_bytes(canonical.read_bytes())
    update = json.loads(update_path.read_text())
    for row in update['changes']:
        row['after'] = sha(Path(row['path']))
    update['final_clarification'] = 'Removed remaining F4=50percent statement and qualified unfulfilled historical same-detector criterion; prior text and receipts preserved.'
    save(update_path, update)
    qa = json.loads(qa_path.read_text())
    qa['reference_changes'] = update['changes']
    qa['historical_limb_reference_sha256'] = sha(canonical)
    qa['scope'] = 'Validate existing entrypoints and two updated references; no claim all skill assets synchronized'
    qa['R02_status'] = 'closed without native promotion; previous receipt preserved'
    save(qa_path, qa)

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state = {
        'utc': now, 'round': 'R03',
        'status': 'DIAGNOSTIC_COMPLETE_CLOSURE_REVIEW_PENDING',
        'delivery_still': '1-PHOTOSHOP/V85.psb (R01 bounded)',
        'claim': CID + ' HELD',
        'completed': ['Measured geometry and available PSF feasibility audit',
                      'Early6 versus same19 and mixed61 train-only source pilot',
                      'Fixed Brno component2/3 comparison on common valid support',
                      'Detector definition and PSF qualification corrections in skills and memory'],
        'candidate': 'early_epoch_R03: NOT_PROMOTED',
        'native_PSB_mutation': False, 'goal_complete': False,
        'active_calculations': [],
        'native_integrity_evidence': 'R02_NATIVE_PRESERVATION.json; no R03 PSB write, no fresh full-file hash claimed',
        'unresolved_condition': 'No verified correction for residual inner limb. Component1 lacks clean independent observations and the available optical/geometry response is not independently qualified for the early short frames.',
        'next': ['Require a new causal hypothesis or independent response/observation before further restoration',
                 'Do not reinterpret optical F4 radius as a universal physical radius correction',
                 'Do not repeat rejected domain/padding/epoch sweeps or replace lost support with claimed signal'],
        'goal_block_audit': {
            'same_condition_documented_goal_turns': ['R02', 'R03'],
            'consecutive_qualifying_turns_observed': 2,
            'this_turn_classification': 'PROGRESS: new source experiment and geometry/PSF qualification',
            'not_marked_blocked': 'Fewer than three consecutive goal turns; full goal remains active and incomplete'
        }
    }
    save(O / 'WORKING_STATE_R03.json', state)
    report = '''# V85 R03 — resultat de la diagnosi

La V85 desada continua sent el lliurament R01: 17 capes de filtres regenerades, correcció del verd de presentació i compost lunar preservat. R03 no ha modificat cap PSB. **Encara no queda resolt tot el limbe.**

## Selecció temporal comprovada

S'han recomposat les mateixes mostres Vixen de sis fotogrames primerencs (15,68–19,57 s, exposició 1/3200 s), els 19 curts i els 61 de train. Les sis mostres reservades no s'han utilitzat. La comparació principal és early6 contra same19; mixed61 és un contrafactual Vixen complet, no el selector D4 real ni la barreja Sony/estrelles.

Als 80 triplets de l'arc superior, early6 i same19 donen exactament el mateix contrast h4: aquests primers fotogrames ja dominaven la font. Això no prova que el moviment lunar sigui innocu. El conjunt primerenc té molt menys suport vàlid i no millora totes les marques. Amb Brno i el mètode congelat, la correlació nominal del component2 baixa de 0,565 (mixed61) a 0,336; la del component3 puja de 0,225 a 0,348. Les diferències entre meitats també incorporen soroll, calibratge, registre i temps.

Decisió: **pilot rebutjat**, sense regenerar filtres de llenç complet a partir d'aquesta font ni incorporar-lo al PSB. Evidència: `early_epoch_R03/DECISION.json`, `METRICS.json` i `brno/QA.json`.

## Contorn i resposta òptica

F4 mesura el màxim de derivada radial, mentre altres vores històriques s'havien mesurat al 50 %. La diferència no justifica sumar 2 píxels al radi físic. Reexpressar les distàncies al contorn F4 tampoc valida aplicar-hi la correcció B(D) calibrada amb una altra abscissa.

Les PSF estel·lars disponibles qualifiquen parcialment el nucli, en altres temps/exposicions/camps. Les ales del model B0 provenen d'un ajust lunar condicionat: no són una mesura estel·lar independent. Els intents inversos anteriors ja tenien resultats negatius. `GEOMETRY_PSF_R03.json` conserva fonts i límits; no demostra impossibilitat absoluta.

## Estat i preservació

La falta d'una observació neta o resposta independent validada a l'arc superior continua impedint justificar una restauració completa. R03 aporta una prova nova negativa i corregeix una premissa geomètrica; no declara el goal complet. V84 i V85 protegides. La darrera verificació completa de bytes és `R02_NATIVE_PRESERVATION.json`; R03 no ha escrit cap PSB.

Skills i memòria actualitzades amb aquests límits, còpies anteriors preservades. Rebut vigent de skills: `SKILL_R03_QA.json`. Estat operatiu: `WORKING_STATE_R03.json`; traspàs `.coordination/HANDOFF_2026-09-22_V85_R03.md`.
'''
    (O / 'R03_DIAGNOSTIC_STATE.md').write_text(report)
    handoff = '''# Traspàs V85 R03 — diagnosi tancada sense nova promoció

Arrel canònica: la carpeta del projecte Desktop. Lliurament natiu vigent: `1-PHOTOSHOP/V85.psb`, R01, SHA d8005f05369eecbd71de6fa58a2e9044c7171a5a4fe9b55232040469a9a17458. Original V84 preservat. No escriure cap PSB existent ni repetir proves rebutjades sense hipòtesi nova.

Entrada de represa: `4-RESULTATS/v85_regeneracio_20260922/R03_DIAGNOSTIC_STATE.md`, `WORKING_STATE_R03.json` i `R03_RECEIPT_MANIFEST.json`. Antecedents i negatius: handoff R02. `GEOMETRY_PSF_R03.json` documenta la diferència entre detectors i les limitacions de les PSF; `early_epoch_R03/DECISION.json` rebutja el pilot temporal.

Goal global V85 incomplet: verd i regeneració lliurats, artefactes residuals al limbe sense correcció íntegra validada. La mateixa manca d'observació/resposta independent està documentada als torns R02 i R03; no marcar complet. R03 ha fet progrés nou. Reavaluar l'evidència al torn següent; el llindar d'estat blocked requereix tres torns consecutius i un impediment real sense progrés possible.

Skills: `SKILL_R03_QA.json`; actualitzacions reversibles a `R03_lessons/`. Cap reserva radiomètrica consumida ni canvi de FOV/RAW/màscares manuals. Cap procés científic propi pendent. L'estat final del claim figura a WORKING_STATE_R03 i al darrer registre de CODEX_STATUS.
'''
    (R / '.coordination/HANDOFF_2026-09-22_V85_R03.md').write_text(handoff)
    status = R / 'IA/ESTAT_ACTUAL.md'
    (lessons / 'ESTAT_ACTUAL_before_R03.md').write_bytes(status.read_bytes())
    prefix = '''# Nota V85 R03 — 22-09-2026

El pilot amb fotogrames primerencs no millora tot el limbe i no s'ha incorporat al PSB. F4 i les altres vores històriques no usaven el mateix detector; les PSF disponibles tampoc validen una correcció física completa de l'arc superior. V85 R01 intacta, goal complet encara pendent. Diagnosi: `4-RESULTATS/v85_regeneracio_20260922/R03_DIAGNOSTIC_STATE.md`; traspàs `.coordination/HANDOFF_2026-09-22_V85_R03.md`. Skills/memòria actualitzades amb els resultats negatius.

'''
    status.write_text(prefix + status.read_text())
    print('R03_CHECKPOINT_READY_FOR_FINAL_REVIEW')

if __name__ == '__main__':
    main()
