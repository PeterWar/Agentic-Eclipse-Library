# Propuestas para Eclipse Image Processor tras estudiar Agentic Eclipse Library

> Historical report. This document preserves its original research, measurements and implementation context. Controls, defaults, sequential processing and export behaviour described below may have changed. Use the [current technical guides](README.md) and [validation boundaries](validation.md) for the active application.

Revisión del 17 de octubre de 2026. **Propuestas y experimentos; no se han cambiado
los filtros de la aplicación.** Las modificaciones de nombre y empaquetado que ya
estaban pendientes permanecen separadas de este estudio.

## 1. Conclusión y orden recomendado

Incorporaría ideas de AEL, pero no sustituiría el motor actual por esa biblioteca.
La mejora más convincente es **RHEF con estadísticas continuas en radio**. Después,
añadiría **NRGF continuo**, una infraestructura explícita de máscaras y geometría,
y dos herramientas de detalle: **multiescala sobre residuo radial** y **realce
tangencial**. Mantendría el WOW actual basado en `watroo`, incluido el modo bilateral
que has escogido por defecto. El WOW bilateral de AEL no es equivalente y tiene
un fallo de inversión de detalle que he reproducido.

Para elegir, agruparía las variantes dentro de cada familia, no como una lista de
16 interruptores. Los ajustes actuales conservarían su comportamiento y sus
identificadores; las nuevas variantes empezarían como opciones adicionales.

| Prioridad | Propuesta | Beneficio esperado | Condición para aceptarla |
| --- | --- | --- | --- |
| P0 | Máscaras, geometría y una sola tubería de preview/export | Evitar contaminación del limbo y divergencias de implementación | Identidad del modo actual y pruebas de escalado |
| P1 | RHEF continuo global; después sectores de 60°/30° | Reducir anillos y ofrecer contraste local angular | Control de anillos, señal inyectada y ausencia de costuras |
| P1 | NRGF continuo estándar/robusto, con entrada lineal o log | Alternativa más sencilla que FNRGF para el gradiente radial | No inventar estructura en un perfil radial y conservar señal tenue |
| P2 | Detalle isotrópico multiescala y tangencial | Sacar filamentos sin depender de un orden Fourier alto | Halos, orientación, soporte y signo del detalle |
| P2 | WOW con control de ruido por escala | No amplificar tanto el grano de un apilado correlacionado | Región de ruido válida y controles con ruido correlacionado |
| P2 | Mezcla de capas y mapeo de detalle separado del algoritmo | Combinar una base natural con detalle regulable | Neutralidad de la capa y ausencia de recorte oculto |
| P3 | Color medido, vista polar y herramientas de cielo | Conservar cromosfera y diagnosticar artefactos | Entrada y linealidad declaradas; no deducir calibración que no existe |
| Investigación | FNRGF continuo/parcial, NAFE y SWAP | Opciones adicionales para casos concretos | Validación nueva; no serían reemplazos automáticos |

## 2. Qué he revisado y qué he ejecutado

