# Earthshine V47: composició candidata i verificació

La V46_Detall de Pere és la referència fotogràfica. Les dades científiques, el PSB original i les sessions obertes es conserven. No s'ha generat textura artificial ni s'ha dibuixat una màscara nova.

## Cadena acotada

1. `a2` restaura el registre original de la textura en sis RAW Vixen. L'ajust global a la vora aparent es descarta perquè empitjora la correlació de textura amb la Sony.
2. `c0` combina les ponderacions normalitzades de dos estimadors existents (totes les èpoques i preferència temporal), al 50/50. Reuneix diferències entre píxels vàlids de cada presa; el canvi de pes no es confon amb una diferència de llum. Composició rectangular en asinh, Poisson amb longitud 8 px i transició freqüencial 8–16 px fixades. 67 Vixen; la Sony és jutge extern.
3. `c1/c2/c3` contrasten marques, 24 sectors del llimb i dues captures Sony de 2 s (06996/06999). Hi ha millores i regressions, que es conserven al rebut. La mediana de la irregularitat dels sectors passa de 0,399 a 0,250 px; 22/24 sectors milloren, dos empitjoren lleument. No equival a resolució angular ni a recuperació completa del relleu.
4. `c4` injecta fases fixades en cada font de la composició: transferència 1,000000–1,000072. Control de l'operador amb pesos fixos, no de tota la cadena RAW, ni de Camera Raw.
5. L'alternativa directa `E` suavitza massa la textura fotogràfica de Pere. L'alternativa `D`, massa conservadora, encara arrossega les dents. La proposta `G` conserva les freqüències amples del revelat anterior i substitueix les fines per la font recomposta. Tot el rectangle usa el mateix operador 8–16 px, abans de Camera Raw; les marques no intervenen en el càlcul.
6. Camera Raw s'executa realment en una còpia amb la recepta local recuperada: exposició −2,10, ombres −100, blancs +16, negres +40, textura +100, claredat +40, soroll de luminància 69. La recepta històrica exacta no s'ha pogut reconstruir. Una corba monòtona global, calibrada amb la capa original i validada en sectors separats, conserva el seu to aproximat. No hi ha correccions de to per radi ni per zones pintades.
7. El canvi final és neutre: el mateix increment enter en R, G i B conserva exactament les diferències cromàtiques de la capa de Pere. Es copia sencera la seva màscara física. La capa original i el retoc manual V46 queden disponibles, ocults al candidat. La resta de capes conserva els seus bytes i estat.
8. PSB de 25 capes, mateix 10551 × 7506 RGB16; dos lectors i `porta_photoshop.sh`, recomposició i comparació de tots els píxels. Cap candidat es publica sense aquesta porta.

## Resultats que NO es promouen

- Els desplaçaments globals inferits de la vora aparent (ronda anterior) perjudiquen textura lunar independent: rebutjats.
- En la font C0, marca verda 3 / 40–64 px / jutge Sony B8 perd el PASS en radiància lineal, mentre el manté en log. Cap afirmació de millora uniforme.
- En 96 combinacions de bandes/sectors no pintats amb Sony 06996/06999: 11 nous PASS i 6 pèrdues de PASS; alineació màxima a 0° als dos. No són 96 proves estadístiques independents.
- El llimb a 180° només té 92/160 perfils comuns complets amb la referència curta/tardana emprada. No s'omple informació absent.
- No es declara recuperat tot l'últim llimb, ni albedo net sense vel, ni resolució equivalent demostrada a DHS. La llum dispersa i la resposta dels filtres continuen limitant el resultat.
- Els PSB interns D/E són comparacions d'assaig, no productes promoguts. E va passar OBRE però va fallar la recomposició; s'ha detectat un identificador Photoshop duplicat a la capa afegida. La proposta G elimina aquest identificador només de la capa nova abans de la porta; cal el seu rebut final, no assumir la cura.
