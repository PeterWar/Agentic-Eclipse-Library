"""D1 (V37) · Punters d'autoritat després de publicar V35.psb: CLAUDE.md (bloc de represa), AGENTS.md, research/README,
IA/README, IA/ESTAT_ACTUAL, IA/ACTIVE.json. Còpies prèvies a docs_before/. Només amb C4_publish.json present i el claim propi."""
from comu37 import *
import shutil, datetime
IA = Path('/Users/USUARI/Desktop/Eclipse 2026/IA'); HANDOFF = ROOT / '.coordination/HANDOFF_2026-09-08_V37.md'; REPORT = ROOT / 'research/154_V37_LIMBE_CONDICIO_DE_CONTORN_I_FRANJA_20260908.md'
BEFORE = HERE37 / 'docs_before'; BEFORE.mkdir(exist_ok=True)


def snapshot(p):
    dst = BEFORE / (('IA_' if str(p).startswith(str(IA)) else 'ROOT_') + p.name)
    if not dst.exists():
        shutil.copy2(p, dst)
    return {'original': str(p), 'snapshot': str(dst), 'sha256_before': sha(dst)}


def main():
    pub = json.loads((REB37 / 'C4_publish.json').read_text()); gate = json.loads((REB37 / 'C4_photoshop_gate.json').read_text()); c3 = json.loads((REB37 / 'C3_portes.json').read_text())
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == 'CLAUDE_MARQUES_V36_20260908'
    assert HANDOFF.exists() and REPORT.exists(); snaps = []
    lc = c3['limbe_cadena']; rp = c3['rivet_purs']
    resum = (f"V37 és el lliurable editable actual: `{pub['path']}` (lleugera: base lineal V36 (idèntica) + 10 filtres V37; OBRE 10551 px x 7506 px · 11 capes).\n"
             f"{pub['bytes']:,} bytes. SHA-256 `{pub['sha256']}`.\n\n"
             "Marques de la V36 al limbe (research/154): (1) les capes ACHF 01–06 estaven SATURADES al voltant de la Lluna per la mitjana d'un sol costat contra el forat (banda sense estructura fins a 1,08–1,16 R☉, des de la V29) → condició de contorn al forat també per a l'ACHF de cadena: "
             f"saturació del 50 % a r {lc['01']['V36']['r_on_saturacio_cau_a_0.5']} → {lc['01']['V37']['r_on_saturacio_cau_a_0.5']} (01), {lc['06']['V36']['r_on_saturacio_cau_a_0.5']} → {lc['06']['V37']['r_on_saturacio_cau_a_0.5']} (06); "
             f"(2) rivet clar a la vora del forat al MGN/WOW (+1,5–2 σ on la vora és més a prop del Sol que el primer anell sencer) → farcit B que conserva les mitjanes dels anells parcials: rivet màxim P03 {rp['P03']['V36']['rivet_max_abs']:.2f} → {rp['P03']['V37']['rivet_max_abs']:.2f} σ, P04 {rp['P04']['V36']['rivet_max_abs']:.2f} → {rp['P04']['V37']['rivet_max_abs']:.2f} σ; "
             "(3) la FRANJA de la unió temporal (oest, 18 px, 13–16 fotogrames, gra 7–9 %) queda al producte (norma 27-08): banda apagada al NRGF/RHEF; decisió pendent de Pere (forat circular al radi màxim de la unió o conservar).\n\n"
             f"Rebut: `V37_REBUT.md` al costat del PSB. Vistes V36|V37: `{IAOUT37}/lliurables/vistes/`. Traspàs: `{HANDOFF}`. Codi: `research/tools/v37_20260908/`. Judici visual de Pere obert.\n")
    for p, title in [(IA / 'README.md', '# 08-09-2026 (tarda) — V36 lliurada: vora dels 8 s Sony, anells discrets de NRGF/RHEF, errata de la LUT Sony'), (IA / 'ESTAT_ACTUAL.md', '# Estat actual — V37')]:
        snaps.append(snapshot(p)); s = p.read_text(); p.write_text(title + '\n\n' + resum + '\n---\n\n' + s)
    p = IA / 'ACTIVE.json'; snaps.append(snapshot(p)); a = json.loads(p.read_text()); prev = a['current_product']
    a['updated'] = pub['published_utc']; a['phase'] = 'post-eclipse-V37-lean-origin-cured'; a['formal_worktree_handoff'] = str(HANDOFF)
    a['paths']['current_technical_editable'] = pub['path']; a['paths']['current_delivery_manifest'] = str(HERE37 / 'delivery_manifest.json'); a['paths']['current_visual_output'] = str(IAOUT37)
    a['current_product'] = {'path': pub['path'], 'sha256': pub['sha256'], 'bytes': pub['bytes'], 'size': [W, H], 'depth': 16, 'layers': pub['layers'], 'published_utc': pub['published_utc'], 'PASS': True,
                            'PASS_scope': 'container, gates (Vixen-edge step, A-edge step, limb ring bias, H1, azimuthal, Photoshop); visual acceptance by Pere pending', 'artifact_free': False, 'source': prev, 'photoshop': gate['result'],
                            'cure': 'V36 + lunar-hole boundary condition for the ACHF chain layers (they were tanh-saturated out to 1.08-1.16 R since V29) + fill variant B keeping partial-ring means for the isotropic operators; temporal-union strip kept pending Pere decision',
                            'limitations': ['frame-entry grain steps remain (capture origin, 2027)', 'thin residual at the west limb 1.04-1.06 (temporal-union strip) and a trous fine lines', 'Vixen blue-channel rings, NE spot, Sony long-frame registration: open debts'],
                            'manifest': str(HERE37 / 'delivery_manifest.json'), 'report': str(REPORT)}
    a['visual_task'] = {'status': 'DELIVERED_V37_PENDING_PERE_VISUAL_JUDGEMENT', 'target': pub['path'], 'next_action': 'No automatic task; Pere reviews the 10 layers and the V36|V37 views'}
    a['history'] = {'previous_active_snapshot': str(BEFORE / 'IA_ACTIVE.json'), 'previous_active_sha256': sha(BEFORE / 'IA_ACTIVE.json'), 'meaning': 'V36 preserved; V37 published as a new file'}
    p.write_text(json.dumps(a, indent=2, ensure_ascii=False) + '\n')
    p = ROOT / 'AGENTS.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-08_V36.md`**'; assert old in s
    s = s.replace(old, '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-08_V37.md`** (Claude: V37: condició de contorn al forat lunar també per a les capes ACHF (estaven saturades fins a 1,08–1,16 R☉ des de la V29), farcit B als operadors purs; la franja de la unió temporal queda i Pere decideix; research/154). Abans deia: **El traspàs vigent és\n`.coordination/HANDOFF_2026-09-08_V36.md`**', 1); p.write_text(s)
    p = ROOT / 'CLAUDE.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '## 1. Punt de represa\n\n'; assert old in s
    nou = old + ("⏭️ **08-09-2026 (vespre) — V37 LLIURADA: `.coordination/HANDOFF_2026-09-08_V37.md` i `research/154_V37_LIMBE_CONDICIO_DE_CONTORN_I_FRANJA_20260908.md`.** "
                 f"Per ordre de Pere («els d'a prop del limbe els veig claríssims»). `{pub['path']}` (SHA-256 `{pub['sha256']}`, {gate['result']}; lleugera; base V36 idèntica). "
                 "Mesurat: (1) les capes ACHF 01–06 estaven SATURADES al voltant de la Lluna per la mitjana d'un sol costat contra el forat (|d/escala| > 25 al limbe, > 1 fins a 1,08–1,16 R☉; banda sense estructura; des de la V29) → condició de contorn al forat també per a l'ACHF de cadena; "
                 "(2) el rivet clar del MGN/WOW a la vora del forat era el farcit V35 extrapolat des del primer anell SENCER amb un pendent 7× més suau que el del limbe → farcit B (mitjanes dels anells parcials conservades, pendent local que decau); "
                 "(3) la FRANJA de la unió temporal de la Lluna (oest, 1,005–1,046 R☉, 18 px): 13–16 fotogrames, pes 3–4× menor, gra 7–9 % (10×): tots els filtres la mostren; la norma del 27-08 la conserva; **DECISIÓ PENDENT DE PERE** (conservar o forat circular al radi màxim de la unió). "
                 "Refusats amb número: dues màscares (rivet 9,7 σ), NRGF amb μ/σ extrapolats (5,2 σ). Judici de Pere obert.\n\n")
    s = s.replace(old, nou, 1); p.write_text(s)
    p = ROOT / 'research/README.md'; snaps.append(snapshot(p)); s = p.read_text(); line = "- [153 — V36: la vora quadrada dels 8 s de la Sony (vinyetatge), els anells discrets de NRGF/RHEF, i l'errata de la LUT Sony](154_V37_LIMBE_CONDICIO_DE_CONTORN_I_FRANJA_20260908.md)\n"
    if '154_V37' not in s:
        s = line + s
    p.write_text(s)
    savejson(REB37 / 'D1_autoritat.json', {'snapshots': snaps, 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}); log('autoritat actualitzada')


if __name__ == '__main__':
    main()
