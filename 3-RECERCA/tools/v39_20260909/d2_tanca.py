"""D2 (V39) · Tancament: CLAUDE_STATUS a RELEASED i claim fora. Només després de C4 publish, C5 i D1."""
from comu39 import *
import shutil, datetime


def main():
    pub = json.loads((REB39 / 'C4_publish.json').read_text()); gate = json.loads((REB39 / 'C4_photoshop_gate.json').read_text()); assert (REB39 / 'D1_autoritat.json').exists()
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    st = ROOT / '.coordination/CLAUDE_STATUS.md'; s = st.read_text(); old = '## V39 — soroll dels filtres i capes triades per Pere — IN_PROGRESS (09-09)\n\n- status: IN_PROGRESS · serial_writes: HELD · owner: Claude · claim_id: CLAUDE_V39_20260909\n'
    assert old in s
    new = ('## V39 — soroll dels filtres i capes triades per Pere — RELEASED (09-09)\n\n'
           f'- `status: RELEASED` · `serial_writes: RELEASED` · `owner: null` · `released_utc: {now}` · claim_id que hi havia: CLAUDE_V39_20260909\n'
           f"- Lliurat: `{pub['path']}` (SHA-256 `{pub['sha256']}`, {pub['bytes']:,} bytes, {gate['result']}). Traspàs: `.coordination/HANDOFF_2026-09-09_V39.md`. Informe: `research/156`. Rebut `V39_REBUT.md` al costat del PSB. Eines `research/tools/v39_20260909/`.\n"
           '- Fitxers tocats: CLAUDE.md (bloc de represa), AGENTS.md, research/README.md (156), IA/README.md, IA/ESTAT_ACTUAL.md, IA/ACTIVE.json, memòria. Cap PSB previ tocat (V38, V38_everythingNOTawesome intactes).\n')
    st.write_text(s.replace(old, new))
    cl = ROOT / '.coordination/claim.lock'; o = json.loads((cl / 'owner.json').read_text()); assert o['claim_id'] == 'CLAUDE_V39_20260909'; shutil.rmtree(cl); log('D2 fet · claim alliberat')


if __name__ == '__main__':
    main()
