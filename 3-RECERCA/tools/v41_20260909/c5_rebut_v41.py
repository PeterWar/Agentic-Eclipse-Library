"""C5 (V41) · Rebut al costat del PSB (V41_REBUT.md), RESULTAT.md, manifest i còpia IA. Només després de c4_projecte_v41 publish."""
from comu41 import *
import shutil
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')


def main():
    pub = json.loads((REB41 / 'C4_publish.json').read_text()); ver = json.loads((REB41 / 'C4_verification.json').read_text()); gate = json.loads((REB41 / 'C4_photoshop_gate.json').read_text()); pk = json.loads((REB41 / 'C4_packaging.json').read_text())
    b4e = json.loads((REB41 / 'B4e_rhef_upsilon.json').read_text()); e1e = json.loads((REB41 / 'E1e_rotacio_AB.json').read_text()); e1f = json.loads((REB41 / 'E1f_filtres_al_pic_real.json').read_text())['filtres']; ce = e1e['capa_estrelles']
    L = ['# V41 — les capes de la V40 sense cap reducció de soroll, més una segona RHEF (υ 0,35) · research/159', '',
         f"Lliurada el {pub['published_utc']} per ordre de Pere («oblidem-nos de moment de reduir el soroll, hi ha el que hi ha; V41 partint de V39 sense artefactes i només amb les capes de la V40, però sense la reducció de soroll»; «un filtre RHEF més amb settings lleugerament diferents»).", '',
         f"- Fitxer: `{pub['path']}` · 10551 × 7506 · RGB16 · {pub['layers']} capes · {pub['bytes']:,} bytes · SHA-256 `{pub['sha256']}`.", f"- Photoshop real: **{gate['result']}**. Verificació capa a capa contra les fonts: {sum(1 for r in ver['rows'] if r['exact'])} de {len(ver['rows'])} exactes.",
         f"- Fonts: `V39.psb` `{pk['fonts']['V39.psb']}` · `V38.psb` `{pk['fonts']['V38.psb']}` · `V40.psb` (ordre, modes, opacitats, visibilitats) `{pk['fonts']['V40.psb']}`.", '',
         '## Què és', '',
         '1. **Cap píxel nou de filtre i cap tractament de soroll.** Els set filtres que la V39 i la V40 havien tractat (01/04/05/06 ACHF, P03 MGN, P04 WOW, P05 WOW bilateral) són els de la **V38, byte a byte** (la recepta sense guany: el codi V39/V40 amb τ = 0 la reprodueix a 4e-9 / 8e-5). Per això al PSB es diuen «· V38».',
         '2. **La resta, de la V39** (les teves 06–12, les dues bases de pantalla V39, 03 r0/r4/07 V38, P01/P01b/P02 V39; P01 i P02 són idèntiques a les de la V38).',
         f"3. **Capa nova `P02b RHEF υ 0,35 · V41`** (oculta, Superposar al 5 % com la P02): la mateixa RHEF amb la funció «upsilon» de la implementació de referència de Gilly & Cranmer (sunkit-image, υ = {b4e['upsilon']:g} per defecte; la V38 no l'aplicava): gamma de dos costats tallada a la mitjana ({b4e['mid']:.3f}) que acosta TOT valor a 0,5 → en Superposar és una RHEF més feble pertot (la meitat d'amplitud al gruix) amb més contrast local només a l'1–10 % més fosc i més brillant de cada anell. Quantils 1/10/25/50/75/90/99 %: " + ' '.join(f'{v:.3f}' for v in b4e['quantils_x']) + ' → ' + ' '.join(f'{v:.3f}' for v in b4e['quantils_y']) + '.',
         '4. Opacitats (Photoshop; cru 0–255 entre parèntesis): 01/04/05 13 % (33), 06 12 % (31), P01/P01b 13 % (33), P02/P02b 5 % (13), P03/P04 13 % (33), P05 Llum forta 17 % (43): les de la V40. Les màscares dels set filtres són les de V38.psb; les altres, la mateixa requantitzada pel re-desat de Photoshop (±1 nivell a 2.852 px): efecte nul.', '',
         '## Les estrelles (research/159 §3)', '',
         f"- El seguiment solar no és la causa (~2 px en tota la totalitat). Les estrelles són al límit del gra: {e1e['estrelles_diferents_amb_pic']} de 33 estrelles diferents passen de 4 σ (suavitzat σ 2); apilades al pic real, +13,6 σ i radi a mig màxim 2,7 px (FWHM ≈ 5 px).",
         f"- La capa `Estrelles` de la V38 no seia sobre les estrelles: pic real a ({ce['desplacament_mitja_px'][0]:+.0f}, {ce['desplacament_mitja_px'][1]:+.0f}) px de mitjana, i no rígid: translació sola {ce['rms_translacio_sola_px']:.1f} px rms, rotació {ce['rotacio_arcmin']:+.1f}′ + translació {ce['rms_rotacio_px']:.1f} px. Bé que la vas treure; si torna, re-registrar amb rotació.",
         f"- **Causa del doblat: els dos apuntaments de la Sony no coincideixen a les estrelles.** B cau a 6–14 px de A; els {e1e['n']} vectors A→B s'ajusten amb una rotació de {e1e['rotacio_arcmin']:+.2f}′ al voltant del Sol (residu {e1e['rms_residu_px']:.2f} px per component, {e1e['rms_nomes_translacio_px']:.1f} amb només translació; nul de {e1e['nul']['permutacions']} permutacions: cap hi arriba): la rotació de camp del salt de la muntura del 28-08 (+7,9′), que la composició no aplica (F1.3 només trasllada). {e1e['dobles']} de {e1e['estrelles_diferents_amb_pic']} estrelles surten dobles a la fusió. La traça de la B (angle comú +33…+45°) és una altra cosa: desregistre per translació entre els seus fotogrames llargs.",
         f"- Els filtres canvien l'empremta però no creen el doblat (apilat al pic real, 12 estrelles): base +{e1f['base fusió']['centre_sigma']:.1f} σ r½ {e1f['base fusió']['r_mig_px']:.1f} px; ACHF 01 +{e1f['01 ACHF fi 2-32']['centre_sigma']:.1f} σ r½ {e1f['01 ACHF fi 2-32']['r_mig_px']:.1f} (×2 més ample); MGN +{e1f['P03 MGN']['centre_sigma']:.1f} σ; WOW +{e1f['P04 WOW']['centre_sigma']:.1f} σ; NRGF la respecta; RHEF la converteix en rang (+1…+47 σ segons l'anell).",
         '- Decisió teva: (recomanat, V42) recompondre l\'apuntament B amb la rotació mesurada; després deixar-les, tornar-les com a capa de llum mesurada sobre filtres calculats sense elles, o treure-les declarat. Cap PSF sintètica.', '',
         '## Capes del projecte (de baix a dalt)', ''] + [f"- {c['name']} — {c.get('font', c.get('kind'))}{' (visible)' if c.get('visible') else ''}" for c in pk['capes']]
    L += ['', "Vistes: `output/v41_20260909/lliurables/vistes/` (compost, galeries d'estrelles). Codi: `research/tools/v41_20260909/`. Informe: `research/159`. V38, V39, V40 intactes. Judici visual de Pere obert."]
    txt = '\n'.join(L) + '\n'; (CT / 'V41_REBUT.md').write_text(txt); (OUT41 / 'lliurables').mkdir(parents=True, exist_ok=True); (OUT41 / 'lliurables/RESULTAT.md').write_text(txt)
    savejson(HERE41 / 'delivery_manifest.json', {'psb': pub, 'photoshop': gate, 'verification_sha256': ver['sha256'], 'layers': ver['rows'], 'fonts': pk['fonts'], 'rhef_upsilon': b4e, 'report': 'research/159'})
    shutil.copytree(OUT41 / 'lliurables', IAOUT41 / 'lliurables', dirs_exist_ok=True); shutil.copytree(REB41, IAOUT41 / '4-rebuts', dirs_exist_ok=True); log('rebut i còpia IA fets')


if __name__ == '__main__':
    main()
