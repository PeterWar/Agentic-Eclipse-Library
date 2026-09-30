"""A self-contained Catalan study. Run with bundled Python (ReportLab installed)."""
from pathlib import Path
import json,csv,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT

R=Path(__file__).resolve().parents[3];O=R/'output/relativitat_revisio_20260914';F=O/'figures'
font=Path('/Users/USUARI/.venvs/eines-ia-py312/lib/python3.12/site-packages/matplotlib/mpl-data/fonts/ttf')
for name,file in [('Deja','DejaVuSans.ttf'),('DejaB','DejaVuSans-Bold.ttf'),('DejaI','DejaVuSans-Oblique.ttf')]:pdfmetrics.registerFont(TTFont(name,str(font/file)))
pdfmetrics.registerFontFamily('Deja',normal='Deja',bold='DejaB',italic='DejaI',boldItalic='DejaB')
NAVY=colors.HexColor('#182e48');TEAL=colors.HexColor('#087f83');GREY=colors.HexColor('#536171');LIGHT=colors.HexColor('#edf4f4')
styles={
 'title':ParagraphStyle('title',fontName='DejaB',fontSize=26,leading=32,textColor=NAVY,spaceAfter=15),
 'h':ParagraphStyle('h',fontName='DejaB',fontSize=18,leading=23,textColor=NAVY,spaceAfter=13),
 'sub':ParagraphStyle('sub',fontName='DejaB',fontSize=11.3,leading=16,textColor=TEAL,spaceBefore=10,spaceAfter=6),
 'p':ParagraphStyle('p',fontName='Deja',fontSize=10.3,leading=15,spaceAfter=9,textColor=NAVY),
 'small':ParagraphStyle('small',fontName='Deja',fontSize=8.4,leading=12,spaceAfter=7,textColor=GREY),
 'cell':ParagraphStyle('cell',fontName='Deja',fontSize=9,leading=12,textColor=NAVY),
 'head':ParagraphStyle('head',fontName='DejaB',fontSize=9,leading=12,textColor=colors.white),
}
story=[];md=[]
def P(s,style='p'):
    story.append(Paragraph(s,styles[style]));md.append(s.replace('<b>','**').replace('</b>','**').replace('<br/>','\n'))
def H(s):P(s,'h');md[-1]='## '+md[-1]
def SUB(s):P(s,'sub');md[-1]='### '+md[-1]
def T(headers,rows,widths):
    allrows=[[Paragraph(str(x),styles['head']) for x in headers]]+[[Paragraph(str(x),styles['cell']) for x in row] for row in rows]
    t=Table(allrows,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#ccdada'))]));story.extend([t,Spacer(1,9)])
    md.extend(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in rows])
def FIG(name,height,caption):
    from reportlab.lib.utils import ImageReader
    p=F/(name+'.png');w,h=ImageReader(str(p)).getSize();story.append(Image(str(p),width=height*w/h,height=height));P(caption,'small');md.append('!['+caption+']('+str(p)+')')
def PAGE():story.append(PageBreak());md.append('\n---\n')
def REF(n,url,label):return f'<link href="{url}" color="#087f83">[{n}] {label}</link>'

