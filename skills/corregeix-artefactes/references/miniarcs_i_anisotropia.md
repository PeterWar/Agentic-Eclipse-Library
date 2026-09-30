# Miniarcs concèntrics: diagnòstic i prevenció

Lliçó mesurada a V30 (05-09-2026), `3-RECERCA/137_V30_minicercles_i_variants.md`.
És un precedent, no una recepta universal de sigma 4 o sigma 8.

## Separar tres causes abans de corregir

1. Graons radiomètrics d'exposicions: poden dibuixar contorns poligonals.
   Compara fotogrames comuns i reservats; corregeix pedestal/escala justificats
   a l'origen. Exemple V29 capa03, 3-RECERCA/136.
2. Perfils radials interpolats (rho, MAD, H1): poden afegir una ondulació
   comuna als azimuts. Fes una ablació de cada perfil; H1 baix només controla
   el nivell mitjà del detall, no exclou microestructura espúria.
3. Kernel només angular: el soroll queda allargat tangencialment en arcs.
   Mesura el camp abans/després de cada etapa i prova soroll d'entrada
   sintètic amb llavor, geometria i validesa fixades. No atribueixis a H1
   allò que persisteix quan el retires.

## Modificar l'operador, amb transferència mesurada

Una opció és una gaussiana radial petita sobre la representació polar,
normalitzada `G_r(p*valid)/G_r(valid)`, abans d'una única tornada al llenç.
La validesa prové de les observacions, no de les marques. No omplir radiància
no observada, no ampliar el disc lunar, no crear fades a un radi solar fix.
Verifica que sigma radial zero reprodueix el filtre anterior.

La transferència addicional lineal ideal és
`exp(-2*pi^2*sigma_r^2/lambda_r^2)`. No és la transferència de tota la cadena:
cal injectar senyal abans de l'operador, mantenir la mateixa base i màscares,
i tornar a passar interpolació, tanh, S/N i H1 abans de mesurar el delta.
Declara si la injecció és sobre radiància derivada o RAW; no les equiparis.
Una alternativa autoritzada pot lliurar-se oculta per comparar, amb
l'atenuació declarada i el judici estètic pendent; no pot dir-se PASS en una
banda que no arriba al llindar.

A V30: sigma4 redueix l'RMS radial 4–32 px de quatre zones marcades a
0,476–0,550 de V29; sigma8 a 0,132–0,161. La injecció aparellada real conserva
0,967–1,011 amb sigma4 a longituds radials 96/160/256 px. Sigma8 conserva
0,873–0,891 a 96 px (atenuació deliberada, NO PASS 0,90) i passa a >=160 px.
Els números dels noms ACHF són sigmes de kernels, no vores de bandes FFT.

## Validar sense fer que el jutge s'adapti al candidat

- Compara contra l'altre tren FIX, sense suavitzar-lo també amb el candidat.
  Mesura correlació i amplitud coherent en bandes FFT amb finestres i validesa
  declarades. Comparar V29 amb V30 demostra retenció, no realitat científica.
- El tren que alimenta el mateix compost no és una validació independent.
  Manca de correlació no classifica cada píxel com a soroll.
- Mostra llenç sencer, limbe, cada sector marcat i estructures no marcades
  al 100%. Declara residus. Les marques localitzen; no esdevenen màscares.
- Revalida angle zero, controls de gir, H1, H1b, suport, canals PSB reoberts
  i Photoshop real. Conserva els filtres acceptats byte a byte.
- Les variants del detall fi es comparen a igual opacitat i substituint la
  capa pare. Un augment de contrast exterior sense corroboració s'anomena
  textura reforçada; no promet més resolució ni més corona.

Per comparar amb Brno usa els compostos REALS identificats per hash i un
registre congelat; mateixa descodificació de color als dos costats. Canviar
una etiqueta Vxx d'un script amb fonts fixes no compara aquella versió.
