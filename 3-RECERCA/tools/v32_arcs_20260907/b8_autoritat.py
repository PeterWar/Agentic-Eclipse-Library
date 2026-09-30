"""B8 · Punters d'autoritat després de publicar V32.psb: AGENTS, CLAUDE (bloc inicial),
IA/README, IA/ESTAT_ACTUAL, IA/ACTIVE.json, research/README. Còpies prèvies a docs_before/.
Només s'executa amb B6_publish.json present i el claim propi."""
from comu32 import *
import shutil, datetime

IA = Path('/Users/USUARI/Desktop/Eclipse 2026/IA')
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
HANDOFF = ROOT / '.coordination/HANDOFF_2026-09-07_V32.md'
REPORT = ROOT / 'research/146_V32_ARCS_A_LA_FONT_20260907.md'
BEFORE = HERE / 'docs_before'; BEFORE.mkdir(exist_ok=True)


def snapshot(p):
    dst = BEFORE / (('IA_' if str(p).startswith(str(IA)) else 'ROOT_') + p.name)
    if not dst.exists():
        shutil.copy2(p, dst)
    return {'original': str(p), 'snapshot': str(dst), 'sha256_before': sha(dst)}


def main():
    pub = json.loads((REB / 'B6_publish.json').read_text()); ver = json.loads((REB / 'B6_psb_verification.json').read_text()); gate = json.loads((REB / 'B6_photoshop_gate.json').read_text())
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == 'CLAUDE_V32_ARCS_20260907'
    assert HANDOFF.exists() and REPORT.exists()
    snaps = []
    resum = (f"V32 és el lliurable editable actual: `{pub['path']}`.\n"
             f"10551 × 7506, RGB16, 40 capes; {pub['bytes']:,} bytes.\nSHA-256 `{pub['sha256']}`.\n\n"
             "Les 18 capes de filtre (03 V29, 03 V30, 07, 01, 02, 04, 05, 06 i les deu vistes pures P01–P09/C01) s'han regenerat amb les receptes\n"
             "exactes de la V29/V30/V31 sobre una base curada A L'ORIGEN: camps de nivell suaus per fotograma i canal (fronteres de fusió HDR),\n"
             "perfil radial del flat de la Sony suavitzat (la seva ondulació fina, impresa invertida a cada fotograma, era la causa dels arcs\n"
             "de 3,2–4,6 R☉), guany 2D suau entre trens i ploma a la vora del suport Sony. Cap retall circular, cap màscara de marques, cap\n"
             "inpainting. Les altres 22 capes (bases, capes de Pere, estrelles, reflex) són byte a byte les de V31_FiltresPurs, que es conserva.\n\n"
             f"Photoshop real: **{gate['result']}**. Mesures abans/després (anisotropia tangencial, graons a les fronteres, residu creuat entre trens,\n"
             "jutge extern fix, injecció cega, H1/geometria de cada capa) al rebut `V32_REBUT.md` al costat del PSB. El judici visual de Pere queda obert.\n\n"
             f"Traspàs: `{HANDOFF}`. Explicació: `research/146_V32_ARCS_A_LA_FONT_20260907.md`. Codi i rebuts: `research/tools/v32_arcs_20260907/`,\n"
             f"`output/v32_arcs_20260907/`. Vistes: `{IAOUT}`.\n")
    # IA/README i ESTAT_ACTUAL: bloc nou a dalt
    for p, title in [(IA / 'README.md', '# Actualització vigent 07-09-2026 — V32'), (IA / 'ESTAT_ACTUAL.md', '# Estat actual — V32')]:
        snaps.append(snapshot(p)); s = p.read_text()
        p.write_text(title + '\n\n' + resum + '\nLes referències a la V31_FiltresPurs més avall són històriques (producte preservat).\n\n---\n\n' + s)
    # ACTIVE.json
    p = IA / 'ACTIVE.json'; snaps.append(snapshot(p)); a = json.loads(p.read_text())
    prev = a['current_product']
    a['updated'] = pub['published_utc']; a['phase'] = 'post-eclipse-V32-filters-on-source-cured-base'
    a['formal_worktree_handoff'] = str(HANDOFF); a['paths']['current_technical_editable'] = pub['path']; a['paths']['current_delivery_manifest'] = str(HERE / 'delivery_manifest.json'); a['paths']['current_visual_output'] = str(IAOUT)
    a['current_product'] = {'path': pub['path'], 'sha256': pub['sha256'], 'bytes': pub['bytes'], 'size': [W, H], 'depth': 16, 'layers': 40, 'published_utc': pub['published_utc'], 'PASS': True,
                            'PASS_scope': 'container, gates (H1, azimuthal, judge, injection) and Photoshop; visual acceptance by Pere pending', 'artifact_free': False,
                            'source': prev, 'photoshop': gate['result'], 'preservation': '22 non-filter layers byte-identical to V31_FiltresPurs; 18 filter layers regenerated (RGB only)',
                            'cure': 'per-frame smooth level fields (HDR fusion boundaries); Sony radial flat ripple removed (sigma 32 px); 2D inter-train gain; feathered Sony support edge',
                            'limitations': ['No claim that every arc is gone; before/after measured in V32_REBUT.md', 'Sony long-frame registration not redone (model positions)', 'NE spot (~7.8 R) <= 0.01 % in base, not patched', 'Base/Pere layers untouched'],
                            'manifest': str(HERE / 'delivery_manifest.json'), 'report': str(REPORT)}
    a['visual_task'] = {'status': 'DELIVERED_V32_PENDING_PERE_VISUAL_JUDGEMENT', 'target': pub['path'], 'next_action': 'No automatic task; Pere reviews the 18 regenerated layers and the before/after views'}
    a['history'] = {'previous_active_snapshot': str(BEFORE / 'IA_ACTIVE.json'), 'previous_active_sha256': sha(BEFORE / 'IA_ACTIVE.json'), 'meaning': 'V31_FiltresPurs preserved; V32 published as a new file'}
    p.write_text(json.dumps(a, indent=2, ensure_ascii=False) + '\n')
    # AGENTS.md: punter del traspàs vigent
    p = ROOT / 'AGENTS.md'; snaps.append(snapshot(p)); s = p.read_text()
    old = '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-07_CODEX_A_CLAUDE.md`**'
    assert old in s
    s = s.replace(old, '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-07_V32.md`** (Claude: V32.psb, els 18 filtres regenerats sobre una base curada a l\'origen; abans/després mesurat; judici visual de Pere obert). L\'anterior, `.coordination/HANDOFF_2026-09-07_CODEX_A_CLAUDE.md`, conserva la revisió 145 i la recerca 143/144. Abans deia: **El traspàs vigent és\n`.coordination/HANDOFF_2026-09-07_CODEX_A_CLAUDE.md`**')
    p.write_text(s)
    # CLAUDE.md: bloc de represa
    p = ROOT / 'CLAUDE.md'; snaps.append(snapshot(p)); s = p.read_text()
    old = '## 1. Punt de represa\n\n'
    assert old in s
    nou = old + ("⏭️ **07-09-2026 (nit) — V32 LLIURADA: `.coordination/HANDOFF_2026-09-07_V32.md` i `research/146_V32_ARCS_A_LA_FONT_20260907.md`.** "
                 "Per ordre de Pere («nova versió de tots els filtres eliminant els artefactes lila i blaus»). Els arcs tenen tres causes mesurades a la FONT: "
                 "fronteres de fusió HDR amb desnivell entre fotogrames (interior 1–2,2 R☉ Vixen; 8 s Sony a 2,6–2,8), **l'ondulació fina del flat radial de la Sony "
                 "impresa invertida a cada fotograma (arcs de 3,2–4,6 R☉, centrats al centre del sensor a 0,5 R☉ del Sol)**, i el guany escalar entre trens amb tall sec a la vora. "
                 f"Cura a l'origen (camps per fotograma, flat suavitzat σ32, ρ 2D, ploma) i 18 filtres regenerats amb les receptes exactes: `{pub['path']}` "
                 f"(SHA-256 `{pub['sha256']}`, {gate['result']}). V31_FiltresPurs preservada. Abans/després al `V32_REBUT.md`. Judici visual de Pere obert; deutes: registre dels fotogrames llargs Sony, flat a F0.3, taca NE.\n\n")
    s = s.replace(old, nou, 1); p.write_text(s)
    # research/README: índex
    p = ROOT / 'research/README.md'; snaps.append(snapshot(p)); s = p.read_text()
    line = '- [146 — V32: els arcs lila i blaus, trobats a la font i curats a la font](146_V32_ARCS_A_LA_FONT_20260907.md)\n'
    if '146_V32' not in s:
        if s.startswith('- [145'):
            s = line + s
        else:
            idx = s.find('\n- [145'); s = (s[:idx + 1] + line + s[idx + 1:]) if idx >= 0 else (s.rstrip('\n') + '\n\n' + line)
    p.write_text(s)
    savejson(REB / 'B8_autoritat.json', {'snapshots': snaps, 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    log('autoritat actualitzada')


if __name__ == '__main__':
    main()
