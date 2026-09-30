"""D1 (V42) · Traspàs + punters d'autoritat: HANDOFF_2026-09-10_V42.md, CLAUDE.md (bloc de represa), AGENTS.md, research/README (160), IA/README, IA/ESTAT_ACTUAL, IA/ACTIVE.json. Còpies prèvies a docs_before/."""
from comu42 import *
import shutil, datetime
IA = Path('/Users/USUARI/Desktop/Eclipse 2026/IA'); HANDOFF = ROOT / '.coordination/HANDOFF_2026-09-10_V42.md'; REPORT = ROOT / 'research/160_V42_SONY_B_ROTADA_FILTRES_SENSE_ESTRELLES_RHEF_LOCAL_POWAAAH3_20260910.md'
BEFORE = HERE42 / 'docs_before'; BEFORE.mkdir(exist_ok=True); CLAIM = 'CLAUDE_V42_20260910'


def snapshot(p):
    dst = BEFORE / (('IA_' if str(p).startswith(str(IA)) else 'ROOT_') + p.name)
    if not dst.exists(): shutil.copy2(p, dst)
    return str(dst)


def main():
    pub = json.loads((REB42 / 'C4_publish.json').read_text()); gate = json.loads((REB42 / 'C4_photoshop_gate.json').read_text()); e2o = json.loads((REB42 / 'E2_AB_v36.json').read_text()); e2f = json.loads((REB42 / 'E2_AB_final.json').read_text()); p2 = json.loads((REB42 / 'P2_powaaah.json').read_text()); b3b = json.loads((REB42 / 'B3b_sense_estrelles.json').read_text())
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == CLAIM; assert REPORT.exists(); snaps = []
    resum_b = f"A→B a les estrelles {e2o['rms_brut']:.1f} → {e2f['rms_brut']:.1f} px rms (rotació {e2o['rotacio']['theta_arcmin']:+.2f}′ → {e2f['rotacio']['theta_arcmin']:+.2f}′; elongació de B {e2o['elongB_mediana']:.2f} → {e2f['elongB_mediana']:.2f})"
    HANDOFF.write_text(f"""# Handoff — V42: apuntament B de la Sony recompost (rotació +8,1′ + registre dels llargs), filtres sense estrelles amb capa d'estrelles, quatre RHEF, modes de Pere, POWAAAH3 alineat i LROC

10-09-2026 (matinada) · Claude · claim `{CLAIM}`. Ordre de Pere: aplicar les correccions de research/159 (estrelles), treure les estrelles dels filtres i deixar-les en una capa de llum mesurada, més RHEF amb paràmetres diferents, el POWAAAH3 com a capa alineada (li agrada el seu earthshine), la cara de la Lluna de la NASA, i revisar l'alineament de totes les capes. Modes/opacitats/visibilitats: els que Pere va desar a la seva V41 (Superposar als ACHF, Multiplicar a NRGF/RHEF, Llum suau al MGN).

Producte: `{pub['path']}` ({pub['layers']} capes; SHA-256 `{pub['sha256']}`, {pub['bytes']:,} bytes; Photoshop `{gate['result']}`). Informe: `{REPORT.name}`. Rebut: `V42_REBUT.md` al costat del PSB. V38–V41 intactes.

## Què canvia a l'origen

- B2 V42 (`b2_recomposicio_v42.py`): rotació de +8,10′ al voltant del Sol per a tot l'apuntament B (signe calibrat: amb −8,10′ la separació dobla) i correccions de translació per als fotogrames llargs de B mesurades a les estrelles fotograma a fotograma (`e2_estrelles_ab.py`, `b2c_correccions.py`; DSC06993 (−4,2, −5,6) px al llenç, DSC06996 (+0,2, −2,0), DSC06999 (−0,6, −2,1)). {resum_b}.
- B3 V42: fusió amb la B nova (porta A+B acceptada). B3b: {b3b['n']} estrelles del catàleg substituïdes per fons local + gra veí a la fusió, la Vixen i la Sony ABANS dels filtres; `Estrelles (llum mesurada)` = corba(fusió) − corba(fusió sense estrelles) (Linear Dodge).
- Filtres V42 (b4a/b4b/b4c/b4d clons de la V38 sobre la base sense estrelles, cap reducció de soroll), bases V42 (b4e), RHEF: P02 + υ 0,35 + LOCAL 60° i 30° (`b4f_rhef_variants_v42.py`: rang dins de banda radial 8 px × sector, interpolació bilineal).
- POWAAAH3 (`p2_powaaah_alinea.py`, `p2b_powaaah_rotacio.py`): escala {p2['escala_pow_per_llenc']:.4f} (disc {p2['disc']['R']:.1f} px), rotació {p2['rotacio_deg']:+.2f}° (mars vs LROC i corona), disc al forat V38; màscara de disc.
- `Compara LROC` byte a byte de la V39. Alineament de totes les capes mesurat (`e3_alineament_capes.py`, `e3b_rotacio_fina.py`, taula al rebut): filtres ≤ 0,05 px; estrelles (1, 0) px; POWAAAH3 i LROC al forat (≤ 0,9 px). ⛔ TROBALLA: les capes 06–12 de Pere van DESPLAÇADES ≈ (−12, −1) px (est) respecte de la base i de tots els filtres, corona i Lluna alhora (`e3f_translacio_sectors.py`: Pearson per sectors 1,25–1,6 R☉, control exacte; E4: la Lluna de les capes 12/11/10 és 14,2–15,4 px a l'est del forat V38; vista `E4b`). L'E3 (correlació de fase amb màscara comuna) quedava clavada a zero i deia ≤ 0,05 px; la «rotació» de l'E3b/E3d era el dipol d'aquesta translació. Ve de la V38 (mateixa geometria): forat/LROC/POWAAAH3/earthshine i les capes visibles 12/07/06 de Pere no comparteixen la Lluna. Cura (V43, decisió de Pere): moure les seves set capes un vector enter mesurat capa a capa (≈ (+12, +1)) o la cadena a l'inrevés.
- F1 earthshine (`b2_lluna_v42.py` + `f1_earthshine_v42.py`): 8 fotogrames registrats sobre la Lluna amb la geometria viva, sense guarda al limbe; apuntament B EXCLÒS (fantasma +30–35 % dins del disc als tres B, 16 σ, `f1c`; σ 4–5×); pesos per soroll mesurat entre sensors (DSC06987 24 %, DSC06984 10 %, Vixen 3×20–23 %); vel = perfil radial fins a 0,975 R + poly 4 (r ≤ 0,85); residu × LROC r +0,540 a 2–12 px (nuls ≤ 0,007), +0,681 a 4–16 px. Quatre capes OCULTES: `lineal (corba)` mesurada i tres `relleu` al nivell del POWAAAH3 (×2,58 el vel, declarat), color mesurat, relleu només a r ≤ 0,85 R (fos a 0,95), K 28,6/36,7/70,4 per a contrast sRGB 12 % (gra), 12 % (σ3) i 24 % (σ3); màscara fins a la vora del forat.

## Pendent / següent

- ⏭️ V43 (decisió de Pere): moure les seves set capes (≈ (+12, +1) px, enter, mesurat capa a capa amb `e3f`) o la cadena, perquè Lluna i corona coincideixin; després, la seva tria d'earthshine (variant, nivell, color) i el judici visual (RHEF locals, capa d'estrelles, POWAAAH3, earthshine).
- `v42_lluna_tren_g0.py` (capes_totals_v14) queda abandonat (depenia d'un run vell); les tessel·les bones són les de `b2_lluna_v42.py`.
""")
    resum = (f"V42 és el lliurable editable actual: `{pub['path']}` ({pub['layers']} capes; {pub['bytes']:,} bytes; SHA-256 `{pub['sha256']}`; Photoshop `{gate['result']}`).\n\n"
             f"Apuntament B de la Sony recompost amb rotació +8,1′ i registre dels seus fotogrames llargs ({resum_b}); filtres sobre una base sense estrelles + capa `Estrelles (llum mesurada)`; RHEF P02/υ/local 60°/local 30°; modes de la V41 de Pere; POWAAAH3 alineat (earthshine) i LROC.\n\n"
             f"Rebut: `V42_REBUT.md` al costat del PSB. Vistes: `{IAOUT42}/lliurables/vistes/`. Traspàs: `{HANDOFF}`. Codi: `research/tools/v42_20260910/`. Informe: `research/160`. Judici visual de Pere obert; següent: apilat nou d'earthshine.\n")
    for p, title in [(IA / 'README.md', '# 10-09-2026 — V42 lliurada: Sony B rotada i registrada, filtres sense estrelles, RHEF locals, POWAAAH3 i LROC'), (IA / 'ESTAT_ACTUAL.md', '# Estat actual — V42')]:
        snaps.append(snapshot(p)); s = p.read_text(); p.write_text(title + '\n\n' + resum + '\n---\n\n' + s)
    p = IA / 'ACTIVE.json'; snaps.append(snapshot(p)); a = json.loads(p.read_text()); prev = a['current_product']
    a['updated'] = pub['published_utc']; a['phase'] = 'post-eclipse-V42-sonyB-rotation-starfree-filters'; a['formal_worktree_handoff'] = str(HANDOFF)
    a['paths']['current_technical_editable'] = pub['path']; a['paths']['current_delivery_manifest'] = str(HERE42 / 'delivery_manifest.json'); a['paths']['current_visual_output'] = str(IAOUT42)
    a['current_product'] = {'path': pub['path'], 'sha256': pub['sha256'], 'bytes': pub['bytes'], 'size': [W, H], 'depth': 16, 'layers': pub['layers'], 'published_utc': pub['published_utc'], 'PASS': True,
                            'PASS_scope': 'container, layer verification (byte-exact copies / exact u16), star-based A/B registration gate, Photoshop; visual acceptance by Pere pending', 'artifact_free': False, 'source': prev, 'photoshop': gate['result'],
                            'cure': 'Sony pointing B recomposed with +8.10 arcmin field rotation about the Sun and star-measured per-frame translations for its long frames; filters computed on a star-free base; measured-light star layer; four RHEF variants; POWAAAH3 aligned; LROC', 'limitations': ['no noise reduction (by order)', "Pere's layers 06-12 are translated about (-12, -1) px (east) relative to the chain (corona and Moon alike; since V38); fix = integer move of his layers or of the chain (V43, Pere decides)", 'earthshine relief layers: declared level x2.58 and amplification x29-71 over a 0.5 % signal'], 'manifest': str(HERE42 / 'delivery_manifest.json'), 'report': str(REPORT)}
    a['visual_task'] = {'status': 'DELIVERED_V42_PENDING_PERE_VISUAL_JUDGEMENT', 'target': pub['path'], 'next_action': 'V43: Pere decides whether to move his 7 layers (~(+12,+1) px) or the chain; then earthshine variant'}
    a['history'] = {'previous_active_snapshot': str(BEFORE / 'IA_ACTIVE.json'), 'previous_active_sha256': sha(BEFORE / 'IA_ACTIVE.json'), 'meaning': 'V41 preserved; V42 published as a new file'}
    p.write_text(json.dumps(a, indent=2, ensure_ascii=False) + '\n')
    p = ROOT / 'AGENTS.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-09_V41.md`**'; assert old in s
    s = s.replace(old, "**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-10_V42.md`** (Claude: V42: Sony B rotada +8,1′ i registrada per estrelles; filtres sense estrelles + capa d'estrelles; RHEF locals; POWAAAH3 i LROC; earthshine nou F1; les capes de Pere van desplaçades ≈ (−12, −1) px respecte de la cadena (V43); research/160). Abans deia: " + old, 1); p.write_text(s)
    p = ROOT / 'CLAUDE.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '## 1. Punt de represa\n\n'; assert old in s
    nou = old + (f"⏭️ **10-09-2026 (matinada) — V42 LLIURADA: `.coordination/HANDOFF_2026-09-10_V42.md` i `research/160_V42_SONY_B_ROTADA_FILTRES_SENSE_ESTRELLES_RHEF_LOCAL_POWAAAH3_20260910.md`.** Per ordre de Pere (aplicar les correccions de les estrelles, filtres sense estrelles amb capa de llum mesurada, més RHEF, POWAAAH3 com a capa alineada, LROC, revisar l'alineament). `{pub['path']}` (SHA-256 `{pub['sha256']}`, {gate['result']}; {pub['bytes']:,} bytes). "
                 f"A l'origen: l'apuntament B de la Sony recompost amb ROTACIÓ +8,10′ al voltant del Sol (signe calibrat) i correccions de translació per estrelles dels seus tres fotogrames llargs → {resum_b}. Filtres (recepta V38, cap reducció de soroll) sobre la fusió V42 SENSE ESTRELLES ({b3b['n']} del catàleg, fons local + gra veí) i capa `Estrelles (llum mesurada)` (corba(fusió) − corba(sense), Linear Dodge). RHEF: P02, υ 0,35, i LOCAL 60°/30° (rang dins de banda radial 8 px × sector, interpolació bilineal). Modes/opacitats/visibilitats de la V41 re-desada per Pere (SHA 0c6d953a…, no la lliurada; Multiplicar a les RHEF: conserva el color). POWAAAH3 (HDR de Pere) alineat: escala {p2['escala_pow_per_llenc']:.4f}, rotació {p2['rotacio_deg']:+.1f}° (mars vs LROC), disc al forat V38, màscara de disc. `Compara LROC` byte a byte. Alineament mesurat: filtres ≤ 0,05 px entre ells, POWAAAH3/LROC al forat; ⛔ les capes 06–12 de Pere van DESPLAÇADES ≈ (−12, −1) px (est) respecte de la cadena, corona i Lluna alhora (E3f per sectors amb control exacte; E4: la seva Lluna 14–15 px a l'est del forat; E4b) — ve de la V38; l'E3 (fase amb màscara comuna) ho amagava (clavada a zero) i la «rotació» E3b/E3d era el dipol de la translació → V43: moure les seves set capes (≈ (+12, +1), enter) o la cadena, decisió de Pere. EARTHSHINE NOU (F1): 8 fotogrames sobre la Lluna amb geometria viva, B EXCLÒS (fantasma +30 % dins del disc als tres B, 16 σ), pesos per soroll entre sensors, residu × LROC +0,540 (nuls ≤ 0,007); 4 capes ocultes (lineal mesurada + relleu 12 % gra / 12 % σ3 / 24 % σ3 al nivell POWAAAH3 ×2,58 declarat, color mesurat, relleu només a r ≤ 0,85 R). ⏭️ V43: la causa de l'anell interior; Pere tria l'earthshine. Judici obert.\n\n")
    s = s.replace(old, nou, 1); p.write_text(s)
    p = ROOT / 'research/README.md'; snaps.append(snapshot(p)); s = p.read_text()
    if '160_V42' not in s: s = "- [160 — V42: Sony B rotada +8,1′ i registrada per estrelles; filtres sense estrelles + capa d'estrelles; RHEF locals; POWAAAH3 alineat i LROC](160_V42_SONY_B_ROTADA_FILTRES_SENSE_ESTRELLES_RHEF_LOCAL_POWAAAH3_20260910.md)\n" + s; p.write_text(s)
    savejson(REB42 / 'D1_autoritat.json', {'snapshots': snaps, 'handoff': str(HANDOFF), 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}); log('autoritat actualitzada')


if __name__ == '__main__':
    main()
