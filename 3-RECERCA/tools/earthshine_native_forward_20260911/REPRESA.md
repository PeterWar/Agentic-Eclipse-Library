# Represa acotada — model natiu del llimb

V49 continua publicada i immutable; aquest pas és diagnòstic. Llegir `output/earthshine_native_forward_20260911/RESULTAT.md` abans de reprendre. Goal actiu, Pere autoritza continuar sense confirmacions. No crear agents nous. No fer servir IA generativa per a la imatge científica.

## No repetir allò ja executat

- A0: operador positiu natiu qualificat per constant, pla, adjunt i refinament. `native_operator.py` integra exactament el píxel sota un nucli gaussià i parteix la quadratura segons l’ocultació observada. Grid de radiància bilineal unitari; GL4; contorn refinat16. Sigma0,97 és una hipòtesi, no una PSF mesurada universal. No hi ha ales àmplies.
- B0:12 jocs de matrius guardats a `matrices/`; mostres `xy,g,variance,weight_variance,q,J,green_plane,raw_relative`. La variància de pesos se suavitza sobre la graella verda; els valors observats no.
- B1 mòbil PASS numèric; B1 estàtic va quedar lleument curt del KKT. **B2_static_refined és el control estàtic convergit**; no usar B1 estàtic com a últim resultat.
- C0: perfils natius complets d’onze preses i24angles. Posicions relatives via30..330°, dreta0/±15° exclosa. Només curts qualificats; llargs censurats sense nova posició. Transladar una vora brillant no equival a registrar la textura lunar.
- C1/C2: sis curts entrenen,2976/2994 reservats a la dreta. Mateixes observacions/pesos/regularització als tres models. Correcció de translació estimada fora de la dreta redueix error449–454 de48,352→1,981 i60,130→35,922, però hi ha regressions en altres bandes. Lluna latent mediana3694→1473G. No promogut. Afegir amplada per presa baixa a522G amb molts negatius no restringits; no és detall recuperat.
- C3: model afí REFUSAT pels nous sectors intercalats. RMSdreta0,340→0,406.199comparacions,39dreta. No tornar a ajustar lliurement una el·lipse ni atribuir-la a refracció sense evidència.
- D0: textura lunar creuada amb tresSonyA, dins0,70R.0/16candidats amb acord suficient. Controls d’equivariança PASS no impliquen registre físic PASS. No aplicar aquests vectors. `reference1/reference2` del fitxer SonyB2 anterior són subplans verds, NO meitats temporals.
- E0: síntesi i figura científica inspeccionada; cap nou PSB. FontsV49/estilCameraRaw/màscara/capes preservats.

## Dos problemes físics que encara no s’han separat

1. El contorn V44 és una mediana de17preses curtes amb residus de posició; no se’ls retirava la translació abans de fer-lo. El registre de textura V44 només afinava exposicions>=1s. Un model amb ocultació fixa i posició exacta per a totes les preses està massa restringit. Però la correcció rígida estimada de la vora tampoc és una solució global demostrada.
2. El nucli gaussià estret no modela les ales de dispersió. Més brillantor latent vora el llimb pot absorbir errors de PSF o geometria. Les prediccions primerenques/tardanes encara divergeixen. L’anàlisi anterior d’ales amb escena congelada no és una inferència conjunta PSF+Lluna+Sol.

Una continuació útil ha de formular una hipòtesi concreta que resolgui aquests dos límits i declarar prediccions noves abans d’ajustar. Evitar tornar a cercar sigmes/translacions/deformacions sobre els mateixos resultats. La injecció de textura i el jutge entre trens segueixen pendents per a qualsevol font latent nova. Cap recompte de matrius o PASS numèric substitueix aquesta validació.

## Coordenades i moviments

ROI lunar1400 a fullcanvas(4677,3077); centre(699,568111973117,699,6475341408573). Pilot observat x1117..1187,y630..770. Nodesfont x1085..1220,y598..803. Camp final10551×7506 intacte.

`solar_center_in_lunar_grid` deB3 antic inclou `native.shift`. Quan es canvien les coordenades per registrar físicament la Lluna, s’ha de transformar també el Sol. C1 treballa amb `xy−pose` per a les dues fonts i moviment solar relatiu d’efemèride sense sumar-hi de nou el desplaçament de registre. No restar shifts indiscriminadament ni modificar les imatges per corregir una fórmula.

Runtime `/Users/USUARI/.venvs/eines-ia-py312/bin/python`, `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1`. El mòdul comprova el claim `CODEX_EARTHSHINE_NATIVE_FORWARD_20260911`; no executar mutacions antigues després del release sense adquirir un claim propi i adaptar-ne explícitament el control. Tots els càlculs han acabat; no hi ha processos o documents de treball propis per recuperar. Cap nova porta Photoshop necessària en aquest pas perquè no hi ha imatge publicada nova.
