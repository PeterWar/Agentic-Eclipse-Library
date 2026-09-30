"""E1 (V40) · Omple el §4 de research/157 amb els números del pilot (C3, C3c, C3d, A3b wg, A2d dispersió, B4a H1). Idempotent: substitueix el bloc §4."""
from comu40 import *
REPORT = ROOT / 'research/157_V40_GRA_FORA_DE_LA_CORONA_WIENER_REGIONAL_I_GARROTE_20260909.md'
fmt = lambda v: 'n/d' if v is None or (isinstance(v, float) and not np.isfinite(v)) else f'{v:.2f}'


def main():
    tau = json.loads((CAU39 / 'tau.json').read_text()); c3 = json.loads((REB39 / 'C3_portes.json').read_text()); c3c = json.loads((REB39 / 'C3c_jutge_brno.json').read_text()); c3d = json.loads((REB39 / 'C3d_vores_i_gra_candidata.json').read_text())
    b4a = json.loads((REB39 / 'B4a_capes_cadena.json').read_text()); disp = json.loads((REB39 / 'A2d_dispersio_particions.json').read_text()) if (REB39 / 'A2d_dispersio_particions.json').exists() else {}
    L = ['## 4. Resultats del pilot (candidata V40 contra V38 i V39)', '',
         '**Soroll per anell** (rms de capa − 0,5; 1,1–1,5 / 1,5–2 / 2–2,65 / 2,65–3,5 / 3,5–5 / 5–7 R☉), V38 → V40:', '', '| capa | V38 | V40 |', '|---|---|---|']
    for k, row in c3['soroll_per_anell'].items(): L.append(f"| {k} | {' / '.join(f'{x:.3f}' for x in row['V38'])} | {' / '.join(f'{x:.3f}' for x in row['V39'])} |")
    L += ['', '**Porta de GRA** (residu candidata/V38 per banda ≤1 / 1–2 / 2–4 / 4–8 / 8–16 / 16–32 / 32–64 px a finestres on la banda és soroll; objectiu ≤ 0,08 fi, ≤ 0,12 agregat; entre parèntesis el total de la V39):', '', '| capa | finestra | residu per banda | total V40/V38 (V39/V38) |', '|---|---|---|---|']
    for k, g in c3d['gra'].items():
        for wn, per in g.items():
            if 'residu_candidata_sobre_V38' in per: L.append(f"| {k} | {wn} | {' / '.join(f'{v:.2f}' for v in per['residu_candidata_sobre_V38'])} | {per['residu_total']:.2f} ({per['V39']['total'] / max(per['V38']['total'], 1e-9):.2f}) |")
    L += ['', '**Porta de VORES** (rms per bins de distància signada a la vora exterior del camp de la Vixen, r > 2,8 R☉; salt = rms a 300–900 px dins / rms a 30–300 px fora; no pot ser pitjor que la V38):', '', '| capa | salt V38 | salt V39 | salt V40 |', '|---|---|---|---|']
    for k, rows in c3d['vora_vixen'].items(): L.append(f"| {k} | ×{rows.get('V38_salt', float('nan')):.2f} | ×{rows.get('V39_salt', float('nan')):.2f} | ×{rows.get('candidata_salt', float('nan')):.2f} |")
    bb = c3c.get('BrnoBrno_1deg', {}).get('r', [None] * 3)
    L += ['', f"**Jutge Brno** (1°; rangs 1,2–3 / 3–5 / 5–9 R☉; control Brno×Brno {' / '.join(f'{v:+.2f}' for v in bb)}; transferència agregada, «n/d» = Brno no hi correlaciona ≥ 0,10; [un Brno fora]; (sectors p16/med/p84)):", '',
          '| capa | corr V38 | corr V40 | nul | transferència | rms V40/V38 |', '|---|---|---|---|---|---|']
    for k, row in c3c['capes'].items():
        d1 = row['1deg']; tr = ' / '.join(f"{fmt(t)} [{fmt(a)},{fmt(b)}] ({fmt(s0)}/{fmt(s1)}/{fmt(s2)})" for t, (a, b), (s0, s1, s2, _) in zip(d1['transferencia_cov'], d1['transferencia_un_brno_fora_min_max'], d1['transferencia_sectors_p16_med_p84_n']))
        L.append(f"| {k} | {' / '.join(f'{v:+.2f}' for v in d1['corr_V38'])} | {' / '.join(f'{v:+.2f}' for v in d1['corr_V39'])} | {' / '.join(f'{v:+.2f}' for v in d1['nul_V39'])} | {tr} | {' / '.join(f'{v:.2f}' for v in d1['rms_V39_V38'])} |")
    L += ['', 'A 4,5°: ' + '; '.join(f"{k} {' / '.join(fmt(v) for v in row['4.5deg']['transferencia_cov'])}" for k, row in c3c['capes'].items()) + '.', '']
    h1 = '; '.join(f"{k} H1 {v['H1']['worst']['error']:.3f} · H1b {v['H1b']:.2f}" for k, v in b4a['capes'].items()); L += [f"**H1/H1b (ACHF, b4a):** {h1} (V38: 0,078/2,53 · 0,063/2,66 · 0,056/1,86 · 0,044/1,57).", '']
    if disp:
        L += ['**Dispersió del soroll entre les dues particions** (mediana |N1−N2|/(N1+N2) i quocient pAB / parell-senar): ' + '; '.join(f"{lab}: " + ', '.join(f"{o['clau'].replace('vixen_', '')} {o['dispersio_mediana']:.2f} ({o['quocient_pAB_sobre_parell_senar']:.2f})" for o in outs if o['clau'].startswith('vixen_') and any(t in o['clau'] for t in ('dog2', 'dog8', 'bpachf16', 'atrous3', 'bilat0', 'bilat3')) and o['clau'][6:] in ('dog2', 'dog8', 'bpachf16', 'atrous3', 'bilat0', 'bilat3')) for lab, outs in disp.items()) + '.', '']
    L += ["**Corba de preu (A3b, injecció cega, cota inferior):** quocient V40/V38 d'un blob DoG ± de σ 2 / 8 / 24 px a 1 / 3 / 10 %:", '']
    for win in ('1.6R', '3.7R', '5.5R'):
        p = REB39 / f"A3b_injeccio_{tau['mode']}_k{tau['k']:g}_tau{tau['tau']:g}_f{tau['se_factor']:g}_min{tau['se_min']:g}_{win}.json"
        if not p.exists(): continue
        res = json.loads(p.read_text())['finestres'][win]['resultats']; L.append(f"- **{win}**: " + ' · '.join(f"{op} " + ' '.join(f"{res[f'{op}_s{s}_a{a}']['quocient']:.2f}" for a in ('0.01', '0.03', '0.1') for s in (2, 8, 24) if f'{op}_s{s}_a{a}' in res) for op in ('MGN', 'WOW', 'ACHF01', 'ACHF04', 'ACHF06')) + '  (ordre: 1 % σ2/8/24, 3 % σ2/8/24, 10 % σ2/8/24)')
    L += ['', 'Vistes: `output/v39_20260909/lliurables/vistes/C3_retall_*`, `C3d_vora_vixen_*` (1:1 a la vora de la Vixen: V38 | V39 | candidata), `output/v40_20260909/lliurables/vistes/C4_compost_V40_llenc_sencer.png`.', '']
    s = REPORT.read_text(); i = s.index('## 4. '); j = s.index('## 5. '); s = s[:i] + '\n'.join(L) + '\n' + s[j:]; REPORT.write_text(s); log('§4 del 157 omplert')


if __name__ == '__main__':
    main()
