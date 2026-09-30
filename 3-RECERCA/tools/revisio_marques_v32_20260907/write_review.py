"""Publica lliurables/RESULTAT.md: revisió capa a capa (22 capes) i taula de totes les marques amb
família, radis, fotogrames que canvien (A2) i correlació creuada amb control nul (A7). Enllaços a
les vistes. No toca cap PSB."""
from extract import *
NOTES = {
0: ('Sense pintura', 'Les diferències contra V32.psb són la re-quantització ±1 DN16 de Photoshop (360.744 px, màxim 1). Cap traç.'),
1: ('Sense pintura', 'Igual que la capa 00: només ±1 DN16 de re-quantització. Cap traç.'),
2: ('Sense marques', 'Azimutal r0 (recepta V29). Pere no hi ha pintat res; la diagonal groga de la V31 ja no hi és marcada.'),
3: ('Sense marques', 'Azimutal r4 (recepta V30). Cap traç.'),
4: ('Sense marques', 'Azimutal suau r8. Cap traç.'),
5: ('Corona interior (verds i lila)', 'Tres verds a 1,51–1,83 R☉ i un lila a 1,47–1,57: correlació Vixen×Sony B +0,62/+0,82/+0,50 als verds i +0,83 al lila, amb nuls a −0,01/+0,05/0,00/−0,07 (A7). El lila seu a l\'entrada dels 2 s (1,47), on el nivell ja és pla i el gra baixa un 2 %. Corona; preservar.'),
6: ('Només la taca NE', 'Un sol traç, el cercle de la taca NE (7,5–8,2 R☉). Vegeu la família G del 147: clot de 2σ només a la Sony B.'),
7: ('Contorns transversals: corona + graons de gra', 'Deu liles a 1,30–1,94 R☉, un d\'ells cercle sencer (1,73–1,88). Correlació creuada +0,5…+0,8 (nuls −0,1…+0,2): els traços ressegueixen la vora de la zona d\'estructura fina de la corona interior (vista polar). El filtre 1–16 px hi afegeix els graons de gra de 1,21/1,33/1,96 R☉.'),
8: ('Arcs a 4,2–4,6 i cercle 3,9–4,6: vora del S/N; taca NE', 'A σ24 cap font té estructura a 3,9–4,6 (correlació +0,01 = nul); a la base V31 hi havia anells i a la V32 no (polar). El traç ressegueix on els streamers deixen de veure\'s. El lila de 1,47–1,56 és corona (+0,82). La taca NE és la família G.'),
9: ('Arcs a 3,6–4,7: vora del S/N; taca NE', 'Mateixa lectura que la capa 05 a l\'escala 4–64 px: correlacions +0,01/+0,01/+0,01 als tres traços intermedis. Taca NE: família G.'),
10: ('Sense marques', 'Byte a byte idèntica a V32.psb (0 px diferents).'),
11: ('Sense marques', 'Byte a byte idèntica a V32.psb.'),
12: ('Cercles a la vora del llenç; limbe', 'Cercles sencers a 8,44–8,68 i 11,56–12,04 R☉ i arcs parcials al primer radi: on els anells toquen les vores del llenç (8,47 inferior, 8,57 superior, 11,78 dreta). Dos traços al limbe (1,03–1,07) on entren els fotogrames d\'1/30–1/8 s.'),
13: ('Zona taronja (color nou), cercle a la vora del llenç', 'La taca taronja (N, 4,3–9,3 R☉) marca on la RHEF surt clara: rang mitjà 0,77–0,80, idèntic a la V31; Vixen i Sony B coincideixen a ±0,2 % i el compost no hi usa l\'apuntament A: la RHEF ordena el gradient del cel. El cercle a 8,41–8,62 i els tres arcs al mateix radi són la vora del llenç.'),
14: ('Contorns interiors (corona), graó dels 10 s, limbe', 'Nou liles: 1,56–1,89 R☉ corona (+0,58…+0,81, nuls ≤ +0,21); 1,98–2,18 (cercle sencer) a l\'entrada dels 10 s de la Vixen, on el gra fi baixa un 18–23 % (A8) i el MGN ho dibuixa; limbe 1,03–1,08 (×2) i 1,12–1,37 (entrades dels 0,5 s i 1 s).'),
15: ('Contorns interiors (corona), rampa, limbe', 'Catorze liles: interiors 1,57–1,89 corona (+0,44…+0,79); cercles a 2,00–2,10 i 2,13–2,23 sobre el graó de gra dels 10 s i l\'inici de la rampa Vixen→Sony; 2,29–2,57 a la rampa (+0,46); 1,28–1,35 a l\'entrada de l\'1 s; limbe 1,12–1,32.'),
16: ('Rampa Vixen→Sony (gra de la Sony), limbe, interiors', 'Vint-i-un liles: a 2,26–2,72 (×3) i 2,23–2,51 els dos trens no comparteixen el que el traç ressegueix (+0,20/+0,24/+0,74/+0,49, nuls −0,17/−0,01/+0,07/+0,14): gra de la Sony a la rampa. Nou traços al limbe (1,03–1,33), on el test no discrimina. Els interiors (1,30–2,03) són corona (+0,66…+0,96).'),
17: ('Sense marques', 'NAFE: cap traç.'), 18: ('Sense marques', 'Precursor ACHF σ16: cap traç.'), 19: ('Sense marques', 'Precursor ACHF σ32: cap traç.'), 20: ('Sense marques', 'SWAP: cap traç.'), 21: ('Sense marques', 'Control passa-alt lineal: cap traç.')}


