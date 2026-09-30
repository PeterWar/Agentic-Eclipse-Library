"""D1 (V35) · Punters d'autoritat després de publicar V35.psb: CLAUDE.md (bloc de represa), AGENTS.md, research/README,
IA/README, IA/ESTAT_ACTUAL, IA/ACTIVE.json. Còpies prèvies a docs_before/. Només amb C4_publish.json present i el claim propi."""
from comu35 import *
import shutil, datetime
IA = Path('/Users/USUARI/Desktop/Eclipse 2026/IA'); HANDOFF = ROOT / '.coordination/HANDOFF_2026-09-08_V35.md'; REPORT = ROOT / 'research/151_V35_VORA_VIXEN_FORAT_I_LIMBE_20260908.md'
BEFORE = HERE35 / 'docs_before'; BEFORE.mkdir(exist_ok=True)


def snapshot(p):
    dst = BEFORE / (('IA_' if str(p).startswith(str(IA)) else 'ROOT_') + p.name)
    if not dst.exists():
        shutil.copy2(p, dst)
    return {'original': str(p), 'snapshot': str(dst), 'sha256_before': sha(dst)}


def main():
    pub = json.loads((REB35 / 'C4_publish.json').read_text()); gate = json.loads((REB35 / 'C4_photoshop_gate.json').read_text()); c3 = json.loads((REB35 / 'C3_portes.json').read_text())
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == 'CLAUDE_V35_20260908'
    assert HANDOFF.exists() and REPORT.exists(); snaps = []
    vv = c3['vora_vixen']['capes']; lb = c3['limbe_biaix_anell_sigma']
    resum = (f"V35 és el lliurable editable actual: `{pub['path']}` (lleugera: base lineal V35 + 10 filtres; OBRE 10551 px x 7506 px · 11 capes).\n"
             f"{pub['bytes']:,} bytes. SHA-256 `{pub['sha256']}`.\n\n"
             "Cures a l'origen de les marques de la V34 (research/151): (1) distàncies a la vora sobre suports plens (la V34 feia entrar la Sony a 1,0–1,36 R☉ per la trampa del forat lunar); "
             "(2) la Vixen conformada a la Sony·ρ en baixa freqüència de 2,65 R☉ enfora i el seu pes esvaït en 720 px a la vora del seu suport (el contorn del FOV Vixen era un graó de nivell de −0,8 % i de gra a la base); "
             "(3) pes de l'apuntament A esvaït en 480 px; (4) relleu entre trens 1,9→3,5 R☉; (5) P03/P04/P05 amb condició de contorn declarada (perfil azimutal mitjà al forat lunar i fora del suport, només com a entrada de l'operador): "
             f"biaix d'anell al limbe P03 {lb['P03']['V34']:.1f} → {lb['P03']['V35']:.1f} σ, P04 {lb['P04']['V34']:.1f} → {lb['P04']['V35']:.1f} σ, P05 {lb['P05']['V34']:.1f} → {lb['P05']['V35']:.1f} σ; "
             f"graó a la vora Vixen (÷ rms) P01 {vv['P01']['V34']['grao_sobre_rms']:+.2f} → {vv['P01']['V35']['grao_sobre_rms']:+.2f}, P03 {vv['P03']['V34']['grao_sobre_rms']:+.2f} → {vv['P03']['V35']['grao_sobre_rms']:+.2f}.\n\n"
             f"Rebut: `V35_REBUT.md` al costat del PSB. Vistes V34|V35 (retalls a les marques de Pere i a la vora Vixen, polars, gra per radi): `{IAOUT35}/lliurables/vistes/`. Traspàs: `{HANDOFF}`. Codi: `research/tools/v35_20260908/`. Judici visual de Pere obert.\n")
    for p, title in [(IA / 'README.md', '# 08-09-2026 — V35 lliurada: vora Vixen, trampa del forat, limbe dels operadors isotròpics'), (IA / 'ESTAT_ACTUAL.md', '# Estat actual — V35')]:
        snaps.append(snapshot(p)); s = p.read_text(); p.write_text(title + '\n\n' + resum + '\n---\n\n' + s)
    p = IA / 'ACTIVE.json'; snaps.append(snapshot(p)); a = json.loads(p.read_text()); prev = a['current_product']
    a['updated'] = pub['published_utc']; a['phase'] = 'post-eclipse-V35-lean-origin-cured'; a['formal_worktree_handoff'] = str(HANDOFF)
    a['paths']['current_technical_editable'] = pub['path']; a['paths']['current_delivery_manifest'] = str(HERE35 / 'delivery_manifest.json'); a['paths']['current_visual_output'] = str(IAOUT35)
    a['current_product'] = {'path': pub['path'], 'sha256': pub['sha256'], 'bytes': pub['bytes'], 'size': [W, H], 'depth': 16, 'layers': pub['layers'], 'published_utc': pub['published_utc'], 'PASS': True,
                            'PASS_scope': 'container, gates (Vixen-edge step, A-edge step, limb ring bias, H1, azimuthal, Photoshop); visual acceptance by Pere pending', 'artifact_free': False, 'source': prev, 'photoshop': gate['result'],
                            'cure': 'filled-support distances (lunar-hole trap); Vixen conformed to Sony*rho (delta sigma256) beyond 2.65 R and tapered 720 px at its support edge; Sony-A tapered 480 px; train handover 1.9-3.5 R; P03/P04/P05 with declared boundary condition (azimuthal mean profile as operator input only)',
                            'limitations': ['frame-entry grain steps remain (capture origin, 2027)', 'residual ring at 1.00-1.03 R (physical limb, partial rings)', 'Vixen blue-channel rings, NE spot, Sony long-frame registration: open debts'],
                            'manifest': str(HERE35 / 'delivery_manifest.json'), 'report': str(REPORT)}
    a['visual_task'] = {'status': 'DELIVERED_V35_PENDING_PERE_VISUAL_JUDGEMENT', 'target': pub['path'], 'next_action': 'No automatic task; Pere reviews the 10 layers and the V34|V35 views'}
    a['history'] = {'previous_active_snapshot': str(BEFORE / 'IA_ACTIVE.json'), 'previous_active_sha256': sha(BEFORE / 'IA_ACTIVE.json'), 'meaning': 'V34 preserved; V35 published as a new file'}
    p.write_text(json.dumps(a, indent=2, ensure_ascii=False) + '\n')
    p = ROOT / 'AGENTS.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-07_V34.md`**'; assert old in s
    s = s.replace(old, '**El traspàs vigent és\n`.coordination/HANDOFF_2026-09-08_V35.md`** (Claude: V35 curada a l\'origen: vora Vixen conformada i esvaïda, trampa del forat lunar, P03/P04/P05 amb condició de contorn, relleu 1,9→3,5; causa del MGN documentada a research/151 §1). Abans deia: **El traspàs vigent és\n`.coordination/HANDOFF_2026-09-07_V34.md`**', 1); p.write_text(s)
    p = ROOT / 'CLAUDE.md'; snaps.append(snapshot(p)); s = p.read_text(); old = '## 1. Punt de represa\n\n'; assert old in s
    nou = old + ("⏭️ **08-09-2026 (matinada) — V35 LLIURADA, curada a l'ORIGEN: `.coordination/HANDOFF_2026-09-08_V35.md` i `research/151_V35_VORA_VIXEN_FORAT_I_LIMBE_20260908.md`.** "
                 f"Per ordre de Pere («Mira V34_artefactes i fes V35»; MGN: la majoria fora, documentat a 151 §1; nou artefacte: contorn del FOV Vixen a tots els filtres; P05 mai corregit). `{pub['path']}` (SHA-256 `{pub['sha256']}`, {gate['result']}; lleugera). "
                 "Mesurat a la font: la Vixen anava −2,9 % a la seva vora (ρ ajustat només a 1,5–4) i el seu pes queia 0,36→0 en 160 px (graó −0,8 % de nivell i 30 % de gra a la base); ⛔ la V34 tenia la TRAMPA DEL FORAT LUNAR a `distanceTransform` (la Sony entrava al 96 % a 1,0–1,1 R☉); "
                 "el «recurrent» del P05 (i P03/P04) és la mitjana local D'UN SOL COSTAT dels operadors isotròpics contra el forat (biaix 4–7 σ al limbe) i, al WOW, la còpia de la silueta del forat a ±2^s (rectangles). "
                 f"Cures: suports plens, δ σ256 (Vixen→Sony·ρ, residu G 1,10→0,39 %), esvaïments 720/480 px, relleu 1,9→3,5, condició de contorn declarada als operadors (biaix P05 {lb['P05']['V34']:.1f}→{lb['P05']['V35']:.1f} σ). Queden: entrades dels fotogrames (captura), anells blaus, taca NE. Judici de Pere obert.\n\n")
    s = s.replace(old, nou, 1); p.write_text(s)
    p = ROOT / 'research/README.md'; snaps.append(snapshot(p)); s = p.read_text(); line = '- [151 — V35: les marques de la V34 mesurades a la font i curades a l\'origen (vora Vixen, trampa del forat, limbe dels operadors isotròpics, relleu); i què causava el MGN](151_V35_VORA_VIXEN_FORAT_I_LIMBE_20260908.md)\n'
    if '151_V35' not in s:
        s = line + s
    p.write_text(s)
    savejson(REB35 / 'D1_autoritat.json', {'snapshots': snaps, 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}); log('autoritat actualitzada')


if __name__ == '__main__':
    main()
