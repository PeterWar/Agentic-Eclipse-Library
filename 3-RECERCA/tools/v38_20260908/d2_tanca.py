"""D2 (V38) · Tancament: CLAUDE_STATUS a RELEASED i claim fora. Només després de C4 publish, C5 i D1."""
from comu38 import *
import shutil, datetime


def main():
    pub = json.loads((REB38 / 'C4_publish.json').read_text()); gate = json.loads((REB38 / 'C4_photoshop_gate.json').read_text()); assert (REB38 / 'D1_autoritat.json').exists()
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    st = ROOT / '.coordination/CLAUDE_STATUS.md'; s = st.read_text(); old = '## V38 franja / instant de la Lluna — IN_PROGRESS (08-09, nit)\n\n- status: IN_PROGRESS · serial_writes: HELD · owner: Claude · claim_id: CLAUDE_V38_FRANJA_20260908\n'
    assert old in s
    new = ('## V38 — projecte complet amb la Lluna a l\'inici — RELEASED (08-09, nit)\n\n'
           f'- `status: RELEASED` · `serial_writes: RELEASED` · `owner: null` · `released_utc: {now}` · claim_id que hi havia: CLAUDE_V38_FRANJA_20260908\n'
           f"- Lliurat: `{pub['path']}` (SHA-256 `{pub['sha256']}`, {pub['bytes']:,} bytes, {gate['result']}). Traspàs: `.coordination/HANDOFF_2026-09-08_V38.md`. Informe: `research/155`. Rebut `V38_REBUT.md` al costat del PSB. Eines `research/tools/v38_20260908/`.\n"
           '- Fitxers tocats: CLAUDE.md (bloc de represa + millora D al bloc de tasca futura), AGENTS.md, research/README.md (155 i títol de la 154 corregit), IA/README.md, IA/ESTAT_ACTUAL.md, IA/ACTIVE.json, memòria. Cap PSB previ tocat (V32, V37, V37_forat_circular intactes).\n')
    st.write_text(s.replace(old, new))
    cl = ROOT / '.coordination/claim.lock'; o = json.loads((cl / 'owner.json').read_text()); assert o['claim_id'] == 'CLAUDE_V38_FRANJA_20260908'; shutil.rmtree(cl); log('D2 fet · claim alliberat')


if __name__ == '__main__':
    main()
