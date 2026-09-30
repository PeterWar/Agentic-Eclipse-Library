# Handoff — operador natiu i resposta intermèdia — 2026-09-11T22:07:22.677512+00:00

**V49 vigent i preservada. Operador verificat numèricament; correcció fotogràfica nova encara no qualificada. Goal global actiu.** No s’ha invocat Photoshop ni alterat Camera Raw. Pere autoritza continuar autònomament en passos mesurats. Cap equivalència amb DHS ni recuperació de tot el llimb acreditada.

Informe `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_intermediate_witness_20260911/RESULTAT.md`. Represa `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_intermediate_witness_20260911/REPRESA.md`. Manifest `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_intermediate_witness_20260911/delivery_manifest.json`. Producte `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V49.psb`, SHA `21896b1b40bfd2ba0c13aec07491bebbaf05f4f91dbe2698957e392b3928bc2d`. Codi a Downloads; actius a Desktop. Sense Git, maquinari, agents nous o generació de textures.

## Resultats que no cal repetir

- p12=0,01406309541811233 es manté congelat. Hipòtesi declarada: component addicional de 4 px. Vuit RAW entrenen, dotze són comprovacions retrospectives, vuit nous per a aquest ajust proven C2/C3: 2960/2962/2964/2966 i 3012/3016/3020/3024. No són dades verges respecte de tot el projecte.
- A0/B0: testimoni aproximat f4=0,0248282; totes les sis èpoques milloren, però dues no superen el 5% predeclarat. A1/B1: cascada física H12(H4(X)), p4=0,0257283; X reté el nucli estret. Meitats 0,0254048/0,0258031. Millores per èpoques 1/4/6/7/C2/C3: 4,26/9,27/8,31/34,15/1,50/12,45%. Gate global FAIL; no promoció.
- **C0 identifica un error numèric:** amb una escena coneguda, aplicar els termes de la correcció a predictors interpolats deixa RMS 5,67/5,74 G al contorn (límit 2 G). Convolucionar directament sobre la graella verda u,v de pas √2, amb sigma/√2, dona RMS≈0,00093 G. Textures conegudes de 8/16/32 px conservades en dues fases. Fantomes només de validació, mai font lunar.
- D0 reconstrueix 28 camps natius complets amb calibració existent. **3202063 mostres** congelades coincideixen exactament en radiància, variància, qualitat, validesa i coordenades; 28 SHA de RAW iguals. Caches `D0_native_field_*.npz` reutilitzables, sense interpolar radiància. No repetir la lectura/calibració.
- D1/E0 controla la predicció del propi soroll: cada verd usa termes òptics de l’altre verd. Dues files per cel·la es mantenen separades fins al score. p4=0,02714295880522035; meitats 0,0260299/0,0276471. Millores 1/4/6/7/C2/C3: 3,26/5,29/5,53/24,46/0,53/7,98%. 71/72 sectors no empitjoren més d’un 2%, però només 4/6 èpoques superen 5%; gate global FAIL. El senyal intermedi no desapareix amb aquest control, però no és suficient per publicar la correcció.
- C1 valida numèricament el verd oposat al p4 anterior. **C2 repeteix al p4 final:** 8/8 PASS, RMS 0,119520/0,149805 G, textures i GL4/GL6 dins dels límits. És qualificació aritmètica, no de la PSF real. Resta de la sèrie E0 ≤0,021906 G; no confondre-la amb error físic.
- F0 és l’informe/figura inspeccionada. Les comparacions interpolat/natiu/crossgreen canvien suport i estadístic: no són una diferència fotogràfica aparellada. Cada percentatge usa el seu propi control zero.

## Continuació concreta

Conservar l’operador natiu i els camps D0. No repetir la correcció intermèdia sobre predictors interpolats. No rebaixar els gates fallats ni barrejar preses llargues sense qualificar amb curtes corregides. Cal resoldre resposta del nucli/ales i completat temporal de les zones censurades abans de construir una nova font o PSB.

Pista física nova F1: el projecte identifica un Vixen VSD90SS; el fabricant declara obertura nominal de 90 mm i focal nominal de 495 mm (`https://www.vixen.co.jp/product/26131_4/`). Provar la difracció de la pupil·la amb l’escala angular **mesurada** de la cadena i un interval espectral declarat pot ser més informatiu que afegir gaussianes lliures. Cal verificar la configuració òptica efectiva; cap Airy s’ha calculat ni aplicat. No ajustar longitud d’ona o geometria per fer desaparèixer el halo dels mateixos targets.

La Lluna conserva radiància desconeguda per cel·la; no forçar-la a zero. Els verds separen fotons però comparteixen calibració/FPN i no substitueixen el jutge entre telescopis. Mantenir els límits de reutilització de dades i de model de llum oculta. No nous retocs manuals del contorn ni modificació de l’estètica de Pere. Una nova font necessita corroboració de textura i, si arriba a PSB, porta Photoshop i recomposició.

Z0 verifica 56 arrays congelats, 28 RAW, originals V46/V47/V48, V49 i 3 XMP. Autoritat preservada abans d’actualitzar. Cap consulta o alteració de documents vius; cap document de treball creat. Tots els càlculs finalitzats. Només aquest registrador tanca el claim amb handoff explícit i zero processos propis de càlcul.
