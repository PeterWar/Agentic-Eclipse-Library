# Recerca causal del gramòfon — protocol inicial

Autorització: Pere, 06-09-2026, explorar funció contínua bidimensional i les
quatre passes. Producte V31 immutable. Sense PSB nou en aquesta recerca.

Hipòtesis que es poden refutar:

1. Els bins i l'acoblament anular poden crear arcs sense arcs d'entrada.
2. Una regressió local contínua amb suport compacte elimina l'acoblament
   entre zones separades per més del seu radi de dependència.
3. La resta de fons pot preservar textura fina i destruir estructures més
   amples: cal trobar i declarar la banda vàlida, no ocultar-la.
4. Cap estimador de fons que preservi una estructura real pot distingir-la
   sempre d'un artefacte idèntic ja present a la base.

Candidats preregistrats abans de mirar el jutge real:

- Q2: regressió quadràtica local de log(I), sis bases cartesianes.
- LR: regressió local de log(I) sobre [1, log(r)], coeficients diferents a
  cada píxel, estimats en un veïnat cartesià compacte; no comparteix anells.
- Pes radial LOCAL Wendland C2: (1-t)^4(1+4t), 0<=t<1, zero fora.
- Radis de suport 96 i 160 px en proves sintètiques; 160 px al pilot real.
- Primer sortida D=log(I)-fons amb guany1, sense normalització de contrast.
  Després ablació independent D/sqrt(W(D²)+0.002²). El terra0.002 és un
  paràmetre experimental declarat, no una mesura del soroll del sensor.
- Controls: mitjana local de log(I), NRGF amb/sense interpolació; MGN
  publicat en el pilot real. Cap H1, notch, retall circular o inpainting.

Proves: nul r^-3, pedestal additiu, forats/cobertura, polinomi conegut,
impuls/arcs locals, textura Fourier a4/8/16/32/64/128/256px, fase i orientació,
artefacte radial injectat a l'entrada. La transferència es mesura per resposta
central diferencial, comparada amb la textura coneguda; 0.90–1.10 sense
reajust de guany per banda. Controls dolents han de fallar.

Pilot real: Sony sola (abans/després dels offsets disponibles), mateixa
graella, Vixen original immutable de jutge. No filtrar la base fusionada
per provar independència: el veïnat pot travessar la franja de mescla. La
calibració escalar entre trens existent es declara; no s'ajusta localment
el jutge ni el candidat contra el jutge. Mateixa visualització i escales.

Marc: normalized convolution/local polynomial regression, no afirmació
d'invenció. La transferència gaussiana de Q2 no s'aplica a Wendland: es
mesura el nostre nucli efectiu. Estudi limitat a G; no certificació RGB.

## Extensió motivada pels primers resultats (21:15 UTC aprox.)

Els models lineals absorbeixen arcs locals reals. Provar una sola reestimació
del fons amb pesos de certesa suaus pseudo-Huber: w=1/sqrt(1+(D/0.002)^2),
on D és el residual del primer ajust. No es modifica ni interpola cap píxel
observat. És un refit amb certesa pilot, NO IRLS exacte per consulta. La
dependència passa de h a2h, cal declarar-la. El0.002 és una escala fixada de
0.2% aproximat en logI, no es tria segons el jutge real.

Validació nova amb arcs d'una altra posició i amplituds0.0002/0.002/0.02,
amb/sense soroll0.001. Recalcular els pesos a cada injecció; congelar-los
faria una prova falsa. Incloure halo/forma i no només correlació/amplitud.
Una millora dels arcs forts no demostraria preservació dels arcs febles.

## Prova causal de font, abans del filtre (21:20 UTC aprox.)

Fit només Sony G: diferències entre fotogrames al mateix píxel i sobre les
zones comunes no saturades. Comparar un offset constant per fotograma amb
un pla additiu2D per fotograma (constant+x+y), mateixa àncora i guanys.
Entrenament en sectors angulars alterns1.08–4.5R, validació als altres,
i extrapolació a4.5–8.5R separada. Cap estimació del fons a partir de les
formes de la corona; la part comuna cancela en les diferències. Font de
mostreig24px existent, no RAW reprocessat. Cap pla s'aplica a la fotografia
sense prova nativa i jutge extern. La reducció de desacord entre fotos,
per si sola, no és certificació de supressió dels arcs del producte.
