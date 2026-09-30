export const meta = {
  name: 'v74-marques-pere-diagnosi',
  description: 'Diagnosi de les 7 marques noves de Pere a la V74 (negres, taca, lila) amb 3 diagnosticadors i 1 verificador adversari',
  phases: [
    { title: 'Diagnosi', detail: 'tres lectors independents: punts negres, taca de l\'earthshine, limbe lila' },
    { title: 'Verificació', detail: 'un escèptic intenta refutar cada troballa amb les dades' },
  ],
}

const COMU = `
CONTEXT (projecte «Eclipse 2026» de Pere, arrel /Users/USUARI/Desktop/Eclipse 2026; no hi ha git; treballa NOMÉS al scratchpad, no escriguis res dins de l'arrel del projecte, no obris Photoshop, no toquis cap PSB).
Idioma: català planer als textos que tornis.
Python: ~/.venvs/eines-ia-py312/bin/python (numpy, scipy, psd-tools, PIL, matplotlib, tifffile).
Scratchpad de treball (llegeix-hi i escriu-hi): S4=/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad
Altres scratchpads (només lectura): NEW=/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad (V71 de Pere: roi71_L{id}.npz, compo71.py, roi71_compost.npz) i OLD=/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad (V69: roi_L{id}.npz; raw_disc_norm_2000.npy = disc lunar als RAW Vixen 10 s normalitzat per anells; vel_*.npy = models de vel/glow; corona_hdr_3000.npy).

DADES DE LA V74 RE-DESADA PER PERE (17-09 vespre, 25 capes), ROI lunar = llenç (4377,2777)–(6377,4777), 2000×2000 px:
- S4/roi74p_L{id}.npz per a cada capa visible (+62 LROC oculta): claus c0,c1,c2 (RGB uint16), c-1 (alfa pròpia), c-2 (màscara d'usuari) — tot en coordenades de la ROI.
- S4/v74pere_index_psb69.json: índex de capes (id, name, visible, opacity 0–255, blend, mask{background,disabled}). Ordre de baix a dalt: 3 base (normal), 41,42 NRGF (multiply), 47,49,51,53 ACHF (overlay), 45,46 RHEF (multiply), 55,56 WOW (overlay), 30 Earthshine (normal, revelat de Pere, gris neutre), 76 Interiors (fotos de Pere, normal), 96,204,206 perles «07 1/15 x2 quar» (fotos de Pere, normal), 202 estrelles (linear dodge), 222 «Capa 1» = marques de Pere (normal; IGNORA-LA a la composició).
- S4/compo74.py: recomposició Photoshop verificada (fórmula W3C amb alfa del fons; coincideix amb el compost desat per Photoshop a 0,0 DN16 al disc i 1,4 a la corona). Ús: import sys; sys.path.insert(0,S4); import compo74 as c; C,a = c.recompon(exclou=(222,))  → C float32 (2000,2000,3) en [0,1] (AdobeRGB, gamma ~2,2), a = alfa. Amb retorna_passos=True torna (C,a,passos) on passos[id]=(C_després_de_la_capa, a). c.carrega(id) → (rgb float, alfa efectiva = alfa×màscara×opacitat). c.LAYERS[id] dóna nom/blend/opacitat. c.OVERRIDE[id]=ruta_npz permet provar variants d'una capa.
- S4/roi74p_C_sensemarques.npy: el compost V74 sense la capa 222 (ja calculat). S4/roi74p_compost.npz['C']: compost desat per Photoshop (RGBA, aplanat sobre blanc).
- S4/marques74_masks.npz: màscares booleanes m1…m7 de les 7 marques de Pere (coordenades ROI) i ent_m1…ent_m7 = entorn immediat (corona de 8–40 px al voltant de la marca, mateixa banda radial ±15 px, mateix costat del limbe).
- S4/e1_marques_222.json: per marca: bbox (llenç), centre, rgb8 del traç, r_lluna, az, r_min, r_max.
- Geometria: centre lunar a la ROI (998,88, 998,41); silueta fotografiada R = 456,0 px; azimut antihorari des de +x amb y cap amunt (90 = dalt, 180 = oest/esquerra, 270 = baix). r i az: Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-998.88,Y-998.41); az=(np.degrees(np.arctan2(-(Y-998.41),X-998.88)))%360.
- Lab aproximat (AdobeRGB gamma 2,2): lin=C**2.2; M=[[0.5767,0.1856,0.1882],[0.2974,0.6273,0.0753],[0.0270,0.0707,0.9911]]; XYZ=lin@M.T; blanc (0.9505,1,1.089); L*=116 f(Y)−16, a*=500(f(X/Xn)−f(Y)), b*=200(f(Y)−f(Z/Zn)).
- V71 de Pere (referència que a ell li agrada «globalment») al NEW: mateixes claus; compo71 igual que compo74. Canvis meus V71→V74 (dins de r ≤ 458 px només): base gris fosc dins la silueta (erf σ 1 a R 456), capa 57 POWAAAH3 (Pere l'ha ESBORRADA a la seva V74), 10 filtres neutres dins la silueta (multiply→1,0; overlay→0,5). Pere hi ha afegit: màscara de la capa 76 retocada a x 5218–5343, y 3306–3392 (llenç; r≈435, az≈102) per «un error d'alineació de la protuberància de dalt que l'enclotava».

EL QUE DIU PERE (17-09 vespre, literal): «he fet nova capa artefactes, ignora el color de la capa, és només indicatiu de les zones; els artefactes que veig en la corona interior són negres, i l'artefacte en l'earthshine és una regió massa fosca que no pot venir de cap filtre perquè earthshine es sobreposa a la resta de la imatge, ha de venir de com fas l'earthshine. Marcats en lila, artefactes en el llimb de l'earthshine.»
Marques: m1 lila (traç llarg AL limbe de dalt, az ≈ 73–113, r 448–466); m2 negra (az 109, r 465–471); m3 negra (az 117, r 470–474); m4 negra (az 155, r 476–480); m5 negra (az 167, r 474–481); m7 negra (az 234, r 459–470); m6 = taca (regió gran dins del disc, az 255, r 167–412).

NORMES DEL PROJECTE QUE MANEN: (1) causa arrel, mai cosmètica: cap suavitzat, retall o pedaç que amagui un artefacte sense curar-ne la causa a la font; (2) no tocar el treball manual de Pere (màscares, alfa, encaix, les seves fotos 76/96/204/206, el revelat de la capa 30 com a tal) sense el seu vistiplau explícit: si la causa és seva, s'ha de DIR, no corregir d'amagat; (3) LROC (capa 62) i Brno són jutges, mai font: cap píxel seu al producte; (4) cap cercle booleà sobre màscares (fa el limbe dentat); (5) mesura «marca contra entorn immediat», i atribueix capa a capa (retorna_passos); (6) tot número al rebut: escriu els teus resultats a S4/<prefix>_*.json i les vistes a S4/v_<prefix>_*.png (retalls al 100–400 %, mateix to abans/després).
`

