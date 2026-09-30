# Contrast tècnic: QE efectiva i temps d'exposició en càmeres FF

## Objectiu

Auditar una comparativa de càmeres per a:

- eclipse solar 2026 controlat amb gphoto2;
- DSO portàtil amb òptiques ràpides, exposicions de 10–30 s, sense guiatge;
- moltes preses RAW i calibratge/stacking exigent.

No inventis percentatges de QE. Separa dada publicada, estimació física i
desconegut. Cita URLs directes per a qualsevol xifra específica d'una càmera.

## Càmeres

Referències de l'usuari:

- Sony A7S original
- Sony A7 III
- Canon EOS 6D original

Candidates:

- Canon EOS R5
- Canon EOS R5 Mark II
- Canon EOS R6 Mark II
- Canon EOS R6 Mark III
- Nikon Z5 II
- Nikon Z6 III
- Nikon Z7 II
- Nikon Z8

## Dades comparables existents

Mesures RAW normalitzades a 14 bits. Les exposicions habituals de l'usuari són
ISO 3200 i 6400.

| Càmera | ISO | Gain e-/ADU | RN e- | DR eng EV | t+5% actual s |
|---|---:|---:|---:|---:|---:|
| Canon 6D | 6400 | 0.076 | 1.376 | 9.63 | 10.9 |
| Sony A7S | 3200 | 0.316 | 1.310 | 11.90 | 6.0 |
| Sony A7 III | 3200 | 0.184 | 1.257 | 11.19 | 11.1 |
| Canon R5 | 3200 | 0.097 | 1.537 | 9.98 | 30.2 |
| Canon R5 II | 3200 | 0.106 | 1.853 | 9.82 | 44.0 |
| Canon R6 II | 6400 | 0.094 | 1.214 | 10.26 | 10.1 |
| Canon R6 III | 6400 | 0.072 | 1.828 | 9.30 | 30.8 |
| Nikon Z5 II | 3200 | 0.168 | 1.329 | 10.94 | 12.3 |
| Nikon Z6 III | 3200 | 0.163 | 1.659 | 10.56 | 19.2 |
| Nikon Z7 II | 6400 | 0.036 | 0.927 | 9.88 | 11.2 |
| Nikon Z8 | 3200 | 0.070 | 1.133 | 10.55 | 16.7 |

El full original usa:

- `t = C × RN² / P`
- `C = 10` per a aproximadament +5% de soroll
- referència A7S a SQM 22 i f/2.8: `P = 2.86 e-/s/píxel`
- els `P` de les altres càmeres s'han escalat provisionalment només per àrea
  de píxel, és a dir, assumint la mateixa eficiència efectiva.

## Preguntes

1. És científicament correcte corregir amb
   `P_camera = P_A7S × area_rel × eta_rel`, on `eta_rel` és l'eficiència
   efectiva total càmera (òptica interna, microlents, CFA i filtres), i després
   `t_QE = t_actual / eta_rel`?
2. Què convé comparar per DSO amb càmeres de consum: QE nua del silici,
   T×QE sistèmica, resposta RAW verda, o una mesura per canal/espectre?
3. Existeix una font pública homogènia que doni valors comparables per a totes
   aquestes càmeres? Si no, proposa el protocol mínim per mesurar `eta_rel`
   amb RAWs i una càmera de referència.
4. Pots aportar valors o intervals específics per model? Només si són
   defensables i amb URL directa; si no, marca `ND`.
5. Cal una columna separada a 656.3 nm per H-alfa? Com tractaries una càmera
   modificada i una no modificada?
6. Amb la informació disponible, pot la QE alterar materialment el rànquing
   basat en `t+5%`? Identifica quines diferències són robustes i quines no.
7. Audita dos errors possibles:
   - confondre BSI/stacked amb una QE numèrica determinada;
   - afirmar que el binning de programari d'una càmera de molts MP millora per
     si sol la relació entre read noise i soroll de cel.

Retorna: veredicte, correccions, taula camera/eta/qualitat/font, protocol de
mesura i efecte sobre la decisió. Separa fets, inferències i incertesa.
