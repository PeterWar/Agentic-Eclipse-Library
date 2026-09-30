"""D1 (V40) · Traspàs + punters d'autoritat després de publicar V40.psb: HANDOFF_2026-09-09_V40.md, CLAUDE.md (bloc de represa), AGENTS.md, research/README
(157), IA/README, IA/ESTAT_ACTUAL, IA/ACTIVE.json. Còpies prèvies a docs_before/."""
from comu40 import *
import shutil, datetime
IA = Path('/Users/USUARI/Desktop/Eclipse 2026/IA'); HANDOFF = ROOT / '.coordination/HANDOFF_2026-09-09_V40.md'; REPORT = ROOT / 'research/157_V40_GRA_FORA_DE_LA_CORONA_WIENER_REGIONAL_I_GARROTE_20260909.md'
BEFORE = HERE40 / 'docs_before'; BEFORE.mkdir(exist_ok=True); CLAIM = 'CLAUDE_V40_20260909'


def snapshot(p):
    dst = BEFORE / (('IA_' if str(p).startswith(str(IA)) else 'ROOT_') + p.name)
    if not dst.exists(): shutil.copy2(p, dst)
    return str(dst)


def main():
    pub = json.loads((REB40 / 'C4_publish.json').read_text()); gate = json.loads((REB40 / 'C4_photoshop_gate.json').read_text()); c3 = json.loads((REB39 / 'C3_portes.json').read_text()); c3c = json.loads((REB39 / 'C3c_jutge_brno.json').read_text()); c3d = json.loads((REB39 / 'C3d_vores_i_gra_candidata.json').read_text()); tau = json.loads((CAU39 / 'tau.json').read_text())
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == CLAIM; assert REPORT.exists(); snaps = []
    sor = c3['soroll_per_anell']; f = lambda k, i: f"{sor[k]['V38'][i]:.3f}→{sor[k]['V39'][i]:.3f}"
    resum_soroll = f"rms a 3,5–5 R☉: P03 {f('P03', 4)}, P04 {f('P04', 4)}, P05 {f('P05', 4)}, 01 {f('01', 4)}, 06 {f('06', 4)}"
    gra = '; '.join(f"{k} {g['5.5R']['residu_total']:.2f}" for k, g in c3d['gra'].items() if '5.5R' in g and 'residu_total' in g['5.5R'])
    ft = lambda v: 'n/d' if v is None or not np.isfinite(v) else f'{v:.2f}'
    brno = ', '.join(f"{k} {ft(c3c['capes'][k]['1deg']['transferencia_cov'][0])}/{ft(c3c['capes'][k]['1deg']['transferencia_cov'][1])}" for k in ('01', '05', '06', 'P03', 'P04', 'P05') if k in c3c['capes'])
    vores = '; '.join(f"{k} ×{r.get('V38_salt', float('nan')):.2f}→×{r.get('candidata_salt', float('nan')):.2f}" for k, r in c3d['vora_vixen'].items())
    HANDOFF.write_text(f"""# Handoff — V40: el gra fora de la corona (Wiener regional + garrote, soroll a totes les vores) i les capes que Pere va deixar

09-09-2026 · Claude · claim `{CLAIM}`. Ordre de Pere: la V39 «no ha millorat el soroll en res» i el terme creuat dibuixava el rectangle de la Vixen; contrast amb Codex xhigh (tema `v40-desencallar-soroll`): coincideix en el diagnòstic i en la regla. Capes: només les 15 de `V39_Artefactes.psb` + les seves 06–12.

Producte: `{pub['path']}` ({pub['layers']} capes; SHA-256 `{pub['sha256']}`, {pub['bytes']:,} bytes; Photoshop `{gate['result']}`). Informe: `{REPORT.name}` (mètode i història a `research/156`). Rebut: `V40_REBUT.md` al costat del PSB. V38, V39 i V39_Artefactes intactes.

## Diagnòstic de la V39 (mesurat) i cura

- El llindar tou k = 2 deixa el 58 % de l'amplitud del soroll pur (sintètic 0,58; P03 a 5,5 R☉ 0,246 → 0,150 = 0,61): l'ull veu presència de gra, no amplitud. El terme creuat existia només al suport comú i queia a zero a la vora de la Vixen (rms de la 01: 0,017 fora → 0,037 dins, ×2,2). L'estimador de soroll per meitats era invàlid també a la vora exterior del camp (ln(E/O) ×13 a 0–2 px).
- Cura: guany per banda g = max(1 − N/E regional, 1 − (kσ)²/w²) amb k = {tau['k']:g}; residu de soroll pur 0,06; compacte fort protegit (5 σ 0,64, 7 σ 0,82); dins de la corona sense canvi; cap terme creuat; soroll mesurat amb d ≥ max(16 px, ℓ) de TOTES les vores del suport i dues particions de fotogrames (mitjana, dispersió anotada).
- Resultat: {resum_soroll}. Residu de gra total a 5,5 R☉ (V40/V38): {gra}. Salt dins/fora a la vora de la Vixen (V38→V40): {vores}. Jutge Brno (transferència 1,2–3 / 3–5): {brno}.

## Límits

- Corba de preu declarada (A3b): fora de la corona un tret feble aïllat per sota del S/N regional de la seva banda s'atenua; ja no és porta universal. H1 de 01/04/05 heretat de la V38. Meitats Sony de la V29. Guarda per escala sense nul empíric de rotacions Vixen–Sony (pendent).
- Judici visual de Pere obert.

## Reutilització

`research/tools/v39_20260909/`: a2/a2c/a4 (soroll per banda, `dist_vora_suport`, particions parell/senar i pA/pB), b2_meitats (pA/pB), filtres_v39 (mode `wg`), b4a/b4c, c3/c3c/c3d, a3b; `research/tools/v40_20260909/`: comu40, c4_projecte_v40, c5_rebut_v40, d1/d2.
""")
    resum = (f"V40 és el lliurable editable actual: `{pub['path']}` ({pub['layers']} capes; {pub['bytes']:,} bytes; SHA-256 `{pub['sha256']}`; Photoshop `{gate['result']}`).\n\n"
             f"Filtres MGN/WOW/ACHF amb guany per banda = max(Wiener regional, garrote k {tau['k']:g}) i soroll mesurat a totes les vores (dues particions); {resum_soroll}; residu de gra a 5,5 R☉ {gra}. Capes: les 15 de V39_Artefactes + les 06–12 de Pere.\n\n"
             f"Rebut: `V40_REBUT.md` al costat del PSB. Vistes: `{IAOUT40}/lliurables/vistes/`. Traspàs: `{HANDOFF}`. Codi: `research/tools/v40_20260909/` i `v39_20260909/`. Informe: `research/157`. Judici visual de Pere obert.\n")
    for p, title in [(IA / 'README.md', '# 09-09-2026 — V40 lliurada: el gra fora de la corona amb Wiener regional + garrote i soroll a totes les vores'), (IA / 'ESTAT_ACTUAL.md', '# Estat actual — V40')]:
        snaps.append(snapshot(p)); s = p.read_text(); p.write_text(title + '\n\n' + resum + '\n---\n\n' + s)
    p = IA / 'ACTIVE.json'; snaps.append(snapshot(p)); a = json.loads(p.read_text()); prev = a['current_product']
    a['updated'] = pub['published_utc']; a['phase'] = 'post-eclipse-V40-regional-wiener-garrote'; a['formal_worktree_handoff'] = str(HANDOFF)
    a['paths']['current_technical_editable'] = pub['path']; a['paths']['current_delivery_manifest'] = str(HERE40 / 'delivery_manifest.json'); a['paths']['current_visual_output'] = str(IAOUT40)
    a['current_product'] = {'path': pub['path'], 'sha256': pub['sha256'], 'bytes': pub['bytes'], 'size': [W, H], 'depth': 16, 'layers': pub['layers'], 'published_utc': pub['published_utc'], 'PASS': True,
                            'PASS_scope': 'container, layer-by-layer verification, grain gate (half-set noise per band), Vixen-edge gate, independent Brno judge, Photoshop; visual acceptance by Pere pending', 'artifact_free': False, 'source': prev, 'photoshop': gate['result'],
                            'cure': f"per-band gain inside MGN/WOW/ACHF = max(regional Wiener 1 - N/E, garrote k {tau['k']:g}) with noise measured from two independent half-set partitions, all support edges excluded per scale; no cross-train gain; layers restricted to the 15 Pere kept in V39_Artefactes plus his 06-12",
                            'limitations': ['price curve declared: weak isolated features below regional S/N attenuated outside the corona', 'H1 01/04/05 inherited from V38', 'Sony half-sets from V29'], 'manifest': str(HERE40 / 'delivery_manifest.json'), 'report': str(REPORT)}
    a['visual_task'] = {'status': 'DELIVERED_V40_PENDING_PERE_VISUAL_JUDGEMENT', 'target': pub['path'], 'next_action': 'No automatic task; Pere reviews'}
    a['history'] = {'previous_active_snapshot': str(BEFORE / 'IA_ACTIVE.json'), 'previous_active_sha256': sha(BEFORE / 'IA_ACTIVE.json'), 'meaning': 'V39 preserved; V40 published as a new file'}
    p.write_text(json.dumps(a, indent=2, ensure_ascii=False) + '\n')
    p = ROOT / 'AGENTS.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-09_V39.md`**'; assert old in s
    s = s.replace(old, "**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-09_V40.md`** (Claude: V40: guany per banda = max(Wiener regional, garrote k=3) amb soroll mesurat a totes les vores i dues particions, sense terme creuat; capes retallades per Pere; research/157). Abans deia: " + old, 1); p.write_text(s)
    p = ROOT / 'CLAUDE.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '## 1. Punt de represa\n\n'; assert old in s
    nou = old + (f"⏭️ **09-09-2026 (tarda) — V40 LLIURADA: `.coordination/HANDOFF_2026-09-09_V40.md` i `research/157_V40_GRA_FORA_DE_LA_CORONA_WIENER_REGIONAL_I_GARROTE_20260909.md`.** Per ordre de Pere (la V39 «no ha millorat el soroll en res»; rectangle de la Vixen al P04/P05). `{pub['path']}` (SHA-256 `{pub['sha256']}`, {gate['result']}; {pub['bytes']:,} bytes). "
                 "⛔ Mesurat: el llindar tou k=2 de la V39 deixava el 58 % de l'amplitud del soroll pur (l'ull veu presència de gra, no amplitud); el terme creuat dibuixava el rectangle de la Vixen (existia només al suport comú); l'estimador de soroll per meitats era invàlid també a la vora exterior del camp Vixen (×13 a 0–2 px). Cura (acordada amb Codex xhigh): guany per banda g = max(1 − N/E regional, garrote 1 − (3σ)²/w²) → residu de soroll pur 0,06, compacte fort protegit (5 σ 0,64), dins de la corona sense canvi; CAP terme creuat com a guany; soroll amb d ≥ max(16, ℓ) px de TOTES les vores del suport i dues particions de fotogrames. "
                 f"{resum_soroll}; residu de gra a 5,5 R☉ (V40/V38) {gra}; salt a la vora de la Vixen {vores}; Brno (transferència 1,2–3 / 3–5) {brno}. Corba de preu declarada (A3b): fora de la corona el feble aïllat s'atenua. Capes: NOMÉS les 15 de `V39_Artefactes.psb` + les 06–12 de Pere (ordre seva: res del que va treure). V38/V39 intactes. Judici de Pere obert.\n\n")
    s = s.replace(old, nou, 1); p.write_text(s)
    p = ROOT / 'research/README.md'; snaps.append(snapshot(p)); s = p.read_text()
    if '157_V40' not in s:
        s = "- [157 — V40: el gra fora de la corona amb Wiener regional + garrote per banda, soroll mesurat a totes les vores i sense terme creuat](157_V40_GRA_FORA_DE_LA_CORONA_WIENER_REGIONAL_I_GARROTE_20260909.md)\n" + s
        p.write_text(s)
    savejson(REB40 / 'D1_autoritat.json', {'snapshots': snaps, 'handoff': str(HANDOFF), 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}); log('autoritat actualitzada')


if __name__ == '__main__':
    main()
