"""El transformat entre el llenç de `CapesTotalsV13.psd` i el llenç comú d'avui.

## Què és el llenç de la V13, mesurat i no suposat

És la **graella del sensor de la Vixen sense girar**: la zona visible del RAW
(6960×4640) seu a l'offset (457, 463) d'un llenç de 7648×5353. O sigui

    sensor_x = X13 - 457 + left_margin(172) = X13 - 285
    sensor_y = Y13 - 463 + top_margin (108) = Y13 - 355

⏭️ **I les capes NO estan registrades entre elles**: cada una seu a la posició
crua del seu fotograma. Mesurat ajustant el limbe lunar per màxim de gradient a
les capes on es pot ajustar i comparant-lo amb el que la cadena mesura al
fotograma que les va originar:

| capa | fotograma | Lluna V13 → sensor | Lluna de la cadena | diferència |
|---|---|---|---|---|
| 12 | 572A2956 | (3751,11 · 2385,04) | (3751,61 · 2385,95) | (−0,50 · −0,91) |
| 11 | 572A2968 | (3751,33 · 2383,62) | (3751,24 · 2383,27) | (+0,09 · +0,35) |
| 10 | 572A2969 | (3751,71 · 2383,46) | (3751,20 · 2382,98) | (+0,52 · +0,48) |
| 09 | 572A2975 | (3748,61 · 2380,74) | (3750,91 · 2381,02) | (−2,29 · −0,28) |
| 08 | 572A2970 | (3750,29 · 2382,43) | (3751,15 · 2382,68) | (−0,86 · −0,25) |
| 06 | 572A2971 | (3749,98 · 2381,59) | (3751,10 · 2382,38) | (−1,12 · −0,79) |

Sense cap desplaçament de registre, el limbe cau a **≤2,3 px** d'on la cadena
diu que és. La capa 09 és la pitjor i té motiu propi: és un apilat de dos
fotogrames separats **62 s**, o sigui que la seva Lluna ja hi surt escombrada
17 px i el cercle ajustat n'és la mitjana.

⏭️ **Conseqüència per a la V14**: el transformat de cada màscara ha de fer
servir el Sol del SEU fotograma, no un de comú. És el que vol dir «alinea les
imatges amb la corona i ajusta també les màscares»: la imatge la torna a
registrar la cadena, i la màscara ha de seguir el mateix registre.

⚠️ Escala: el limbe lunar mesurat a la V13 val 451,8-453,7 px i la cadena en
mesura 452,36 de mediana als seus 56 fotogrames. **L'escala és 1**: els dos
llenços són píxels del mateix sensor. (El 455,50 del rebut és el radi
d'efemèride, que no és una mesura del limbe.)
"""

from __future__ import annotations

import math

import numpy as np
import cv2

# el llenç de la V13
W13, H13 = 7648, 5353
OFF_X, OFF_Y = 457, 463          # on seu la zona visible del RAW
LEFT_MARGIN, TOP_MARGIN = 172, 108   # marges del RAW de la Canon R6 Mark III


def v13_a_sensor(x13: float, y13: float) -> tuple[float, float]:
    return x13 - OFF_X + LEFT_MARGIN, y13 - OFF_Y + TOP_MARGIN


def mapes_base(W: int, H: int, pa_north_deg: float):
    """La part del mapa invers que NO depèn del fotograma.

    El llenç comú → sensor és, per a un fotograma amb el Sol a (sx, sy):

        sensor_x =  ca·dX + sa·dY + sx
        sensor_y = -sa·dX + ca·dY + sy      amb dX = X−CX, dY = Y−CY

    o sigui que canviar de fotograma només suma una constant. Es calcula el
    tros comú una vegada i s'estalvien dues graelles de 290 MB per capa.
    """
    th = math.radians(-pa_north_deg)
    ca, sa = math.cos(th), math.sin(th)
    XX, YY = np.meshgrid(np.arange(W, dtype=np.float32),
                         np.arange(H, dtype=np.float32))
    dX = XX - W / 2.0; dY = YY - H / 2.0
    del XX, YY
    bx = (ca * dX + sa * dY).astype(np.float32)
    by = (-sa * dX + ca * dY).astype(np.float32)
    return bx, by


def warp_v13(img13: np.ndarray, bx: np.ndarray, by: np.ndarray,
             sol_x: float, sol_y: float,
             interp: int = cv2.INTER_LINEAR,
             border: int = cv2.BORDER_REPLICATE) -> np.ndarray:
    """Un mapa del llenç V13 portat al llenç comú.

    ⛔ `sol_x`, `sol_y` són en coordenades de `raw_image` (marges inclosos), que
    és el que la cadena desa a `F1.2_sol_llenc.json`.
    ⏭️ La vora es REPETEIX i no s'omple amb cap constant. Fora del rectangle del
    sensor no hi ha dada de cap manera, o sigui que la validesa de la capa hi
    posarà zero igualment; repetir la vora només evita fabricar una frontera
    dura enmig d'una màscara que hi arriba plana.
    """
    mx = (bx + (sol_x - LEFT_MARGIN + OFF_X)).astype(np.float32)
    my = (by + (sol_y - TOP_MARGIN + OFF_Y)).astype(np.float32)
    return cv2.remap(img13, mx, my, interp, borderMode=border)
