# Represa — candidat de dispersió ampla

V49 continua sent el producte; aquest pas no ha alterat imatges. Goal global actiu, autorització desatesa vigent. Informe `output/earthshine_scatter_witness_20260911/RESULTAT.md` i resum `E0_summary.json`. No repetir els fits completats ni buscar de nou un sigma sobre els mateixos jutges.

## Resultat que es conserva

- Candidat `Y=((1−p)I+pG12)X`, amb X que conserva el nucli òptic real. p=0,01406309541811233, sigma addicional12px. No és una PSF única identificada. A0/B0testimoni12/24px, controlgir90°nul, meitats angulars1,356–1,461% aproximadament. B1 ajust físic amb dos instants entrenant i quatre èpoques reservades: millora22,76/21,72/31,65/53,25%;47/48sectors no empitjoren més de2%.
- Inversa nativa: a=p/(1−p); X=(Y−aBY+a²B²Y−a³B³Y+a⁴B⁴Y)/(1−p). B=Gaussian12; B^k és Gaussian12sqrt(k). Resta acotada<0,000801G en aquests camps. El terme Y és la mostra nativa; només els termes amplis provenen de la imatge interpolada. Cap deconvolució de sigma1px.
- C0injecció:8/8PASS, dues fases natives reals2976/2994. Errorbaseline0,539/0,545G RMS; píxelGL4vs6<0,042G. Textures8/16/32px recuperades amb errorrelatiu<0,001%. Fantomes només de prova, mai com a dades lunars.
- Aquesta qualificació és per a dades observades completes. Encara no hi ha una font de67captures corregida ni una nova porta Photoshop.

## Completat de saturació: problema concret pendent

D0/D1:55preses fan camps auxiliars lunar+solar, excloent12targets. Primer model12/36PASS; forats de cobertura i vora lunar observada contaminada reutilitzada com latent. No promogut.

D2:51preses, exclou també2967/2985/2997/3003. Lunar auxiliar=mediana mesurada r<350 (no textura inventada ni reemplaçament de dades), coronal auxiliar=continuació gaussiana sigma4 limitada a8px de suport real. Màscares reals2978/2980/2983, independents del soroll del targetcurt.100%suport,24/36PASS. **Totes12les comprovacions435–449fallen**:medianaabs5,7–11,9G;P95abs38,5–134,5G. Gatesimmutables5/25G. No promoure la continuació auxiliar ni relaxar-ne els límits per obtenir una imatge.

`E1_completion_map_572A2967.npz` i`...572A3003.npz` guarden predicció, llum observada, error, suport i màscara real llarga. `E1_completion_error_maps.json` localitza el residu per24sectors; no s’hi ajusta cap paràmetre. És el punt útil següent per estudiar l’error de geometria/llum, no tornar a executarD0/D2 només per obtenir mapes.

## Proper assaig amb hipòtesi nova

Congelar p i estudiar un model per fotograma que utilitzi la corona no saturada i les restriccions de saturació per estimar la geometria/llum que manca, amb nous targets reservats. Una desigualtat de censura aporta informació, però no autoritza tractar el màxim observat com la vora física. La correcció ampla ja té evidència; la incertesa es concentra en la llum que arriba dels píxels censurats i el model d’ocultació.

No aplicar els vectors de texturaD0 del torn anterior(0/16qualificats), la deformacióafíC3refusada, un retall de màscara o la inversió delHDRestàtic. No barrejar silenciosament curtes corregides amb llargues sense corregir. Una futura correcció només pot modificar mostres realment observades; el completat auxiliar mai es converteix en textura lunar recuperada.

El Sol dels camps auxiliars usa coordenades per captura `solar_center=MC−J*lluna_offset+native.shift`; el remapat solar és només per al model de llum. La Lluna original i la seva geometria fotogràfica no es canvien. D2guarda les51fonts i les16exclusions a `D2_training_sources.json`. D2targets nous són només nous en aquest assaig; comparteixen la calibració històrica i no són independents de tot el projecte.

## Operació

Inputs:67`A0_quincunx_*` i20`A0_native_samples_*` de `output/earthshine_native_psf_20260911`. CapRAWreapilat. Les primeres88fonts i la receptaCameraRaw deV48/V49 continuen congelades. Eines noves sota aquest directori; sortides sota `output/earthshine_scatter_witness_20260911`.

Runtime `/Users/USUARI/.venvs/eines-ia-py312/bin/python`, `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1`. Scripts comproven claim `CODEX_EARTHSHINE_SCATTER_WITNESS_20260911`; adquirir claim propi abans de mutar i adaptar-ne el control explícitament. No invocar constructors antics que sobreescriuen sortides ja enregistrades. Sense Git, maquinari, agents nous o generació d’imatges científiques per IA. Cap procés de càlcul o còpia de Photoshop pròpia pendent.
