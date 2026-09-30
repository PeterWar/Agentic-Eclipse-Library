"""Record the final bounded channel hypothesis and its negative outcome."""
from a87_r03_close import R, O, T, CID, sha, save
from pathlib import Path
import datetime
import json

def main():
    assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == CID
    out = O / 'camera_channels_R03'
    assert not (out / 'DECISION.json').exists()
    qa = json.loads((out / 'QA.json').read_text())
    rows = {row['component']: row for row in qa['rows']}
    assert qa['common_cameraG_RGBG_triplets'] == 902
    assert rows[1]['camera_G']['rms'] > rows[1]['RGB_G']['rms']
    save(out / 'DECISION.json', {
        'status': 'NO_SOURCE_SUBSTITUTION_JUSTIFIED',
        'finding': 'The RGB matrix modulates the normal contrast, but the component1 depression persists in calibrated camera-green before the matrix. A green-only source is not a complete correction of the marked limb.',
        'component1': rows[1], 'component4': rows[4],
        'limits': ['The CFA estimates already include the existing calibrations, temporal fields and B(D) factors',
                   'The cancellation ratio describes a scalar sum; it is not noise variance or a condition number for the complete chain',
                   'No claim of absent chromatic or registration effects in individual frames',
                   'This is the full Vixen train B2+S4 counterfactual, not the final native composite',
                   'Smaller absolute contrast elsewhere can remove real structure; no promotion follows from that statistic'],
        'source_raster_or_PSB_changed': False,
        'full_canvas_cameraG_filters_generated': False
    })
    save(O / 'F4_PAIR_COVERAGE_R03.json', {
        'method': 'Read-only comparison of a42 frozen pair membership and existing F4 frame fits',
        'a42_pairs': 78, 'early': 6, 'late': 13,
        'F4_early': 6, 'F4_late': 0, 'both_members_F4': 0,
        'cached_summary_products': {'offsets': 234, 'pair_bin_medians': 15186, 'summaries': 311},
        'pixel_coordinates_or_residuals_in_summary': False,
        'conclusion': 'Rebinning only early coordinates cannot independently separate epoch, reference and optical response. A relative early-pair ordering test is possible, but cannot calibrate absolute limb radiance or provide a clean component1 interior reference.',
        'relative_ordering_test_executed': False,
        'review': 'limb_diagnosis exact read-only membership and producer audit',
        'no_reserved_N_read': True
    })
    report_path = O / 'R03_DIAGNOSTIC_STATE.md'
    (O / 'R03_lessons/R03_DIAGNOSTIC_STATE_before_channels.md').write_bytes(report_path.read_bytes())
    report = report_path.read_text()
    old = 'Amb Brno i el mètode congelat, la correlació nominal del component2 baixa de 0,565 (mixed61) a 0,336; la del component3 puja de 0,225 a 0,348.'
    new = 'Amb Brno i el mètode congelat, la comparació principal early6 contra same19 dona 0,336 contra 0,387 al component2 i 0,348 contra 0,353 al component3. El comparador secundari mixed61 dona 0,565 i 0,225, respectivament.'
    assert old in report
    report = report.replace(old, new)
    marker = '## Estat i preservació\n'
    section = '''## Comprovació dels canals abans de RGB

S'ha reproduït el contrafactual Vixen train d'a71 als mateixos 4.047 píxels i 902 triplets, conservant calibratge, pesos, B(D), matriu i guanys. La conversió de verd és −0,1770·R + 1,6855·G − 0,5084·B. Els termes additius reprodueixen RGB G exactament.

Al component1, el contrast normal mitjà és −0,022861 en RGB G i −0,026312 en el verd de càmera anterior a la matriu; RMS 0,033081 i 0,033999. Per tant, la franja ja és present abans de convertir a RGB. La matriu canvia el contrast local —en altres components l'amplifica modestament—, però no és una explicació suficient ni justifica substituir tota la font per verd de càmera. No s'ha generat cap nou filtre ni canviat cap color. `camera_channels_R03/QA.json` i `DECISION.json`.

La reclassificació F4 dels parells a42 tampoc dona una referència absoluta: F4 cobreix els sis primers fotogrames, cap dels tretze tardans i, per tant, cap dels 78 parells als dos membres. Una prova relativa entre primers fotogrames seria possible, però no calibraria la resposta absoluta del veí interior. `F4_PAIR_COVERAGE_R03.json`.

'''
    assert marker in report
    report_path.write_text(report.replace(marker, section + marker))
    state_path = O / 'WORKING_STATE_R03.json'
    state = json.loads(state_path.read_text())
    state['completed'].extend(['Sparse calibrated-camera versus RGB channel decomposition at frozen 902 triplets',
                               'F4 pair-coverage audit: no early/late pair with both F4 fits'])
    state['candidate'] = ['early_epoch_R03: NOT_PROMOTED', 'camera_channels_R03: NO_SOURCE_SUBSTITUTION_JUSTIFIED']
    state['next'].append('A relative early-pair geometric ordering test remains possible, but cannot alone resolve absolute limb response; do not present it as a clean judge of component1.')
    save(state_path, state)
    rel = Path('corregeix-artefactes/references/lunar_boundary_and_display.md')
    canonical = R / '.claude/skills' / rel
    consumer = Path('/Users/USUARI/.codex/skills') / rel
    assert canonical.read_bytes() == consumer.read_bytes()
    (O / 'R03_lessons/lunar_reference_before_channels.md').write_bytes(canonical.read_bytes())
    extra = '''
La descomposició per canals R03 confirma que la matriu RGB modula el contrast,
però la depressió del component1 ja existeix al verd de càmera calibrat abans
de la matriu. No atribuir una franja a coeficients negatius sense mesurar les
contribucions, ni substituir la font perquè baixa un RMS que pot incloure
estructura real. Prova train només, 902 triplets comuns, cap PSB canviat:
`camera_channels_R03/QA.json` i `DECISION.json`.
'''
    canonical.write_text(canonical.read_text() + extra)
    consumer.write_bytes(canonical.read_bytes())
    update_path = O / 'R03_lessons/UPDATE_RECEIPT.json'
    update = json.loads(update_path.read_text())
    (O / 'R03_lessons/UPDATE_RECEIPT_before_channels.json').write_bytes(update_path.read_bytes())
    for row in update['changes']:
        row['after'] = sha(Path(row['path']))
    now = datetime.datetime.now(datetime.timezone.utc)
    note = Path('/Users/USUARI/.codex/memories/extensions/ad_hoc/notes') / (now.strftime('%Y-%m-%dT%H-%M-%SZ') + '-eclipse-v85-r03-camera-channels.md')
    assert not note.exists()
    note.write_text('''# Eclipse V85 R03: canals abans de RGB

Actualització autoritzada per Pere dins l'encàrrec V85. Arrel canònica Desktop/Eclipse 2026.
Als mateixos 902 triplets train, la depressió de l'arc superior persisteix al verd de càmera calibrat abans de la matriu RGB (mean −0,026312; RGB G −0,022861). La matriu modula la franja però no és una causa suficient; no s'ha canviat la font ni el PSB. Menys contrast no equival a menys artefacte si també pot retirar estructura real.
Evidència: 4-RESULTATS/v85_regeneracio_20260922/camera_channels_R03/{QA,DECISION}.json. V85 R01 es conserva; correcció integral del limbe encara no validada.
''')
    update['camera_diagnostic_memory_note'] = str(note)
    save(update_path, update)
    skill_path = O / 'SKILL_R03_QA.json'
    skill = json.loads(skill_path.read_text())
    (O / 'R03_lessons/SKILL_R03_QA_before_channels.json').write_bytes(skill_path.read_bytes())
    skill['reference_changes'] = update['changes']
    skill['lunar_reference_sha256'] = sha(canonical)
    save(skill_path, skill)
    print('R03_CAMERA_DIAGNOSTIC_RECORDED_NO_NATIVE_CHANGE')

if __name__ == '__main__':
    main()
