"""D2 (V37fc) · Tancament: CLAUDE_STATUS a RELEASED, nota a CLAUDE.md, research/154 §4 i handoff V37, claim fora. Només després de C4 publish + C5."""
from comu37fc import *
import shutil, datetime


def main():
    pub = json.loads((REB37FC / 'C4_publish.json').read_text()); gate = json.loads((REB37FC / 'C4_photoshop_gate.json').read_text()); now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    sha_, nb = pub['sha256'], pub['bytes']; ps = gate['result']
    # CLAUDE_STATUS
    st = ROOT / '.coordination/CLAUDE_STATUS.md'; s = st.read_text(); old = '## V37 forat circular (variant per comparar) — IN_PROGRESS (08-09, nit)\n\n- status: IN_PROGRESS · serial_writes: HELD · owner: Claude · claim_id: CLAUDE_V37FC_20260908\n'
    assert old in s
    new = ('## V37 forat circular (variant per comparar) — RELEASED (08-09, nit)\n\n'
           f'- `status: RELEASED` · `serial_writes: RELEASED` · `owner: null` · `released_utc: {now}` · claim_id que hi havia: CLAUDE_V37FC_20260908\n'
           f"- Lliurat: `{pub['path']}` (SHA-256 `{sha_}`, {nb:,} bytes, Photoshop: {ps}). Rebut: `{CT / 'V37_forat_circular_REBUT.md'}`; vistes a `{VIS37FC}` i `{IAOUT37FC}`. Eines: `research/tools/v37fc_20260908/` (a0 forat, b4a/b4c/b4d amb la recepta V37, c3 comparació, c4, c5, d2).\n"
           '- Què és: la V37 amb el forat lunar circular a r < 461 px (1,046 R☉, radi màxim de la unió temporal) i els mateixos filtres regenerats. NO és una cura: és la segona opció d\'enquadrament del limbe que Pere ha demanat veure. V37.psb intacta. Cap PSB de Pere tocat.\n')
    st.write_text(s.replace(old, new))
    # CLAUDE.md: una frase al bloc V37
    cm = ROOT / 'CLAUDE.md'; c = cm.read_text(); anc = '(conservar o forat circular al radi màxim de la unió). Refusats amb número: dues màscares (rivet 9,7 σ), NRGF amb μ/σ extrapolats (5,2 σ). Judici de Pere obert.'
    assert anc in c and 'V37_forat_circular.psb' not in c
    c = c.replace(anc, anc + f" ⏭️ **08-09 (nit): les DUES versions existeixen perquè Pere triï** («les vull veure i després decidir»): `V37.psb` (franja conservada) i `V37_forat_circular.psb` (SHA-256 `{sha_}`, {ps}; forat circular a 1,046 R☉, mateixa recepta; NO és una cura, és enquadrament; rebut `V37_forat_circular_REBUT.md` al costat; eines `research/tools/v37fc_20260908/`). Quan Pere triï, l'altra s'arxiva.")
    cm.write_text(c)
    # research/154 §4
    r154 = ROOT / 'research/154_V37_LIMBE_CONDICIO_DE_CONTORN_I_FRANJA_20260908.md'; t = r154.read_text(); anc2 = '## 5. Trampes d\'aquesta ronda'; assert anc2 in t and 'V37_forat_circular' not in t
    t = t.replace(anc2, f"### 4 bis. Les dues versions (08-09, nit)\n\nPere: «pots fer-me les dues versions? les vull veure i després decidir». Feta la segona: `V37_forat_circular.psb` (SHA-256 `{sha_}`, {nb:,} bytes, {ps}) = la mateixa base V36 amb r < 461 px (1,046 R☉) tret del suport (36.119 px) i els 10 filtres regenerats amb la recepta exacta de la V37. Comparació V37 | V37fc (rivet per capa, vista polar del limbe, retalls 1:1 a l'oest i al sud-oest): `output/v37fc_20260908/lliurables/vistes/` i el rebut `V37_forat_circular_REBUT.md`. No és una cura de res: la causa de la franja continua essent la de §4; el forat circular només l'exclou del producte al preu dels 18 px de corona interior de l'oest (dada real amb 10× més gra). Decisió de Pere.\n\n{anc2}")
    r154.write_text(t)
    # handoff V37
    h = ROOT / '.coordination/HANDOFF_2026-09-08_V37.md'; ht = h.read_text(); assert 'V37_forat_circular' not in ht
    h.write_text(ht.rstrip('\n') + f"\n\n## Afegit 08-09 (nit): la variant amb forat circular\n\nPere ha demanat veure les dues versions abans de decidir. `V37_forat_circular.psb` (SHA-256 `{sha_}`, {ps}) és a `Capes Totals/` al costat de la V37: mateixa base amb r < 1,046 R☉ fora del suport i la mateixa recepta de filtres. Rebut `V37_forat_circular_REBUT.md`; eines `research/tools/v37fc_20260908/`; estat a `CLAUDE_STATUS.md` (RELEASED). Cap dels dos PSB substitueix l'altre fins que Pere triï.\n")
    # claim fora
    cl = ROOT / '.coordination/claim.lock'; o = json.loads((cl / 'owner.json').read_text()); assert o['claim_id'] == 'CLAUDE_V37FC_20260908'; shutil.rmtree(cl); log('D2 fet · claim alliberat')


if __name__ == '__main__':
    main()
