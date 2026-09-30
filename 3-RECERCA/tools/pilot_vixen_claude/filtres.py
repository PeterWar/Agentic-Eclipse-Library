"""Fase 3 · Filtres, sobre el compost del pilot i amb la seva pròpia variància.

Tot el que hi ha aquí surt de `research/82`, que llegeix els papers de Brno amb
les fórmules a la mà. Les tres conseqüències que aquell document treu i que
governen aquest fitxer:

1. **La porta de soroll és el criteri**, no la nitidesa. Dels filtres publicats
   només WOW i NAFE en porten una de veritat. ⛔ I aquí sí que es pot fer bé:
   el compost del pilot **porta el seu mapa de variància per píxel** (`1/Σw`,
   `VAR_adu_s2.npy`), o sigui que el llindar no s'estima, es calcula.
2. Per a **alçades grans** la mateixa Brno diu de normalitzar per anell
   (NRGF/FNRGF) i deixar l'**ACHF per al detall fi**.
3. **σ d'un segment ∝ la seva mitjana** (tesi, fig. 6.15): un passa-alt lineal
   necessita guany creixent amb el radi. Es treballa en **ln I**, i llavors el
   guany hi surt sol.

## L'ACHF, i què és de veritat

La tesi §5.2 en dona la fórmula: `C = exp(−[(r−ρ)² + (r(φ−ϕ))²]/2σ²)`. Això és
una gaussiana en (Δr, arc), i (Δr, arc) **són les coordenades locals de la
imatge**: o sigui que el nucli de l'ACHF **és isòtrop**, és a dir, una gaussiana
normal i corrent. El que el fa diferent d'un unsharp qualsevol és l'altra
meitat de la fórmula: **la convolució incompleta normalitzada pel pes**, que és
com tracta la Lluna, el fora de camp i «les parts diferents» de la imatge.

    g = (I·w) ⊗ G_σ / (w ⊗ G_σ)

⛔ **I això és exactament la norma del rectangle ben feta**: el filtre s'avalua a
**tot el rectangle**, i l'única cosa que el limita és que no hi hagi dada —que
entra pel pes, no per cap circumferència—. Un ACHF retallat a un cercle hi
posaria el halo que la norma prohibeix.
"""
from __future__ import annotations

import math
import os

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.signal import savgol_filter


