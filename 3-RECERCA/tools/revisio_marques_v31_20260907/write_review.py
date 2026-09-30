"""Publish a layer-by-layer review and complete brush-component catalogue."""
from extract import *
import csv,html

NOTES={
0:('Base sense marques','Corona de color i gradient ampli. No s’ha detectat pintura: el groc natural de la base s’ha exclòs de la segmentació de pinzell després de revisar la vista. La base no rep un certificat general d’absència d’artefactes.'),
1:('Costura diagonal NW','La franja groga es veu sense pintura, paral·lela al marge NW però dins de la cobertura. El granulat exterior és fort i direccional. El nom V29 no converteix aquesta capa en un control independent.'),
2:('Costura diagonal NW','La mateixa franja diagonal persisteix a la variant V30. La suavització de l’operador no elimina aquesta discontinuïtat comuna.'),
3:('Costura diagonal NW','La variant azimutal r8 conserva la franja marcada; dos components de pinzell són fragments del mateix problema de marge. No són dos defectes independents.'),
4:('Costura diagonal NW','La capa ACHF fi 2–32 només té anotada la diagonal. S’hi observa textura fina exterior; l’absència d’altres marques no és un PASS dels miniarcs.'),
5:('Costura i arcs intermedis','Sis segments liles assenyalen contorns transversals entre aproximadament 3,3 i 4,5 radis solars. La textura tangencial es veu a l’original; el traç no identifica cada cresta individual. Se separen de la diagonal groga.'),
6:('Costura i contorns interiors','Quatre marques liles a aproximadament 1,3–1,8 radis travessen filaments de la corona interior. No corresponen al mateix domini que els arcs exteriors de la capa 02. També hi ha dos fragments de pintura groga de la diagonal.'),
7:('Costura, arcs i taca NE','Contorns liles a uns 3,2–4,2 radis i una taca encerclada en blau al NE, prop de (8375,2090), a uns 7,8 radis. La taca és una anomalia local: aquesta vista no prova que sigui un ghost.'),
8:('Costura, arcs i taca NE','Repeteix els contorns intermedis i la taca NE de la capa 05, ara encerclada en lila. La coincidència entre filtres de la mateixa font localitza el problema, però no identifica la seva causa.'),
9:('Contorns amplis, interiors i una recta','NRGF mostra la diagonal NW, contorns liles exteriors d’uns 8–11 radis, arcs blaus interiors/intermedis i una recta obliqua al sud (L09-M25). Els canvis amplis de nivell no sempre defineixen una vora nítida. La recta es cataloga separadament dels arcs.'),
10:('Contorns exteriors i ratlles interiors','RHEF té la diagonal, contorns liles exteriors i una taca encerclada NE. Les marques blaves prop del limbe assenyalen feixos de ratlles gairebé paral·leles i anomalies locals. El mecanisme de bandes del RHEF està documentat en un control nul anterior; no atribueix automàticament totes aquestes marques al mateix mecanisme.'),
11:('Contorns interiors successius','MGN presenta molts contorns liles interiors transversals als filaments, alguns amb colzes o trams aplanats, i dos segments blaus més exteriors. No es descriuen com a cercles perfectes. El granulat fort limita la lectura dels més febles.'),
12:('Arcs blaus; verds dubtosos','WOW mostra perímetres blaus fragmentats a la corona intermèdia/exterior i dos segments laterals interiors. Les vuit components verdes envolten estructura corbada interior. Hi ha estructura local compartida entre Vixen i Sony, però cada ondulació verda continua indeterminada; poden coexistir senyal real i resposta del filtre.'),
13:('Arc ample i contorns amb colzes','WOW bilateral té dos grans traços liles i contorns blaus interiors amb colzes, segments quasi rectes i transicions transversals. Canviar els pesos bilaterals modifica la resposta, però no estableix quin contorn és físic.'),
14:('Costura i anomalies del limbe','NAFE té la diagonal NW i quatre marques blaves molt pròximes al limbe, aproximadament 1,04–1,11 radis, sobre transicions clares/fosques estretes. No hi ha anotació extensa de cercles exteriors; això no el valida globalment.'),
15:('Sense pintura; halo i poca lectura exterior','El precursor ACHF sigma16 concentra la resposta al limbe: vora clara i halo fosc adjacent. L’exterior gairebé blanc mostra poc detall amb aquesta escala de visualització. No pot funcionar com a prova visual d’absència d’arcs.'),
16:('Sense pintura; halo més ample','El precursor ACHF sigma32 mostra una resposta clara/fosca més ampla al limbe i exterior gairebé gris uniforme. Cal distingir la sortida del filtre de la seva escala de pantalla; no hi ha PASS d’absència d’artefactes.'),
17:('Sense pintura; exterior poc visible','SWAP concentra la corona visible a l’interior i deixa l’exterior gairebé negre. No es distingeix un patró concèntric prominent, però la poca visibilitat exterior limita aquesta observació.'),
18:('Sense pintura; resposta del passa-alt','El control lineal passa-alt24 mostra vora clara i halo fosc adjacent, amb exterior força uniforme. L’escala global de pantalla no el converteix en un control negatiu concloent dels arcs d’altres capes.')}

