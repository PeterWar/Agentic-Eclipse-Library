"""C5 (V35) · Rebut al costat del PSB i a lliurables, manifest i còpia IA. Només després de c4 publish."""
from comu35 import *
import shutil
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')


def main():
    pub = json.loads((REB35 / 'C4_publish.json').read_text()); ver = json.loads((REB35 / 'C4_verification.json').read_text()); gate = json.loads((REB35 / 'C4_photoshop_gate.json').read_text())
    b3 = json.loads((REB35 / 'B3_fusio.json').read_text()); c3 = json.loads((REB35 / 'C3_portes.json').read_text()); b4 = json.loads((REB35 / 'B4a_capes_cadena.json').read_text())
    a1 = json.loads((REB35 / 'A1_vora_vixen.json').read_text()); a2 = json.loads((REB35 / 'A2_p05_limbe_roi.json').read_text()); a3 = json.loads((REB35 / 'A3_vora_sonyA.json').read_text())
    recs = {t: json.loads((HERE35 / 'purs/receipts' / (t + '.json')).read_text()) for t in ('P03_MGN', 'P04_WOW', 'P05_WOW_bilateral')}
    tr = b3['trains']; prof = tr['perfil_pesos']; ch = tr['channels']
    def at(g, r_):
        rr = np.array(g['r']); i = int(np.argmin(np.abs(rr - r_))); return i
    L = ['# V35 — les marques de la V34 curades a l\'origen (research/151): vora Vixen, trampa del forat, limbe dels operadors isotròpics, relleu entre trens', '',
         f"Lliurada el {pub['published_utc']} per ordre de Pere («Mira V34_artefactes i fes V35»). PSB LLEUGER: base lineal V35 + les 10 capes iterades; composició per grup de la V34 intacta; V34.psb intacta.", '',
         f"- Fitxer: `{pub['path']}` · 10551 × 7506 · RGB16 · {pub['layers']} capes · {pub['bytes']:,} bytes · SHA-256 `{pub['sha256']}`.", f"- Photoshop real: **{gate['result']}**. Modes/màscares de les capes: de `V32.psb`.", '',
         '## Què hi havia a la V34 (mesurat a la font, A1–A3, revisió de 66 marques de Pere)', '',
         f"1. **Contorn del FOV Vixen dins del camp Sony (marcat a les 10 capes).** A la vora del seu suport la Vixen anava **{a1['perfil_vora_r>4'][8]['mismatch_pct_R_G_B'][1]:+.1f} %** (G, σ64) respecte de la Sony·ρ (el ρ només s'ajustava a 1,5–4 R☉), i el seu pes queia de 0,36 a 0 en 160 px: graó de nivell de **{a1['perfil_vora_r>4'][9]['grao_fusio_vs_sony_pct']:+.2f} %** a la base i graó de gra {a1['perfil_vora_r>4'][7]['gra_fi_pct']:.3f} → {a1['perfil_vora_r>4'][10]['gra_fi_pct']:.3f} %.",
         f"2. **Trampa del forat lunar (nova a la V34).** La distància «a la vora del suport Vixen» es calculava amb el forat lunar dins: la Sony entrava a 1,0–1,36 R☉ (pes Vixen mediana {a1['pes_vixen_interior'][0]['wv_p50']:.2f} a 1,0–1,1, {a1['pes_vixen_interior'][1]['wv_p50']:.2f} a 1,1–1,2, {a1['pes_vixen_interior'][2]['wv_p50']:.2f} a 1,2–1,3). Marques del P05 al limbe.",
         f"3. **Vora de l'apuntament A dins de B** (fusió A+B per variància): nivell net (−0,1 %), però graó de gra {a3['perfil_vora_A'][5]['gra_fi_B_pct']:.3f} → {a3['perfil_vora_A'][7]['gra_fi_fusio_pct']:.3f} % en 160 px (r 6–13 R☉).",
         f"4. **Anells al limbe del MGN i dels dos WOW (recurrent V31–V34) i rectangles del WOW.** Operadors isotròpics amb el forat lunar com a suport absent: mitjana local d'un sol costat contra un gradient de ×2 cada 44 px → biaix d'anell {a2['cases']['A_suport_tal_qual/WOWbil']['ring_bias_in_sd_units_max_1.0_1.3']:.1f} σ (WOW bil.), {a2['cases']['A_suport_tal_qual/WOW']['ring_bias_in_sd_units_max_1.0_1.3']:.1f} σ (WOW), {a2['cases']['A_suport_tal_qual/MGN']['ring_bias_in_sd_units_max_1.0_1.3']:.1f} σ (MGN) a 1,0–1,3 R☉; l'à trous dispers copia la silueta del forat a ±2^s px (rectangles marcats al P04). Amb el forat omplert NOMÉS per a l'entrada de l'operador: {a2['cases']['B_forat_omplert_perfil_radial/WOWbil']['ring_bias_in_sd_units_max_1.0_1.3']:.1f} / {a2['cases']['B_forat_omplert_perfil_radial/WOW']['ring_bias_in_sd_units_max_1.0_1.3']:.1f} / {a2['cases']['B_forat_omplert_perfil_radial/MGN']['ring_bias_in_sd_units_max_1.0_1.3']:.1f} σ.",
         "5. **Relleu entre trens** 2,0→2,65 R☉: el gra de la base queia a la meitat en 130 px (marques P04/P05 a 2,2–2,7).",
         "6. Contorns transversals interiors (isofotes d'entrada dels fotogrames, 1,2–2,1 R☉): graons de gra que la V34 va deixar a 0,93; origen de captura. Queden, més subtils.", '',
         '## Què canvia la V35 (tot a la composició i a la condició de contorn dels operadors; cap suavitzat, cap màscara, cap retall)', '',
         f"1. Distàncies a la vora sobre suports PLENS: Vixen sola fins a 1,9 R☉ de debò (pes {prof[0]['frac_vixen_p50']:.2f} a 1,0–1,1, {prof[2]['frac_vixen_p50']:.2f} a 1,2–1,3).",
         f"2. Vixen conformada a la Sony·ρ en baixa freqüència (δ σ256 a tot el solapament, entrada smoothstep 2,0→2,65): residu |ln V/Sρ| als sectors reservats G {ch['1']['holdout_delta_abans_median_abs_pct']:.2f} → {ch['1']['holdout_delta_despres_median_abs_pct']:.2f} %, R {ch['0']['holdout_delta_abans_median_abs_pct']:.2f} → {ch['0']['holdout_delta_despres_median_abs_pct']:.2f} %, B {ch['2']['holdout_delta_abans_median_abs_pct']:.2f} → {ch['2']['holdout_delta_despres_median_abs_pct']:.2f} %.",
         f"3. Pes Vixen esvaït en {TAPER_VIXEN_PX:.0f} px a la vora del seu suport (0 → 0,36 entre 0 i 700 px); pes A esvaït en {TAPER_A_PX:.0f} px a la seva.",
         f"4. Relleu entre trens {RELLEU_R[0]}→{RELLEU_R[1]} R☉ (la variància només afegeix Vixen): fracció Vixen " + ', '.join(f"{z['r']} R☉ {z['frac_vixen_p50']:.2f}" for z in prof if z['frac_vixen_p50'] is not None and z['r'] >= 1.9) + '.',
         "5. P03/P04/P05: entrada de l'operador = base on hi ha suport + perfil azimutal mitjà (ln) de la pròpia imatge al forat lunar i fora del suport; sortida només al suport físic; LUT de pantalla de la V34. P01/P02 amb l'anell sencer (b4d) com la V34. Capes 01–06 amb la recepta exacta.", '',
         '## Portes, mateixa vara (V34 → V35)', '', '(Les dues columnes de vora d\'aquesta primera taula són per calaixos de distància: valen per a les capes passa-alt (01–06, P03–P05) i NO per a P01/P02, on els calaixos dins/fora cauen a radis diferents i el camp llis fa de «graó»; la porta bona per a totes és la taula aparellada de sota.)', '', '| capa | graó a la vora Vixen (÷ rms) | graó a la vora A (÷ rms) | biaix d\'anell al limbe (σ) | gra fi 4 R☉ | H1 pitjor |', '|---|---|---|---|---|---|']
    for k, g in c3['gra'].items():
        if k.startswith('base'):
            continue
        vv = c3['vora_vixen']['capes'][k]; va = c3['vora_A']['capes'][k]; lb = c3['limbe_biaix_anell_sigma'][k]; i4 = at(g, 4.0)
        h1 = f"{b4['capes'][k]['H1']['worst']['error']:.4f}" if k in b4['capes'] else '–'
        f = lambda d: '–' if d is None else f'{d:+.2f}'
        L.append(f"| {k} | {f(vv['V34']['grao_sobre_rms'])} → {f(vv['V35']['grao_sobre_rms'])} | {f(va['V34']['grao_sobre_rms'])} → {f(va['V35']['grao_sobre_rms'])} | {lb['V34']:.2f} → {lb['V35']:.2f} | {g['fi_v34'][i4]:.4f} → {g['fi_v35'][i4]:.4f} | {h1} |")
    c3b = json.loads((REB35 / 'C3b_vora_aparellada.json').read_text()) if (REB35 / 'C3b_vora_aparellada.json').exists() else None
    if c3b:
        L += ['', 'Graó APARELLAT a la vora (mitjana local σ24 a +150 px dins − a −150 px fora, al llarg de la normal, mediana sobre el contorn, ÷ rms de la banda 6–12 px; entre parèntesis el control nul: mateix càlcul al contorn desplaçat 600 px cap endins). Aquesta és la porta que val per a NRGF/RHEF (la per calaixos no hi val):', '',
              '| capa | vora Vixen V34 (nul) | vora Vixen V35 (nul) | vora A V34 (nul) | vora A V35 (nul) |', '|---|---|---|---|---|']
        for k, row in c3b['capes'].items():
            g = lambda d: f"{d['grao_sobre_rms']:+.2f} ({d['nul_sobre_rms']:+.2f})"
            L.append(f"| {k} | {g(row['V34']['vixen'])} | {g(row['V35']['vixen'])} | {g(row['V34']['A'])} | {g(row['V35']['A'])} |")
    bv = c3['vora_vixen']['capes']; bins = c3['vora_vixen']['bins_px']
    def pick(d, lo, hi):
        v = [x for b, x in zip(bins, d) if x is not None and lo <= b < hi]; return float(np.mean(v)) if v else float('nan')
    L += ['', f"Base (r > 4 R☉, ±50–250 px de la vora Vixen, calaixos amb el biaix radial COMÚ a les dues versions, o sigui que només val la diferència): nivell V34 {pick(bv['base_V34']['nivell_pct'], 50, 250) - pick(bv['base_V34']['nivell_pct'], -250, -50):+.2f} % → V35 {pick(bv['base_V35']['nivell_pct'], 50, 250) - pick(bv['base_V35']['nivell_pct'], -250, -50):+.2f} % (la V35 puja 0,6 % dins respecte de fora: és el graó de −0,7 % que la V34 imprimia i la V35 no, coherent amb A1); gra fi fora/dins V34 {pick(bv['base_V34']['gra_fi_pct'], -250, -50):.3f}/{pick(bv['base_V34']['gra_fi_pct'], 50, 250):.3f} % → V35 {pick(bv['base_V35']['gra_fi_pct'], -250, -50):.3f}/{pick(bv['base_V35']['gra_fi_pct'], 50, 250):.3f} %.",
          f"Relleu 1,8–3,5 R☉: pendent màxim del gra de la base V34 {c3['relleu']['base_V34']['max_dlnsigma_per_0.1R']:.2f} → V35 {c3['relleu']['base_V35']['max_dlnsigma_per_0.1R']:.2f} (|Δ ln σ| per 0,1 R☉).",
          f"NRGF/RHEF, anisotropia a la vora del llenç (σ32): NRGF {c3['tangencial_vora_llenc']['P01']['σ32']['V34']:+.2f} → {c3['tangencial_vora_llenc']['P01']['σ32']['V35']:+.2f}; RHEF {c3['tangencial_vora_llenc']['P02']['σ32']['V34']:+.2f} → {c3['tangencial_vora_llenc']['P02']['σ32']['V35']:+.2f}.",
          f"Porta A+B (correlació amb la Vixen a 2,5–5 R☉): σ12 {b3['pointings']['porta']['sigma12']['B_sola']:+.3f} → {b3['pointings']['porta']['sigma12']['A+B']:+.3f}, σ24 {b3['pointings']['porta']['sigma24']['B_sola']:+.3f} → {b3['pointings']['porta']['sigma24']['A+B']:+.3f}: {'acceptada' if b3['pointings']['porta']['acceptada_A+B'] else 'refusada'}.", '',
          '| r (R☉) | gra fi base V32 | V34 | V35 (%) |', '|---|---|---|---|']
    g32, g34, g35 = c3['gra']['base_V32'], c3['gra']['base_V34'], c3['gra']['base_V35']
    for r_ in (1.3, 1.6, 2.0, 2.2, 2.4, 2.65, 3.0, 4.0, 5.0, 6.0, 8.0):
        L.append(f"| {r_} | {g32['fi_pct'][at(g32, r_)]:.3f} | {g34['fi_pct'][at(g34, r_)]:.3f} | {g35['fi_pct'][at(g35, r_)]:.3f} |")
    L += ['', '## Límits i preu declarat', '',
          "- La conformació δ fa que de 2,65 R☉ enfora la baixa freqüència de la base sigui la de la Sony·ρ (com a la V32/V34): la Vixen només hi afegeix la seva alta freqüència i el seu gra menor. On la Vixen és a menys de 700 px de la seva vora, el seu pes és més petit que a la V34 (menys reducció de gra allà).",
          "- El relleu 1,9→3,5 conserva la resolució nativa de la Vixen fins més enfora i deixa més gra a 2,2–2,6 que la V34 (gra fi a 2,4: vegeu la taula): és el preu de no fer un salt.",
          "- El farcit del forat lunar és una condició de contorn de l'operador: cap píxel farcit entra al producte. Al primer anell (1,00–1,03 R☉) queda un residu (anells parcials).",
          "- Contorns transversals interiors (entrada dels fotogrames) i vora del suport Sony: sense canvis; origen de captura (requisit 2027). Anells blaus de la Vixen, taca NE, registre dels fotogrames llargs Sony: deutes que continuen.",
          "- Judici visual de Pere obert. Vistes: `output/v35_20260908/lliurables/vistes/` (retalls V34|V35 a les seves marques i a la vora Vixen, polars, gra per radi, A1–A4).", '',
          "Codi: `research/tools/v35_20260908/` (comu35, a1–a3, b3, b4a, b4c_purs, b4d, c3, c4, c5). Rebuts: `output/v35_20260908/4-rebuts/`. Revisió de marques: `research/tools/revisio_marques_v34_20260908/`, `output/revisio_marques_v34_20260908/`."]
    txt = '\n'.join(L) + '\n'; (CT / 'V35_REBUT.md').write_text(txt); (OUT35 / 'lliurables/RESULTAT.md').write_text(txt)
    savejson(HERE35 / 'delivery_manifest.json', {'psb': pub, 'photoshop': gate, 'verification_sha256': ver['sha256'], 'layers': ver['rows'], 'base': 'fusion_total_v35', 'canvis': REP_CANVIS})
    shutil.copytree(OUT35 / 'lliurables', IAOUT35 / 'lliurables', dirs_exist_ok=True); shutil.copytree(REB35, IAOUT35 / '4-rebuts', dirs_exist_ok=True); log('rebut i còpia IA fets')


if __name__ == '__main__':
    main()