def treu_perfil_radial(imatge: np.ndarray, pes: np.ndarray, radis: np.ndarray,
                       n: int = 600):
    """Resta la mediana per anell: és el NRGF, i ha d'anar DAVANT de l'ACHF.

    ⛔ Sense això, l'ACHF **s'inventa estructura**. Mesurat amb el control
    d'entrada llisa: una corona perfectament llisa `r^-2,5` hi dona un detall
    del **6,6 %** de l'amplitud del senyal, i no és corona: és la **curvatura**
    del perfil, que un passa-alt gaussià llegeix com a estructura. És el mateix
    error que la porta E2 va patir dues vegades (§10 i §13 de research/99), i
    la solució és la mateixa: treure primer el que és radial.

    És també el que Brno prescriu —«FNRGF per a les estructures grans, ACHF per
    al detall fi, i composar»— i el que la fig. 6.15 de la tesi implica: la σ
    d'un segment és proporcional a la seva mitjana, o sigui que el que s'ha de
    filtrar és el **contrast relatiu**, no la lluminància.

    ## ⛔ Les quatre maneres de fer-ho malament, totes mesurades el 24-08-2026

    Pere va veure centenars d'anells concèntrics amb dents de serra a
    `fase3_achf_fisiques_flat-si.png`. No n'hi havia una causa, n'hi havia
    quatre, i totes viuen aquí:

    1. **Restar el perfil per calaix** (`med[idx]`) en lloc d'interpolar. Amb
       calaixos de 9,475 px al llenç del pilot, l'esglaó entre calaixos veïns
       val **16,4 % a 1,05 R☉**, 8,8 % a 1,5 i 3,7 % a 2,0. I com que la
       frontera d'un calaix és una circumferència rasteritzada sobre la graella
       de píxels, cada esglaó surt amb dents de serra.
    2. **Definir els calaixos sobre tot el mapa de radis** i no sobre el rang on
       hi ha dada. Els de dins del disc lunar queden buits, s'omplen per
       extrapolació plana i el suavitzat els barreja amb els primers bons:
       **1,62 % just al limbe**.
    3. **Suavitzar amb `mode="nearest"`**, que repeteix una constant als
       extrems i esbiaixa la vora exterior d'un perfil que baixa dret: 0,32 %.
    4. I la que queda quan les altres tres estan arreglades: **calaixos
       uniformes en r i un suavitzat que no preserva la curvatura**. Sobre una
       corona de Baumbach amb 300 calaixos, uniforme+gaussiana deixa 0,256 % i
       0,832 % al limbe. En **log r** i amb Savitzky-Golay d'ordre 2 queda en
       **0,043 % i 0,194 %**: sis vegades millor amb els mateixos calaixos.
       El motiu és físic: la corona és una suma de lleis de potències, o sigui
       una **recta en log-log**, i allà interpolar i suavitzar no esbiaixen. De
       propina, els calaixos surten estrets on el perfil és dret i amples on és
       pla, que és exactament on convé cadascun.
    """
    v = imatge.ravel()
    m = (pes.ravel() > 0) & np.isfinite(v) & (radis.ravel() > 0)
    rv = radis.ravel()[m]
    if rv.size < 100:
        raise ValueError("perfil radial buit")
    t_tot = np.log(np.maximum(radis, 1e-9))
    tv = np.log(rv)
    # ⛔ Un calaix no pot ser més estret que UN píxel: amb calaixos sub-píxel la
    # mediana per anell la fan quatre píxels de cantonada i el perfil segueix el
    # soroll, que és el que el suavitzat existeix per evitar. Un píxel i no dos
    # perquè el que limita l'artefacte al limbe és el nombre de calaixos i no la
    # finestra del suavitzat: mesurat amb la geometria del llenç, doblar-los baixa
    # el residu de 1,0 a 0,35 per mil i canviar la finestra no el mou (0,1 %). I a
    # 1,04 R☉ l'anell té 2.878 px de circumferència: mostra de sobres.
    # El pas radial per píxel surt del mateix mapa de radis, i s'agafa el p99 i
    # no la mediana perquè al llarg d'una fila dr/dx = cos(angle)/r_sol_px i la
    # seva mediana val 0,707 vegades el pas de veritat.
    pas = float(np.percentile(np.abs(np.diff(radis, axis=1)), 99))
    # ⛔ I un terra per a r_min: si el mapa de pesos arriba al centre, r_min→0,
    # el rang en log es dispara i els calaixos de dins queden tots buits. El
    # terra és de dos píxels, que és la mateixa condició de sota per un altre
    # camí. (Ho va destapar el control d'entrada llisa, que sí que cobreix el
    # centre; al llenç de veritat la Lluna ja el tapa.)
    # el mínim de veritat, amb un terra d'un píxel; un percentil hi llençaria
    # els píxels del limbe, que són justament on el perfil és més dret.
    r_min = max(float(rv.min()), 1.0 * pas)
    tv = tv[tv >= math.log(r_min)]
    if tv.size < 100:
        raise ValueError("perfil radial buit")
    n_max = int((tv.max() - tv.min()) * r_min / max(1.0 * pas, 1e-12))
    n = int(max(8, min(int(n), max(8, n_max))))
    vores = np.linspace(float(tv.min()), float(tv.max()), n + 1)
    centres = 0.5 * (vores[:-1] + vores[1:])
    idx = np.clip(np.digitize(t_tot.ravel(), vores) - 1, 0, n - 1)
    med = np.full(n, np.nan)
    o = np.argsort(idx[m]); ii = idx[m][o]; vv = v[m][o]
    talls = np.searchsorted(ii, np.arange(n + 1))
    for a in range(n):
        seg = vv[talls[a]:talls[a + 1]]
        if seg.size > 50:
            med[a] = np.median(seg)
    bons = np.isfinite(med)
    if bons.sum() < 8:
        raise ValueError("perfil radial buit")
    med = np.interp(np.arange(n), np.flatnonzero(bons), med[bons])
    # Savitzky-Golay d'ordre 2: preserva una paràbola exactament, o sigui que no
    # esbiaixa la curvatura que queda; una gaussiana sí que l'esbiaixa.
    # ⛔ Configurable NOMÉS per a la prova de si els anells circulars són del
    # suavitzat: la finestra val 0,18 R☉ a 1,5 i 0,24 a 2,0, que és exactament
    # l'amplada dels arcs marcats. Un Savitzky-Golay d'ordre 2 sobre un perfil
    # amb genolls deixa sobrepassada d'una finestra d'ample. Si els anells es
    # mouen amb la finestra, són del filtre.
    _sg = os.environ.get("PILOT_NRGF_SG")
    if _sg:
        finestra = int(_sg) | 1
        finestra = int(min(max(5, finestra), (len(med) // 2) * 2 - 1))
    else:
        finestra = int(min(max(5, (n // 40) * 2 + 1), (len(med) // 2) * 2 - 1))
    if finestra >= 5:
        med = savgol_filter(med, finestra, 2, mode="interp")
    # ⛔ I restar-lo per INTERPOLACIÓ CONTÍNUA, mai per calaix.
    fons = np.interp(t_tot, centres, med).astype(np.float32)
    return (imatge - fons).astype(np.float32), med, np.exp(vores)

def treu_residu_circular(detall: np.ndarray, pes: np.ndarray, radis: np.ndarray,
                         pas_px: float = 0.5):
    """Segona passada NRGF, **després** de l'ACHF: deixa el detall amb la
    mediana azimutal EXACTAMENT zero a tot radi.

    ## Per què n'hi ha d'haver dues, i per què la segona pot ser exacta

    La primera passada (`treu_perfil_radial`) ha de **suavitzar** el perfil, i
    això no és una tria: a `ln I` la dispersió dins d'un anell la domina la
    corona, no el soroll —σ ≈ 0,3 en ln, o sigui un 30 % azimutal—, i l'error
    típic de la mediana d'un anell de 3.300 px val 1,25·0,3/√3300 = **0,65 %**.
    Restar la mediana crua hi injectaria un tremolor circular tres vegades més
    gros que tot el detall que declarem. El suavitzat és necessari.

    ⛔ **I el suavitzat és el que deixa els lòbuls.** Un Savitzky-Golay d'ordre 2
    amb finestra F no reprodueix la curvatura del perfil dins de F, i el residu
    és un ondulat de període ~F. Mesurat el 24-08-2026 sobre el compost del
    pilot, refent la fase 3 amb finestres de 9, 29 i 61 calaixos: a 1,182 R☉ el
    lòbul val +0,179 %, +0,074 % i −0,038 %, i a 1,303 R☉ −0,250 %, −0,153 % i
    −0,040 %. **Es mouen amb la finestra: són del filtre, no de la corona.**
    Cap finestra els mata —el rms circular es queda entre 0,13 i 0,15 % a les
    tres—, o sigui que triar-ne una de bona no és la solució.

    La segona passada sí que pot ser exacta, i el número ho diu: després de
    l'ACHF la dispersió dins d'un anell ja no és la corona sinó **el detall**,
    σ ≈ 0,0023 en ln, i l'error típic de la mediana cau a 1,25·0,0023/√3300 =
    **0,005 %**, o sigui **quaranta vegades per sota** de l'artefacte que ha de
    treure. Amb calaixos d'un píxel, restar la mediana crua d'anell no costa
    res i deixa la component circular a zero **per construcció**.

    Això no és cosmètica sinó cura: no importa QUÈ hagi deixat la primera
    passada —lòbuls del Savitzky-Golay, vores de calaix, un centre desplaçat—,
    perquè tot això és circular i aquí es cancel·la. El que NO toca, i no ha de
    tocar, és res que no sigui circular: les costures de la fusió HDR segueixen
    **isofotes**, no circumferències, i s'han de curar a la fase 2.

    ⛔ Tampoc no esborra estructura coronal: la corona no té simetria circular
    més enllà de la caiguda radial mitjana, que és justament el que el NRGF
    treu per definició. Restar una constant per anell no pot **crear** cap
    estructura azimutal.

    ⚠️ **El pas de calaix és mig píxel, i està calibrat.** Sobre una corona de
    Baumbach al mostreig del llenç de veritat (R☉ = 440,6 px), la primera
    passada sola deixa un residu circular que val el **25 %** del detall; la
    segona el baixa **×64 amb calaixos d'un píxel i ×272 amb mig**, i a un quart
    de píxel ja no guanya res. Per sota d'un píxel els calaixos deixen de tenir
    prou mostra i el que es guanya és resolució, no precisió.

    Retorna `(detall_net, perfil_circular, vores_r)`.
    """
    v = detall.ravel()
    m = (pes.ravel() > 0) & np.isfinite(v)
    if m.sum() < 100:
        return detall.astype(np.float32), np.zeros(0), np.zeros(0)
    rv = radis.ravel()[m]
    vv = v[m]
    r0, r1 = float(rv.min()), float(rv.max())
    # el pas ve en píxels de la reixa: es tradueix a unitats de `radis`
    pas = float(np.percentile(np.abs(np.diff(radis, axis=1)), 99)) * pas_px
    n = int(max(8, min(20000, math.ceil((r1 - r0) / max(pas, 1e-12)))))
    vores = np.linspace(r0, r1, n + 1)
    idx = np.clip(np.digitize(rv, vores) - 1, 0, n - 1)
    o = np.argsort(idx, kind="stable")
    idx_s, v_s = idx[o], vv[o]
    talls = np.searchsorted(idx_s, np.arange(n + 1))
    med = np.full(n, np.nan, np.float64)
    for i in range(n):
        a, b = talls[i], talls[i + 1]
        if b - a >= 8:
            med[i] = np.median(v_s[a:b])
    bo = np.isfinite(med)
    if bo.sum() < 4:
        return detall.astype(np.float32), np.zeros(0), vores
    centres = 0.5 * (vores[:-1] + vores[1:])
    # ⛔ interpolació CONTÍNUA, mai `med[idx]`: restar per calaix torna a posar
    # els esglaons amb dents de serra que Pere va marcar el 24-08 (research/100).
    med_ple = np.interp(centres, centres[bo], med[bo])
    fons = np.interp(radis, centres, med_ple).astype(np.float32)
    return (detall - fons).astype(np.float32), med_ple, vores



def _vores_adaptatives(x: np.ndarray, n_objectiu: int, minim: int) -> np.ndarray:
    """Vores de calaix en `x` amb **almenys `minim` mostres a cadascun**.

    ⛔ Ni uniformes ni per quantil, i el 24-08-2026 va costar dues rondes
    entendre per què:

    - **uniformes en log**: l'extrem brillant té pocs píxels, els seus calaixos
      no arriben al mínim, es descarten i **aquella zona no es corregeix mai**.
      Mesurat al pilot: la mediana per nivell quedava plana a zero a tot arreu
      **excepte per damunt de 6.991 ADU/s**, on arribava a **+0,4 %** — i és
      justament la corona interior, on Pere tenia marcats els arcs;
    - **per quantil**: tots els calaixos tenen el mateix nombre de mostres, però
      els nivells brillants es queden amb quatre calaixos i la resolució hi
      desapareix.

    L'adaptativa fa el que toca: camina en `x` ordenat i tanca un calaix quan té
    prou mostres, de manera que **cap zona queda sense corregir** i la resolució
    és tan fina com la mostra permet a cada lloc.
    """
    xs = np.sort(x)
    n = xs.size
    if n < 2 * minim:
        return np.array([xs[0], xs[-1] * (1.0 + 1e-9)])
    pas = max(minim, int(math.ceil(n / max(n_objectiu, 1))))
    talls = list(range(0, n, pas))
    if n - talls[-1] < minim:          # l'últim calaix no pot quedar coix
        talls = talls[:-1]
    vores = [xs[0]] + [float(xs[i]) for i in talls[1:]] + [float(xs[-1]) * (1.0 + 1e-9)]
    return np.unique(np.asarray(vores, float))


def treu_residu_per_nivell(detall: np.ndarray, pes: np.ndarray, nivell: np.ndarray,
                           n: int = 1500):
    """Tercera passada: deixa la mediana del detall **per calaix de NIVELL** a zero.

    ## Per què el nivell, i per què és el germà exacte de la passada radial

    Les dues famílies d'artefactes que Pere va marcar el 24-08-2026 tenen la
    mateixa forma matemàtica en dos espais diferents:

    | família | és constant a... | es cura restant la mediana per... |
    |---|---|---|
    | anells concèntrics | **radi** constant | calaix de **radi** (`treu_residu_circular`) |
    | costures de fusió | **nivell** constant | calaix de **nivell** (aquí) |

    ⛔ I això no és una analogia: **les fronteres de fusió HDR SÓN isofotes per
    construcció**. El pes d'un fotograma d'exposició `t` només depèn del seu
    valor cru `g·t`, o sigui que tota la maquinària de fusió —el `taper`, el
    sostre, la rampa— és **funció exclusiva del nivell**. Qualsevol biaix que en
    surti ho ha de ser també. Per això aquesta passada no persegueix una causa
    concreta: **les cobreix totes alhora**, mesurades o no.

    ⛔ **I no es menja estructura coronal.** Un passa-alt té mitjana local zero
    per construcció; condicionar-lo al nivell no pot donar una mitjana no nul·la
    si no hi ha artefacte. Dues regions igual de brillants —una nansa i un
    plomall— tenen detall diferent, i la seva mitjana és zero. El que sí que té
    mitjana no nul·la a un nivell concret és exactament el que la fusió hi ha
    posat.

    ⚠️ Va **després** de `treu_residu_circular` i és independent: l'una treu el
    que és funció del radi, l'altra el que és funció del nivell, i una isofota no
    és una circumferència.

    `nivell` és el compost (en unitats lineals) al mateix llenç que `detall`.
    """
    v = detall.ravel()
    m = (pes.ravel() > 0) & np.isfinite(v)
    nv = nivell.ravel()
    m &= np.isfinite(nv) & (nv > 0)
    if m.sum() < 1000:
        return detall.astype(np.float32), np.zeros(0), np.zeros(0)
    x = np.log(nv[m])          # ⛔ en log: la fusió va per raons, no per diferències
    vv = v[m]
    # ⛔ Calaixos ADAPTATIUS: vegeu `_vores_adaptatives`. Ni uniformes en log
    # —deixen l'extrem brillant sense corregir— ni per quantil.
    vores = _vores_adaptatives(x, n, 200)
    n = len(vores) - 1
    if n < 8:
        return detall.astype(np.float32), np.zeros(0), np.zeros(0)
    idx = np.clip(np.digitize(x, vores) - 1, 0, n - 1)
    o = np.argsort(idx, kind="stable")
    idx_s, v_s = idx[o], vv[o]
    talls = np.searchsorted(idx_s, np.arange(n + 1))
    med = np.full(n, np.nan)
    for i in range(n):
        a, b = talls[i], talls[i + 1]
        if b - a >= 60:
            med[i] = np.median(v_s[a:b])
    bo = np.isfinite(med)
    if bo.sum() < 4:
        return detall.astype(np.float32), np.zeros(0), vores
    centres = 0.5 * (vores[:-1] + vores[1:])
    med_ple = np.interp(centres, centres[bo], med[bo])
    # ⛔ interpolació CONTÍNUA sobre TOT el rectangle, mai per calaix
    x_tot = np.log(np.maximum(nivell, 1e-30))
    fons = np.interp(x_tot, centres, med_ple).astype(np.float32)
    return (detall - np.where(pes > 0, fons, 0.0)).astype(np.float32), med_ple, np.exp(vores)


def rms_per_nivell(detall: np.ndarray, pes: np.ndarray, nivell: np.ndarray,
                   n: int = 1500) -> dict:
    """Quant del detall és funció exclusiva del NIVELL, o sigui de la fusió."""
    v = detall.ravel()
    m = (pes.ravel() > 0) & np.isfinite(v)
    nv = nivell.ravel()
    m &= np.isfinite(nv) & (nv > 0)
    if m.sum() < 1000:
        return {"n_calaixos": 0, "rms_nivell": math.nan, "rms_detall": math.nan,
                "fraccio": math.nan, "maxim_absolut": math.nan}
    x, vv = np.log(nv[m]), v[m]
    vores = _vores_adaptatives(x, n, 200)
    nb = len(vores) - 1
    idx = np.clip(np.digitize(x, vores) - 1, 0, max(nb - 1, 0))
    o = np.argsort(idx, kind="stable")
    idx_s, v_s = idx[o], vv[o]
    talls = np.searchsorted(idx_s, np.arange(nb + 1))
    med = [float(np.median(v_s[a:b])) for a, b in zip(talls[:-1], talls[1:])
           if b - a >= 60]
    if len(med) < 4:
        return {"n_calaixos": len(med), "rms_nivell": math.nan,
                "rms_detall": float(np.std(vv)), "fraccio": math.nan,
                "maxim_absolut": math.nan}
    rn_, rd = float(np.std(med)), float(np.std(vv))
    return {"n_calaixos": len(med), "rms_nivell": rn_, "rms_detall": rd,
            "fraccio": rn_ / rd if rd > 0 else math.nan,
            "maxim_absolut": float(np.max(np.abs(med)))}


def rms_circular(detall: np.ndarray, pes: np.ndarray, radis: np.ndarray,
                 r0: float = 1.05, r1: float = 5.0, pas_r: float = 0.005,
                 cobertura_minima: float = 0.5) -> dict:
    """Quant del detall és una circumferència centrada al Sol.

    L'estadístic és el **rms de la mediana azimutal per anell**, comparat amb
    el rms del detall sencer. Un detall sa el té petit; un que porti anells
    concèntrics el té gros. És la mesura de l'artefacte que Pere va marcar en
    groc i en lila el 24-08-2026.

    ⛔ **Un anell que no és un anell no compta.** El criteri d'inclusió ha de ser
    la **fracció del cercle** que té dada, no un recompte de píxels: mesurat el
    24-08-2026 al tren Sony, un llindar de 200 píxels deixava entrar una
    escletxa de 256 px amb un **3,9 % de cobertura** a la vora interior de la
    dada, i aquella sola escletxa —d'amplada un calaix— feia que la porta H1
    declarés un 14,2 % d'anells quan fora d'ella el residu és de **±0,008 %**.
    Una vora de la dada no és un anell concèntric.
    """
    v = detall.ravel()
    m = (pes.ravel() > 0) & np.isfinite(v)
    if m.sum() < 100:
        return {"n_anells": 0, "rms_circular": math.nan, "rms_detall": math.nan,
                "fraccio": math.nan}
    rv, vv = radis.ravel()[m], v[m]
    vores = np.arange(r0, r1 + 0.5 * pas_r, pas_r)
    n = len(vores) - 1
    idx = np.digitize(rv, vores) - 1
    dins = (idx >= 0) & (idx < n)
    idx, vd = idx[dins], vv[dins]
    # cercle sencer de cada calaix, en píxels: 2·π·r·Δr amb r i Δr en píxels
    rpx = float(np.percentile(np.abs(np.diff(radis, axis=1)), 99))
    r_sol_px = 1.0 / max(rpx, 1e-12)
    centres_r = 0.5 * (vores[:-1] + vores[1:])
    ple = 2.0 * math.pi * centres_r * r_sol_px * pas_r * r_sol_px
    o = np.argsort(idx, kind="stable")
    idx_s, v_s = idx[o], vd[o]
    talls = np.searchsorted(idx_s, np.arange(n + 1))
    med = []
    for i in range(n):
        a, b = talls[i], talls[i + 1]
        if (b - a) >= 200 and (b - a) >= cobertura_minima * ple[i]:
            med.append(float(np.median(v_s[a:b])))
    if len(med) < 4:
        return {"n_anells": len(med), "rms_circular": math.nan,
                "rms_detall": float(np.std(vv)), "fraccio": math.nan}
    rc = float(np.std(med))
    rd = float(np.std(vv))
    return {"n_anells": len(med), "rms_circular": rc, "rms_detall": rd,
            "fraccio": rc / rd if rd > 0 else math.nan,
            "maxim_absolut": float(np.max(np.abs(med)))}


def achf(imatge: np.ndarray, pes: np.ndarray, sigmes, *,
         variancia: np.ndarray | None = None, n_soroll=(5.0, 3.0, 2.0, 1.0)):
    """ACHF multi-σ amb convolució incompleta i porta de soroll.

    `imatge` en **ln**, `pes` 1 on hi ha dada i 0 on no, `variancia` la del
    logaritme (σ_lnI = σ_I / I). Retorna (detall, diagnòstic).

    La porta és la de WOW: `d · erf(|d| / (n_s·σ_d))`, que **no és un llindar
    dur** —no deixa vores— i que va a zero on tot el que hi ha és soroll.
    """
    imatge = np.asarray(imatge, np.float32)
    w = np.asarray(pes, np.float32)
    iw = np.where(w > 0, imatge, 0.0).astype(np.float32)
    detall = np.zeros_like(imatge)
    diag = []
    ns = list(n_soroll) if hasattr(n_soroll, "__len__") else [float(n_soroll)] * len(sigmes)
    # ⛔ Els σ comparteixen la mateixa entrada, o sigui que el seu soroll se suma
    # COHERENTMENT: sumar-los sense normalitzar multiplica el soroll per l'arrel
    # del nombre d'escales. Mesurat amb el control de soroll pur: tres escales
    # sumades a pèl donaven **1,66 σ** de sortida amb la porta a n_s = 3.
    pesos_e = np.ones(len(sigmes)) / len(sigmes)
    for k_e, s in enumerate(sigmes):
        num = gaussian_filter(iw, s, mode="nearest")
        den = gaussian_filter(w, s, mode="nearest")
        g = np.where(den > 1e-6, num / np.maximum(den, 1e-6), 0.0)
        d = np.where(w > 0, imatge - g, 0.0).astype(np.float32)
        nse = ns[k_e] if k_e < len(ns) else ns[-1]
        if variancia is not None:
            # variància del passa-alt: el terme suau hi aporta ~1/(4πσ²) del
            # soroll original, o sigui res per a σ ≥ 2 px. Es pren σ_d ≈ σ_I.
            sd = np.sqrt(np.maximum(variancia, 0.0)).astype(np.float32)
            from scipy.special import erf
            porta = erf(np.abs(d) / np.maximum(nse * sd, 1e-12))
            passat = float(np.mean(porta[w > 0]))
            d = (d * porta).astype(np.float32)
        else:
            passat = 1.0
        detall += pesos_e[k_e] * d
        diag.append({"sigma_px": float(s), "n_soroll": float(nse),
                     "pes": float(pesos_e[k_e]),
                     "amplitud_rms": float(np.std(d[w > 0])),
                     "fraccio_que_passa_la_porta": round(passat, 5)})
    return detall, diag


def perfil_amplitud(detall: np.ndarray, pes: np.ndarray, radis: np.ndarray,
                    r0: float, r1: float, n: int):
    """Amplitud del passa-alt per anell: el perfil sobre el qual va la porta G."""
    vores = np.linspace(r0, r1, n + 1)
    idx = np.digitize(radis.ravel(), vores) - 1
    v = detall.ravel()
    bo = (idx >= 0) & (idx < n) & (pes.ravel() > 0) & np.isfinite(v)
    o = np.argsort(idx[bo]); ii = idx[bo][o]; vv = np.abs(v[bo][o])
    talls = np.searchsorted(ii, np.arange(n + 1))
    amp = np.full(n, np.nan); pes_n = np.zeros(n)
    for a in range(n):
        seg = vv[talls[a]:talls[a + 1]]
        if seg.size > 200:
            amp[a] = np.median(seg)
            pes_n[a] = seg.size
    return 0.5 * (vores[:-1] + vores[1:]), amp, pes_n


def control_entrada_llisa(shape, pes, sigmes, r_sol_px: float,
                          treu_radial: bool = True, r_lluna_rsol: float = 460.0 / 440.60,
                          bandes=((1.0, 1.5), (1.5, 2.5), (2.5, 5.0), (5.0, 99.0)), **kw):
    """⛔ Control obligatori: una corona PERFECTAMENT llisa no pot donar detall.

    És l'entrada dolenta coneguda d'aquesta fase. Un filtre que hi tregui
    estructura se l'està inventant, i el que hi trobi és la seva pròpia
    resposta de vora i el seu error numèric, no corona.

    ⛔ **I ha de tenir la geometria de veritat.** Fins al 24-08-2026 aquest
    control corria SENSE disc lunar i amb una `r^-2,5` que divergeix al centre:
    el 98 % del «detall» que mesurava vivia a r < 1,04 R☉ —on de veritat hi ha
    la Lluna i no hi ha dada—, i amb la geometria bona el número baixa 14
    vegades. Un control que mesura una singularitat que la imatge no té no diu
    res de la imatge. Ara porta la Lluna i una corona de **Baumbach**, que és
    la que té la curvatura de debò.

    I es reporta **per banda**, perquè l'artefacte no és uniforme: viu al limbe,
    que és on el perfil és més dret i on el detall coronal importa més.
    """
    h, w_ = shape
    yy, xx = np.mgrid[0:h, 0:w_]
    r = (np.hypot(xx - w_ / 2, yy - h / 2) / r_sol_px).astype(np.float32)
    x = np.maximum(r, 1.0)
    llis = np.log(1e-6 * (0.0532 * x ** -2.5 + 1.425 * x ** -7
                          + 2.565 * x ** -17)).astype(np.float32)
    pes = (np.asarray(pes, np.float32) * (r >= r_lluna_rsol)).astype(np.float32)
    y = treu_perfil_radial(llis, pes, r)[0] if treu_radial else llis
    d, _ = achf(y, pes, sigmes, **kw)
    m = pes > 0
    per_banda = {}
    for a, b in bandes:
        mm = m & (r >= a) & (r < b)
        if mm.sum() > 500:
            per_banda[f"{a:g}-{b:g}"] = float(np.std(d[mm]))
    return {"rms_del_detall": float(np.std(d[m])),
            "rms_de_l_entrada": float(np.std(llis[m])),
            "relacio": float(np.std(d[m]) / max(np.std(llis[m]), 1e-12)),
            "geometria": f"amb disc lunar a {r_lluna_rsol:.4f} R☉ i corona de Baumbach",
            "per_banda": per_banda}

def control_soroll_pur(shape, pes, sigmes, sigma_soroll: float,
                       n_soroll=(5.0, 3.0, 2.0, 1.0)):
    """⛔ Segon control: soroll pur ha de quedar per sota de la porta.

    Si el filtre en treu amplitud, la porta de soroll no serveix i el que
    sortirà a la imatge de veritat serà soroll realçat amb cara d'estructura.
    """
    rng = np.random.default_rng(20260824)
    x = rng.normal(0.0, sigma_soroll, shape).astype(np.float32)
    var = np.full(shape, sigma_soroll ** 2, np.float32)
    d, _ = achf(x, pes, sigmes, variancia=var, n_soroll=n_soroll)
    m = pes > 0
    return {"rms_del_detall": float(np.std(d[m])),
            "sigma_del_soroll": sigma_soroll,
            "relacio": float(np.std(d[m]) / sigma_soroll)}