def content():
 P('Posar a prova<br/>la relativitat general','title')
 P('Estudi V2 · Eclipsi del 12 d’agost de 2026 i preparació del 2 d’agost de 2027','sub')
 P('Revisió del 14 de setembre de 2026 · Dades natives incorporades fins a la V65','small')
 P('<b>Les noves estrelles milloren la base de treball, però encara no tenim una mesura fiable de la deflexió gravitacional amb les dades del 2026.</b> Aquesta versió reprodueix l’estudi anterior, recalcula la sensibilitat i prova el model amb les posicions natives dels RAW. El resultat principal és identificar què falta perquè la prova sigui convincent.')
 T(['Què podem afirmar','Resultat de la revisió'],[
 ['Fotografia V65','60 fonts representades, 62 identificadors i dos parells no resolts. La PSF gaussiana final és una representació fotogràfica.'],
 ['Mostra per a aquesta anàlisi','51 estrelles amb centre refinat i SNR ≥ 5 en almenys dos RAW d’un tren; 23 amb SNR ≥ 10. S’usa tot el camp natiu, també fora del PSB.'],
 ['Sensibilitat simplificada 2026','σ(ε): 0,529 a l’estudi antic; 0,489 a la nova selecció de llindar 5. Amb termes radials de placa: 0,845 en tots dos casos. Són previsions condicionals.'],
 ['Mesura de relativitat','No qualificada. El coeficient ajustat és massa sensible al model de distorsió, al color i a la selecció de fonts.'],
 ['Objectiu 2027','Distingir GR de mitja deflexió a 5σ exigeix σ(ε) ≤ 0,10, inclosos els sistemàtics. Cal demostrar-ho en assaigs, no donar-ho per fet.']
 ],[145,354])
 SUB('La decisió que proposa l’estudi')
 P('Conservar el 2026 com a banc de proves real per a l’extracció de centres, la distorsió i els controls nuls. Preparar el 2027 com un experiment de calibratge: el nombre d’estrelles i el temps de totalitat ajuden, però no substitueixen una escala de placa estable i independent.')
 P('Abast: anàlisi i planificació. Els RAW, els catàlegs originals, les versions Photoshop i l’alineament manual de Pere s’han mantingut intactes. No s’ha creat una nova mesura física a partir de píxels reconstruïts.','small')
 PAGE()

 H('1. Quina quantitat volem mesurar')
 P('La gravetat solar desplaça la posició aparent d’una estrella cap enfora del Sol. A distàncies angulars petites, la predicció és <b>α ≈ ε · 1,75119″ / r</b>, amb r en radis solars. En la parametrizació PPN, ε = (1 + γ) / 2: GR correspon a ε = 1; la predicció històrica de mitja deflexió, a ε = 0,5; absència de deflexió solar, a ε = 0.')
 P('S’han emprat GM solar nominal = 1,3271244 × 10²⁰ m³/s² i radi solar nominal = 695.700 km. Són constants de conversió IAU; aquesta elecció fixa la normalització i no mesura el radi físic de la fotosfera. El radi angular al nostre eclipsi és aproximadament 946,660″. [1]')
 FIG('02_field2026',240,'Camp natiu 2026: 51 identificadors únics, no 51 mesures independents. Els cercles indiquen distància al Sol; no mostren un desplaçament observat de relativitat.')
 SUB('La correcció indispensable al catàleg')
 P('El codi antic calculava <b>apparent()</b>, que ja inclou la deflexió solar. Ara es construeixen dues prediccions: amb el Sol i sense el Sol com a deflector. Es conserven l’aberració, el moviment propi, el temps de propagació i les altres masses. La diferència entre les dues prediccions és la plantilla que multiplica ε. La documentació de Skyfield confirma aquesta separació. [2]')
 P('La reproducció del catàleg antic coincideix a menys de 10⁻¹¹″. La plantilla nova concorda amb la fórmula de l’angle finit al pla tangent fins a 9,2 × 10⁻⁶ en valor relatiu. Són comprovacions del càlcul, no de la precisió de les observacions. La fórmula 1/r sola diferia un 0,62% a 4° per l’efecte de la projecció gnomònica; aquesta diferència s’ha conservat al rebut.','small')
 PAGE()

 H('2. Què aporten realment les estrelles noves')
 P('La V65 aporta extraccions de 15 RAW: set Sony i vuit Vixen, amb 62,9 s d’exposició sumada entre trens. Aquesta suma no és una única exposició ni 62,9 s de dades astromètriques independents. Es treballa amb els dos verds del CFA natiu, abans d’interpolar, i amb el centre de cada fotograma.')
 T(['Selecció','Sony','Vixen','Úniques entre trens'],[
 ['Antiga identificada','38','22','No se sumen com a úniques'],
 ['Centre lliure; SNR ≥ 5 en ≥ 2 RAW','43','22','51'],
 ['Centre lliure; SNR ≥ 10 en ≥ 2 RAW','21','10','23']],[244,65,65,125])
 P('S’exclouen els dos sistemes dobles coneguts. També s’exclou qualsevol centre que el procés fotogràfic havia mantingut a la posició prevista per manca de senyal. La cerca V65 estava guiada pel catàleg: superar el llindar no la converteix retroactivament en una detecció cega. Els llindars 5 i 10 són proves de sensibilitat, no garanties d’absència de biaix.')
 FIG('01_forecast',225,'Comparació sota els mateixos errors per posició adoptats a l’estudi antic. Els recomptes sumen estrella-tren: hi ha estrelles comunes. No s’han combinat aquests errors com si fossin independents de catàleg, atmosfera i calibratge en una mesura final.')
 P('<b>El guany és modest.</b> La mostra de llindar 5 dona 2,05σ de sensibilitat ideal per GR contra zero i 1,02σ per GR contra mitja deflexió. Amb distorsió radial lliure baixa a 1,18σ i 0,59σ. Res d’això és significació observada. El llindar 10 dona menys estrelles i pitjor previsió geomètrica amb aquest error uniforme; no demostra que les dades hagin empitjorat.')
 P('HIP 46335 és la novetat més interessant prop del Sol: senyal màxim verd de 6,21 a Sony i 8,95 a Vixen; passa el llindar 5, però no el 10. HIP 46345 continua sent una referència més robusta. La precisió de les fonts properes pesa més que afegir moltes fonts febles allunyades.','small')
 PAGE()

 H('3. Què passa quan ajustem els RAW')
 P('S’ha fet una prova exploratòria amb la selecció de SNR ≥ 10, una placa lliure per fotograma i ε compartit. Per poder ajustar cada placa amb graus de llibertat suficients, entren sis RAW Sony i tres Vixen: <b>107 posicions de 23 estrelles</b>. Es presenten els models declarats abans dels ajustos, inclosos els que donen resultats manifestament inadequats.')
 T(['Model de placa','Sony: ε','Vixen: ε','Combinat: ε'],[
 ['Afí (6 paràmetres / RAW)','−45,50','−4,74','−30,97'],
 ['Afí + cúbics radials (10 / RAW)','1,44','2,78','1,75'],
 ['Quadràtic (12 / RAW)','−45,93','−2,16','−35,00']],[254,80,80,85])
 P('<b>Aquests números són diagnòstics del model, no mesures de relativitat.</b> Un coeficient proper a 1 en una variant no valida la prova. La placa afí no descriu prou bé la distorsió; els termes addicionals canvien fortament el senyal atribuït a ε. El model quadràtic requereix més estrelles per RAW i usa 100 posicions de vuit fotogrames: no és una comparació d’ajustos amb mostres perfectament idèntiques.')
 T(['Control del model radial','Resultat'],[
 ['Incertesa calculada des dels residus','σ(ε) = 2,53; amb agrupació de l’error per estrella, 1,53. Cap de les dues inclou tot el pressupost sistemàtic.'],
 ['Treure una estrella cada vegada','El combinat passa d’1,12 a 4,15. La font més influent és HIP 46345 / TYC 826-899-1.'],
 ['Canviar el llindar 10 → 5','ε combinat: 1,75 → 2,91. La mostra feble no és intercanviable amb la robusta.'],
 ['Afegir dependència empírica del color','ε combinat: 1,75 → 3,14. No és una calibració cromàtica, sinó una prova de fragilitat.'],
 ['Meitats de fotogrames, llindar 10','Sony: 1,99 / −0,08. Vixen: 2,15 / 4,07. Mostres petites i catàleg compartit.'],
 ['Injeccions ε = 0; 0,5; 1','Recuperades amb error < 10⁻⁸ a nivell de coordenades. Validen l’àlgebra, no els RAW ni la PSF.']],[250,249])
 P('S’han conservat també els ajustos ponderats per l’error ideal de la PSF i els controls tangencials. El model radial combinat dona una amplitud tangencial de 6,15 en unitats de la plantilla rotada: tampoc ofereix un control nul net. Tots els resultats són als JSON, sense seleccionar només els favorables.','small')
 PAGE()

 H('4. El pressupost d’error encara obert')
 P('La deflexió d’una estrella a tres radis solars és d’uns 0,58″: aproximadament 0,18 píxels Sony o 0,27 píxels Vixen. La precisió del centre pot ser millor que un píxel, però només si es controlen els efectes que el desplacen sistemàticament.')
 T(['Font d’error','Què sabem ara','Què falta validar'],[
 ['PSF i moviment','La V65 mesura perfils natius diferents segons el RAW. La PSF final σ = 1,5 píxels del PSB és escollida.','Modelar el traç i la resposta del píxel en els RAW; comparar centres amb una PSF alternativa i dades reservades.'],
 ['Fonts febles','Els centres lliures només s’ajustaven a SNR ≥ 5, dins una finestra acotada.','Injeccions cegues des dels RAW amb catàleg i selecció independents; quantificar l’atracció cap a la llavor.'],
 ['Catàleg','Tycho-2/Hipparcos i moviment propi reproduïts. El catàleg antic utilitzat no aporta paral·laxi completa ni covariàncies.','Nova solució de referència amb Gaia, propagació a l’època, paral·laxi, covariàncies i revisió de binàries. [3]'],
 ['Atmosfera i color','El Sol era a 9,07°. T = 20 °C i P = 930 mbar són hipòtesis. T = 10 °C canvia ε radial en +0,094.','Mesures meteorològiques i banda efectiva; refracció diferencial i cromàtica amb controls.'],
 ['Temps i registre','S’usen centres per RAW, sense la transformació fotogràfica final. +15 s canvia ε radial en +0,043.','Certificar el rellotge i el centre temporal d’exposició; quantificar la resposta variable durant una presa.'],
 ['Distorsió i escala','El model radial antic té quatre termes empírics de grau 3 en eixos del camp solar.','Calibrar la distorsió en coordenades del detector i la seva estabilitat. No imposar escala fixa perquè doni ε = 1.']],[94,199,206])
 SUB('Què no arreglen l’earthshine i el revelat')
 P('La correcció del limbe, les perles i la corona millora la fotografia i ajuda a entendre el fons. No aporta una referència estel·lar externa, ni redueix automàticament l’error de placa. Tampoc la supressió d’estrelles dels filtres ni el seu dibuix gaussià es poden emprar com a dades independents de relativitat.')
 P('Les injeccions natives V65 ja mostraven el límit: centres simulats a SNR 30 tenien error radial p95 de 0,126 píxels amb la PSF correcta. El desacord deliberat de PSF produïa errors de flux > 10% en 33 de 168 proves. Són controls condicionals de l’extracció, no una certificació astromètrica absoluta.','small')
 PAGE()

 H('5. El 2027 té una geometria més favorable')
 T(['Lloc i data','Altura solar','Massa d’aire aprox.','Totalitat orientativa'],[
 ['Lleó, 12-08-2026','9,07°','6,11','103,7 s al contracte històric'],
 ['Cadis, 02-08-2027','37,44°','1,64','Uns 3 minuts'],
 ['Luxor, 02-08-2027','81,77°','1,01','Uns 6 min 20 s']],[185,88,101,125])
 P('Altures i camps recalculats amb DE440s i les coordenades declarades. La durada es dona arrodonida: el model de discs esfèrics retorna 106,6 / 178,8 / 384,9 s, diferents dels contactes del contracte 2026 i de la convenció NASA. No incorpora el relleu lunar ni serveix per programar els contactes. NASA situa el màxim global del 2027 al voltant de 6 min 23 s. [4]','small')
 FIG('03_field2027',239,'Camp real Hipparcos V ≤ 8 a Luxor. Marcs centrats al Sol, orientats est-nord i amb les escales natives del 2026. Les estrelles del mapa són prediccions de catàleg, no promeses de detecció durant l’eclipsi.')
 T(['Estrella','V','Distància al Sol','Deflexió prevista'],[
 ['HIP 43206','7,22','1,80 R☉','0,975″'],
 ['HIP 43079','7,87','1,89 R☉','0,927″'],
 ['HIP 43044','8,26','1,95 R☉','0,896″'],
 ['δ Cancri / HIP 42911','3,94','3,11 R☉','0,564″']],[222,60,108,109])
 P('Les fonts més properes reben més deflexió, però també tenen més corona de fons. Cal confirmar el senyal i evitar saturar δ Cancri. El Sol alt redueix el problema atmosfèric geomètric; la turbulència, els núvols, el fons i l’estabilitat tèrmica no queden garantits.','small')
 PAGE()

 H('6. Un objectiu quantitatiu per al 2027')
 P('La nova previsió utilitza les posicions reals d’un subconjunt Hipparcos, sense repartir aleatòriament estrelles per l’anell. Al camp est-nord hi ha <b>41 fonts Sony i 12 Vixen amb V ≤ 8</b>. S’assumeix que totes es poden mesurar amb el mateix error independent final: és una condició exigent, sobretot prop de la corona.')
 FIG('04_scenarios2027',215,'Previsió condicional amb placa afí + cúbics radials lliures. L’error horitzontal és el del centre final d’una estrella, després de combinar exposicions; no és l’amplada de la PSF. Els sistemàtics compartits no disminueixen com 1/√N.')
 T(['Error per estrella','Sony: σ(ε)','Vixen: σ(ε)'],[
 ['0,030″ = 30 mas','2,13%','3,57%'],
 ['0,050″ = 50 mas','3,55%','5,94%'],
 ['0,100″ = 100 mas','7,09%','11,88%'],
 ['0,200″ = 200 mas','14,19%','23,77%']],[237,131,131])
 P('Aquesta taula no tria el millor instrument ni prediu el temps d’exposició necessari. Imposa el mateix error a estrelles de magnituds i fons diferents, i el camp pot canviar amb l’orientació. Hipparcos no és un catàleg complet de les fonts febles; els escenaris V ≤ 9 s’inclouen als CSV com a subconjunt, no com a cens total.')
 SUB('Condicions perquè tingui sentit anunciar una prova')
 P('<b>Objectiu principal:</b> σ(ε) total ≤ 0,10 i un biaix controlat, per separar ε = 1 de ε = 0,5 a 5σ si GR és correcta. <b>Objectiu millor:</b> σ(ε) ≤ 0,05. En termes de γ, les incerteses són el doble. Cap nivell de sigma s’ha de calcular només amb l’error formal d’un ajust que falla els controls.')
 P('En aquesta geometria, un error independent de 0,10″ ja deixa la Vixen prop del límit del 10% abans dels sistemàtics. La calibració externa de la placa podria millorar-ho, però la seva incertesa s’ha de propagar. El nombre total d’estrelles, per si sol, no resol el problema.','small')
 PAGE()

 H('7. Pla experimental que es pot posar a prova')
 P('L’objectiu dels assaigs previs és mesurar el pressupost d’error amb el tren real. No es proposa cap compra ni canvi físic automàtic. La missió fotogràfica de l’eclipsi continua protegida; un experiment addicional no ha de comprometre les captures principals.')
 T(['Fase','Feina i criteri de pas proposat'],[
 ['1 · Centres natius','Ajustar PSF integrada sobre cada píxel CFA, amb traç i fons local. Comparar dos models plausibles sobre fonts reservades. Perseguir estabilitat de centre de 0,05-0,10″ i mesurar-ne els biaixos.'],
 ['2 · Catàleg i geometria','Propagar posició, moviment propi, paral·laxi i covariància. Fixar l’època, la banda i el model sense Sol. Separar binàries i fonts problemàtiques sense mirar ε.'],
 ['3 · Placa independent','Camps de calibratge que cobreixin les mateixes zones del detector; repetir amb les temperatures i orientacions previstes. Determinar escala/distorsió i estabilitat sense ajustar-les per apropar-se a GR.'],
 ['4 · Prova nocturna nul·la','Reduir dues nits o sessions com si fossin eclipsi/control, amb les deflexions astronòmiques d’ambdues èpoques modelades. Objectiu de biaix proposat |Δε| < 0,03 i intervals que cobreixin zero. Una sola prova no demostra cobertura estadística.'],
 ['5 · Injeccions cegues','Injectar ε = 0; 0,5; 1 i amplituds intermèdies abans de la detecció. Variar PSF, color, traç, fons i fases de píxel; reservar estrelles i fotogrames. Verificar cobertura dels intervals i biaix, no només recuperació mitjana.'],
 ['6 · Congelar i executar','Congelar mostres, calibratge, llindars, models i controls abans de veure el resultat de l’eclipsi. Adquirir meteo i rellotge, evitar moviments manuals i validar tota la seqüència en sec.'],
 ['7 · Resultat científic','Publicar separadament sensors, meitats i variants declarades. Si falla un control essencial, publicar el límit i la causa; no escollir el model que dona ε més proper a 1.']],[99,400])
 SUB('Quina lliçó ens deixa Bruns')
 P('L’experiment del 2017 va obtenir un coeficient d’aproximadament 1,752″ amb incertesa del 3,4%. Va utilitzar camps de calibratge a banda i banda del Sol durant la totalitat per determinar la placa. Quan estimava escala i deflexió només amb les estrelles de l’eclipsi, el resultat canviava. La lliçó útil és la calibració independent; no és una garantia que el nostre material reprodueixi aquella precisió. [5]')
 P('Si es prepara una banda estreta o una càmera diferent, cal una validació pròpia de senyal, PSF i estabilitat. Les especificacions d’un fabricant no substitueixen aquest assaig.','small')
 PAGE()

 H('8. Què es rectifica respecte de l’estudi antic')
 T(['Afirmació o simplificació antiga','Tractament en aquesta versió'],[
 ['1,9σ podia semblar una detecció','Es reprodueix σ(ε) = 0,5289 com a previsió. El codi no resolia ε observat.'],
 ['38 + 24 fonts com una sola mostra','Dos candidats Vixen no tenien identificació de catàleg. Si es retiren, la previsió antiga és 0,5742, no 0,5289.'],
 ['Més estrelles = precisió proporcional','S’analitzen posicions mesurades, SNR, distància al Sol, degeneració i dependència entre observacions.'],
 ['PSF rodona = moviment recuperat','El render fotogràfic no prova que el centre original sigui insesgat ni que hi hagi més resolució.'],
 ['Èxit pràcticament garantit el 2027','Es retira. El 10% i el 5% són objectius condicionats a controls i pressupost d’error.'],
 ['Guany per magnitud mal expressat','En règim de fons dominant, una magnitud menys de flux redueix el SNR aproximadament ×2,512 a igual exposició; el pes estadístic baixa ×6,31.'],
 ['Models de població com a camp real','S’afegeix previsió amb coordenades Hipparcos reals. Els recomptes febles antics no s’han tornat a certificar.'],
 ['“No és ciència” si no millora el rècord','Una prova òptica independent pot ser un experiment científic útil i formatiu. No cal presentar-la com una mesura competitiva del límit actual de γ.']],[235,264])
 SUB('Resultat final de l’anàlisi')
 P('<b>No s’ha obtingut una detecció qualificada de deflexió el 2026.</b> Sí que s’ha millorat l’estudi: tenim una plantilla solar explícita, una mostra nativa auditada, la reproducció dels números antics, una prova directa de la fragilitat dels ajustos i escenaris 2027 basats en posicions reals.')
 P('La conclusió no és que el 2026 contingui zero informació ni que el 2027 sigui impossible. És que, amb els models i controls disponibles, no es pot atribuir de manera fiable el desplaçament residual a la relativitat. La prioritat tècnica és calibrar la placa i validar el centroide, especialment prop del Sol.')
 PAGE()

 H('9. Fonts, mètode i reproducció')
 P('El paquet conserva el protocol, els hashes d’entrada, les coordenades mesurades, totes les variants d’ajust, els controls i els gràfics. La versió anterior s’ha mantingut intacta. No hi ha una nova porta Photoshop perquè aquesta entrega és un estudi i no modifica cap PSB.')
 SUB('Fonts primàries consultades')
 refs=[
 (1,'https://iauarchive.eso.org/static/resolutions/IAU2015_English.pdf','IAU, resolució B3 (2015): constants solars nominals.'),
 (2,'https://rhodesmill.org/skyfield/api-position.html','Skyfield: Astrometric.apparent i l’argument deflectors.'),
 (3,'https://www.cosmos.esa.int/web/gaia/dr3','ESA Gaia DR3: contingut astromètric i època de referència.'),
 (4,'https://eclipse.gsfc.nasa.gov/SEgoogle/SEgoogle2001/SE2027Aug02Tgoogle.html','NASA / Fred Espenak: eclipsi total del 2 d’agost de 2027.'),
 (5,'https://arxiv.org/pdf/1802.00343','D. G. Bruns (2018), Gravitational Starlight Deflection Measurements during the 21 August 2017 Total Solar Eclipse.'),
 ]
 for n,url,label in refs:P(REF(n,url,label),'small')
 P('Consulta: 14-09-2026. Gaia DR3 s’esmenta com a referència disponible per a una futura reducció; no s’ha descarregat ni incorporat una nova solució Gaia en aquests resultats, ni s’afirma que sigui la darrera publicació. No es proclama un rècord actual de precisió d’eclipsis.','small')
 SUB('Evidència pròpia principal')
 T(['Fitxer del paquet','Contingut'],[
 ['A0_input_hashes.json + PROTOCOL.md','Fonts congelades i hipòtesis abans de l’ajust.'],
 ['A1_native_centroids.csv / A3_analysis_sample.csv','Centres S19, deduplicació, mostres i exclusions.'],
 ['A2_no_sun_and_GR.csv','Posicions sense Sol i plantilla de deflexió per RAW.'],
 ['A3_geometry_forecasts.csv / A3_diagnostic_fits.json','Reproducció antiga, previsions i tots els ajustos.'],
 ['A3_controls / A4_environment_sensitivity / A5_frame_halves','Jackknife, injeccions, color, temps, temperatura i meitats.'],
 ['A4_Hipparcos_2027_field.csv / A4_2027_conditional_scenarios.csv','Camp real i escenaris amb errors declarats.'],
 ['VERIFICACIO.json + MANIFEST.json','Validació numèrica, comprovació d’originals i integritat de l’entrega.']],[266,233])
 P('Arrel de càlcul: <b>research/tools/relativitat_revisio_20260914/</b>. Executar a1_inputs.py, a2_ephemeris.py, a3_inference.py, a4_controls_2027.py, a5_verify.py i b1_figures.py amb Python científic; b2_report.py amb Python de documents. RUNBOOK.md conté les ordres i les dependències exactes. La reconstrucció és local i conserva les fonts.')
 P('Antecedents: research/75 (mesures natives), research/77 (pla anterior), research/79 i research/97 (qualificacions de la deflexió), Work_2026-08-17 i rebuts V65 S19/S20/S25/S26. La selecció i la PSF s’havien treballat en la via fotogràfica abans d’aquesta revisió: les comprovacions actuals no són una validació cega de punta a punta.','small')

