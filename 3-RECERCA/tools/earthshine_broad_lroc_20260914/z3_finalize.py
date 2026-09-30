"""Finalize the investigated, uncorrected result and release the owned claim."""
from pathlib import Path
import datetime
import hashlib
import json
from pypdf import PdfReader

R = Path.cwd()
O = R / 'output/earthshine_broad_lroc_20260914'
T = R / 'research/tools/earthshine_broad_lroc_20260914'
lock = R / '.coordination/claim.lock'
claim_id = 'CODEX_EARTHSHINE_BROAD_LROC_20260914'

def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()

def write_json(path, data):
    assert not path.exists(), path
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

assert json.loads((lock / 'owner.json').read_text())['claim_id'] == claim_id
start = json.loads((O / 'A0_start.json').read_text())
assert sha(R / '.coordination/CLAUDE_STATUS.md') == start['claude_status_sha256']
authorities = json.loads((O / 'Z2_authorities.json').read_text())
for row in authorities['rows']:
    assert sha(row['path']) == row['after_sha256']

pdf = O / 'ESTUDI_TACA_EARTHSHINE.pdf'
reader = PdfReader(pdf)
texts = [page.extract_text() for page in reader.pages]
text = '\n'.join(texts)
assert len(texts) == 8 and all(t.strip() for t in texts)
assert 'NumPy' in text and 'SciPy' in text
assert 'canal G' in text
assert 'lroc_color_poles_4k.tif' in text
assert 'eines-ia-py312' in text
before = PdfReader(O / 'receipts/REPORT_before_library_names.pdf')
assert len(before.pages) == 8
assert all(reader.pages[i].extract_text() == before.pages[i].extract_text() for i in range(7))
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
qa = dict(
    time=now, pdf=str(pdf), sha256=sha(pdf), pages=8,
    character_count=len(text), links=sum(len(p.get('/Annots', [])) for p in reader.pages),
    pages_1_to_7_unchanged_since_full_visual_review=True,
    page_8_rerendered_and_visually_reviewed_after_library_name_correction=True,
    full_green_channel_only_scope_verified=True,
    independent_report_review='PASS qualified after correcting V53 reproduction claim to G only',
    panel_open_result='queued; visible opening not verified',
)
write_json(O / 'Z3_final_pdf_QA.json', qa)

files = []
for root in [T, O]:
    for path in sorted(root.rglob('*')):
        if path.is_file():
            files.append(dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path)))
manifest = dict(
    time=now, status='NO_CORRECTION_QUALIFIED',
    investigation_documented=True, correction_request_complete=False,
    no_new_psb=True, no_photoshop_edits=True,
    manual_geometry_preserved=True,
    preservation_receipt=str(O / 'Z1_preservation.json'),
    source_hashes=json.loads((O / 'Z1_preservation.json').read_text())['sources'],
    report_pdf=str(pdf), report_pdf_sha256=sha(pdf),
    report_markdown=str(O / 'RESULTAT.md'),
    handoff=authorities['handoff'],
    authority_hashes=authorities['rows'],
    independent_agents_completed=['causal_audit', 'dhs_independent', 'lroc_provenance'],
    processes='No owned background workers at closure; finalizer exits after lock removal.',
    files=files,
)
write_json(O / 'MANIFEST_FINAL.json', manifest)
with (R / '.coordination/CODEX_STATUS.md').open('a') as handle:
    handle.write(
        f'\n## {now} · SERIAL_WRITES RELEASED · BROAD MARK STILL UNCORRECTED\n'
        'Deep investigation report and reproducible receipts complete; correction not qualified. '
        'No V69 and no Photoshop edits. V67/V68 saved bytes unchanged; user unsaved documents preserved. '
        'All three read-only agents completed; zero owned background workers. '
        f'Explicit handoff: {authorities["handoff"]}. '
        f'Final manifest: {O / "MANIFEST_FINAL.json"}. '
        'Continuation authorization remains valid; do not treat documentation completion as artifact repair.\n'
    )
assert sha(R / '.coordination/CLAUDE_STATUS.md') == start['claude_status_sha256']
assert json.loads((lock / 'owner.json').read_text())['claim_id'] == claim_id
assert sorted(p.name for p in lock.iterdir()) == ['owner.json']
write_json(O / 'RELEASE.json', dict(
    time=now, claim_id=claim_id, state='RELEASED',
    manifest_sha256=sha(O / 'MANIFEST_FINAL.json'),
    code_status_sha256=sha(R / '.coordination/CODEX_STATUS.md'),
    claude_status_unchanged=True, owned_background_workers=0,
    handoff=authorities['handoff'], correction_request_complete=False,
))
(lock / 'owner.json').unlink()
lock.rmdir()
print(json.dumps(dict(status=manifest['status'], pdf_sha256=sha(pdf), pages=8,
                      manifest_files=len(files), serial_writes='RELEASED'), indent=2))
