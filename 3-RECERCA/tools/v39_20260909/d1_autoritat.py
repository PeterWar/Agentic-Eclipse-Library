"""D1 (V39) · Traspàs + punters d'autoritat després de publicar V38.psb: HANDOFF_2026-09-09_V39.md (generat), CLAUDE.md (bloc de represa),
AGENTS.md, research/README (i corregeix el títol de la línia 154), IA/README, IA/ESTAT_ACTUAL, IA/ACTIVE.json. Còpies prèvies a docs_before/."""
from comu39 import *
import shutil, datetime
IA = Path('/Users/USUARI/Desktop/Eclipse 2026/IA'); HANDOFF = ROOT / '.coordination/HANDOFF_2026-09-09_V39.md'; REPORT = ROOT / 'research/156_V39_SOROLL_DELS_FILTRES_GUANY_WIENER_SOROLL_MESURAT_20260909.md'
BEFORE = HERE39 / 'docs_before'; BEFORE.mkdir(exist_ok=True); CLAIM = 'CLAUDE_V39_20260909'


def snapshot(p):
    dst = BEFORE / (('IA_' if str(p).startswith(str(IA)) else 'ROOT_') + p.name)
    if not dst.exists():
        shutil.copy2(p, dst)
    return str(dst)


def main():
    pub = json.loads((REB39 / 'C4_publish.json').read_text()); gate = json.loads((REB39 / 'C4_photoshop_gate.json').read_text()); c3 = json.loads((REB39 / 'C3_portes.json').read_text()); tau = json.loads((CAU39 / 'tau.json').read_text())
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == CLAIM; assert REPORT.exists(); snaps = []
    sor = c3['soroll_per_anell']; f = lambda k, i: f"{sor[k]['V38'][i]:.3f}→{sor[k]['V39'][i]:.3f}"
    resum_soroll = f"rms a 3,5–5 R☉: P03 {f('P03', 4)}, P04 {f('P04', 4)}, P05 {f('P05', 4)}, 01 {f('01', 4)}, 04 {f('04', 4)}, 06 {f('06', 4)}"
    jut = []
    for k in ('P03', 'P04', 'P05', '01'):
        if f'{k}_V38' in c3['jutge_extern'] and f'{k}_V39' in c3['jutge_extern']:
            c38 = np.mean([rw['corr_capa_vs_Vixen_original'] for rw in c3['jutge_extern'][f'{k}_V38'][0::3]]); c39 = np.mean([rw['corr_capa_vs_Vixen_original'] for rw in c3['jutge_extern'][f'{k}_V39'][0::3]]); jut.append(f"{k} {c38:+.2f}→{c39:+.2f}")
    c3c = json.loads((REB39 / 'C3c_jutge_brno.json').read_text()); c3b = json.loads((REB39 / 'C3b_transferencia_real.json').read_text())
    br = lambda k, key, i: c3c['capes'][k]['1deg'][key][i]
    ft = lambda v: 'n/d' if v is None or not np.isfinite(v) else f'{v:.2f}'
    resum_brno = ', '.join(f"{k} corr {br(k, 'corr_V38', 1):+.2f}→{br(k, 'corr_V39', 1):+.2f} (transf. {ft(br(k, 'transferencia_cov', 1))}, rms ×{br(k, 'rms_V39_V38', 1):.2f})" for k in ('P03', 'P04', 'P05', '01', '06') if k in c3c['capes']) + '; a 1,2–3 R☉ transferència 0,95–1,00 a totes les capes'
    HANDOFF.write_text(f"""# Handoff — V39: el soroll dels filtres fora de la corona (guany per banda amb el soroll MESURAT + el que els dos telescopis confirmen) i el projecte segons Pere

09-09-2026 · Claude · claim `{CLAIM}`. Ordre de Pere (/goal): V39 a partir de `V38_everythingNOTawesome.psb`; passa-alt deprecat; validacions de P05 i la resta; reduir el soroll de WOW/MGN/ACHF fora de la corona sense renunciar-hi; contrast amb Codex xhigh (dues rondes, tema `v39-soroll-filtres`).

Producte: `{pub['path']}` ({pub['layers']} capes; SHA-256 `{pub['sha256']}`, {pub['bytes']:,} bytes; Photoshop `{gate['result']}`). Informe: `{REPORT.name}`. Rebut: `V39_REBUT.md` al costat del PSB. V38 i V38_everythingNOTawesome intactes.

## Diagnòstic i cura

- MGN i WOW normalitzen cada escala per la seva energia LOCAL: on domina el soroll, l'amplifiquen a contrast unitat (rms de P03 creixia de 0,16 a 1,1–1,5 R☉ a 0,25 a 5–7 R☉; NRGF constant 0,19). L'ACHF ho fa en part (perfil de contrast radial + tanh). Soroll mesurat en meitats (fotogrames alternats): a 2,65–3,5 R☉ el 66–91 % de l'energia de les bandes ≤ 20 px és soroll; de 3,5 enfora el 90–100 %.
- Cura (dins dels operadors, per BANDA entre σ consecutives): g = max(g_Auchère, g_creuat). g_Auchère = erf(|w|/(√2·k·σ_banda)) amb k = {tau['k']:g} i σ_banda el soroll MESURAT de la banda (meitats A2/A2c/A4, per canal a l'ACHF); g_creuat = potència que Vixen i Sony veuen alhora dividida per la de la fusió (finestra max(6ℓ, 24 px), guarda 1 σ). τ = 0 → V38 exacta. Codex (xhigh) va refusar els mapes var_* com a soroll (contenen estructura) i, a la ronda 2, va demanar la transferència sobre estructura real i la potència creuada: d'aquí el terme creuat i el guany per banda.
- Tres rectificacions mesurades: (1) el «jutge extern» de les V34–V38 (Vixen original a 4 finestres) NO era independent (pes Vixen 0,37–0,44 a la base; cap finestra amb pes < 0,03): el jutge independent és BRNO (mètode v30 congelat, `c3c_jutge_brno.py`); (2) l'estimador de soroll per meitats era invàlid als 16 px de la vora del forat lunar (×32 a 1 px) i feia un anell al limbe → exclosos a la font (`comu39.lluny_del_forat`); (3) el guany per passa-alt atenuava l'estructura confirmada quasi tant com el soroll (cov ×0,4–0,7) → guany per banda + creuat.
- Resultat: {resum_soroll}. Jutge Brno (3–5 R☉, 1°): {resum_brno}.
- Bases de pantalla noves amb la corba declarada (total, visible; cel/4, oculta) sobre la fusió V38; bases V32 ocultes. 02 passa-alt i P06–P09/C01 deprecats. P01b amb extrapolació en ln r.

## Límits

- RHEF no tocat (nord sorollós: mateixa idea aplicable). P01 i P01b tots dos visibles com Pere els tenia. Anells blaus, taca NE. Meitats Sony de la cadena V29 (aproximació declarada); una sola partició (sense incertesa del soroll). La porta d'injecció (A3b) és una cota inferior (les injeccions no entren als trens, el creuat no les veu): cel·les < 0,90 declarades al rebut.
- Portes declarades: A3b no passa a 1 %/2 px (36/135 cel·les < 0,90); H1 01/04/05 heretat de la V38; creuat prop de la vora de la Sony (≤ 0,1 al guany); guarda sense nul empíric. V39 = candidata amb portes declarades (Codex ronda 3: PARCIAL).
- Judici visual de Pere obert.

## Reutilització

`research/tools/v39_20260909/`: a1 (model blanc, descartat), a2/a2c/a4 (soroll per escala i per banda amb meitats, vora del forat exclosa), a3/a3b (banc de proves i injecció), filtres_v39 (operadors amb guany per banda) + creuat_v39 (terme creuat), b2 (meitats Vixen), b4a/b4c/b4d/b4e, c3/c3b/c3c (portes, coherència, jutge Brno), c4_projecte_v39, c5, d1, d2, f1 (revisió FlamaVermella BlurX).
""")
    resum = (f"V39 és el lliurable editable actual: `{pub['path']}` ({pub['layers']} capes; {pub['bytes']:,} bytes; SHA-256 `{pub['sha256']}`; Photoshop `{gate['result']}`).\n\n"
             f"Filtres MGN/WOW/ACHF amb guany per banda = max(llindar tou Auchère k {tau['k']:g} amb soroll mesurat en meitats, terme creuat Vixen×Sony); {resum_soroll}. Jutge independent Brno (3–5 R☉): {resum_brno}. Bases de pantalla amb la corba declarada; capes segons `V38_everythingNOTawesome`; passa-alt i pilots deprecats.\n\n"
             f"Rebut: `V39_REBUT.md` al costat del PSB. Vistes: `{IAOUT39}/lliurables/vistes/`. Traspàs: `{HANDOFF}`. Codi: `research/tools/v39_20260909/`. Informe: `research/156`. Judici visual de Pere obert.\n")
    for p, title in [(IA / 'README.md', '# 09-09-2026 — V39 lliurada: el soroll dels filtres fora de la corona, curat amb soroll mesurat'), (IA / 'ESTAT_ACTUAL.md', '# Estat actual — V39')]:
        snaps.append(snapshot(p)); s = p.read_text(); p.write_text(title + '\n\n' + resum + '\n---\n\n' + s)
    p = IA / 'ACTIVE.json'; snaps.append(snapshot(p)); a = json.loads(p.read_text()); prev = a['current_product']
    a['updated'] = pub['published_utc']; a['phase'] = 'post-eclipse-V39-per-band-gain-measured-noise-cross-train'; a['formal_worktree_handoff'] = str(HANDOFF)
    a['paths']['current_technical_editable'] = pub['path']; a['paths']['current_delivery_manifest'] = str(HERE39 / 'delivery_manifest.json'); a['paths']['current_visual_output'] = str(IAOUT39)
    a['current_product'] = {'path': pub['path'], 'sha256': pub['sha256'], 'bytes': pub['bytes'], 'size': [W, H], 'depth': 16, 'layers': pub['layers'], 'published_utc': pub['published_utc'], 'PASS': True,
                            'PASS_scope': 'container, layer-by-layer verification, half-set noise per band, blind ± injection transfer (lower bound), independent Brno judge (structure correlation and transfer per ring), Photoshop; visual acceptance by Pere pending', 'artifact_free': False, 'source': prev, 'photoshop': gate['result'],
                            'cure': f"per-band gain inside MGN/WOW/ACHF = max(Auchere soft threshold k {tau['k']:g} with noise measured from alternating half-sets (lunar-hole edge excluded, per channel for ACHF), cross-train Wiener term Vixen x Sony); declared tone-curve display bases (total visible, sky/4 hidden); layers as in Pere's V38_everythingNOTawesome; pass-band 02 and V31 pilots deprecated",
                            'limitations': ['RHEF untouched', 'P01 and P01b both visible as Pere set them', 'Vixen blue-channel rings, NE spot'], 'manifest': str(HERE39 / 'delivery_manifest.json'), 'report': str(REPORT)}
    a['visual_task'] = {'status': 'DELIVERED_V39_PENDING_PERE_VISUAL_JUDGEMENT', 'target': pub['path'], 'next_action': 'No automatic task; Pere reviews'}
    a['history'] = {'previous_active_snapshot': str(BEFORE / 'IA_ACTIVE.json'), 'previous_active_sha256': sha(BEFORE / 'IA_ACTIVE.json'), 'meaning': 'V38 preserved; V39 published as a new file'}
    p.write_text(json.dumps(a, indent=2, ensure_ascii=False) + '\n')
    p = ROOT / 'AGENTS.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-08_V38.md`**'; assert old in s
    s = s.replace(old, "**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-09_V39.md`** (Claude: V39: guany per banda dins de MGN/WOW/ACHF = max(llindar tou amb soroll MESURAT en meitats, terme creuat Vixen×Sony); jutge independent Brno; bases de pantalla amb la corba declarada; capes segons Pere; research/156). Abans deia: " + old, 1); p.write_text(s)
    p = ROOT / 'CLAUDE.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '## 1. Punt de represa\n\n'; assert old in s
    nou = old + (f"⏭️ **09-09-2026 — V39 LLIURADA: `.coordination/HANDOFF_2026-09-09_V39.md` i `research/156_V39_SOROLL_DELS_FILTRES_GUANY_WIENER_SOROLL_MESURAT_20260909.md`.** Per ordre de Pere (/goal V39 des de `V38_everythingNOTawesome.psb`). `{pub['path']}` (SHA-256 `{pub['sha256']}`, {gate['result']}; {pub['bytes']:,} bytes). "
                 "Causa del soroll fora de la corona: MGN i WOW normalitzen cada escala per la seva energia LOCAL (on domina el soroll l'amplifiquen a contrast unitat); l'ACHF en part; mesurat en meitats, de 3,5 R☉ enfora el 90–100 % de l'energia de les bandes ≤ 20 px és soroll. Cura dins dels operadors, per BANDA entre σ consecutives: g = max(g_Auchère, g_creuat) — llindar tou erf(|w|/(√2·k·σ_banda)) amb k = "
                 f"{tau['k']:g} i el soroll MESURAT de la banda (meitats de fotogrames alternats, ⛔ no els mapes var_*; per canal a l'ACHF), i el terme CREUAT (potència que Vixen i Sony veuen alhora / potència de la fusió: els sorolls dels dos sensors són independents). τ = 0 → V38 exacta. {resum_soroll}. "
                 "⛔ TRES RECTIFICACIONS: (1) el «jutge extern» de les V34–V38 (Vixen original a 4 finestres) NO era independent (pes Vixen 0,37–0,44 a la base; cap finestra amb pes < 0,03): el jutge independent és BRNO (mètode v30 congelat; `c3c_jutge_brno.py`; a 3–5 R☉ Brno×Brno només 0,38); (2) l'estimador de soroll per meitats és INVÀLID als 16 px de la vora del forat lunar (les meitats hi tenen la vora a sub-píxel: ×32 a 1 px) i feia un anell al limbe → `comu39.lluny_del_forat`; (3) un guany per PASSA-ALT atenua l'estructura confirmada quasi tant com el soroll (cov ×0,4–0,7) encara que la correlació es conservi → guany per banda + creuat. "
                 f"Jutge Brno (3–5 R☉, 1°): {resum_brno}. PORTES DECLARADES (Codex ronda 3, PARCIAL): injecció A3b NO passa a les cel·les d'1 %/2 px (0,73–0,82; 36 de 135 < 0,90; cota inferior: el creuat no veu injeccions); H1 de 01/04/05 (0,077/0,063/0,056) HERETAT de la V38 (idèntic), H1b millora; el creuat pot inflar coherència a 2,0–2,4 R☉ prop de l'entrada de la Sony (efecte ≤ 0,1 al guany: el llindar ja hi val 0,89–1,00); guarda sense nul empíric. Per això la V39 és CANDIDATA amb portes declarades, no successora certificada. Bases de pantalla amb la corba declarada (total visible, cel/4 oculta; recepta V29 new_tone). Capes tal com Pere les va deixar; 02 passa-alt i P06–P09/C01 DEPRECATS; P01b en ln r. RHEF no tocat. Judici de Pere obert.\n\n")
    s = s.replace(old, nou, 1); p.write_text(s)
    p = ROOT / 'research/README.md'; snaps.append(snapshot(p)); s = p.read_text()
    if '156_V39' not in s:
        s = "- [156 — V39: el soroll dels filtres fora de la corona, curat amb un guany de Wiener per escala i el soroll mesurat en meitats](156_V39_SOROLL_DELS_FILTRES_GUANY_WIENER_SOROLL_MESURAT_20260909.md)\n" + s
    p.write_text(s)
    savejson(REB39 / 'D1_autoritat.json', {'snapshots': snaps, 'handoff': str(HANDOFF), 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}); log('autoritat actualitzada')


if __name__ == '__main__':
    main()
