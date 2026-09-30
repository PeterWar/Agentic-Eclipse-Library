# Handoff — model natiu del llimb — 2026-09-11T20:28:03.713317+00:00

**V49 continua vigent i immutable. No V50; goal global actiu.** Aquesta ronda qualifica un operador físic natiu i identifica sensibilitat a la geometria, però no promou cap camp latent ni canvi de registre a la fotografia. Pere autoritza continuar en passos mesurats sense confirmacions repetides; els seus canvis vius de V48 eren només inspecció. Originals i estètica Camera Raw preservats.

Informe `/Users/USUARI/Downloads/Eclipse 2026/output/earthshine_native_forward_20260911/RESULTAT.md`. Represa exacta `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_native_forward_20260911/REPRESA.md`. Codi `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_native_forward_20260911`. Manifest `/Users/USUARI/Downloads/Eclipse 2026/research/tools/earthshine_native_forward_20260911/delivery_manifest.json`. Producte `/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V49.psb`, SHA `21896b1b40bfd2ba0c13aec07491bebbaf05f4f91dbe2698957e392b3928bc2d`; la porta Photoshop és la de V49 anterior, no una porta nova d’aquesta ronda. Downloads és codi; Desktop són actius. Sense Git, maquinari, delegació o generació de textura artificial.

## Evidència i límits

- A0: integració positiva sobre CFA natiu, píxel integrat analíticament sota nucli gaussià i cel·les partides per ocultació. Constant/pla/adjunt/refinament PASS. Diferència màxima de quadratura <0,108 G davant un salt 500→100.000 G; no qualifica la PSF física.
- B0/B1: 12 preses primerenques/tardanes, 8 entrenen i 4 reservades; fonts M/C separades, Sol mòbil contra control estàtic. B1 mòbil convergeix sense negatius lunars; estàtic convergit a **B2_static_refined**. Encara falla la predicció dels últims píxels; no hi ha recuperació fotogràfica validada.
- V44 afinava registre per textura només en preses>=1 s; el contorn era una mediana de curtes sense retirar translacions residuals. C0 mesura posicions nadiues fora de la dreta; hi ha residus d’aproximadament1 píxel, però no són una correcció global demostrada.
- C1/C2: 6 curts ajusten, 2976/2994 reservats a la dreta. Translació de l’operador mesurada en altres sectors: error449–454 baixa48,352→1,981 i60,130→35,922 (95,9% i40,3%). **Percentatge d’error del model, no de detall recuperat.** Lluna latent mediana3694→1473 G. Regressió2994 en445–449. Afegir amplada per presa baixa a522 G i necessita molts negatius sense restriccions; no promogut. Tots tres tenen convergència numèrica.
- C3: model afí refusat amb199parelles en nous sectors intercalats; a la dreta RMS0,340→0,406 píxels. No atribuir el resultat a refracció atmosfèrica ni deformar el PSB.
- D0: textura interior creuada amb3presesSonyA, meitats angulars i control conegut.0/16registres compleixen els acords exigits, tot i control d’equivariança PASS. No aplicar-ne vectors. Subplans verds Sony1/2 no són meitats temporals.
- E0: figura científica revisada i resultats guardats. No s’ha invocat Photoshop. Z0:34inputs natius consumits, originalsV46/V47/V48, V49 i3XMP rehash exactes; cap RAW reapilat en aquest pas.

## Continuació sense repetir assaigs

El límit segueix sent separar el senyal lunar real de la dispersió solar i de la incertesa geomètrica. Una nova hipòtesi ha de representar-los conjuntament i declarar prediccions noves/refutables abans d’ajustar. Les ales òptiques àmplies no s’han inferit conjuntament; els sigmes de perfil continuen sent descriptius. No repetir PSF uniforme, translacions de vora lluminosa, inversió del HDR estàtic ni deformació afí contra els mateixos jutges. Injecció de textura i jutge entre trens pendents abans de substituir cap font fotogràfica.

Matrius i mostres ja desades; no reapilar88RAW per reprendre. Respectar el canvi de coordenades comú a Lluna i Sol: `solar_center_in_lunar_grid` antic incorpora `native.shift`; C1 retira aquesta suma del moviment relatiu quan registra amb `xy−pose`. No moure fonts per corregir una fórmula. La màscara V49 heretada és un encaix fotogràfic, no només ocultació física.

Tots els processos de càlcul acabats; cap document de treball propi creat. Handoff explícit, només el registrador tanca ara el seu claim. Goal actiu, sense afirmació de llimb complet ni d’equivalència DHS.
