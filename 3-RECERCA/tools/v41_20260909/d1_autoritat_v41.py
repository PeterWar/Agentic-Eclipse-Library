"""D1 (V41) · Traspàs + punters d'autoritat: HANDOFF_2026-09-09_V41.md, CLAUDE.md (bloc de represa), AGENTS.md, research/README (159), IA/README, IA/ESTAT_ACTUAL, IA/ACTIVE.json. Còpies prèvies a docs_before/."""
from comu41 import *
import shutil, datetime
IA = Path('/Users/USUARI/Desktop/Eclipse 2026/IA'); HANDOFF = ROOT / '.coordination/HANDOFF_2026-09-09_V41.md'; REPORT = ROOT / 'research/159_V41_SENSE_REDUCCIO_DE_SOROLL_RHEF_UPSILON_I_LES_ESTRELLES_20260909.md'
BEFORE = HERE41 / 'docs_before'; BEFORE.mkdir(exist_ok=True); CLAIM = 'CLAUDE_V41_20260909'


def snapshot(p):
    dst = BEFORE / (('IA_' if str(p).startswith(str(IA)) else 'ROOT_') + p.name)
    if not dst.exists(): shutil.copy2(p, dst)
    return str(dst)


def main():
    pub = json.loads((REB41 / 'C4_publish.json').read_text()); gate = json.loads((REB41 / 'C4_photoshop_gate.json').read_text()); e1e = json.loads((REB41 / 'E1e_rotacio_AB.json').read_text())
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == CLAIM; assert REPORT.exists(); snaps = []
    HANDOFF.write_text(f"""# Handoff — V41: les capes de la V40 sense cap reducció de soroll, una segona RHEF (υ 0,35) i el diagnòstic de les estrelles

09-09-2026 (nit) · Claude · claim `{CLAIM}`. Ordre de Pere: «oblidem-nos de moment de reduir el soroll, hi ha el que hi ha; V41 partint de V39 sense artefactes i només amb les capes de la V40, però sense la reducció de soroll»; «un filtre RHEF més amb settings lleugerament diferents»; pregunta sobre les estrelles.

Producte: `{pub['path']}` ({pub['layers']} capes; SHA-256 `{pub['sha256']}`, {pub['bytes']:,} bytes; Photoshop `{gate['result']}`). Informe: `{REPORT.name}`. Rebut: `V41_REBUT.md` al costat del PSB. V38, V39, V40 intactes.

## Què és

- Reassemblatge sense cap píxel nou de filtre: 01/04/05/06 ACHF i P03/P04/P05 són els de la **V38 byte a byte** (recepta sense guany; τ = 0 del codi V39/V40 la reprodueix a 4e-9 / 8e-5) i es diuen «· V38»; la resta (06–12 de Pere, bases V39, 03/07, P01/P01b/P02) de la V39; ordre, modes, opacitats i visibilitats de la V40. Verificació byte a byte contra les fonts.
- Capa nova `P02b RHEF υ 0,35 · V41` (oculta, Superposar al 5 % com la P02): la RHEF V38 amb la funció upsilon de la referència (sunkit-image `apply_upsilon`, υ 0,35): acosta tot valor a 0,5 → una RHEF més feble pertot, amb més contrast local només a les cues (1–10 % extrems de cada anell).

## Les estrelles (mesurat, research/159 §3)

- El seguiment solar no és la causa (~2 px). Les estrelles són al límit del gra (FWHM ≈ 5 px al pic real). La capa `Estrelles` de la V38 no seia sobre les estrelles reals: girada ~11′ respecte de la base (desplaçament mitjà (+20, +8) px, 12–33 px); bé que Pere la va treure; si torna, re-registrar amb rotació.
- **Causa del doblat: els dos apuntaments de la Sony no coincideixen a les estrelles**: rotació de {e1e['rotacio_arcmin']:+.2f}′ al voltant del Sol (residu {e1e['rms_residu_px']:.2f} px sobre {e1e['n']} estrelles diferents; nul de 2.000 permutacions: cap hi arriba) = la rotació de camp del salt de la muntura (research/125, +7,9′), que la composició no aplica (F1.3 només trasllada) → 6–14 px a 7–13 R☉, {e1e['dobles']} de {e1e['estrelles_diferents_amb_pic']} estrelles dobles. La traça de la B (angle comú, no tangencial) és desregistre per translació entre els seus fotogrames llargs: la rotació no la treu. Els filtres canvien l'empremta (l'ACHF l'eixampla ×2, la RHEF la fa rang) però no creen el doblat.
- ⏭️ V42 recomanada (decisió de Pere): recompondre l'apuntament B amb la rotació mesurada (també corregeix el desregistre de la corona exterior de la Sony a 7–13 R☉); després: deixar-les / capa de llum mesurada sobre filtres sense estrelles / treure-les declarat. Cap PSF sintètica.

## Reutilització

`research/tools/v41_20260909/`: c4_projecte_v41 (reassemblatge amb verificació exacta, capes u16 noves), b4e_rhef_upsilon (υ paramètric), e1/e1b/e1c/e1d (estrelles: una a una, apilat amb nul, galeries, pic real per apuntament), c5/d1/d2.
""")
    resum = (f"V41 és el lliurable editable actual: `{pub['path']}` ({pub['layers']} capes; {pub['bytes']:,} bytes; SHA-256 `{pub['sha256']}`; Photoshop `{gate['result']}`).\n\n"
             "Les capes de la V40 sense cap reducció de soroll (filtres 01/04/05/06/P03/P04/P05 = V38 byte a byte) més `P02b RHEF υ 0,35 · V41` (oculta). Estrelles: dobles perquè l'apuntament B de la Sony va rotat +8,1′ respecte de l'A (research/159; nul passat); V42 recomanada.\n\n"
             f"Rebut: `V41_REBUT.md` al costat del PSB. Vistes: `{IAOUT41}/lliurables/vistes/`. Traspàs: `{HANDOFF}`. Codi: `research/tools/v41_20260909/`. Informe: `research/159`. Judici visual de Pere obert.\n")
    for p, title in [(IA / 'README.md', '# 09-09-2026 (nit) — V41 lliurada: capes de la V40 sense reducció de soroll, RHEF υ 0,35 i el diagnòstic de les estrelles'), (IA / 'ESTAT_ACTUAL.md', '# Estat actual — V41')]:
        snaps.append(snapshot(p)); s = p.read_text(); p.write_text(title + '\n\n' + resum + '\n---\n\n' + s)
    p = IA / 'ACTIVE.json'; snaps.append(snapshot(p)); a = json.loads(p.read_text()); prev = a['current_product']
    a['updated'] = pub['published_utc']; a['phase'] = 'post-eclipse-V41-no-noise-reduction'; a['formal_worktree_handoff'] = str(HANDOFF)
    a['paths']['current_technical_editable'] = pub['path']; a['paths']['current_delivery_manifest'] = str(HERE41 / 'delivery_manifest.json'); a['paths']['current_visual_output'] = str(IAOUT41)
    a['current_product'] = {'path': pub['path'], 'sha256': pub['sha256'], 'bytes': pub['bytes'], 'size': [W, H], 'depth': 16, 'layers': pub['layers'], 'published_utc': pub['published_utc'], 'PASS': True,
                            'PASS_scope': 'container, byte-exact layer verification against V39/V38 sources, Photoshop; no noise gates apply (no noise treatment by order of Pere); visual acceptance by Pere pending', 'artifact_free': False, 'source': prev, 'photoshop': gate['result'],
                            'cure': 'none: V40 layer set with V38 filter pixels (no per-band gain); new hidden RHEF layer with reference upsilon 0.35', 'limitations': ['noise outside the corona as in V38 (by order)', 'Sony pointing B rotated +8.1 arcmin vs A (null-tested): stars doubled at 7-13 Rsun; B long frames misregistered by translation (trail) (V42 candidate)'], 'manifest': str(HERE41 / 'delivery_manifest.json'), 'report': str(REPORT)}
    a['visual_task'] = {'status': 'DELIVERED_V41_PENDING_PERE_VISUAL_JUDGEMENT', 'target': pub['path'], 'next_action': 'No automatic task; Pere reviews; V42 (Sony B rotation) only if Pere asks'}
    a['history'] = {'previous_active_snapshot': str(BEFORE / 'IA_ACTIVE.json'), 'previous_active_sha256': sha(BEFORE / 'IA_ACTIVE.json'), 'meaning': 'V40 preserved; V41 published as a new file'}
    p.write_text(json.dumps(a, indent=2, ensure_ascii=False) + '\n')
    p = ROOT / 'AGENTS.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-09_V40.md`**'; assert old in s
    s = s.replace(old, "**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-09_V41.md`** (Claude: V41 = capes de la V40 sense cap reducció de soroll (filtres V38 byte a byte) + RHEF υ 0,35 oculta; estrelles: apuntament B de la Sony rotat +8,1′ → V42 candidata; research/159). Abans deia: " + old, 1); p.write_text(s)
    p = ROOT / 'CLAUDE.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '## 1. Punt de represa\n\n'; assert old in s
    nou = old + (f"⏭️ **09-09-2026 (nit) — V41 LLIURADA: `.coordination/HANDOFF_2026-09-09_V41.md` i `research/159_V41_SENSE_REDUCCIO_DE_SOROLL_RHEF_UPSILON_I_LES_ESTRELLES_20260909.md`.** Per ordre de Pere («no m'agraden els ajustos de la V40; oblidem-nos de moment de reduir el soroll, hi ha el que hi ha»). `{pub['path']}` (SHA-256 `{pub['sha256']}`, {gate['result']}; {pub['bytes']:,} bytes). "
                 "Les 22 capes de la V40 amb els set filtres (01/04/05/06 ACHF, P03 MGN, P04 WOW, P05 bilateral) presos de la **V38 byte a byte** (recepta sense cap guany; es diuen «· V38») i la resta de la V39; ordre/modes/opacitats/visibilitats de la V40; verificació byte a byte contra les fonts. Capa nova `P02b RHEF υ 0,35 · V41` (oculta, Superposar al 5 % com la P02): la funció upsilon de la referència (sunkit-image) que la V38 no aplicava: acosta tot valor a 0,5 (RHEF més feble pertot, contrast local només a les cues). "
                 f"⛔ ESTRELLES (mesurat, amb nul): el seguiment solar NO és la causa (~2 px); la capa `Estrelles` de la V38 estava girada ~11′ respecte de la base (12–33 px); el doblat és que **l'apuntament B de la Sony va rotat {e1e['rotacio_arcmin']:+.2f}′ respecte de l'A al voltant del Sol** (residu {e1e['rms_residu_px']:.2f} px sobre {e1e['n']} estrelles; = la rotació de camp del salt de la muntura del 28-08) i la composició només el trasllada: 6–14 px a 7–13 R☉, {e1e['dobles']} de {e1e['estrelles_diferents_amb_pic']} estrelles dobles; la traça de la B és desregistre per translació entre els seus fotogrames llargs; els filtres canvien l'empremta (ACHF ×2 més ample, RHEF en rang) però no creen el doblat. ⏭️ V42 candidata (decisió de Pere): recompondre B amb la rotació mesurada; després deixar-les / capa de llum mesurada / treure-les declarat. V38/V39/V40 intactes. Judici de Pere obert.\n\n")
    s = s.replace(old, nou, 1); p.write_text(s)
    p = ROOT / 'research/README.md'; snaps.append(snapshot(p)); s = p.read_text()
    if '159_V41' not in s:
        s = "- [159 — V41: les capes de la V40 sense cap reducció de soroll, una segona RHEF (υ 0,35) i les estrelles (apuntament B de la Sony rotat +8,1′)](159_V41_SENSE_REDUCCIO_DE_SOROLL_RHEF_UPSILON_I_LES_ESTRELLES_20260909.md)\n" + s; p.write_text(s)
    savejson(REB41 / 'D1_autoritat.json', {'snapshots': snaps, 'handoff': str(HANDOFF), 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}); log('autoritat actualitzada')


if __name__ == '__main__':
    main()
