# Propuesta: grupo «Color Correction» en el PSB

> Historical report. This document preserves its original research, measurements and implementation context. Controls, defaults, sequential processing and export behaviour described below may have changed. Use the [current technical guides](README.md) and [validation boundaries](validation.md) for the active application.

Estado: implementado y comprobado con Photoshop 2026. La casilla «Add Color Correction to PSB (sRGB)» está disponible junto al formato de capas y comienza desmarcada.

## Conclusión

Es viable incorporar una casilla «Añadir Color Correction al PSB», desmarcada inicialmente. La referencia para las capas debe ser la guía de Photoshop. La guía de Lightroom es una alternativa visual, no una segunda receta que deba acumularse sobre la anterior.

Ambas guías describen una interpretación creativa del color y advierten que su receta es una reconstrucción propuesta. No añaden detalle, enfoque, reducción de ruido ni contraste. Por ello, el acabado debe partir de la composición actual de la aplicación, después de sus filtros, estirado y color RGB.

## Capas propuestas

Por encima de las capas existentes se añadiría un grupo «Color Correction», modo **Normal**, opacidad **50 %**. Orden de arriba abajo:

| Elemento | Ajustes | Modo y opacidad | Máscara |
| --- | --- | --- | --- |
| Cielo suave | Tono/Saturación: Colorear desactivado; Azules H=0/S=-20/L=0; Cianes H=0/S=-10/L=0 | Normal, 100 % | Cielo |
| Calidez de corona | Equilibrio de color: sombras 0/0/0; medios +8/-2/-8; luces +4/0/-6; Conservar luminosidad activado | Color, 30 % | Corona |
| Cobre–dorado–marfil | Mapa de degradado con los cinco topes de la tabla siguiente; sin invertir, tramado activado; puntos medios 50 %; método Clásico | Color, 30 % | Corona |
| Base de color | Copia RGB16 de la composición actual, antes de este acabado | Normal, 100 % | Validez observada original |

Las capas actuales de filtros y color permanecerían debajo del grupo. Son el «Original» con el que se mezcla el acabado; no se sustituye la fuente lineal ni se recalculan sus filtros para un mero cambio de opacidad del acabado.

| Posición | Color sRGB |
| --- | --- |
| 0 % | `#3A2638` |
| 35 % | `#B96343` |
| 65 % | `#EDAA64` |
| 85 % | `#F7D7A4` |
| 100 % | `#FFF4DE` |

El 50 % se aplica al grupo completo, con una base que cubra el lienzo observado y lo aísle en modo Normal. No equivale a reducir otra vez a la mitad las opacidades de los ajustes ni a sustituir el grupo por capas que atraviesen libremente todas las inferiores.

La guía pide objeto inteligente y Camera Raw como preparación editable. Sus ajustes nuevos son neutros: exposición, contraste, intensidad y saturación a cero, sin añadir tratamiento de detalle. No hace falta ejecutar Camera Raw para reproducir esos pasos neutros. Una primera versión con base de píxeles y ajustes nativos tendría que declarar esa diferencia; no ofrecería un Camera Raw inteligente editable.

## Máscaras: automatización inicial y revisión

La guía de Photoshop exige seleccionar y refinar visualmente la corona, incluyendo rayos débiles y excluyendo cielo y Luna. Indica expresamente que no existe un umbral universal. Lightroom propone una elipse y rangos de luminancia como punto de partida, pero también exige corrección con pincel.

La aplicación puede preparar una máscara inicial usando la geometría lunar, la luminancia de la composición visual y la validez observada. Las máscaras deben quedar como máscaras de capa nativas editables, separadas de la transparencia original. No se modifican las máscaras científicas ni se rellenan datos ausentes.

La máscara Cielo debe calcularse separadamente, protegiendo disco y rayos: invertir Corona sin más seleccionaría también la Luna. El tamaño de la corona, los umbrales y el desvanecido no deben presentarse como valores calibrados para cualquier imagen. Antes de aceptar el acabado se necesita revisar el limbo y los rayos débiles al 100 %.

Una imagen monocroma puede recibir el mapa cálido como color creativo. El ajuste de azules/cianes no creará un cielo azul si no existe ese color en la base.

## Cambios necesarios en la aplicación

1. **Interfaz y ajustes:** casilla junto a la exportación por capas, disponible para PSB y desmarcada inicialmente. Guardarla en el JSON; los JSON anteriores deben cargar con ella desmarcada. La selección de esta opción debe conservarse entre imágenes siguiendo la política de las opciones de exportación.
2. **Exportador:** ampliar `core/psb_export.py`. Actualmente escribe capas de píxeles RGB16, modos, opacidad y transparencia; no construye grupos ni estas capas de ajuste. La dependencia instalada `psd-tools==1.26.0` contiene estructuras de lectura/escritura para Gradient Map, Color Balance y Hue/Saturation, grupos y máscaras. Es una base técnica útil, pero no demuestra por sí sola que un archivo nuevo se recomponga correctamente en Photoshop.
3. **Metadatos y validación:** extender la receta y el verificador, que actualmente esperan una lista plana de capas RGB y alfa. Deben comprobar la jerarquía, los tres tipos de ajuste, sus parámetros, las máscaras y el modo/opacidad del grupo, además de conservar las comprobaciones existentes.
4. **Color — implementación:** el PSB con esta opción lleva un perfil ICC sRGB generado por LittleCMS e incrustado. Los hex de la guía se interpretan en sRGB. La base procede del RGB de presentación generado por la aplicación, que se declara asumido sRGB en los metadatos; no se modifican los datos lineales. Esto no añade gestión ni conversión general de perfiles ICC de entrada al procesador. Si la fuente necesita una conversión de un perfil RGB diferente, debe prepararse correctamente antes de cargarla; asignar el perfil de salida no realiza esa conversión de origen.
5. **Alcance — decisión del usuario:** el acabado se prepara exclusivamente en el PSB, dentro del grupo **Color Correction**. **No se muestra ni se calcula para la vista previa de la aplicación.** La exportación TIFF/JPEG conserva la composición habitual, sin este acabado. La diferencia entre esos productos y un PSB con el grupo visible es intencionada. La recomposición de las capas de ajuste debe comprobarse en Photoshop; no introducir un renderizador del acabado para la vista previa de la aplicación.