Repositorio AEL: [revisión exacta 5629b37071ec87a32f3cf37b5ce6dfcc8b02ada1](https://github.com/PeterWar/Agentic-Eclipse-Library/tree/5629b37071ec87a32f3cf37b5ce6dfcc8b02ada1),
versión del paquete 1.3.2. Comparación con los algoritmos locales y el historial
local en `9e09b1854d408f123c08b7b292b2f34dd2273c7c`, más los cambios pendientes de
nombre/empaquetado. No he instalado su plugin ni sustituido dependencias.

He leído el código del banco portátil y sus primitivas, estadísticas radiales,
normalización, geometría, transformaciones polares, presentación, controles y
pruebas relevantes. También he seguido las referencias hacia implementaciones
históricas de NRGF/RHEF/FNRGF, MGN, WOW, el precursor circular, NAFE y SWAP. Los
scripts históricos dependen de rutas, constantes, datos o bibliotecas nativas del
autor; los he estudiado, no los he ejecutado como si fueran portables.

Las fuentes principales son [filters.py](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/5629b37071ec87a32f3cf37b5ce6dfcc8b02ada1/ael/filters.py),
[filterbank.py](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/5629b37071ec87a32f3cf37b5ce6dfcc8b02ada1/ael/filterbank.py),
[radial.py](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/5629b37071ec87a32f3cf37b5ce6dfcc8b02ada1/ael/radial.py)
y la distinción del propio autor entre [capas publicadas y biblioteca](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/5629b37071ec87a32f3cf37b5ce6dfcc8b02ada1/docs/PAPER_AND_LIBRARY.md).
No son intercambiables: las recetas portátiles no reproducen píxel a píxel su
imagen publicada.

Comprobaciones realizadas:

- **81 pruebas de AEL pasan; 3 se omiten** porque no está instalado `psd-tools`.
  Las tres son de Photoshop/PSB, por lo que no afirmo haber validado ese formato.
- **Las 51 pruebas de tu aplicación siguen pasando.** Estabilidad numérica no
  equivale a demostrar fidelidad estructural; hacen falta los controles nuevos
  descritos más abajo.
- Las **16 recetas AEL** se ejecutaron sobre tu TIFF reducido a 512 px. A 1500 px
  se comprobaron ocho recetas representativas y tres filtros actuales.
- Se midieron anillos sobre un perfil conocido, respuesta a detalle tenue,
  independencia respecto al contenido almacenado fuera de la máscara y cambios
  al expresar los datos en distintas unidades.
- Se comparó WOW en **12 condiciones físicas**: Luna centrada/descentrada,
  ruido 0/0,3/1 %, y dos frecuencias angulares. Cada caso incluye la escena base
  y la misma escena con una señal conocida añadida.

Entorno: Apple Silicon, Python 3.14.8, NumPy 2.5.4, SciPy 1.18.1, OpenCV 5.0.0,
PySide6 6.12.0 y watroo 0.0.4. Los tiempos siguientes son una medición por caso,
no un benchmark estadístico ni una comparación a igual definición matemática.

## 3. El banco de 16 recetas: qué contiene realmente

| Familia | Recetas AEL | Diferencia principal |
| --- | --- | --- |
| NRGF | `nrgf`, `nrgf_log` | Valores originales frente a logaritmo; perfil continuo robusto |
| RHEF | `rhef`, `rhef_upsilon`, `rhef_local60`, `rhef_local30` | Anillo completo o sectores solapados; curva Upsilon opcional |
| Detalle angular | `achf_angular`, `achf_angular4`, `achf_angular8` | Pasa-alto tangencial de 1° con suavizado adicional de 0/4/8 px |
| Detalle isotrópico | `achf_iso_01`, `_04`, `_05`, `_06` | Diferentes escalas y suavizados sobre un residuo log-radial |
| Multiescala | `mgn`, `wow`, `wow_bilateral` | Tres procedimientos de normalización/realce, con presentación propia |

No hay un FNRGF mantenido dentro de ese banco. Existe un experimento histórico
que conserva solo el dominio angular suficientemente observado. Esto es relevante
para tu petición de extender FNRGF hasta la diagonal: alcanzar las esquinas no
significa disponer de un anillo completo.

## 4. RHEF: la propuesta que probaría primero

Tu `rhef_normalize` ordena intensidades dentro de cada anillo y obtiene rangos
exactos con empates promediados. Al cruzar a otro anillo cambia de golpe la
población de comparación. El filtro puede ser finito y estable, y aun así generar
bandas sobre un gradiente pronunciado.

AEL mide **257 cuantiles de log-intensidad por celda**, interpola las distribuciones
en radio y, en la variante local, también en ángulo. Después invierte esa
distribución interpolada para obtener el rango del píxel. No desenfoca la imagen:
interpela la estadística usada para transformarla. Los vecinos despoblados no se
convierten en observaciones inventadas.

**Resultado reproducido:** escena r^-3 con estructura angular del 2 %, radio solar
120 px, imagen 660 × 660. Misma medida de ondulación radial y rangos de salida
comparables, sin Upsilon:

| Operador | Perfil pronunciado | Entrada aplanada de control |
| --- | ---: | ---: |
| RHEF actual, anillos de 2 px | 0,17346 | 0,01973 |
| RHEF continuo de AEL | 0,01625 | 0,01980 |

En esta escena, la medida de anillos cae aproximadamente **10,7 veces** y queda
cerca del nivel del control de muestreo. No extrapolaría ese factor a cualquier
fotografía. El continuo aproxima los rangos mediante cuantiles; no promete
identidad con el ordenamiento exacto actual.

Interfaz propuesta dentro de RHEF:

- `Actual / compatible`.
- `Continuo — anillo completo`.
- `Continuo — local 60°` y `Continuo — local 30°`.
- Upsilon activable con exponentes bajo/alto enlazados por defecto; separarlos
  en controles avanzados. Tu motor ya admite `upsilon_h_val`, aunque la GUI solo
  expone un exponente.

El local de 30° da más contraste fino, pero puede reducir diferencias amplias
entre direcciones. No es una mejora universal del global: conviene mezclarlo
suavemente con una base que mantenga las grandes estructuras. Tampoco elimina
ruido por el mero hecho de ordenar intensidades.

Implementación pensada: conservar `rhef_normalize`; añadir un núcleo
`rhef_continuous_normalize(..., valid, bin_px, sector_deg, quantile_count)` y un
helper explícito `apply_upsilon(q, low, high)` con transición en q=0,5. El nuevo
backend debe reconocer datos no positivos como un dominio especial del modo log,
no desplazarlos o eliminarlos silenciosamente después de restar cielo. Las
variantes log/asinh, si se estudian, deben tener nombres y pruebas distintos.

## 5. NRGF: añadirlo, no confundirlo con FNRGF

El [NRGF original](https://arxiv.org/abs/astro-ph/0602174) sustrae un perfil radial
y normaliza su dispersión. FNRGF añade dependencia angular mediante Fourier.
Disponer de ambos permite elegir cuánto contraste angular modificar sin obligar
a subir el orden de Fourier.

El NRGF 1.3.2 de AEL tiene más elaboración que interpolar medias de anillos:

1. Nodos en el radio medio realmente observado de cada anillo.
2. Corrección de pendiente y curvatura antes de medir el nivel.
3. Perfil local Hermite; dispersión positiva interpolada en log con PCHIP.
4. Modelos lineal/log/asinh para el perfil, elegidos mediante ajuste.
5. Rechazo de anillos sin dispersión angular medible, empates dominantes y tramos
   con menos de cuatro anillos. Estos píxeles quedan sin resultado de filtro.

No copiaría únicamente el suavizado de nodos: las pruebas del proyecto muestran
que un suavizado gaussiano del perfil puede introducir sesgo y anillos. Tampoco
ocultaría que el operador tiene límites en soles pequeños, perfiles con cambios
muy rápidos y anillos parcialmente observados. Su
[validación 1.3.2](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/5629b37071ec87a32f3cf37b5ce6dfcc8b02ada1/docs/VALIDATION_1.3.2.md)
los documenta; no es una certificación independiente.

Variantes propuestas: `NRGF continuo — media/STD`, `NRGF continuo — mediana/MAD`,
y una opción avanzada de entrada lineal/log. Robusto puede ser un buen valor
inicial nuevo, pero preservaría la versión estándar para comparación. Un anillo
sin resultado conservaría la base al mezclar; no se rellenaría con una corona
sintética ni se pondría negro por defecto.

Para FNRGF conservaría `Actual estabilizado`. Como investigación añadiría
`Continuo experimental`, interpolando los coeficientes estadísticos entre radios
y regularizando la dispersión positiva. En anillos parciales habría que elegir
explícitamente entre dominio completo, ajuste ponderado con control de
condicionamiento, o retorno a la base. **No basta con interpolar sectores vacíos
como ceros**. Un ajuste parcial de Fourier puede no estar determinado aunque el
número total de píxeles sea grande; hay que controlar cobertura y condición del
sistema. Esta variante requeriría validación propia, no llamarla reproducción del
[FNRGF publicado](https://doi.org/10.1088/0004-637X/737/2/88).

## 6. WOW: mantener watroo y estudiar el ruido, no cambiar de bilateral

Tu aplicación utiliza el backend de los autores `watroo`. AEL incluye otro WOW,
con starlet, máscara, suelo de ruido y, en sus recetas, sustracción previa de una
spline radial sobre ln L. Su bilateral añade pesos y correcciones particulares.
El mismo nombre no garantiza la misma operación.

**Pruebas propias de signo:**

| Variante | Correlación mínima–máxima con la señal añadida | Casos con signo invertido |
| --- | ---: | ---: |
| AEL WOW de su receta | 0,687–0,954 | 0/12 |
| AEL bilateral de su receta | −0,266–0,054 | 8/12 |
| watroo estándar, salida del núcleo | 0,634–0,895 | 0/12 |
| watroo bilateral, salida del núcleo | 0,396–0,921 | 0/12 |

Estas no son cuatro variantes matemáticamente iguales: comparan recetas distintas
y un mismo objetivo de conservar el signo. La escena física usa una Luna oscura;
no se alimenta al filtro sin máscara con los valores brillantes ocultos bajo la
Luna en la escena de referencia de AEL. Al hacer eso, la comparación de un filtro
sin máscara queda dominada por datos que para AEL no existen; es un contraejemplo
a una comparación ingenua, no un fallo demostrado en una fotografía real.

La inversión de AEL ya está reconocida en sus
[lecciones de campo](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/5629b37071ec87a32f3cf37b5ce6dfcc8b02ada1/docs/FIELD_LESSONS.md#reproduced-in-the-package-and-not-fixed-yet).
Su batería de 84 pruebas **excluye expresamente** el bilateral de la prueba de
transferencia de detalle y de algunas comprobaciones sectoriales. Por eso
81 pruebas aprobadas no significan que este problema esté resuelto.

Lo que sí incorporaría es medir el ruido por escala, especialmente en apilados:
registrar, interpolar y apilar correlaciona el ruido. En un control blanco, los
factores medidos coinciden aproximadamente con los teóricos. Al correlacionarlo
con un gaussiano de sigma 0,8 px, la distribución relativa en las escalas 2–4
resulta 3,2–4,5 veces la referencia blanca; con sigma 1,5 llega a 7,2–17,7 veces.
La normalización de esta estimación usa la primera escala: no son mediciones
fotométricas independientes de la varianza del sensor.

Propuesta: conservar `WOW estándar` y `WOW bilateral` actuales; añadir como
experimental `WOW con suelo de ruido por escala`, preferiblemente estándar antes
que inventar otro bilateral. Parámetros: escalas/pesos, región de ruido o mapa
externo, suelo de ruido y umbral suave. No interpretar automáticamente una región
con corona tenue como ruido ni extrapolar escalas grandes sin declararlo.

La aplicación a ln L menos perfil radial puede dar un estilo útil, pero es un
preprocesamiento separado, no una corrección del WOW original. Validarlo con
limbo descentrado antes de ofrecerlo como predeterminado.

## 7. MGN, ACHF y nuevos realces de detalle

### MGN

Conservaría tu MGN compatible. La mejora útil de AEL es la convolución normalizada
sobre datos válidos y las escalas/pesos configurables. Su gaussiano grande usa
reducción de resolución y reconstrucción; es una aproximación de rendimiento, no
un reemplazo exacto de SciPy. Un backend `MGN con máscara` debería mantener una
ruta exacta y probar cualquier ruta rápida cerca de los umbrales de decimación.

No copiaría sus constantes absolutas sin revisar: en un ensayo de unidades, su
receta MGN cambió hasta 0,012 en la capa [0,1] al multiplicar la entrada por 1e-8.
Tu motor ya tiene protecciones de unidades que conviene conservar. La diferencia
no invalida todo MGN: es una limitación concreta de esa implementación y escena.
La referencia científica es [Morgan y Druckmüller, 2014](https://arxiv.org/abs/1403.6613).

### ACHF y detalle isotrópico

Tu ACHF actual usa un kernel circular adaptativo, acepta vecinos opuestos y
protege la separación de regiones. AEL `achf_isotropic` sustrae un perfil radial
en log, promedia varios pasa-altos gaussianos y suaviza el resultado. Ambos son
realces de detalle, pero **no son el mismo ACHF**.

Mantendría `ACHF adaptativo actual` y añadiría una sección o variante denominada
`Detalle isotrópico multiescala`. Sus cuatro recetas pueden resumirse en presets
Fino/Medio/Grueso con escalas visibles en avanzado. La opción `_04` usa
1/2/4/8/16 px y suavizado final 1,5 px; las otras cambian escalas y suavizado.
No pondría cuatro controles independientes con nombres crípticos.

En tu TIFF, las capas isotrópicas calculadas directamente con sus presets muestran
halos y saturaciones muy fuertes cerca de la Luna. Son capas de detalle, no
imágenes finales a adoptar al 100 %. El autor atribuye parte de los problemas al
perfil radial estimado en anillos parciales; enmascarar el resultado después no
corrige ese sesgo en la estimación. Exigiría controles de Luna descentrada,
prominencias y un borde recto de cobertura antes de ofrecer esa combinación.

### Detalle tangencial

Un pasa-alto a lo largo del arco puede destacar rayos finos sin aplanar de la misma
forma la estructura radial. AEL lo calcula en coordenadas polares: sustrae una
media angular, respeta la periodicidad en 0°/360° y vuelve a la cuadrícula original.
Su versión sin suavizado obtuvo correlación 0,982 con el detalle inyectado de la
escena de referencia. Esa cifra no significa superioridad general.

Control principal en grados; escalas de suavizado en píxeles; centro solar
explícito. Mostrarlo como `Detalle tangencial`, no como copia exacta del ACHF
adaptativo. No usar un polar enorme fijo: elegir muestreo por radio y comprobar
el viaje polar→cartesiano para limitar aliasing y costuras.

### Otras ideas estudiadas

- **Starlet con pesos por escala:** base práctica para un detalle multiescala
  transparente y para diagnosticar ruido. Puede compartir infraestructura con
  WOW sin presentarse como el mismo algoritmo.
- **NAFE:** aparece en scripts históricos y requiere una implementación nativa
  para rendir bien. Interesante, pero pospondría su integración por coste,
  dependencia del parámetro de ruido, compilación para macOS/Windows y necesidad
  de revisar la procedencia/licencia de la referencia de terceros.
- **SWAP:** el propio piloto histórico lo trata como transferencia experimental
  de EUV a luz blanca. No lo priorizaría para tu objetivo.
- **Larson–Sekanina:** puede crear copias laterales claras/oscuras de un rayo.
  Si se añade, separado y desactivado por defecto; no como supuesto recuperador
  de estructura real.

## 8. Máscaras, geometría, color y presentación

### Tres conceptos distintos de máscara

Propondría separar **datos observados**, **selección de aplicación** y **soporte
válido del resultado**. La Luna puede contener datos reales de luz cenicienta:
excluirla del filtro coronal no significa declarar que esos píxeles no existen.

Para un gaussiano sobre una máscara M:

`media = G(I · M) / G(M)`

Solo se produce una estadística cuando hay soporte suficiente. Rellenar con cero
es correcto dentro del numerador acompañado de ese denominador; no lo es pasar
una imagen con agujeros rellenados de cero a un filtro ordinario y considerar el
borde una observación. La región de aplicación se combina al final con la base.

En los 16 filtros AEL, cambiar los valores guardados fuera de una máscara de
prueba por 1e20 dejó idéntico el resultado dentro de ella y no produjo píxeles
finitos fuera. El angular conservó aproximadamente el 95 % del soporte en ese
pequeño ensayo por las interpolaciones necesarias: también hay que medir lo que
se pierde, no solo lo que no se inventa.

### Sol, Luna y escalas

AEL distingue centro/radio solar y lunar. Tu app usa la geometría detectada de la
Luna como referencia para los filtros radiales. Es una aproximación práctica,
pero no demuestra que los dos centros coincidan. Mantenerla por compatibilidad y
permitir un centro solar independiente en avanzado sería útil.

Usaría coordenadas flotantes y la transformación de centro de píxel de OpenCV:
`x_preview = (x_full + 0.5) · escala_x − 0.5`, e igual para Y con su propia escala.
Evita usar la relación de alturas para todo en imágenes rectangulares con
redondeo. La nueva geometría también daría el radio hasta la esquina más lejana
cuando el centro esté desplazado; esto es distinto de la semidiagonal centrada
que solicitaste para el límite actual.

Su `fit_limb` ofrece refinamiento subpíxel, ajuste geométrico robusto, exclusión de
ángulos con prominencias y un RMS del borde. Lo tomaría como segunda fase después
de tu Hough inicial, devolviendo incertidumbre y sin sustituir un centro manual
silenciosamente. No he establecido un centro solar independiente de tu TIFF.

### Color y linealidad

Tu cargador convierte RGB a mono. AEL conserva cromaticidad medida y aplica el
detalle a luminancia. Propondría preservar `source_rgb` y una luminancia de trabajo,
con opciones mono/conservar color y protección de cromosfera. Hay que controlar
RGB frente a BGR en la ruta OpenCV: sus archivos decodificados no usan el mismo
orden de canales que TIFF/Pillow. No usaría un tinte como supuesto color físico.

Tampoco he demostrado que el TIFF facilitado sea radiométricamente lineal. Los
modelos de cielo/extinción deben distinguir un stack lineal de una edición ya
procesada. No aplicar por defecto una calibración física a una imagen de estado
desconocido.

### Capas, unidades y tonos

AEL suele producir capas centradas en 0,5 y mezclarlas con Multiply/Overlay;
tu motor ejecuta filtros secuencialmente y mezcla salidas en unidades de entrada.
Un resultado atractivo de una capa no autoriza a insertarlo directamente como
intensidad para el siguiente filtro.

Separaría el núcleo de la presentación: salida con unidad conocida
(intensidad/rango/detalle adimensional), transformación de visualización y mezcla.
Mantendría el modo actual, y añadiría una mezcla de detalle centrada, con cero
neutral, junto a una base inalterada. El tanh robusto de AEL puede ser una opción
suave frente al min/max, pero no lo haría automático ni ocultaría que comprime
contraste. Primero validaría la mezcla en gris; el color viene después.

AEL contiene una idea de soft-log para valores negativos tras restar cielo. He
reproducido cancelación numérica en su implementación: con señal -10000 y suelo 1
produce -Inf. No copiar esa expresión directamente. Su equivalente estable es
`log(suelo) + asinh(señal / (2 · suelo))`, con suelo positivo y aritmética validada.

La resta de cielo debe ser una herramienta opcional con regiones elegidas y
comprobación fuera de las regiones de ajuste. En tu imagen el campo ronda seis
radios solares hasta las esquinas; no se puede asumir que el cielo más allá de
6–7 radios esté disponible ni libre de corona. El modelo puede sustraer corona
real. La corrección de extinción necesita geometría/fecha/sitio y datos apropiados;
la dejaría para una fase posterior.

## 9. Cómo cambiaría el código

Propuesta de estructura; estos archivos nuevos todavía no están implementados:

```text
core/
  geometry.py             # centros flotantes, mapas, transformación preview/full
  image_state.py          # valores, RGB opcional, máscaras, ruido y versión
  masked_ops.py           # convolución normalizada y soporte
  radial_continuous.py    # NRGF y RHEF continuos
  detail_filters.py       # isotrópico/tangencial/starlet
  filter_registry.py      # identificadores de familias y variantes
  pipeline.py             # ejecución única para preview y exportación
  presentation.py         # mapeo y mezcla explícitos
  filters.py              # compatibilidad con funciones actuales y FilterWorker
```

El registro tendría especificaciones estables, por ejemplo `rhef.legacy.v1`,
`rhef.continuous.v1`, `rhef.local.v1`, `nrgf.continuous.v1`, `wow.watroo.v1`,
`wow.noise-aware.experimental`, `achf.adaptive.v1` y `detail.tangential.v1`.
Los parámetros no se identificarían por el texto traducido de un desplegable.

Un contrato posible es:

```python
result = operator.evaluate(image, context, parameters)
# result.values: matriz
# result.valid: dónde el operador pudo calcular un valor
# result.units: intensity / rank01 / normalized_detail
# result.diagnostics: cobertura, regularización, parámetros efectivos
```

`FilterWorker` seguiría proporcionando las señales Qt, pero llamaría al mismo
`execute_pipeline` que la exportación. Ahora esas secuencias están duplicadas en
`core/filters.py` y `gui/app.py`; cada variante nueva multiplica el riesgo de que
se configure de forma diferente en ambas.

El contexto de resolución debe declarar qué escalar:

| Parámetro | Política |
| --- | --- |
| Sigma espacial, soporte circular y ancho RHEF | Escalar píxeles según preview/full |
| Radio en R_sun, Fourier Order, Upsilon y grados tangenciales | Mantener valor adimensional/angular |
| Número de anillos FNRGF | Conservar el recálculo solicitado: más anillos al exportar; documentar que no es la misma discretización física que mantener el número fijo |
| Ruido local y por escala | Reestimar a esa resolución; no escalar una sigma de preview como si fuera un radio |
| Soporte y cobertura | Evaluar con la máscara a esa resolución, sin convertir interpolación en observación |

La tabla de variantes de GUI viviría en una fábrica compartida, no en más bloques
condicionales duplicados. Controles avanzados solo para la variante seleccionada;
300 ms de pausa de edición se conservan. RHEF local a 1500 px puede tardar varios
segundos, así que cachearía geometría y tablas por versión de entrada/máscara y
parámetros, y descartaría resultados obsoletos mediante un identificador de
petición. Invalidar toda la cadena posterior cuando cambie una etapa anterior.

También guardaría una receta JSON con versión de cada operador, geometría,
máscaras, políticas de escala y presentación; acompañaría al TIFF sin cambiar
el formato de imagen. Esto hace reproducibles una comparación y una exportación.

## 10. Coste medido con tu imagen

Tiempo de una evaluación de receta a 1500 × 1500; excluye escritura y GUI:

| Receta | Tiempo aproximado |
| --- | ---: |
| NRGF continuo AEL | 1,22 s |
| RHEF continuo global AEL | 1,53 s |
| RHEF local 30° AEL | 4,44 s |
| Detalle isotrópico `_04` AEL | 0,26 s |
| Tangencial AEL | 0,25 s |
| MGN AEL | 0,22 s |
| WOW AEL | 0,45 s |
| WOW bilateral AEL | 2,17 s |
| FNRGF actual, configuración del ensayo | 0,38 s |
| RHEF actual | 0,29 s |
| WOW bilateral actual, seis escalas | 1,20 s |

No son definiciones equivalentes. AEL mide y presenta una capa, puede usar
aproximaciones gaussianas y excluye la Luna; los wrappers actuales tienen otro
mapeo y dominio. No usar esta tabla para afirmar que una implementación es un
cierto número de veces mejor que otra.

La geometría del ensayo real supuso Sol=Luna detectada (1154, 1150, radio 272 px
en el original); no es una medición solar independiente. En las recetas AEL se
excluyó el interior lunar y un margen del 3 %. Las comparativas gráficas muestran
capas con escalas de presentación diferentes, **no una clasificación de calidad**.

## 11. Plan de entrega y criterios de aceptación

**Entrega 1: infraestructura compatible.** Extraer geometría y ejecución común,
mantener todos los resultados actuales mediante adaptadores, introducir máscaras
sin confundir datos observados y selección. Pruebas de identidad en ausencia de
máscaras y exportación de las mismas recetas en dos resoluciones.

**Entrega 2: RHEF continuo global.** Comparación A/B contra actual, mismo TIFF,
misma política de mezcla y congelando umbrales antes de evaluar. Añadir después
local 60°/30° y Upsilon asimétrica. No cambiar el predeterminado hasta revisar
fotografías y controles, no solo medidas de una escena sintética.

**Entrega 3: NRGF y detalle tangencial.** Añadir operadores por separado; conservar
el FNRGF actual. No activar una cadena de varios filtros nuevos simultáneamente
al compararlos.

**Entrega 4: ruido multiescala e isotrópico.** Primero controles con ruido blanco y
correlacionado y máscaras de ruido explícitas; después el preprocesamiento
log-radial. El bilateral AEL no entra en esta entrega.

Para cada variante exigiría:

- Perfil radial sin estructura: no rayos/costuras reproducibles ni anillos por
  encima del control de muestreo que corresponda. Separar promedio anular y
  sectores: un artefacto angular puede cancelarse en un promedio completo.
- Dos realizaciones independientes de ruido: la estructura artificial fija al
  operador no debe correlacionarse como si fuera señal real.
- Detalle tenue positivo y negativo inyectado, con signo, amplitud y cobertura;
  recuperar píxeles no basta si el filtro invierte la señal.
- Luna descentrada, prominencias, cobertura rectangular, huecos y anillos
  parciales; pruebas tanto junto al limbo como lejos de él.
- Constantes, empates/cuantiﬁcación, saturación, negativos tras restar cielo,
  intensidades muy pequeñas/grandes y entradas RGB/BGR conocidas.
- Cambios entre parámetros vecinos y transiciones discretas: Fourier 15/16 y
  31/32, cambios de escalas, anillos y umbrales de vecinos de ACHF.
- Comparación preview/export con política explícita; tiempos y memoria máxima.
- Controles positivos de fallo: inyectar un anillo, una costura o una inversión
  de signo y demostrar que la medida los detecta.
- Evaluación con imágenes adicionales no usadas para ajustar el algoritmo. Tu
  TIFF sirve para explorar, pero no puede ser el único juez de una variante.

Las pruebas de referencia actuales seguirían separadas de las de presentación:
una nueva mezcla no debe permitir que una alteración incorrecta del núcleo pase
desapercibida.

## 12. Artefactos y reproducción

Se han guardado resultados locales bajo `build/research/ael-review/` (excluido de
Git): `metrics.json`, `followup.json`, `upstream-tests.log`, las hojas
`ael-layers.png` y `app-layers.png`, y `reproduced.json`. Las hojas pueden mostrar
tu fotografía: no se han subido a ningún servicio ni incorporado al código.

El script de investigación `scripts/research/compare_ael.py` no modifica filtros
y usa una descarga externa de AEL. Para repetir los controles principales:

```bash
git clone https://github.com/PeterWar/Agentic-Eclipse-Library.git /tmp/ael-review
git -C /tmp/ael-review checkout 5629b37071ec87a32f3cf37b5ce6dfcc8b02ada1
.venv/bin/python scripts/research/compare_ael.py \
  --ael-root /tmp/ael-review --upstream-tests
```

Añadir `--image '/ruta/al/original.tiff' --sizes 512 1500` para generar capas y
medirlas sobre una imagen. Este camino presupone TIFF mono o RGB H×W×3, no es un
cargador universal de todos los formatos de la aplicación. No instala AEL en
`.venv` ni necesita instalar `opencv-python-headless` junto a tu OpenCV actual.

El script usa escenas/helpers privados de la revisión fijada de AEL, adecuados
para reproducir este estudio; no serían una dependencia de producción.

## 13. Licencia y procedencia

El paquete AEL declara MIT, copyright 2026 Pere Guerra Serra. Si se adapta código,
conservar su aviso/licencia en `THIRD_PARTY_NOTICES` y citar las publicaciones de
los métodos; no confundir el crédito al software con la autoría científica.
El código histórico puede incorporar material de terceros: revisar cada
procedencia antes de reutilizarlo, especialmente la referencia NAFE. No he
redistribuido AEL dentro de la app ni añadido una dependencia de producción.

La revisión apoya adoptar **RHEF continuo y NRGF** primero; ampliar después el
realce de detalle. Las máscaras, los controles estructurales y una presentación
explícita aportan más que multiplicar presets sin medir qué hacen.
