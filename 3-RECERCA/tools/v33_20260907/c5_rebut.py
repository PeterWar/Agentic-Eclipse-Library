"""C5 · Rebut V33 (al costat del PSB i a lliurables), manifest i punters."""
from comu33 import *
import shutil
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')


def main():
    pub = json.loads((REB33 / 'C4_publish.json').read_text()); ver = json.loads((REB33 / 'C4_verification.json').read_text()); gate = json.loads((REB33 / 'C4_photoshop_gate.json').read_text())
    c0 = json.loads((REB33 / 'C0_resolucio.json').read_text()); c1 = json.loads((REB33 / 'C1_capes_cadena.json').read_text()); c2 = json.loads((REB33 / 'C2_capes_pures.json').read_text()); c3 = json.loads((REB33 / 'C3_portes.json').read_text())
    prof = {z['r']: z for z in c0['perfil']}; sp = {z['r']: z for z in c1['capes']['05']['perfil_sigma']}
    L = [f"# V33 — els filtres amb la resolució que segueix el S/N, i NRGF/RHEF sense la vora del llenç", '',
         f"Lliurada el {pub['published_utc']} per ordre de Pere («fes la V33»; el taronja de la RHEF = zona molt pixelada i sense detall). PSB LLEUGER (norma del 07-09): una base lineal + les 10 capes iterades. Les altres capes de la V32 (bases, azimutals 03/03/07, NAFE, precursors, SWAP, C01, estrelles, reflex, les de Pere) no s'han tocat i es queden a `V32.psb`.", '',
         f"- Fitxer: `{pub['path']}` · 10551 × 7506 · RGB16 · {pub['layers']} capes · {pub['bytes']:,} bytes · SHA-256 `{pub['sha256']}`.", f"- Photoshop real: **{gate['result']}**. Font de modes/màscares: `V32.psb` (`dcfc8f53…`), no modificada. Base: la fusió lineal V32, sense cap canvi.", '',
         '## Què canvia (dos canvis declarats, tots dos als filtres)', '',
         f"1. **Resolució que segueix el S/N** (snmap.sn_v33): σ(x) = max(σ_mapa, σ_local). σ_mapa ve del mapa C0, mesurat: coherència de Fourier entre parelles independents (Sony A×B, Vixen×Sony B) per tessel·les de 512 px, bandes de 8 a 256 px, nul per desplaçament de fase; σ = λ_mín/4 de la banda coherent més fina (transferència 0,29 a λ_mín, 0,73 al doble), 32 px si cap banda és coherent, suavitzat 128 px; a l'interior (r < 2,0) σ = 0,7 fixa com la V29 (les tessel·les no mesuren la corona interior amb la Lluna dins), rampa fins a 2,65. σ_local és f3.suavitza_sn autocalibrat (t 0,18): els graons de gra fi de les entrades de fotogrames. Aplicat a les 5 capes de cadena (en lloc del mapa de resolució congelat de la V29, σ ≤ 8) i, com a pas declarat, al resultat float de les 5 vistes pures (MGN, WOW, WOW bilateral, NRGF, RHEF). σ mediana resultant (capa 05): " + ', '.join(f"{r} R☉ → {sp[r]['sigma_p50']:.1f} px" for r in (1.5, 2.0, 2.65, 3.0, 4.0, 5.0, 6.0, 8.0) if r in sp) + '.',
         f"2. **NRGF/RHEF sense la vora del llenç**: de r_edge = {c2['P01_NRGF']['parameters']['r_edge_R']:.2f} R☉ enfora (primer anell que toca la vora) la mitjana i la desviació de l'anell SENCER s'estimen dels píxels presents amb la forma azimutal z-normalitzada dels 40 últims anells sencers (funció global, la idea pendent de la tesi de Druckmüllerová §6.1.2); el rang de la RHEF passa a la CDF empírica d'aquests anells, contínua amb el rang empíric. Cap retall, cap radi d'exclusió.", '',
         '## Mesures, mateixa vara (V32 → V33)', '', '| capa | gra fi a 4 R☉ (rms u) | gra mitjà a 4 R☉ | H1 pitjor | H1b |', '|---|---|---|---|---|']
    for k, g in c3['gra'].items():
        rr = np.array(g['r']); f32, f33, m32, m33 = (np.interp(4, rr, np.array(g[x])) for x in ('fi_v32', 'fi_v33', 'mig_v32', 'mig_v33'))
        h1 = f"{c1['capes'][k]['H1']['worst']['error']:.4f}" if k in c1['capes'] else '–'; h1b = f"{c1['capes'][k]['H1b']:.2f}" if k in c1['capes'] else '–'
        L.append(f"| {k} | {f32:.4f} → {f33:.4f} | {m32:.4f} → {m33:.4f} | {h1} | {h1b} |")
    tv = c3['tangencial_vora_llenc']
    L += ['', 'Anisotropia tangencial a l\'anell de la vora del llenç (8,3–8,8 R☉; +1 = cercle): ' + '; '.join(f"{k} σ16 {v['σ16']['V32']:+.2f} → {v['σ16']['V33']:+.2f}, σ32 {v['σ32']['V32']:+.2f} → {v['σ32']['V33']:+.2f}" for k, v in tv.items()) + '.', '',
          'Geometria azimutal (pic a 0°, nul a 180°): PASS a les cinc capes de cadena. H1b (potència a la freqüència dels calaixos) queda alt a 01 i 04: allà on la capa queda gairebé plana el quocient es dispara sobre valors petits; es declara, no es corregeix.', '',
          '## Límits', '', '- La resolució exterior és la que els dos trens comparteixen: de 4 R☉ enfora només queden les estructures de 64 px o més; el detall fi que hi hagués per sota queda fora per decisió (Pere: «molt pixelada i amb poc detall»).',
          '- Les vistes pures ja no són pures: porten el suavitzat S/N declarat al nom. Els float abans del suavitzat no es guarden.', '- Les azimutals 03/03/07 i les altres capes no s\'han iterat (cap marca de Pere).', '- El judici visual de Pere queda obert. Vistes: `output/v33_20260907/lliurables/vistes/` (polars V32|V33 per capa i tram, retalls a les marques, gra per radi, mapa C0).', '',
          f"Codi: `research/tools/v33_20260907/` (c0 resolució, c1 cadena, c2 pures, c3 portes, c4 PSB, snmap). Rebuts: `output/v33_20260907/4-rebuts/`."]
    txt = '\n'.join(L) + '\n'; (CT / 'V33_REBUT.md').write_text(txt); (OUT33 / 'lliurables/RESULTAT.md').write_text(txt)
    savejson(HERE33 / 'delivery_manifest.json', {'psb': pub, 'photoshop': gate, 'verification_sha256': ver['sha256'], 'layers': ver['rows'], 'base': 'fusion_total_v32', 'resolution_map': str(CAU33 / 'resolucio_v33.npy')})
    shutil.copytree(OUT33 / 'lliurables', IAOUT33 / 'lliurables', dirs_exist_ok=True); shutil.copytree(REB33, IAOUT33 / '4-rebuts', dirs_exist_ok=True); log('rebut i còpia IA fets')


if __name__ == '__main__':
    main()