## Limitación de la base duplicada

La base del grupo es una copia de la composición en el momento de exportar. Modificar después una capa FNRGF, WOW, etc. situada debajo no actualiza esa copia. El usuario tendría que regenerar «Base de color» para que el acabado parta del nuevo resultado. Los ajustes y las máscaras de color sí seguirían siendo editables.

Evitar esa dependencia exigiría diseñar otro mecanismo; un grupo sin esa base no es una sustitución automáticamente equivalente al procedimiento del PDF.

## Comprobaciones antes de darlo por implementado

- Probar el exportador primero con una imagen pequeña y controles RGB/gris conocidos.
- Reabrir el PSB y comprobar 16 bits, jerarquía, modos, opacidades, parámetros y máscaras.
- Abrirlo en Photoshop y forzar una recomposición: una imagen combinada almacenada correcta no demuestra que los ajustes nativos estén bien escritos.
- Comprobar que cada ajuste se puede editar en su panel correspondiente y que las máscaras se pueden pintar.
- Revisar una imagen real completa y al 100 %, especialmente limbo, rayos débiles y transiciones de color.
- Verificar que el perfil ICC incrustado del PSB sea sRGB y comprobar la interpolación del mapa.
- Confirmar que activar la casilla no modifica ni la vista previa ni los TIFF/JPEG; la corrección de color queda exclusivamente en el PSB.
- Confirmar que desmarcar la opción conserva exactamente el comportamiento de exportación anterior y que los JSON sin esta opción no la activan.

## Fuentes revisadas

- `/path/to/reference-guides/Corona_solar_Photoshop_ES.pdf`: tres páginas, especialmente pasos 3–7.
- `/path/to/reference-guides/Corona_solar_Lightroom_Classic_ES.pdf`: tres páginas; equivalencia visual, máscaras y límites de la mezcla al 50 %.
- Código local: `core/psb_export.py`, `core/layer_package.py`, `core/export.py`, `core/colour.py`, `gui/app.py`, `gui/project_settings.py`.
- Código instalado de `psd-tools` 1.26.0: estructuras y API de ajustes, grupos y máscaras. No se ha usado esa inspección como certificación de renderizado nativo.


## Implementación y validación realizadas

- `core/color_correction.py` crea el grupo Normal/50%, su base RGB16, los tres ajustes nativos, las máscaras de 16 bits y el perfil ICC sRGB. Los parámetros y el método de máscaras quedan registrados en XMP.
- La máscara inicial estima el fondo con la mediana y MAD de luminancia del cuarto exterior del campo observado. Suaviza la pertenencia por luminancia y la transición fuera del disco, sin modificar los píxeles ni completar datos ausentes. No es una selección calibrada universal.
- `core/psb_export.py` conserva la verificación de las capas originales y verifica adicionalmente jerarquía, tipos nativos, parámetros, posiciones de la paleta, máscaras, base, perfil y opacidades.
- El PSB conserva los píxeles de referencia anteriores al acabado y marca `hasRealMergedData=false` en Version Info. Photoshop recompone los ajustes nativos al abrirlo. Así no se inventa un renderizado aproximado del acabado ni se añade un renderizador a la aplicación. Otros lectores que solo presenten la imagen combinada pueden mostrar la referencia sin corrección hasta guardar una nueva composición desde Photoshop.
- La casilla solo se habilita para exportación de capas PSB. No participa en la firma del procesamiento ni dispara filtros o vista previa. Se guarda/restaura mediante JSON y los archivos anteriores que la omitan la desactivan.
- Pruebas automáticas verifican salida PSB nativa, canales y máscaras, protección del disco y datos ausentes, sRGB, fallos atómicos, rechazo del formato TIFF con esta opción, persistencia y ausencia de cambios de vista previa. Los TIFF/JPEG son idénticos con la casilla activada y desactivada.
- Se generó desde la GUI un PSB con una imagen real reducida a 640×427. Photoshop 2026 lo abrió en 16 bits, reconoció el perfil sRGB, el grupo Normal/50% y los cuatro elementos interiores. Guardar una copia nativa confirmó la recomposición y la conservación de los ajustes y máscaras. La comparación visual mantuvo el detalle y aplicó la calidez principalmente a la corona, con desaturación del cielo.
- Artefactos de la comprobación local: `/private/tmp/eip-color-correction-real-e_n5o0i_/`. No se modificaron imágenes originales ni documentos del usuario abiertos en Photoshop.
- No se ha medido todavía el coste en memoria/tiempo a resolución completa. Las máscaras iniciales requieren inspección y posible pincelado en Photoshop. La base sigue siendo una instantánea: editar filtros inferiores no la actualiza por sí solo.

Referencia de los bloques nativos: https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/
