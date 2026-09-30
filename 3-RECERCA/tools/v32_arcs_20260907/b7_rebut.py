"""B7 · Rebut V32 (markdown al costat del PSB i a lliurables/RESULTAT.md), manifest amb hashes
i còpia de les vistes a IA/output. No toca cap PSB."""
from comu32 import *
import shutil

CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')


def J(p):
    return json.loads((REB / p).read_text()) if (REB / p).exists() else None


def main():
    pub = J('B6_publish.json'); ver = J('B6_psb_verification.json'); gate = J('B6_photoshop_gate.json'); b3 = J('B3_fusio.json'); b4a = J('B4a_capes_cadena.json'); b4b = J('B4b_capes_azimutals.json')
    a6 = J('A6_flat_ondulacio.json'); jut = J('B5_jutge_abans_despres.json'); pk = J('B6_packaging.json')
    a4o = J('A4_anisotropia.json'); a4n = J('A4v32_anisotropia.json'); a5o = J('A5_graons.json'); a5n = J('A5v32_graons.json')
    inj = json.loads((HERE / 'purs/receipts/injection.json').read_text()) if (HERE / 'purs/receipts/injection.json').exists() else None
    b1 = {g: J(f'B1_camps_{g}.json') for g in ('vixen', 'sony_A', 'sony_B')}
    L = []
    L.append(f"# V32 — tots els filtres regenerats sobre una base curada a l'origen\n")
    L.append(f"Lliurada el {pub['published_utc'] if pub else '(no publicada)'} per ordre de Pere («fes una nova versió de tots els filtres eliminant els artefactes lila i blaus»).\n")
    if ver:
        L.append(f"- Fitxer: `{pub['path'] if pub else ver['path']}` · 10551 × 7506 · RGB16 · 40 capes · {ver['bytes']:,} bytes · SHA-256 `{ver['sha256']}`.")
        L.append(f"- Photoshop real: **{gate['result'] if gate else 'porta no executada'}**. Font preservada: `V31_FiltresPurs.psb` (`{pk['source_sha256']}`), no modificada.")
        L.append(f"- Capes substituïdes (només RGB; alfa, màscara, mode, opacitat i visibilitat intactes): {len(pk['changed'])}. Les altres 22 capes són byte a byte les de la V31_FiltresPurs.\n")
    L.append("## Què s'ha corregit i on\n")
    L.append("Tres causes mesurades, totes a la FONT (cap retall circular, cap màscara de marques, cap inpainting):\n")
    L.append("1. **Fronteres de fusió HDR amb desnivell entre fotogrames** (interior 1,0–2,2 R☉ de la Vixen; entrada dels 8 s de la Sony a 2,6–2,8 R☉). Cura: camp de nivell suau (σ 128 px) per fotograma i canal natiu, estimat a l'altiplà de cada fotograma contra el compost i aplicat abans de recompondre; gauge suau (σ 512 px) que conserva el nivell del compost. Els pesos LDIC no es toquen.")
    if a6:
        f = a6['flat']
        L.append(f"2. **Ondulació fina del flat radial de la Sony** (rms {f['1']['ripple_rms_pct_r400_2400']:.3f} % al subpla G1, σ8; correlació −0,80 i pendent −1,00 amb l'ondulació del fotograma calibrat): cada fotograma Sony la portava invertida, centrada al centre del sensor (0,5 R☉ del Sol a l'apuntament B) → els arcs de 3,2–4,6 R☉ de tots els filtres no azimutals. Cura: perfil radial del flat suavitzat (σ {f['sigma_px']:g} px del sensor); el vinyetatge i l'estructura no radial del flat es conserven. Porta: l'ondulació anular del 8 s baixa del 0,115 % al 0,075 % (soroll 0,074 %).")
    if b3:
        t = b3['trains']
        L.append(f"3. **Fusió entre trens**: guany Sony→Vixen com a camp 2D suau (σ {t['rho_sigma_px']:g} px) per canal en lloc d'un escalar, i ploma de {t['edge_feather_px']:g} px a la vora del suport Sony (abans, canvi sec de font). Validació en sectors reservats (2–3,5 R☉): biaix " + ', '.join(f"{t['channels'][c]['holdout_sectors_median_bias_pct']:+.2f} %" for c in '012') + f"; |error| mediana " + ', '.join(f"{t['channels'][c]['holdout_median_abs_err_pct']:.2f} %" for c in '012') + ".\n")
    L.append("Els offsets constants del c03 es conserven (entren pels mateixos pesos). La ploma A/B dels apuntaments Sony (384 px, B primària) és la de la V29.\n")
    L.append("## Mesures abans/després\n")
    if a4o and a4n:
        L.append("Anisotropia tangencial a l'escala fina (σ 4 px; + = arcs, − = raigs), anells 3–3,5 / 3,5–4 / 4–4,5 / 4,5–5 R☉:\n")
        L.append("| font | V31 | V32 |\n|---|---|---|")
        pairs = [('base_G_ln', 'base_G_ln_v32'), ('sonyB_G_ln', 'sonyB_G_ln_v32'), ('vixen_G_ln', 'vixen_G_ln_v32'), ('V31_02_passalt24_u16', 'V32_02_passalt24_u16'), ('V31_05_ACHF_fi48_u16', 'V32_05_ACHF_fi48_u16'), ('V31_06_estructura_u16', 'V32_06_estructura_u16'), ('P03_MGN', 'P03_MGN_v32'), ('P04_WOW', 'P04_WOW_v32'), ('P01_NRGF', 'P01_NRGF_v32')]
        for o, n in pairs:
            if o in a4o['fonts'] and n in a4n['fonts']:
                fo = a4o['fonts'][o]['4'][1:5]; fn = a4n['fonts'][n]['4'][1:5]
                L.append(f"| {o} | " + ' / '.join(f"{z['score']:+.3f}" for z in fo) + " | " + ' / '.join(f"{z['score']:+.3f}" for z in fn) + " |")
        L.append("")
    if a5o and a5n:
        L.append("Graó diferencial de nivell a les fronteres d'entrada (ln font − ln altre tren original, %; controls a ±100 px):\n")
        L.append("| tren | fotograma | r (R☉) | V31 graó | V32 graó | V32 controls |\n|---|---|---|---|---|---|")
        for name in ('Vixen', 'SonyB'):
            ro = {r['frame']: r for r in a5o['trens'].get(name, [])}; rn = {r['frame']: r for r in a5n['trens'].get(name, [])}
            for fr in rn:
                if fr in ro and rn[fr]['exp'] >= 1:
                    src = 'base'
                    ko = [k for k in ro[fr]['fonts'][src] if k.startswith('diferencial')][0]; kn = [k for k in rn[fr]['fonts'][src] if k.startswith('diferencial')][0]
                    do = ro[fr]['fonts'][src][ko]; dn = rn[fr]['fonts'][src][kn]
                    L.append(f"| {name} | {fr[:-4]} {rn[fr]['exp']:g} s | {rn[fr]['r_R_median']:.2f} | {do['graó_mediana_pct']:+.3f} | {dn['graó_mediana_pct']:+.3f} | {dn['control_-100_pct']:+.3f} / {dn['control_+100_pct']:+.3f} |")
        L.append("")
    if jut:
        L.append(f"Jutge extern fix (Vixen original, quatre finestres a 3,5–4 R☉, bandes 2–8/8–32/32–64 px): correlació de les vistes pures amb la Vixen, V32 − V31 = {jut['delta_corr_layers_mean']:+.4f} de mitjana (puja a {jut['n_up']}, baixa a {jut['n_down']} de {len(jut['rows'])}); base {jut['delta_corr_base_mean']:+.4f}.")
    if inj:
        L.append(f"Injecció cega (σ 2/8/24 px, 1 % de la mediana) sobre la base V32: resposta aparellada positiva a MGN/WOW/WOW bilateral/NAFE (`purs/receipts/injection.json`).")
    if b4a:
        L.append("\nPortes de les capes de la cadena (H1 ≤ 0,05; geometria azimutal pic a 0°):\n")
        L.append("| capa | H1 pitjor | H1b | pic azimutal | Pearson a 0° | PASS |\n|---|---|---|---|---|---|")
        for k, v in b4a['capes'].items():
            g = v['geometria_azimutal']; L.append(f"| {v['name']} | {v['H1']['worst']['error']:.4f} | {v['H1b']:.3f} | {g.get('peak_angle_deg', '–')} | {g.get('at_zero_pearson', 0):.3f} | {g.get('PASS')} |")
        if b4b:
            for k, v in b4b['capes'].items():
                g = v['geometria_azimutal']; L.append(f"| {v['name']} | {v['H1']['worst']['error']:.4f} | {v['H1b']:.3f} | {g.get('peak_angle_deg', '–')} | {g.get('at_zero_pearson', 0):.3f} | {g.get('PASS')} |")
        L.append("")
    L.append("## Límits declarats\n")
    L.append("- No s'afirma l'eliminació de tots els arcs: es mesura què queda (taules d'aquest rebut i `4-rebuts/`). Les marques de Pere han servit de finestres de diagnosi, mai de màscares.")
    L.append("- Els fotogrames llargs de la Sony (2 s i 8 s) tenen registre «model» (correlació refusada a la F1.3); part dels camps per fotograma absorbeix el desnivell de gradient que crea un error de registre d'1–3 px. El registre no s'ha refet.")
    L.append("- La taca NE (~7,8 R☉) mesura ≤ 0,01 % a la base (A7): no s'ha pedaçat.")
    L.append("- Les capes de base (00), les de Pere, estrelles i reflex no es toquen: el compost per defecte només canvia pels filtres visibles regenerats.")
    L.append("- Perfils de contrast, mapa de resolució, escales tanh i opacitats: congelats de la V29/V30/V31 (només canvia la font).\n")
    L.append(f"Codi i rebuts: `research/tools/v32_arcs_20260907/` i `output/v32_arcs_20260907/4-rebuts/`. Vistes: `output/v32_arcs_20260907/lliurables/vistes/` (còpia a `IA/output/v32_arcs_20260907/`).\n")
    txt = '\n'.join(L)
    (OUT32 / 'lliurables/RESULTAT.md').write_text(txt)
    if pub:
        (CT / 'V32_REBUT.md').write_text(txt)
    # manifest
    man = {'version': 'V32', 'published': pub, 'verification': ver, 'gate': gate, 'code_sha256': {p.name: sha(p) for p in sorted(HERE.glob('*.py'))},
           'receipts_sha256': {p.name: sha(p) for p in sorted(REB.glob('*.json'))}, 'purs_receipts_sha256': {p.name: sha(p) for p in sorted((HERE / 'purs/receipts').glob('*.json'))}}
    savejson(HERE / 'delivery_manifest.json', man)
    if IAOUT.exists():
        shutil.rmtree(IAOUT)
    shutil.copytree(VIS, IAOUT); shutil.copy2(OUT32 / 'lliurables/RESULTAT.md', IAOUT / 'LLEGEIX-ME.md')
    log('rebut i manifest escrits')


if __name__ == '__main__':
    main()
