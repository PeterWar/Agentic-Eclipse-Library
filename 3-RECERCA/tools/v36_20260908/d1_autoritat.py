"""D1 (V36) · Punters d'autoritat després de publicar V35.psb: CLAUDE.md (bloc de represa), AGENTS.md, research/README,
IA/README, IA/ESTAT_ACTUAL, IA/ACTIVE.json. Còpies prèvies a docs_before/. Només amb C4_publish.json present i el claim propi."""
from comu36 import *
import shutil, datetime
IA = Path('/Users/USUARI/Desktop/Eclipse 2026/IA'); HANDOFF = ROOT / '.coordination/HANDOFF_2026-09-08_V36.md'; REPORT = ROOT / 'research/153_V36_MARQUES_V35_VORA_8S_I_ANELLS_DISCRETS_20260908.md'
BEFORE = HERE36 / 'docs_before'; BEFORE.mkdir(exist_ok=True)


def snapshot(p):
    dst = BEFORE / (('IA_' if str(p).startswith(str(IA)) else 'ROOT_') + p.name)
    if not dst.exists():
        shutil.copy2(p, dst)
    return {'original': str(p), 'snapshot': str(dst), 'sha256_before': sha(dst)}


def main():
    pub = json.loads((REB36 / 'C4_publish.json').read_text()); gate = json.loads((REB36 / 'C4_photoshop_gate.json').read_text()); c3 = json.loads((REB36 / 'C3_portes.json').read_text())
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == 'CLAUDE_MARQUES_V35_20260908'
    assert HANDOFF.exists() and REPORT.exists(); snaps = []
    lb = c3['limbe_biaix_anell_sigma']
    g8 = c3['vora_8s']['perfil_gra_base']; bins = g8['base_V35']['bins_px']
    def pick(d, lo, hi):
        v = [x for b, x in zip(bins, d) if x is not None and lo <= b < hi]; return float(np.mean(v)) if v else float('nan')
    ns = c3['nrgf_salt_primer_anell']; rb = c3['rhef_bandes_eix']
    resum = (f"V36 és el lliurable editable actual: `{pub['path']}` (lleugera: base lineal V36 + 10 filtres; OBRE 10551 px x 7506 px · 11 capes).\n"
             f"{pub['bytes']:,} bytes. SHA-256 `{pub['sha256']}`.\n\n"
             "Cures a l'origen de les marques de la V35 (research/153): (1) la vora dels 8 s de la Sony (quadrat arrodonit pel vinyetatge, a 3,3–3,8 R☉; graó de gra del 14 % en ~200 px) MESURADA i declarada com a residu d'origen de captura després de dues cures refusades (finestra quadràtica: +14 % de gra a tot el camp; esvaïment espacial: bony +30 % en 1200 px): "
             f"gra fi de la base a ±150 px del contorn dins/fora V35 {pick(g8['base_V35']['gra_fi_pct'], 50, 250):.3f}/{pick(g8['base_V35']['gra_fi_pct'], -250, -50):.3f} → V36 {pick(g8['base_V36']['gra_fi_pct'], 50, 250):.3f}/{pick(g8['base_V36']['gra_fi_pct'], -250, -50):.3f} %; "
             f"(2) RHEF amb rang en radi continu (les bandes de fase a l'eix desapareixen als retalls; la compleció dels anells parcials del NRGF es va provar i refusar); "
             "(3) ⛔ ERRATA corregida: la LUT de linealitat Sony declarada a V34/V35 no s'havia aplicat mai (`run.tren == 'sony'` contra `SONYTOT`); la V36 l'aplica. P03/P04/P05 amb la recepta V35 (dues alternatives de farcit provades i refusades, A8).\n\n"
             f"Rebut: `V36_REBUT.md` al costat del PSB. Vistes V35|V36: `{IAOUT36}/lliurables/vistes/`. Traspàs: `{HANDOFF}`. Codi: `research/tools/v36_20260908/`. Judici visual de Pere obert.\n")
    for p, title in [(IA / 'README.md', '# 08-09-2026 (tarda) — V36 lliurada: vora dels 8 s Sony, anells discrets de NRGF/RHEF, errata de la LUT Sony'), (IA / 'ESTAT_ACTUAL.md', '# Estat actual — V36')]:
        snaps.append(snapshot(p)); s = p.read_text(); p.write_text(title + '\n\n' + resum + '\n---\n\n' + s)
    p = IA / 'ACTIVE.json'; snaps.append(snapshot(p)); a = json.loads(p.read_text()); prev = a['current_product']
    a['updated'] = pub['published_utc']; a['phase'] = 'post-eclipse-V36-lean-origin-cured'; a['formal_worktree_handoff'] = str(HANDOFF)
    a['paths']['current_technical_editable'] = pub['path']; a['paths']['current_delivery_manifest'] = str(HERE36 / 'delivery_manifest.json'); a['paths']['current_visual_output'] = str(IAOUT36)
    a['current_product'] = {'path': pub['path'], 'sha256': pub['sha256'], 'bytes': pub['bytes'], 'size': [W, H], 'depth': 16, 'layers': pub['layers'], 'published_utc': pub['published_utc'], 'PASS': True,
                            'PASS_scope': 'container, gates (Vixen-edge step, A-edge step, limb ring bias, H1, azimuthal, Photoshop); visual acceptance by Pere pending', 'artifact_free': False, 'source': prev, 'photoshop': gate['result'],
                            'cure': 'V35 + Sony linearity LUT actually applied (V34/V35 erratum) + RHEF continuous-radius rank; the Sony 8 s entry (vignetting-shaped rounded square at 3.3-3.8 R, 14 % grain step) measured and declared (two cures tried and refused)',
                            'limitations': ['frame-entry grain steps remain (capture origin, 2027)', 'thin residual at the west limb 1.04-1.06 (temporal-union strip) and a trous fine lines', 'Vixen blue-channel rings, NE spot, Sony long-frame registration: open debts'],
                            'manifest': str(HERE36 / 'delivery_manifest.json'), 'report': str(REPORT)}
    a['visual_task'] = {'status': 'DELIVERED_V36_PENDING_PERE_VISUAL_JUDGEMENT', 'target': pub['path'], 'next_action': 'No automatic task; Pere reviews the 10 layers and the V35|V36 views'}
    a['history'] = {'previous_active_snapshot': str(BEFORE / 'IA_ACTIVE.json'), 'previous_active_sha256': sha(BEFORE / 'IA_ACTIVE.json'), 'meaning': 'V35 preserved; V36 published as a new file'}
    p.write_text(json.dumps(a, indent=2, ensure_ascii=False) + '\n')
    p = ROOT / 'AGENTS.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-08_V35.md`**'; assert old in s
    s = s.replace(old, '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-08_V36.md`** (Claude: V36: vora dels 8 s Sony més gradual, NRGF/RHEF amb anells interiors i rang continu, ERRATA de la LUT Sony corregida; research/153). Abans deia: **El traspàs vigent és\n`.coordination/HANDOFF_2026-09-08_V35.md`**', 1); p.write_text(s)
    p = ROOT / 'CLAUDE.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '## 1. Punt de represa\n\n'; assert old in s
    nou = old + ("⏭️ **08-09-2026 (tarda) — V36 LLIURADA: `.coordination/HANDOFF_2026-09-08_V36.md` i `research/153_V36_MARQUES_V35_VORA_8S_I_ANELLS_DISCRETS_20260908.md`.** "
                 f"Per ordre de Pere («mira V35_Artefactes»: petits artefactes al limbe). `{pub['path']}` (SHA-256 `{pub['sha256']}`, {gate['result']}; lleugera). "
                 "Marques V35 (26): el QUADRAT gruixut del P05 i la franja del 06 a 3,3–3,8 R☉ són la vora d'entrada dels 8 s de la Sony (quadrat arrodonit pel VINYETATGE del 300 mm sobre el cel; gra −35 % en ~110 px) → dues cures provades i REFUSADES (finestra quadràtica dels 8 s: +14 % de gra a tot el camp; esvaïment espacial 900 px: bony +30 % en 1200 px): residu declarat d'origen de captura (salt ×4); "
                 "els arcs del NRGF a 1,04–1,06 = pics d'anells d'1 px a l'oest (residu; la compleció dels anells parcials del forat es va provar i refusar); les línies horitzontals de la RHEF = bandes de fase del rang discret prop dels eixos → rang en radi continu. "
                 "⛔ **ERRATA V34/V35: la LUT de linealitat Sony NO s'havia aplicat mai (`run.tren == 'sony'` contra `SONYTOT`)**; la V36 l'aplica. Guardarail nou (152 §5.12): cap canvi declarat sense prova que ha entrat. "
                 "Farcit dels operadors isotròpics: el de la V35 (dues alternatives refusades en ROI, A8); residu fi al limbe oest = franja de la unió temporal. Judici de Pere obert.\n\n")
    s = s.replace(old, nou, 1); p.write_text(s)
    p = ROOT / 'research/README.md'; snaps.append(snapshot(p)); s = p.read_text(); line = "- [153 — V36: la vora quadrada dels 8 s de la Sony (vinyetatge), els anells discrets de NRGF/RHEF, i l'errata de la LUT Sony](153_V36_MARQUES_V35_VORA_8S_I_ANELLS_DISCRETS_20260908.md)\n"
    if '153_V36' not in s:
        s = line + s
    p.write_text(s)
    savejson(REB36 / 'D1_autoritat.json', {'snapshots': snaps, 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}); log('autoritat actualitzada')


if __name__ == '__main__':
    main()
