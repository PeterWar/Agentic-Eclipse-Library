"""D2 (V40) · Tancament: CLAUDE_STATUS a RELEASED i claim fora. Només després de publish, C5 i D1."""
from comu40 import *
import shutil, datetime


def main():
    pub = json.loads((REB40 / 'C4_publish.json').read_text()); gate = json.loads((REB40 / 'C4_photoshop_gate.json').read_text()); assert (REB40 / 'D1_autoritat.json').exists()
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    st = ROOT / '.coordination/CLAUDE_STATUS.md'; s = st.read_text(); i = s.index('## V40 — gra fora de la corona'); j = s.index('\n- status: IN_PROGRESS', i); k = s.index('\n', j + 1)
    s = s[:i] + '## V40 — gra fora de la corona (regla acordada amb Codex xhigh) i capes retallades per Pere — RELEASED (09-09, tarda)\n' + f'\n- `status: RELEASED` · `serial_writes: RELEASED` · `owner: null` · `released_utc: {now}` · claim_id que hi havia: CLAUDE_V40_20260909' + f"\n- Lliurat: `{pub['path']}` (SHA-256 `{pub['sha256']}`, {pub['bytes']:,} bytes, {gate['result']}). Traspàs: `.coordination/HANDOFF_2026-09-09_V40.md`. Informe: `research/157`. Rebut `V40_REBUT.md` al costat del PSB." + s[k:]
    st.write_text(s)
    cl = ROOT / '.coordination/claim.lock'; o = json.loads((cl / 'owner.json').read_text()); assert o['claim_id'] == 'CLAUDE_V40_20260909'; shutil.rmtree(cl); log('D2 fet · claim alliberat')


if __name__ == '__main__':
    main()
