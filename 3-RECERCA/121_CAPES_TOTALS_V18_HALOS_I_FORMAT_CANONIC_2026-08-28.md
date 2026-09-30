# 121 — CapesTotalsV18: els halos de la fusió, la igualació en baixa freqüència i el format canònic de Pere

Encàrrec de Pere (28-08-2026, tarda): «no ho has fet bé, ho he hagut de fer jo manualment
amb filtres de Camera Raw. Aprèn del que he fet. [...] Ara el problema el tinc amb la
màscara, que no fusiona bé i surten halos; t'he pintat els halos a una capa. Fes una V18
esforçant-te al màxim per eliminar-los tots; estèticament ha de quedar com la imatge del
VIXEN però amb la corona més gran del camp dels 300 mm.» Continua `research/120`.
Lliurable: `CapesTotalsV18.psb` + rebut + vistes; la V17 (amb les seves edicions) intacta.

## 0. Resum en sis línies

1. **El format canònic de Pere queda après i desat** (`FORMAT_CANONIC_SONY_PERE.json` +
   memòria): interior neutre ~0,90 → cel FOSC i BLAU (0,28-0,41, B/G 1,22), ombres p0,5
   0,075-0,105. El render pla de la cadena NO és un lliurable estètic.
2. Els seus 9 arcs vermells (3,6-4,6 R☉) eren la banda de la seva màscara nova
   (3,75-5,0): la Sony hi era un 8-18 % més brillant que el Vixen de sota → bony anular
   +3-7 %.
3. **La cura: S′ = S·ρ amb ρ = perfil radial × Fourier azimutal (k≤2)** per canal —
   iguala la baixa freqüència de la Sony a la del compost Vixen allà on conviuen →
   qualsevol màscara esdevé lliure de halos per construcció. Pitjor bony final: 0,0024
   (abans 0,03-0,07). Perfil final ≡ Vixen a la mil·lèsima per tota la transició.
4. ⛔ **Dues versions de ρ van ser caçades per les portes** — la lliçó de mètode: (a) un
   camp 2D lliure (suavitzat amb màscara, σ200) PERSEGUEIX les costures locals (la
   d'apuntaments: bony nou del 2 % a az −117°) — el model ha de ser suau per construcció;
   (b) el mostreig clavat a l'últim calaix radial tocava el camp llunyà canònic (p99 de
   la diferència +0,33!) — la finestra d'acció es DECLARA: completa ≤5,5 R☉, fosa fins a
   7,0, exactament 1 més enllà (verificat: p99 = 0,0000 fora de 7).
5. **Res més no canvia**: capes Vixen i Pasalt byte a byte; de la 13 només els RGB (la
   màscara de Pere intacta); HALOS es conserva però invisible. Porta Photoshop: OBRE.
6. Portes noves que queden per a qualsevol fusió: **la verificació per arc marcat**
   (bony sobre l'envolupant monòtona al sector) i **la porta de diferència** (mediana,
   p99 i gradient per anells: què s'ha tocat, on, i cap vora nova).

## 1. Les mesures que manen

- V17 de Pere: capes 08-01 re-enceses (compost de sota sòlid: alfa 1,00, perfil llis
  0,74→0,36 entre 1,75 i 6 R☉); màscara Sony nova 3,75→5,0; capa Sony corregida amb
  Camera Raw (format canònic).
- Desajust a la banda: V 0,451 / S 0,531 a 4,0 R☉ (G); final abans 0,464 (bony) → ara
  0,452 (≡V).
- ρ final: mediana 1,000, p1-p99 [0,78, 1,14]; correcció confinada (mesurat per anells:
  dins 3,5 R☉ p99 |d| 0,006; 3,5-5,5: fins a 0,066; fora de 7: 0,0000).

## 2. Per què la igualació en baixa freqüència és la cura correcta

Un halo de fusió és una DIFERÈNCIA de baixa freqüència (brillantor o color) entre els dos
costats d'una màscara. Igualar els camps de baixa freqüència allà on conviuen — i només
allà — el fa impossible per construcció, conserva el detall fi de tots dos costats, i
desacobla el problema de la forma de la màscara (Pere pot repintar-la sense refer res).
És l'equivalent net del blending multibanda expressat com a correcció de capa, compatible
amb l'estructura de capes de Photoshop.
