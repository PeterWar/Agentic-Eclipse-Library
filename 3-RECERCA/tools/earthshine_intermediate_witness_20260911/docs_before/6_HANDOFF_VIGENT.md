# Handoff — geometria del completat — 2026-09-11T21:34:22.571685+00:00

**V49 vigent i preservada. Assaig de geometria acabat; cap nova font o PSB. Goal global actiu.** No s’ha invocat Photoshop ni alterat Camera Raw. Pere autoritza continuar autònomament amb passos mesurats i sense confirmacions repetides. La millora fotogràfica del llimb complet continua oberta.

Informe `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_completion_geometry_20260911/RESULTAT.md`. Represa `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_completion_geometry_20260911/REPRESA.md`. Manifest `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_completion_geometry_20260911/delivery_manifest.json`. Producte `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V49.psb`, SHA `21896b1b40bfd2ba0c13aec07491bebbaf05f4f91dbe2698957e392b3928bc2d`. Downloads és codi i Desktop són actius. Sense Git, maquinari, agents nous ni generació de textures.

## Evidència que no cal repetir

- Component ampla congelada: p=0,01406309541811233, gaussiana addicional de 12 px, nucli estret retingut. El resultat temporal positiu anterior continua qualificat dins del seu abast; no s’ha refet l’ajust de p.
- A0/A1: referència solar amb 33 curts, excloent els 16 objectius. Registre a 470–650 px amb translació, guany i offset; 15/16 curts coherents entre meitats angulars. 2985 falla (0,419 px). Dels llargs, 2980 passa, 2978 falla (0,489 px), 2983 té suport insuficient. **2983 no té una posició estimada**, no un zero validat. El registrador exigeix almenys 1000 mostres per ajust.
- B0/B1: fase lunar mesurada en verds nadius, amb integració del píxel, component ampla fixada i perfil local de nucli/fons. Només r≥450 px; 435–449 reservat. Una fase angular comuna s’ajusta en 12 curts. Les quatre preses reservades 2967/2985/2997/3003 tenen RMS de predicció 0,545/0,339/0,371/0,520 px. **0/4 passen 0,25 px.** No hi ha un vincle solar-lunar prou precís per assignar automàticament geometria als llargs censurats.
- C0: base, registre solar, fase lunar per presa i fase+amplada. Les quatre variants tenen 24/36 comprovacions positives; **totes les 12 de 435–449 fallen**. Amb la màscara de 2983, la fase mesurada redueix P95 de 133,31 a 53,12 G a 3003, però empitjora 2967 de 40,38 a 94,54 G. Afegir amplada mediana gairebé no canvia res. Límits 5/25 G i 80% de suport intactes. No es promou cap d’aquestes geometries a una font.
- D0: figura inspeccionada i informe. La base reprodueix la ronda anterior amb diferència de correcció <0,008 G per la precisió de l’interpolador auxiliar; conclusions idèntiques.

## Continuació acotada

No repetir desplaçaments globals, el·lipses lliures o ajustos de fase comuns per resoldre aquest residu. Una resposta intermèdia entre nucli≈1 px i ala de 12 px és una hipòtesi nova que es pot comprovar amb diversitat temporal i control angular. La validació ampla anterior a 426–445 no resol per si sola la resposta més propera a la vora. Declarar models i controls abans de provar; no qualificar dades reutilitzades com a verges. Una altra via exigeix suport observat millor per al model solar pròxim, no una continuació més flexible triada pels mateixos errors.

La fase ajustada en un perfil local no és una mesura pura de la topografia: pot confondre protuberància, ales òptiques i fons. La nova prova de completat és withholding espacial dins de cada presa; no valida llargs sense geometria observable. Cap atribució única de l’error demostrada. Cap píxel completat és textura lunar recuperada. Preservar el detall real, les protuberàncies i l’estètica Camera Raw; cap degradat manual.

Z0 ha verificat 83 arrays congelats (67 quincunx i 16 natius), 7 inputs diagnòstics anteriors, originals V46/V47/V48, V49 i 3 XMP. Cap consulta o alteració de documents vius. Càlculs finalitzats; només aquest registrador tanca ara el claim. Handoff explícit, zero processos propis de càlcul o documents de treball. Objectiu encara actiu; no nova porta Photoshop ni equivalència DHS acreditada.