def family(i,m):
    if m['color']=='groc':return 'Costura diagonal interna NW'
    if m['color']=='verd':return 'Contorn interior dubtós; preservar'
    if i in [7,8,10] and m['bbox'][0]>8000 and m['bbox'][1]<2600:return 'Anomalia local NE'
    if m['id']=='L09-M25':return 'Traç recte oblic al sud'
    if i==10 and m['color']=='blau':return 'Ratlles o irregularitat propera al limbe'
    if i==14:return 'Transició estreta al limbe'
    r=m['paint_radius_R_p05_p50_p95'][1]
    return 'Contorn ample exterior' if r>6 else ('Contorn transversal interior' if r<2.5 else 'Arc o contorn intermedi')

rep=json.loads(Path(RUN.rebut('marks_inventory.json')).read_text())
catalog=[]
for l in rep['layers']:
    for m in l['marks']:
        catalog.append(dict(m,layer_index=l['index'],layer=l['name'],family=family(l['index'],m),
            review_status='DUBTOS; no eliminar' if m['color']=='verd' else 'ARTEFACTE CONFIRMAT PER PERE; causa específica pendent',
            correction_applied=False))
write(RUN.rebut('review_catalog.json'),{'layers':[dict(index=i,name=rep['layers'][i]['name'],summary=NOTES[i][0],review=NOTES[i][1]) for i in range(19)],
    'marks':catalog,'scope':'19 annotated document layers; brush components are indexing units, not distinct defects; all causes qualified separately from Pere labels'})
with Path(RUN.lliurable('CATALEG_MARQUES.csv')).open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['ID','capa','color','criteri_Pere','familia','bbox_xyxy','r_p05','r_mediana','r_p95','veredicte'])
    for m in catalog:w.writerow([m['id'],m['layer'],m['color'],m['certainty_by_Pere'],m['family'],m['bbox'],*m['paint_radius_R_p05_p50_p95'],m['review_status']])