def main():
    inv = json.loads(Path(RUN.rebut('marks_inventory.json')).read_text()); cat = json.loads(Path(RUN.rebut('review_catalog.json')).read_text())
    a2 = {m['id']: m for m in json.loads(Path(RUN.rebut('R32_marques.json')).read_text())['marques']}
    a7 = {m['id']: m for m in json.loads(Path(RUN.rebut('R32_A7_correlacio_creuada.json')).read_text())['marks']}
    V = Path(RUN.vista('')); rel = lambda p: f'<{p}>'
    L = ['# Revisió del PSB anotat de la V32, capa a capa', '', f"07-09-2026. **22 capes revisades. `V32_Filtres_Artefactes.psb` i `V32.psb` intactes.** {len(cat['marks'])} components de pinzell: {cat['totals_by_color']['lila']} liles, {cat['totals_by_color']['verd']} verds, {cat['totals_by_color']['taronja']} taronja; 65 solapen marques de la V31, 13 són nous; 64 de les 137 de la V31 no tenen contrapart. Explicació i mesures: `research/147_REVISIO_MARQUES_V32_20260907.md`.", '',
         f"![Totes les capes]({rel(V / '00_totes_les_capes_anotades.png')})", '', f"[Mapa de marques sobre la base]({rel(V / '00_mapa_marques_sobre_base.png')}) · [Histograma de radis]({rel(V / '00_histograma_radis_per_color.png')}) · [Polar interior 1]({rel(V / 'R32_A6_zoom_interior_1.png')}) · [Polar interior 2]({rel(V / 'R32_A6_zoom_interior_2.png')}) · [Polar intermedi 1]({rel(V / 'R32_A6_zoom_intermedi_1.png')}) · [Polar intermedi 2]({rel(V / 'R32_A6_zoom_intermedi_2.png')}) · [Gra per radi]({rel(V / 'R32_A8_gra_per_radi.png')}) · [Anells blaus Vixen]({rel(V / 'R32_A5_anells_blau_vixen.png')}) · [Taca NE]({rel(V / 'R32_A4_taca_NE_fonts.png')})", '', '## Capa a capa', '']
    for row in inv['layers']:
        i = row['index']; s, t = NOTES[i]; L.append(f"### {i:02d} · {row['name']}"); L.append(''); L.append(f'**{s}.** {t}'); L.append('')
        links = [f"[Marcat sencer]({rel(V / f'L{i:02d}_anotada_sencera.png')})", f"[Original sencer]({rel(V / f'L{i:02d}_original_sencera.png')})"] + [f"[Comparació {k}]({rel(p)})" for k, p in enumerate(sorted(V.glob(f'L{i:02d}_comparacio_*.png')), 1)]
        cc = ' · '.join(f'{v} {k}' for k, v in row['color_counts'].items() if v) or 'Sense marques'; L.append(cc + '. ' + ' · '.join(links)); L.append('')
    L += ['## Totes les marques', '', '| ID | capa | color | família | r p05–p95 | fotogrames que canvien al tram (A2) | Vixen×SonyB | nul | SonyA×SonyB | vistes |', '|---|---|---|---|---|---|---|---|---|---|']
    f = lambda v: '–' if v is None else f'{v:+.2f}'
    for m in cat['marks']:
        r = m['paint_radius_R_p05_p50_p95']; a = a2.get(m['id']); c = a7.get(m['id'], {})
        tr = ''
        if a:
            for tag, d in a['trens'].items():
                if d['transicions']:
                    tr += tag + ': ' + ', '.join(f"{z['exp']:g}s@{z['r_transicio_R']:.2f}" for z in d['transicions'][:3]) + ' '
        vis = f"[perfils]({rel(V / f'R32_{m['id']}_perfils.png')})" if (V / f"R32_{m['id']}_perfils.png").exists() else ''
        L.append(f"| {m['id']} | {m['layer'][:22]} | {m['color']} | {m['family'][:38]} | {r[0]:.2f}–{r[2]:.2f} | {tr or '—'} | {f(c.get('r_Vixen_SonyB'))} | {f(c.get('nul_Vixen_SonyB180'))} | {f(c.get('r_SonyA_SonyB'))} | {vis} |")
    Path(RUN.lliurable('RESULTAT.md')).write_text('\n'.join(L) + '\n'); print('RESULTAT.md', len(L), 'línies')


if __name__ == '__main__':
    main()