const SCHEMA_MARQUES = {
  type: 'object',
  properties: {
    marques: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' }, que_es: { type: 'string' }, capa_origen: { type: 'string' }, mecanisme: { type: 'string' },
      evidencia: { type: 'string' }, magnitud: { type: 'string' }, ja_hi_era_a_V71: { type: 'boolean' },
      proposta_origen: { type: 'string' }, toca_treball_de_pere: { type: 'boolean' }, confianca: { type: 'number' } },
      required: ['id','que_es','capa_origen','mecanisme','evidencia','proposta_origen','toca_treball_de_pere','confianca'] } },
    fitxers: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
  required: ['marques','fitxers','notes'],
}

const SCHEMA_TACA = {
  type: 'object',
  properties: {
    diagnostic: { type: 'string' }, mecanisme_origen: { type: 'string' }, evidencia: { type: 'string' },
    metode_correccio_origen: { type: 'string' }, factible_ara: { type: 'boolean' }, que_falta: { type: 'string' },
    resultat_prova: { type: 'string' }, fitxer_capa30_candidata: { type: 'string' }, riscos: { type: 'string' },
    fitxers: { type: 'array', items: { type: 'string' } }, confianca: { type: 'number' },
  },
  required: ['diagnostic','mecanisme_origen','evidencia','metode_correccio_origen','factible_ara','que_falta','resultat_prova','riscos','fitxers','confianca'],
}