intro='''# Revisió del PSB anotat, capa a capa

07-09-2026. **19 capes revisades. El PSB de Pere i la V31 original es conserven intactes.**

El document anotat conté 137 components de pinzell: 16 grocs, 56 blaus, 57 liles i 8 verds. Són segments d’anotació, no 137 defectes independents. Diversos traços encerclen la mateixa estructura o se superposen. Groc, blau i lila conserven l’estat d’artefacte confirmat per Pere; els verds continuen dubtosos.

Les marques separen almenys cinc problemes: **costura diagonal interna, contorns amplis exteriors, arcs transversals interiors/intermedis, anomalies estretes del limbe i una taca local NE**. No es justifica tractar-los tots com un únic «disc de gramòfon».

La diagonal groga es repeteix en 14 capes i és dins de la dada vàlida: la mediana de distància a la vora física és de 383–454 px segons el traç. És una costura interna o una franja paral·lela al marge, no el simple final de la cobertura. Encara no s’atribueix a un fotograma, pes o operador concret.

**Els verds de WOW no s’han de donar per artefactes.** En vuit finestres locals amb suport comú, Vixen i Sony comparteixen estructura; les correlacions descriptives són 0,47–0,86 a les escales fines provades i 0,47–0,98 a les més amples. Això no verifica cada ondulació, ni exclou un halo del filtre superposat. Una novena finestra tenia suport incomplet i no s’ha omplert ni puntuat. Les vuit marques verdes es mantenen dubtoses.

Les marques noves també precisen l’observació anterior sobre la corona interior: ACHF micro, NRGF, MGN, WOW bilateral i NAFE tenen contorns assenyalats per sota de 2 radis del centre. Per tant, l’absència de cercles a l’interior no es pot generalitzar a tots els filtres ni a totes les famílies de marques.

![Totes les capes, amb les marques originals](</Users/USUARI/Downloads/Eclipse 2026/output/revisio_marques_v31_20260907/lliurables/vistes/00_totes_les_capes_anotades.png>)

## Revisió individual

Els enllaços de cada capa mostren el llenç sencer i parelles de la zona pintada amb l’original sense pintura. La comparació és de la mateixa capa: no s’ha reconstruït allò que amaga el pinzell.

'''
body=[]
for l in rep['layers']:
    i=l['index'];base=Path(RUN.vista(''))
    links=[f'[Marcat sencer](<{base/f"L{i:02d}_anotada_sencera.png"}>)',f'[Original sencer](<{base/f"L{i:02d}_original_sencera.png"}>)']
    for k,p in enumerate(sorted(base.glob(f'L{i:02d}_comparacio_*.png')),1):links.append(f'[Comparació {k}](<{p}>)')
    counts=' · '.join(f'{v} {c}' for c,v in l['color_counts'].items() if v) or 'Sense marques'
    body.append(f"### {i:02d} · {l['name']}\n\n**{NOTES[i][0]}.** {NOTES[i][1]}\n\n{counts}. "+' · '.join(links)+'\n')
method='''
## Abast i límits de la revisió

El document anotat té 19 capes RGB16 de 10551×7506, en mode Normal al 100%; l’original té 40 capes. S’han aparellat les 19 per nom exacte amb l’original. A les finestres de les marques, els píxels observats sense pintura coincideixen almenys en un 99,989% dins de 2 nivells de gris de 8 bits; la diferència absoluta mediana és zero. És una comprovació de correspondència visual, no una nova mesura fotomètrica del RAW ni una prova d’identitat de tot el document.

S’han revisat les vistes completes de totes les capes i els fulls de comparació. La segmentació identifica pintura semitransparent per color: els colors naturals de la base no són marques. Les components es mantenen com a unitats d’índex; quan dos colors es toquen, el catàleg conserva la composició cromàtica i usa el color dominant. Els radis són percentils dels píxels del traç, no el radi d’un cercle ajustat ni el radi del centroide d’un arc. Els rectangles dels retalls són només finestres de diagnosi; no esdevenen màscares de correcció.

La prova de les verdes usa G original separat per tren, logaritme, diferències gaussianes cartesianes amb suport normalitzat i detrend quadràtic idèntic. Són escales de diagnosi, no bandes Fourier ni una porta de preservació. El control gira la mateixa finestra Sony 180° sobre ella mateixa, no una altra posició al voltant del Sol; no és una significança calibrada. La coincidència entre filtres purs tampoc és un jutge independent perquè comparteixen base. Brno no s’ha emprat per validar individualment aquestes marques.

Les capes pures no hereten H1, rho40, contrast120 ni el sigma3 dels antics 01/02. Comparteixen la base G corregida, guany global Sony→Vixen i blend 2–2,65 R. Aquesta diferència impedeix aplicar indiscriminadament el diagnòstic dels filtres antics als nous.

No s’ha aplicat cap correcció, retall circular, inpainting o suavitzat al producte. Les capes sense pintura tampoc reben un PASS: una escala de pantalla amb exterior gairebé uniforme pot amagar-hi defectes i senyal alhora. La comprovació física de cada causa i la validació d’una correcció són feina posterior.

Revisió independent: Halley, deu filtres purs i mètodes; Raman, marques verdes i fonts separades. Lectura només. Codi, còpia congelada del PSB, píxels de comparació i rebuts a `research/tools/revisio_marques_v31_20260907`; manifest final a `output/revisio_marques_v31_20260907/4-rebuts/manifest.json`.
'''
text=intro+'\n'.join(body)+method
Path(RUN.lliurable('RESULTAT.md')).write_text(text)
(ROOT/'research/145_REVISIO_MARQUES_V31_20260907.md').write_text(text)
print('REVIEW',len(catalog),'components, 19 layers',flush=True)