def footer(canvas,doc):
    canvas.saveState();w,h=doc.pagesize;canvas.setFillColor(TEAL);canvas.rect(48,h-33,32,3,fill=1,stroke=0);canvas.setFont('Deja',8);canvas.setFillColor(GREY);canvas.drawString(89,h-33,'ECLIPSI · RELATIVITAT GENERAL · ESTUDI V2');canvas.setStrokeColor(colors.HexColor('#d9e3e5'));canvas.line(48,42,w-48,42);canvas.setFont('Deja',7.7);canvas.drawString(48,28,'14 setembre 2026  |  Previsió, diagnòstic i pla experimental');canvas.drawRightString(w-48,28,str(doc.page));canvas.restoreState()

if __name__=='__main__':
    content();pdf=O/'Estudi_relativitat_V2_20260914.pdf'
    doc=SimpleDocTemplate(str(pdf),pagesize=(595.276,841.89),leftMargin=48,rightMargin=48,topMargin=58,bottomMargin=55,title='Posar a prova la relativitat general - Estudi V2',author='Pere Guerra · anàlisi amb Codex',subject='Revisió 2026 amb estrelles V65 i pla experimental 2027')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    (O/'Estudi_relativitat_V2_20260914.md').write_text('# Posar a prova la relativitat general · Estudi V2\n\n'+'\n\n'.join(md)+'\n')
    print(pdf)
