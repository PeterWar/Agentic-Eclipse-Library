"""Verify R03 receipts and release this task's claim after helper completion."""
from a87_r03_close import R, O, T, CID, sha, save
import datetime
import json

def main():
    lock = R / '.coordination/claim.lock'
    owner = json.loads((lock / 'owner.json').read_text())
    assert owner['claim_id'] == CID and owner['round'] == 'R03'
    assert not (O / 'R03_RECEIPT_MANIFEST.json').exists()
    peer = json.loads((O / 'R03_FINAL_REVIEW.json').read_text())
    assert peer['helpers_completed'] and peer['owned_calculations_pending'] == 0
    qa = json.loads((O / 'SKILL_R03_QA.json').read_text())
    for row in qa['reference_changes']:
        assert sha(__import__('pathlib').Path(row['path'])) == row['after']
    for row in qa['skills']:
        assert sha(R / row['canonical']) == row['sha256']
    for row in json.loads((O / 'GEOMETRY_PSF_R03.json').read_text())['sources']:
        assert sha(R / row['path']) == row['sha256']
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state_path = O / 'WORKING_STATE_R03.json'
    state = json.loads(state_path.read_text())
    state.update(status='ROUND_COMPLETE_NO_CANDIDATE_PROMOTED_GOAL_INCOMPLETE',
                 claim=CID + ' RELEASED', serial_writes='RELEASED',
                 owner=None, released_utc=now, closure_review='R03_FINAL_REVIEW.json')
    save(state_path, state)
    receipt_paths = [
        'GEOMETRY_PSF_R03.json', 'early_epoch_R03/FROZEN_TEST.json',
        'early_epoch_R03/METRICS.json', 'early_epoch_R03/COMPLETE.json',
        'early_epoch_R03/DECISION.json', 'early_epoch_R03/brno/METHOD.json',
        'early_epoch_R03/brno/QA.json', 'SKILL_R03_QA.json',
        'R03_lessons/UPDATE_RECEIPT.json', 'R03_lessons/PARTIAL_UPDATE_RECOVERY.json',
        'R03_FINAL_REVIEW.json', 'R03_DIAGNOSTIC_STATE.md', 'WORKING_STATE_R03.json',
        'R02_NATIVE_PRESERVATION.json', 'F4_PAIR_COVERAGE_R03.json',
        'camera_channels_R03/FROZEN_TEST.json', 'camera_channels_R03/QA.json',
        'camera_channels_R03/COMPLETE.json', 'camera_channels_R03/DECISION.json'
    ]
    rows = [{'path': str((O / p).relative_to(R)), 'sha256': sha(O / p)} for p in receipt_paths]
    for n in ['a83_early_epoch_source.py', 'a84_early_source_brno.py',
              'a85_r03_evidence.py', 'a86_finish_r03_lessons.py',
              'a87_r03_close.py', 'a88_release_r03.py',
              'a89_camera_channel_contrast.py', 'a90_record_camera_diagnostic.py']:
        p = T / n
        compile(p.read_text(), str(p), 'exec')
        rows.append({'path': str(p.relative_to(R)), 'sha256': sha(p)})
    for n in ['.coordination/HANDOFF_2026-09-22_V85_R03.md', 'IA/Skills/README.md', 'IA/ESTAT_ACTUAL.md']:
        rows.append({'path': n, 'sha256': sha(R / n)})
    save(O / 'R03_RECEIPT_MANIFEST.json', {
        'utc': now, 'files': rows, 'native_write': False,
        'native_integrity_scope': 'R02 full SHA verification retained; no R03 PSB write or new full SHA assertion',
        'goal_complete': False, 'scientific_status': 'EARLY_EPOCH_CANDIDATE_REJECTED_RESIDUAL_LIMB_UNRESOLVED',
        'serial_writes': 'RELEASED', 'owner': None, 'released_utc': now
    })
    with (R / '.coordination/CODEX_STATUS.md').open('a') as f:
        f.write('\n' + now + ' · V85 R03 RELEASED; serial_writes: RELEASED; owner: null; released_utc: ' + now + '. Claim ' + CID + '. Early-epoch source pilot rejected; geometry detectors and PSF limits clarified. No native PSB modified, R01 delivery preserved. Skills/index/memory updated with backups. Full goal incomplete; two documented turns with unresolved independent-response condition, R03 made new progress. Receipt 4-RESULTATS/v85_regeneracio_20260922/R03_RECEIPT_MANIFEST.json; handoff .coordination/HANDOFF_2026-09-22_V85_R03.md. No owned calculations pending, helpers finished.\n')
    assert json.loads((lock / 'owner.json').read_text())['claim_id'] == CID
    (lock / 'owner.json').unlink()
    lock.rmdir()
    print('R03_RELEASED_GOAL_INCOMPLETE')

if __name__ == '__main__':
    main()