const SCHEMA_VERIF = {
  type: 'object',
  properties: {
    veredictes: { type: 'array', items: { type: 'object', properties: {
      afirmacio: { type: 'string' }, refutada: { type: 'boolean' }, motiu: { type: 'string' }, evidencia_propia: { type: 'string' }, compleix_normes: { type: 'boolean' } },
      required: ['afirmacio','refutada','motiu','evidencia_propia','compleix_normes'] } },
    recomanacio_v75: { type: 'string' }, fitxers: { type: 'array', items: { type: 'string' } },
  },
  required: ['veredictes','recomanacio_v75','fitxers'],
}

const P_NEGRES = COMU + `
LA TEVA FEINA (lector A, prefix «fa»): les CINC MARQUES NEGRES de la corona interior (m2, m3, m4, m5, m7), just fora del limbe (r 459–481). Pere hi veu punts o taques NEGRES (fosques). Mesures prèvies meves (sense la capa de marques): el mínim de (L* − mediana local 21 px) dins de cada marca és −2,4…−3,8 L*, igual a V71; la mitjana marca−entorn és ±2 L*. O sigui: el que hi ha és subtil o compacte. Has de trobar QUÈ són exactament i QUINA CAPA ho fa.
Protocol: (a) per a cada marca, localitza els píxels o grups foscos compactes (L* − mediana local < −2, també prova finestres de 9 i 41 px i el canal G sol); dibuixa'ls; (b) atribució capa a capa amb retorna_passos: en quina capa apareix cada punt fosc (ΔL* del punt contra els seus veïns després de cada capa); (c) confronta amb els ràsters i les alfes de: filtres 41/42 (multiply), 47/49/51/53 (overlay), 45/46 (multiply), 55/56 WOW (overlay; el WOW bilateral fa halos foscos al voltant de punts brillants), les fotos de Pere 76/96/204/206 (ploma/alfa, pols o píxels morts de les fotos 1/15 s), les estrelles 202 (linear dodge: només aclareix, però els filtres es van fer «sense estrelles» i la base té estrelles: forats?), i la base 3; (d) compara amb V71 (NEW): mateixos punts? (e) comprova també la franja 456–462 (just fora de la silueta): a V74 la base té una vora erf σ 1 a 456 i els filtres són neutres fins a 455,5: hi ha una banda fosca entre la silueta i la cromosfera que abans no hi era? mesura el perfil radial per sector a 452–470 a V71 i V74 (L* per anell d'1 px).
Torna, per marca: què és (punt, banda, halo…), capa d'origen, mecanisme, evidència numèrica, magnitud (ΔL* i mida en px), si ja hi era a V71, i una proposta de correcció A L'ORIGEN (a la capa que ho causa, implementable sobre els arrays de la ROI), dient si toca treball de Pere. Si una marca no té cap estructura mesurable, digues-ho amb els números.`

