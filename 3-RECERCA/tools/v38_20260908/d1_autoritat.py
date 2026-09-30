"""D1 (V38) · Traspàs + punters d'autoritat després de publicar V38.psb: HANDOFF_2026-09-08_V38.md (generat), CLAUDE.md (bloc de represa),
AGENTS.md, research/README (i corregeix el títol de la línia 154), IA/README, IA/ESTAT_ACTUAL, IA/ACTIVE.json. Còpies prèvies a docs_before/."""
from comu38 import *
import shutil, datetime
IA = Path('/Users/USUARI/Desktop/Eclipse 2026/IA'); HANDOFF = ROOT / '.coordination/HANDOFF_2026-09-08_V38.md'; REPORT = ROOT / 'research/155_V38_LLUNA_A_L_INICI_FRANJA_A_LA_FONT_I_PROJECTE_COMPLET_20260908.md'
BEFORE = HERE38 / 'docs_before'; BEFORE.mkdir(exist_ok=True); CLAIM = 'CLAUDE_V38_FRANJA_20260908'


def snapshot(p):
    dst = BEFORE / (('IA_' if str(p).startswith(str(IA)) else 'ROOT_') + p.name)
    if not dst.exists():
        shutil.copy2(p, dst)
    return str(dst)


def main():
    pub = json.loads((REB38 / 'C4_publish.json').read_text()); gate = json.loads((REB38 / 'C4_photoshop_gate.json').read_text()); c3 = json.loads((REB38 / 'C3_portes.json').read_text()); pk = json.loads((REB38 / 'C4_packaging.json').read_text())
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == CLAIM; assert REPORT.exists(); snaps = []
    nul = c3['control_nul_fusio']; rp = c3['rivet_per_sector']; r72 = c3.get('rivet_72_P01', {})
    p01 = ''
    if 'P01_resum' in r72 and 'P01x_resum' in r72:
        a, b = r72['P01_resum'], r72['P01x_resum']; p01 = f" P01 contra P01b (μ/σ extrapolats) per azimut: on hi ha cromosfera (W/SE) {a['cromosfera_W_SE_mediana']:+.2f} → {b['cromosfera_W_SE_mediana']:+.2f} σ; a la resta del contorn |màx| {a['resta_max_abs']:.2f} → {b['resta_max_abs']:.2f} σ."
    rivets = ', '.join(f"{k} {v['V37_max']:.2f}→{v['V38_max']:.2f}" for k, v in rp.items() if k in ('01', 'P01', 'P02', 'P03', 'P04', 'P05', '03r4'))
    # --- traspàs
    HANDOFF.write_text(f"""# Handoff — V38: la Lluna a l'inici, la franja de l'oest mesurada a la font, i el projecte complet

08-09-2026 (nit) · Claude · claim `{CLAIM}`. Ordre de Pere: «fem A aplicant les correccions necessàries per treure els artefactes, però anota'm D com a possible millora. Un cop acabada l'A, fes la V38 ja amb totes les capes que havíem eliminat (estrelles, earthshine, part linealitzada, part no linealitzada…) muntat tot en un projecte.»

Producte: `{pub['path']}` (PROJECTE COMPLET, {pub['layers']} capes; SHA-256 `{pub['sha256']}`, {pub['bytes']:,} bytes; Photoshop `{gate['result']}`). V32.psb, V37.psb i V37_forat_circular.psb intactes. Informe: `{REPORT.name}`. Rebut: `V38_REBUT.md` al costat del PSB.

## Què s'ha mesurat (research/155 §1–2)

1. El forat del compost és la INTERSECCIÓ de les posicions de la Lluna (1,005–1,046 R☉), no la «unió» (rectificació del 152/153/154). La Lluna fa 455,5 px i es va moure 28,5 px d'az +3° (t 15 s) a az −148° (t 118 s). La flamarada W només la veuen els fotogrames de l'inici; les miniflamarades del SE només els del final: cap instant les mostra totes dues. Pere tria A (Lluna a l'inici); la D (dos instants declarats) queda anotada com a millora possible.
2. La franja de l'oest, fotograma a fotograma: 15–17 fotogrames (soroll ×2–2,6, NO ×10: el 154 §1c queda rectificat); els 3–4 primers anells (1,005–1,012) són CROMOSFERA (+107/+72/+41/+11 %) vistos per 2–10 fotogrames de 1/3200 s; cap arc coherent d'1 px (coherència azimutal t < 1). Sí: dèficit de llum de cada fotograma prop de la SEVA vora lunar (curts −7 % a 2,5 px, −1,5 % a 10) → corregit a l'origen (B2, taula mesurada per classe d'exposició; residu 0,000; control nul exacte). Guardes més grans i la igualació de nivell per fotograma: provades i refusades (no canvien res mesurable o només treuen dada).

## Què fa la V38

- B2 Vixen amb la correcció de la vora lunar; B3 fusió V35/V36: idèntica a la V36 a r > 1,12 (diferència relativa màxima {nul['rel_max_lluny_r>1.12']:.1e}), a 1,00–1,06 mediana {100*nul['rel_p50_prop_r<1.06']:.2f} % p99 {100*nul['rel_p99_prop']:.1f} %.
- Filtres amb la recepta V37 (01/02/04/05/06, P03/P04/P05, P01/P02) + P01b (NRGF amb μ/σ dels anells parcials extrapolats, oculta) + les azimutals 03 r0/r4 i 07 amb la recepta V32 (b4b).
- Projecte complet: 13 capes de Pere, Fons per raig i Estrelles byte a byte; earthshine ×4 i Reflex desplaçades (+15, +1) px (Lluna a l'inici); bases V32 ocultes; P06–P09/C01 de la V32 ocultes; totes les capes de base/filtre amb màscara nova (fora del disc de la Lluna a l'inici, R 455,5 + 2 px). Visibles com a la V32: 12, 11, Earthshine V24e, base V38, 03 r4, 01, 02, Estrelles, Reflex.

## Portes

- Rivet a la vora del forat (|màx| per sector, σ), abans → V38: {rivets}.{p01}
- Verificació capa a capa contra les fonts: PASS. Photoshop: `{gate['result']}`.

## Límits

- Les miniflamarades del SE queden sota la Lluna (opció A). Els contorns d'entrada dels fotogrames i la vora dels 8 s: captura. Anells del canal blau, taca NE: deutes. P06–P09/C01 i les dues bases V32 no regenerades (ocultes, sufix · V32).
- Judici visual de Pere obert.

## Reutilització

`research/tools/v38_20260908/`: a1_franja_font (recomposició per fotograma al ROI), a2_cura_roi (taula de correcció + control nul), b2/b3/b4a/b4b/b4c/b4d, c3_portes, c4_projecte_complet (build/verify/gate/publish), c5_rebut, d1_autoritat. Trampes noves a research/155 §6 (sed sobre àlies no arriba a rutes literals; primeres diferències sobre pendent; gra amb estructura; dependències natives del purs).
""")
    resum = (f"V38 és el lliurable editable actual: `{pub['path']}` (PROJECTE COMPLET: {pub['layers']} capes; {pub['bytes']:,} bytes; SHA-256 `{pub['sha256']}`; Photoshop `{gate['result']}`).\n\n"
             "La Lluna (earthshine, 455,5 px) és a l'INICI de la totalitat (t 15 s, centre a (+14,8, +0,9) px del Sol): la flamarada de l'oest i la cromosfera queden senceres; les miniflamarades del SE queden sota el disc (opció A triada per Pere; la D, dos instants declarats, anotada com a millora possible). "
             "La franja de l'oest, mesurada fotograma a fotograma, és cromosfera + 15–17 fotogrames (soroll ×2–2,6, no ×10); l'únic biaix real (dèficit de cada fotograma prop de la seva vora lunar) està corregit a l'origen. Base i filtres V37 regenerats; azimutals 03/07 recuperades; capes de Pere, earthshine, estrelles i reflex al projecte.\n\n"
             f"Rebut: `V38_REBUT.md` al costat del PSB. Vistes: `{IAOUT38}/lliurables/vistes/`. Traspàs: `{HANDOFF}`. Codi: `research/tools/v38_20260908/`. Informe: `research/155`. Judici visual de Pere obert.\n")
    for p, title in [(IA / 'README.md', '# 08-09-2026 (nit) — V38 lliurada: projecte complet amb la Lluna a l\'inici; la franja de l\'oest és cromosfera'), (IA / 'ESTAT_ACTUAL.md', '# Estat actual — V38')]:
        snaps.append(snapshot(p)); s = p.read_text(); p.write_text(title + '\n\n' + resum + '\n---\n\n' + s)
    p = IA / 'ACTIVE.json'; snaps.append(snapshot(p)); a = json.loads(p.read_text()); prev = a['current_product']
    a['updated'] = pub['published_utc']; a['phase'] = 'post-eclipse-V38-full-project-moon-at-start'; a['formal_worktree_handoff'] = str(HANDOFF)
    a['paths']['current_technical_editable'] = pub['path']; a['paths']['current_delivery_manifest'] = str(HERE38 / 'delivery_manifest.json'); a['paths']['current_visual_output'] = str(IAOUT38)
    a['current_product'] = {'path': pub['path'], 'sha256': pub['sha256'], 'bytes': pub['bytes'], 'size': [W, H], 'depth': 16, 'layers': pub['layers'], 'published_utc': pub['published_utc'], 'PASS': True,
                            'PASS_scope': 'container, layer-by-layer verification, fusion null control far from the Moon, limb rivet gates, Photoshop; visual acceptance by Pere pending', 'artifact_free': False, 'source': prev, 'photoshop': gate['result'],
                            'cure': 'V37 recipe on a Vixen recomposition with the measured per-frame lunar-edge light deficit corrected at the origin; Moon (earthshine layers + Reflex) placed at the START of totality (+15,+1 px) so the west prominence and chromosphere stay complete; all base/filter layers masked outside the start-disc; azimuthal 03/07 layers regenerated; Pere layers, stars, earthshine, V32 pilots included',
                            'limitations': ['SE mini-prominences under the Moon (option A)', 'frame-entry contours and 8 s edge (capture)', 'Vixen blue-channel rings, NE spot', 'P06-P09/C01 and the two V32 bases are V32-era (hidden)'],
                            'manifest': str(HERE38 / 'delivery_manifest.json'), 'report': str(REPORT)}
    a['visual_task'] = {'status': 'DELIVERED_V38_PENDING_PERE_VISUAL_JUDGEMENT', 'target': pub['path'], 'next_action': 'No automatic task; Pere reviews the full project; option D noted as possible improvement'}
    a['history'] = {'previous_active_snapshot': str(BEFORE / 'IA_ACTIVE.json'), 'previous_active_sha256': sha(BEFORE / 'IA_ACTIVE.json'), 'meaning': 'V37 preserved; V38 published as a new full project'}
    p.write_text(json.dumps(a, indent=2, ensure_ascii=False) + '\n')
    p = ROOT / 'AGENTS.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-08_V37.md`**'; assert old in s
    s = s.replace(old, "**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-08_V38.md`** (Claude: V38 = projecte complet amb la Lluna a l'INICI de la totalitat; la franja de l'oest mesurada a la font és cromosfera + pocs fotogrames, no un artefacte de 10×; dèficit de la vora lunar per fotograma corregit a l'origen; research/155). Abans deia: " + old, 1); p.write_text(s)
    p = ROOT / 'CLAUDE.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '## 1. Punt de represa\n\n'; assert old in s
    nou = old + (f"⏭️ **08-09-2026 (nit) — V38 LLIURADA, PROJECTE COMPLET: `.coordination/HANDOFF_2026-09-08_V38.md` i `research/155_V38_LLUNA_A_L_INICI_FRANJA_A_LA_FONT_I_PROJECTE_COMPLET_20260908.md`.** "
                 f"Per ordre de Pere («fem A… fes la V38 ja amb totes les capes… munta-ho tot en un projecte»). `{pub['path']}` (SHA-256 `{pub['sha256']}`, {gate['result']}; {pub['bytes']:,} bytes). "
                 "**La Lluna (earthshine ×4 + Reflex, R 455,5 px) és a l'INICI de la totalitat** (t 15 s, centre a (+14,8, +0,9) px del Sol; desplaçament (+15, +1)); totes les capes de base i de filtre porten màscara = fora d'aquest disc (+2 px). Així la flamarada de l'oest i la cromosfera queden senceres i les miniflamarades del SE queden sota el disc (opció A; la D —dos instants declarats— anotada com a millora possible al bloc de tasca futura). "
                 "⛔ RECTIFICACIONS: el forat és la INTERSECCIÓ de les posicions lunars (no la «unió»); la franja de l'oest NO té gra ×10: són 15–17 fotogrames (soroll ×2–2,6) i els 3–4 primers anells són CROMOSFERA vista per 2–10 fotogrames de 1/3200 s; cap arc coherent d'1 px. L'únic biaix real (dèficit de llum de cada fotograma prop de la SEVA vora lunar, −7 % a 2,5 px als curts) es corregeix a l'origen (B2) amb taula mesurada; fusió idèntica a la V36 a r > 1,12. "
                 "Capes: 13 de Pere, Fons per raig, Estrelles byte a byte; bases V32 ocultes; base lineal V38; 03 r0/r4/07 (recepta V32 recuperada), 01/02/04/05/06, P01 (+ P01b μ/σ extrapolats, oculta), P02–P05 (recepta V37); P06–P09/C01 de la V32 ocultes. Judici de Pere obert.\n\n")
    s = s.replace(old, nou, 1); p.write_text(s)
    p = ROOT / 'research/README.md'; snaps.append(snapshot(p)); s = p.read_text()
    bad = "- [153 — V36: la vora quadrada dels 8 s de la Sony (vinyetatge), els anells discrets de NRGF/RHEF, i l'errata de la LUT Sony](154_V37_LIMBE_CONDICIO_DE_CONTORN_I_FRANJA_20260908.md)"
    if bad in s:
        s = s.replace(bad, "- [154 — V37: el limbe: capes ACHF saturades contra el forat, farcit que conserva els anells parcials, i la franja de la unió temporal](154_V37_LIMBE_CONDICIO_DE_CONTORN_I_FRANJA_20260908.md)")
    if '155_V38' not in s:
        s = "- [155 — V38: la Lluna a l'inici, la franja de l'oest mesurada a la font (cromosfera, no un artefacte), i el projecte complet](155_V38_LLUNA_A_L_INICI_FRANJA_A_LA_FONT_I_PROJECTE_COMPLET_20260908.md)\n" + s
    p.write_text(s)
    savejson(REB38 / 'D1_autoritat.json', {'snapshots': snaps, 'handoff': str(HANDOFF), 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}); log('autoritat actualitzada')


if __name__ == '__main__':
    main()
