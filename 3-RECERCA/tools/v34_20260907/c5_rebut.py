"""C5 · Rebut V34 (al costat del PSB i a lliurables), manifest i còpia IA. Només després de c4 publish."""
from comu34 import *
import shutil
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')


def main():
    pub = json.loads((REB34 / 'C4_publish.json').read_text()); ver = json.loads((REB34 / 'C4_verification.json').read_text()); gate = json.loads((REB34 / 'C4_photoshop_gate.json').read_text())
    b3 = json.loads((REB34 / 'B3_fusio.json').read_text()); c3 = json.loads((REB34 / 'C3_portes.json').read_text()); b1 = {g: json.loads((REB34 / f'B1_camps_{g}.json').read_text()) for g in ('vixen', 'sony_A', 'sony_B')}; b4 = json.loads((REB34 / 'B4a_capes_cadena.json').read_text())
    porta = b3['pointings']['porta']; prof = b3['trains']['perfil_pesos']
    gb32 = c3['gra']['base_V32']; gb34 = c3['gra']['base_V34']; rr = np.array(gb32['r']); f32 = np.array(gb32['fi_pct']); f34 = np.array(gb34['fi_pct'])
    def at(r_):
        i = int(np.argmin(np.abs(rr - r_))); return f32[i], f34[i]
    L = [f"# V34 — la composició curada a l'origen (research/149): entrada gradual, Sony lineal, fusió per variància. Cap suavitzat.", '',
         f"Lliurada el {pub['published_utc']} per ordre de Pere («atacar el problema en origen; no sacrificar detall»). PSB LLEUGER: base lineal V34 + les 10 capes iterades, amb la recepta de filtres EXACTA de la V32 (mapa de resolució congelat de la V29; res del suavitzat de la V33). V32.psb i V33.psb intactes (la V33 queda refusada).", '',
         f"- Fitxer: `{pub['path']}` · 10551 × 7506 · RGB16 · {pub['layers']} capes · {pub['bytes']:,} bytes · SHA-256 `{pub['sha256']}`.", f"- Photoshop real: **{gate['result']}**. Modes/màscares de les capes: de `V32.psb`.", '',
         '## Els tres canvis, tots a la composició', '',
         "1. **Entrada gradual dels fotogrames**: la finestra de pes (f2.finestra) manté el terra (12→48 DN) i el sostre passa d'una rampa lineal del 70 al 85 % de la saturació a un smoothstep del 35 al 85 % (píxels lineals a la Vixen ±0,13 %; a la Sony, corregits). Els pesos A1 i els camps de nivell B1 s'han recalculat amb la finestra nova.",
         "2. **Linealitat de la Sony corregida** amb la corba mesurada a la dada (parelles d'exposicions veïnes, tres sectors, subpla G): 0 fins al 42,5 % de saturació, −0,4/−0,5 % del 60 al 85 %, −1,2 % al 92 %, −1,7 % al 97 %; aplicada a (raw − dark) abans del flat. La Vixen no en necessita.",
         f"3. **Fusió per variància**: Sony A i B fusionats amb pesos ∝ 1/σ² (variància local del gra fi de ln G, 48 px), ghost de A exclòs, plomes de 160 px; porta contra la Vixen a 2,5–5 R☉: correlació σ12 B sola {porta['sigma12']['B_sola']:+.3f} → A+B {porta['sigma12']['A+B']:+.3f}; σ24 {porta['sigma24']['B_sola']:+.3f} → {porta['sigma24']['A+B']:+.3f}; gra fi a la zona {porta['gra_fi_rms_pct_zona']['B_sola']:.3f} → {porta['gra_fi_rms_pct_zona']['A+B']:.3f} % → **{'A+B acceptada' if porta['acceptada_A+B'] else 'A+B refusada: B sola com la V32'}**. Trens: Vixen sola fins a 1,9 R☉, rampa a 2,1 cap a pesos ∝ 1/σ² de cada tren (abans: smoothstep per radi 2,0–2,65 i Sony sola de 2,65 enfora). Fracció Vixen mediana: " + ', '.join(f"{z['r']} R☉ {z['frac_vixen_p50']:.2f}" for z in prof if z['frac_vixen_p50'] is not None) + '.', '',
         '## Mesures, mateixa vara (V32 → V34)', '', '| r (R☉) | gra fi base V32 (%) | gra fi base V34 (%) |', '|---|---|---|']
    for r_ in (1.3, 1.6, 2.0, 2.3, 2.65, 3.0, 4.0, 5.0, 6.0, 8.0):
        a, b = at(r_); L.append(f'| {r_} | {a:.3f} | {b:.3f} |')
    L += ['', '| capa | gra fi a 4 R☉ | gra mitjà a 4 R☉ | H1 pitjor | H1b |', '|---|---|---|---|---|']
    for k, g in c3['gra'].items():
        if k.startswith('base'):
            continue
        rr2 = np.array(g['r']); f32_, f34_, m32_, m34_ = (np.interp(4, rr2, np.array(g[x])) for x in ('fi_v32', 'fi_v33', 'mig_v32', 'mig_v33'))
        h1 = f"{b4['capes'][k]['H1']['worst']['error']:.4f}" if k in b4['capes'] else '–'; h1b = f"{b4['capes'][k]['H1b']:.2f}" if k in b4['capes'] else '–'
        L.append(f"| {k} | {f32_:.4f} → {f34_:.4f} | {m32_:.4f} → {m34_:.4f} | {h1} | {h1b} |")
    L += ['', 'Camps B1 (residu a l\'altiplà, mediana, última iteració): ' + '; '.join(f"{g} G {b1[g]['channels']['G']['history'][-1]['rms_residu_altipla_mediana_pct']:.3f} %" for g in b1) + '.', '',
          '## Límits', '', '- Cap suavitzat, cap retall, cap màscara: el gra que queda és el de la dada amb tots els fotogrames i tots dos trens on són menys sorollosos.',
          '- Els graons de gra a les entrades dels fotogrames només s\'eixamplen (×2): l\'origen és de captura (salts de 5× entre exposicions, 3 fotogrames per esglaó; requisit 2027).',
          '- La correcció de linealitat de la Sony és una corba mesurada de la dada (no del fabricant); el seu efecte a la vora del sostre és de −0,5 a −1 %.',
          '- Judici visual de Pere obert. Vistes: `output/v34_20260907/lliurables/vistes/` (polars V32|V34, retalls a les marques V32 i V33, gra per radi).', '',
          f"Codi: `research/tools/v34_20260907/` (comu34, a1, b1, b2, b3, b4a, b4c, c3, c4, c5). Rebuts: `output/v34_20260907/4-rebuts/`."]
    txt = '\n'.join(L) + '\n'; (CT / 'V34_REBUT.md').write_text(txt); (OUT34 / 'lliurables/RESULTAT.md').write_text(txt)
    savejson(HERE34 / 'delivery_manifest.json', {'psb': pub, 'photoshop': gate, 'verification_sha256': ver['sha256'], 'layers': ver['rows'], 'base': 'fusion_total_v34', 'canvis': REP_CANVIS})
    shutil.copytree(OUT34 / 'lliurables', IAOUT34 / 'lliurables', dirs_exist_ok=True); shutil.copytree(REB34, IAOUT34 / '4-rebuts', dirs_exist_ok=True); log('rebut i còpia IA fets')


if __name__ == '__main__':
    main()
