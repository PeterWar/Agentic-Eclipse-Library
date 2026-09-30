# Represa — V48 vigent; resposta nativa i encaix fotogràfic

Llegir primer l’informe `output/earthshine_joint_20260911/RESULTAT.md` i les autoritats actualitzades. Producte V48 sense canvis; no hi ha V49 publicada. El canvi de visibilitats del document1297 era només una inspecció de Pere: usar la V48 desada com a referència estètica. La còpia viva arxivada no és una nova preferència.

## Resultats que condicionen el pas següent

1. Ja existeix el model per captura amb Lluna i Sol separats. B6 és l’últim assaig, amb8 preses Vixen d’ajust i4 reservades, P64 d’àrea exacta i sigma1,4275159 calibrat sobre una escena sintètica a través del mesurador de perfils. Convergeix; no queda qualificat com a correcció: persisteixen negatius grans i prediccions irregulars. No tornar al B0 estàtic ni repetir una graella de força sense una hipòtesi nova.
2. Dos errors numèrics detectats i controlats: ocultació4×4 massa grollera, corregida per àrea de polígon; eixamplament del mesurador de perfils, qualificat només amb fantoma uniforme. No confondre aquest darrer sigma amb una PSF física nativa ja mesurada.
3. La màscara de V48 hereta un encaix fotogràfic de la V44 ajustat a la resposta tonal de la capa09. **No és només validesa física.** La seva àrea equival a radi455,935, davant453,544 de la silueta observada. Reduir-la geomètricament sense resoldre les respostes crea un anell negre: C2 ho demostra, no promoure aquestes imatges.
4. La V48 desada té una segona font lunar i LROC visibles sota la font principal. C0/C1 les separa nativament. Retirar-les ajuda parcialment la franja, però també canvia la barreja interior i no resol el vel. Cap variant ha substituït V48.

## Prova següent, acotada i encara no feta

Mesurar en CFA natiu la resposta de les captures d’una sola època, començant per2973,2976 i2978, amb les mateixes transformacions i calibració heretades. Comparar explícitament:

- mostres verdes natives amb el peu real del píxel i la validesa de saturació;
- la font remapada ordinària que usa V48;
- la mesura polar/mediana tangencial usada per A0/A4.

L’objectiu és distingir el desenfocament de la captura del que afegeix el mostreig del diagnòstic, i saber què es pot inferir de les preses llargues censurades. A partir0,5 s no hi havia perfils complets qualificats segons A0: no inventar-los ni usar el màxim de l’última mostra vàlida com a vora. Si cal ajustar amplituds compartides o resposta per exposició, declarar la partició de calibració i reservar sectors o captures nous per predicció. No aplicar desplaçaments globals de vora a la textura: aquesta cura ja la perjudicava.

Abans d’una inversió nova cal una afirmació verificable sobre aquest operador. La matriu del model és simètrica amb adjunts comprovats, però la gaussianitat, la silueta òptica, el seeing per captura i les ales àmplies encara són hipòtesis. B5 només prova direccions amb escenes congelades: no és estimació conjunta d’una PSF ni prova que no hi hagi ales.

Una futura correcció fotogràfica haurà de mantenir el CameraRaw de Pere i protegir les fonts solars. No confondre una aparença fosca obtinguda amb C2 amb recuperació lunar. Qualificar qualsevol PSB nou amb porta Photoshop, segon lector i recomposició; el C0 d’aquesta ronda és només una còpia exacta del producte, no un candidat editat.

## Fitxers i execució

Codi `research/tools/earthshine_joint_20260911`, sortides `output/earthshine_joint_20260911`. Python `/Users/USUARI/.venvs/eines-ia-py312/bin/python`; `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1`. Adquirir un claim nou i ajustar explícitament el claim dels scripts propis; no executar constructors històrics que escriuen els seus outputs.

`forward_model.py` conserva per defecte el P4/sigma antic per reproduir B0/B1. B3 passa P64; B6 passa també `forward_sigma` d’A4. L’ordre dels fitxers importa. B1 va arribar al límit1600 per a l’època5; `b1_resume_late.py` reprèn el checkpoint preservat i convergeix42 iteracions després. B6 reprèn B3 i convergeix373 iteracions després. No repetir els jobs per un timeout; tots estan acabats al handoff.

`C1_native_composition_roi.npz` conté quatre RGB16 natius1400²: baseline, without_all_epochs, single_lunar_source, solar_background. La baseline coincideix amb V48 a3 DN16; single es recompon a1 DN16 amb el RGB de la font i la màscara heretada. `C2_geometric_support_probe.npz` està rebutjat visualment per anell negre. Un primer alfa gaussià espectral tenia excursions de4×10⁻⁷ fora[0,1]; la prova C2 es va fer després amb un nucli espacial positiu, sense afectar B6 ni cap foto.

Les fonts88 són les nadiues de V48 a `output/earthshine_detail_20260911/native`. G/W Vixen67 a `compositor_cache`; les posicions solars dels12 fotogrames consten a `output/earthshine_optics_20260911/B3_epoch_stationarity.json`. No fer servir imatges LROC com a entrada de reconstrucció. Font de resposta i límits de saturació: `A3_VALIDESA_I_LINEALITAT.md`.