const P_TACA = COMU + `
LA TEVA FEINA (lector B, prefix «fb»): la TACA (m6): regió gran de la capa 30 (Earthshine, revelat de Pere) un ~5 % més fosca que el seu entorn immediat (V69 −6,5 %, V71/V74 −5,3 %; a LROC −0,3 %, o sigui NO és relleu lunar; al RAW del disc no es pot jutjar perquè l'earthshine hi és el 0,36 % del senyal). Pere: «ha de venir de com fas l'earthshine». Ho ha de tenir raó: la capa 30 és el revelat de Pere (corba seva, desconeguda però monòtona) del meu producte lineal V68, que venia de V51 (fusió lunar) → V52 (vel de l'ala de la corona RESTAT: mesurat per sector de 5° a la mateixa capa com a mediana radial de 2 px, excés sobre el nivell del disc a −260…−200 px del limbe, suavitzat σ 3 px/10°, MONÒTON (màxim acumulat radial), taper −260→−200, una iteració de refinament) → V53 (taper continu −70→−40) → V68 (patró fi). L'estudi del 14-09 (4-RESULTATS/earthshine_taca_source_20260914/*.json i .coordination/HANDOFF_2026-09-14_TACA_NUVOLS_I_MAXIM_RADIAL.md) va veure que «el màxim acumulat radial pot propagar un tret lunar clar cap enfora com a sobre-resta»; el candidat isotònic (A3) va millorar la marca però va fallar les injeccions en 2 de 3 posicions i NO es va promoure. Els arrays lineals de l'earthshine ja no són al disc (neteja del 16-09; busca'ls igualment: find a l'arrel i a ~/.Trash/Eclipse_neteja_20260916, també noms com Earthshine_V5*, V68, S8, DHS*). Eines: 3-RECERCA/tools/earthshine_* i v68_* (mira quin script feia el vel V52/V53 i l'A3 del 14-09), 3-RECERCA/tools/v71_marques_v69_20260916/a28_vel2d.py (el meu vel 2D de V71, que va passar dins/anell de −9,6 % a +0,9 % però dins/entorn només de −6,5 a −5,4 %).
Protocol: (a) confirma el mecanisme sobre la capa 30 mateixa: perfils radials de L per sector de 5° (r 100–440) als sectors de la taca (az 240–270) contra els veïns (az 210–240 i 270–300): hi ha un tret clar a r petit (~150–170) seguit d'un altiplà deprimit fins a ~370–410 als sectors de la taca (empremta d'un màxim acumulat)? Quantifica el dèficit (ln del quocient sector/veïns en funció de r). (b) Comprova amb LROC (capa 62, jutge): el mateix quocient a LROC ha de ser ~pla. (c) Dissenya la correcció A L'ORIGEN: recalcula l'envolupant del vel als sectors afectats SENSE el màxim acumulat (per exemple envolupant inferior robusta, o isotònica ponderada, o el vel radial de la mediana dels sectors veïns), i converteix-la en una correcció de la capa 30. Com que la capa 30 és post-revelat, raona i prova quina forma té la correcció (additiva en lineal ≈ multiplicativa suau en el revelat si la corba és ~potència; estima l'exponent local de la corba de Pere si pots, p. ex. comparant la capa 30 amb OLD/raw_disc_norm o amb els vel_*.npy). (d) Prova-la sobre els arrays: escriu S4/roi75_L30_candidata.npz (mateixes claus que roi74p_L30.npz; NOMÉS c0,c1,c2 canviats, mateix factor als tres canals; c-1 i c-2 intactes; cap canvi a r > 440), i mesura: taca dins/entorn abans→després (ha d'anar cap a 0 sense passar-se), correlació de la banda de mitjana escala (σ 12–60 en ln) amb LROC per sectors parells/senars abans→després (ha de pujar o quedar igual), canvi màxim de la gran escala σ 60 (ha de ser petit: Pere va refusar V72/V73 perquè li canviaven el «focus de llum» de la Lluna), i que cap altre sector canviï. (e) Injecció cega: injecta un tret gaussià ±3 % (σ 50 px) en dues posicions fora de la taca i comprova que la teva correcció el conserva 0,90–1,10 (norma del projecte). Si res d'això és factible amb el que hi ha, digues exactament què falta i quant costaria refer-ho des dels RAW (0-RAW/Vixen R6III, fotogrames 572A2982–2984 de 10 s i els curts registrats a la Lluna 572A2965–2969).
Sigues honest: si la correcció només «aplana contra els veïns», és cosmètica i s'ha de dir.`

