# 166 — La deflexió gravitatòria amb les dades del 2026: idea abandonada (18-09-2026) i què cal fer el 2027

**Decisió de Pere (18-09-2026):** «anem a abandonar aquesta idea, deprecar-la del paper i treure les marques del Photoshop; anotar-ho com a futura investigació quan preparem l'eclipsi de 2027». Aquest document és aquesta anotació.

## Què es va intentar el 18-09
1. Anotar a la imatge de l'APOD les quatre estrelles més interiors (HIP 46335, 46635, 46345, 46397; 2,2–3,3 R☉) amb la deflexió PREDITA per la relativitat general (0,81, 0,74, 0,66 i 0,54″; fletxes ×1000). Versions v3–v9 de `1-PHOTOSHOP/APOD_anotada_*.psd`. Retirat a la v10.
2. Pere va demanar ensenyar-ho només a les estrelles «on el centroide s'ha mogut de manera identificable». Anàlisi per estrella sobre les dades natives de l'estudi V2 (`IA/output/apod_anotada_20260918/analisi_centroides_per_estrella_20260918/`): amb termes cúbics lliures ajustats a les mateixes estrelles, HIP 46345 dona +0,67 ± 0,26″ però amb placa afí −0,77 ± 0,27″: el signe depenia del model.
3. Camps de calibratge de la MATEIXA NIT trobats a l'escriptori: Sony A7R IIIA + 300 mm a Sagitari (396 × 15 s) i **R6 III + VSD90SS a l'Àguila (572A3170–3175, 6 × 15 s, sensor 36–39 °C, 3 h després de la totalitat)**. Resolts amb un resolutor propi sobre Hipparcos i, amb autorització de Pere, calibrats amb Gaia DR3 (VizieR): distorsió del VSD90SS 12,7″ màx (rms del model 1,26″, 2.674 estrelles), del 300 mm 137″ màx (rms 2,27″, 21.207 posicions); escales nocturnes estables a 10⁻⁵; l'escala del Vixen difereix un 0,19 % de la de l'eclipsi. Tot a `IA/output/apod_anotada_20260918/camps_calibratge_nit_20260918/` (models JSON, scripts, rebuts) i catàlegs a `4-RESULTATS/derivats/Astrometria/Estrelles/catalegs/gaia_dr3_*.csv`.
4. Eclipsi reduït amb la forma de la distorsió fixada i placa afí per fotograma: el soroll radial per estrella al Vixen baixa d'1,42 a 0,57″, però **HIP 46335 −1,56 ± 0,20″ i HIP 46345 −0,87 ± 0,35″ cap ENDINS**, i la Sony (independent) coincideix en el signe. Interpretació: el gradient de brillantor de la corona arrossega el centroide de les estrelles interiors cap al Sol; a 4,4 R☉ el biaix desapareix. El «cap enfora» del punt 2 era un artefacte dels termes lliures.

## Per què s'abandona per al 2026
- Sense camps de calibratge dins de la totalitat no hi ha escala de placa independent (Bruns 2017: camps a ±7,4° durant la totalitat, factor 1,55 en σ(ε)); el sostre queda a ~2σ global (research/77, estudi V2).
- Les estrelles que porten l'efecte (2–3 R☉) tenen un biaix de centroide del gradient de la corona d'1–1,5″, més gran que l'efecte, no modelat.
- La imatge i el paper no han d'insinuar cap mesura: fletxes fora (v10), paràgraf de la secció 6 del whitepaper reescrit (v0.12).

## Què cal fer el 2027 (afegir al pla de research/77)
1. **Camps de calibratge dins de la totalitat**, a banda i banda del Sol (±7°), amb el mateix focus i temperatura: cal control de muntura des de l'app de captura (deute d'enginyeria ja anotat al 77).
2. **Assaig nocturn abans de l'eclipsi** amb els dos trens: distorsió amb Gaia (ja tenim la cadena `calibra_distorsio.py` → `ajust_conjunt.py`), estabilitat de l'escala amb la temperatura (mesurar-la a l'assaig: quantes parts per deu mil per grau).
3. **Centroides interiors amb la corona modelada**: ajustar cada estrella juntament amb un fons local inclinat (o sobre la imatge amb la corona restada) i validar amb injeccions sobre fons real; quantificar el biaix en funció de la distància al Sol.
4. Fotogrames curts i molts (el traç de la muntura era 3 px per exposició el 2026), meteorologia mesurada (T, P) per a la refracció a l'altura de l'eclipsi (37° a Cadis).
5. Lliçons de codi: a 15 s ISO 6400 les Hipparcos saturen (el resolutor ha de rebre els centroides sense refinar); dos processos no poden llegir el mateix CR3 alhora (errors d'E/S de rawpy); PIL no fa antialiàsing (usar cv2 per a les anotacions).

Antecedents: research/77 (pla 2027), research/79, estudi V2 (`4-RESULTATS/relativitat_revisio_20260914/`), memòria de l'APOD (18-09).
