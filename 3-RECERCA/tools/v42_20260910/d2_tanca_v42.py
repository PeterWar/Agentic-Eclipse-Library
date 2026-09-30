"""D2 (V42) · Tancament: CLAUDE_STATUS a RELEASED i claim fora. Només després de publish, C5 i D1."""
from comu42 import *
import shutil, datetime


def main():
    pub = json.loads((REB42 / 'C4_publish.json').read_text()); gate = json.loads((REB42 / 'C4_photoshop_gate.json').read_text()); assert (REB42 / 'D1_autoritat.json').exists()
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    st = ROOT / '.coordination/CLAUDE_STATUS.md'; s = st.read_text(); i = s.index('## V42 — '); j = s.index('\n- status: IN_PROGRESS', i); k = s.index('\n', j + 1)
    s = s[:i] + '## V42 — Sony B rotada i registrada, filtres sense estrelles + capa d\'estrelles, RHEF locals, POWAAAH3 i LROC — RELEASED (10-09, matinada)\n' + f'\n- `status: RELEASED` · `serial_writes: RELEASED` · `owner: null` · `released_utc: {now}` · claim_id que hi havia: CLAUDE_V42_20260910' + f"\n- Lliurat: `{pub['path']}` (SHA-256 `{pub['sha256']}`, {pub['bytes']:,} bytes, {gate['result']}). Traspàs: `.coordination/HANDOFF_2026-09-10_V42.md`. Informe: `research/160`. Rebut `V42_REBUT.md` al costat del PSB." + s[k:]
    st.write_text(s)
    cl = ROOT / '.coordination/claim.lock'; o = json.loads((cl / 'owner.json').read_text()); assert o['claim_id'] == 'CLAUDE_V42_20260910'; shutil.rmtree(cl); log('D2 fet · claim alliberat')


if __name__ == '__main__':
    main()