const P_LILA = COMU + `
LA TEVA FEINA (lector C, prefix «fc»): la MARCA LILA (m1): Pere marca «artefactes en el limbe de l'earthshine» al limbe de DALT (az ≈ 73–113, r 448–466), amb un traç llarg just al limbe i un de curt una mica més amunt. Aquest limbe el vaig canviar a V74: abans (V71) hi havia una franja clara i groga entre la vora de la màscara a mà de la capa 30 (a r 451–455 segons el sector; a dalt la màscara acaba a ~451) i la silueta (456), feta per la ploma blanca de POWAAAH3 (57, ara esborrada per Pere) i el farcit clar de la base; a V74 la base és gris fosc dins la silueta (al nivell de la vora de la capa 30 per sector) i els filtres són neutres dins. Sospita meva: a dalt queda una banda lleugerament més clara (L* 12–20 contra 10 del disc) entre la vora de la màscara de la capa 30 i la silueta, i la foto d'interiors 76 hi deixa passar un 7–17 % (alfa efectiva 0,07–0,17 a r 440–464 a az 90–105) de corona clara DINS de la silueta; a més Pere acaba de retocar la màscara de la 76 a az ≈ 102 (r ≈ 435). També pot ser la vora erf σ 1 (massa tova o massa dura respecte a la cromosfera), o un graó a la vora de la màscara a mà.
Protocol: (a) perfils radials d'1 px (L*, a*, b*, i els 3 canals) per sectors de 5° a az 60–125, r 436–476, a V74 i a V71 (NEW), amb la posició de la vora de la màscara de la capa 30 (c-2 = 0,5) i de la 76 (alfa efectiva) per sector; (b) atribució capa a capa (retorna_passos) del que hi ha a 448–456 i a 456–462 en aquests sectors: qui aporta la banda clara (base farcit? 76? perles 206? filtres residuals?); (c) mesura la nitidesa del limbe (amplada 10–90 % del trànsit per sector) a V71, V74 i als sectors de referència sense marca (az 0–30, 300–330); (d) mira també què fa la vora de la màscara de la capa 30 (a mà): és visible com a graó? on? (e) proposa la correcció a l'origen: per a cada aportació, si és meva (farcit de la base, vora erf, filtres) què s'ha de canviar exactament; si és de Pere (màscara 76, màscara 30) digues-ho i quantifica-ho perquè ell decideixi. Vistes: retalls al 300 % de az 80–110 (V71 | V74) al mateix to i tira polar r 430–480 az 60–125.
Torna per «sub-marca» (traç llarg al limbe; traç curt més amunt) què és i d'on ve.`

phase('Diagnosi')
log('3 lectors independents: punts negres (A), taca de l\'earthshine (B), limbe lila (C)')
const [A, B, C] = await parallel([
  () => agent(P_NEGRES, { label: 'A:punts negres', phase: 'Diagnosi', schema: SCHEMA_MARQUES, effort: 'high' }),
  () => agent(P_TACA,   { label: 'B:taca earthshine', phase: 'Diagnosi', schema: SCHEMA_TACA, effort: 'xhigh' }),
  () => agent(P_LILA,   { label: 'C:limbe lila', phase: 'Diagnosi', schema: SCHEMA_MARQUES, effort: 'high' }),
])

phase('Verificació')
const P_VERIF = COMU + `
LA TEVA FEINA (verificador D, prefix «fd»): ets l'ESCÈPTIC. Tres lectors han diagnosticat les marques de Pere. Intenta REFUTAR cada afirmació amb mesures pròpies sobre les mateixes dades (no et refiïs dels seus números: torna a mesurar el que sigui decisiu; si dubtes, refutada=true), i comprova que cada proposta de correcció compleix les normes (causa arrel, no cosmètica; no toca treball de Pere d'amagat; LROC mai font; cap cercle booleà; res fora del que la causa justifica). Si un lector proposa un fitxer candidat (S4/roi75_L30_candidata.npz), mesura'l tu: taca dins/entorn, correlació amb LROC per sectors parells/senars, canvi de gran escala σ 60, injeccions. Acaba amb una recomanació concreta per a la V75: què s'ha de canviar (capa, regió, com), què NO, i què s'ha de dir a Pere que és seu.
RESULTATS DEL LECTOR A (punts negres): ${JSON.stringify(A)}
RESULTATS DEL LECTOR B (taca): ${JSON.stringify(B)}
RESULTATS DEL LECTOR C (limbe lila): ${JSON.stringify(C)}`
const D = await agent(P_VERIF, { label: 'D:escèptic', phase: 'Verificació', schema: SCHEMA_VERIF, effort: 'xhigh' })
return { A, B, C, D }