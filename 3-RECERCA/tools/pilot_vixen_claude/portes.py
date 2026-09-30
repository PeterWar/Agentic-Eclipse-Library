"""Pilot Vixen · les portes, com a funcions pures i provables.

⛔ Regla que governa aquest fitxer: **una porta que no pot fallar no és una
porta**. Els controls de costura d'agost deien «0,000 σ» a totes les versions
perquè el 85 % de la seva mostra eren zeros exactes. Cada funció d'aquí té, a
`test_portes.py`, una entrada dolenta coneguda que ha de fer-la fallar.
"""
from __future__ import annotations

import math

import numpy as np


def _resultat(estat: str, **camps) -> dict:
    return {"estat": estat, **camps}


# ---------------------------------------------------------------- F0
def porta_f0_esglaons(taxes: dict[float, list[float]], *, factor: float = 1.5,
                      minim_absolut: float = 0.01) -> dict:
    """F0' · coherència entre esglaons d'exposició al mateix anell.

    Si el fosc, el flat i sobretot els TEMPS són correctes, tots els esglaons
    han de mesurar el mateix senyal de corona: la corona no canvia en 100 s i
    el que canvia és només l'obturador. L'estadístic és **corona menys cel**,
    que és cec a un cel additiu —i el cel de la totalitat varia un ±20 %— i
    sensible a qualsevol error MULTIPLICATIU.

    ⛔ **El llindar no es tria: se'l calibra la mesura mateixa.** Cada esglaó té
    dos a quatre fotogrames, i la seva dispersió interna diu amb quina precisió
    es pot mesurar. Demanar una coherència entre esglaons més fina que això
    seria demanar el que la dada no pot donar; deixar-la més ampla seria una
    porta sense dents. Mesurat el 23-08 a la Vixen: dispersió interna 2,5–4,3 %
    i discrepància entre esglaons 1,3–1,6 %.

    ⚠️ **POTÈNCIA**: amb un terra de 2,5–4,3 %, aquesta porta **no pot resoldre**
    un error de temps d'exposició del 2 %. L'escala física s'adopta per
    autoritat del MakerNote, no perquè aquesta prova la demostri; el que la
    prova diu és que no hi ha res de gros trencat.
    """
    if len(taxes) < 3:
        return _resultat("FAIL", motiu="calen almenys tres esglaons", n=len(taxes))
    exps = sorted(taxes)
    med = {e: float(np.median(taxes[e])) for e in exps}
    ref = float(np.median(list(med.values())))
    if not math.isfinite(ref) or ref <= 0:
        return _resultat("FAIL", motiu="referència no positiva", referencia=ref)
    desv = {e: med[e] / ref - 1.0 for e in exps}
    rms = float(np.sqrt(np.mean([d * d for d in desv.values()])))
    pitjor_e = max(desv, key=lambda e: abs(desv[e]))

    # terra de precisió: dispersió de la mitjana dins de cada esglaó
    terres = []
    for e in exps:
        v = np.asarray(taxes[e], float)
        if v.size >= 2 and abs(v.mean()) > 0:
            terres.append(float(v.std(ddof=1) / math.sqrt(v.size) / abs(v.mean())))
    terra = float(np.median(terres)) if terres else math.nan
    limit = max(minim_absolut, factor * terra) if math.isfinite(terra) else minim_absolut
    ok = rms <= limit and abs(desv[pitjor_e]) <= 2.0 * limit
    return _resultat(
        "PASS" if ok else "FAIL",
        anell_senyal_referencia_adu_s=round(ref, 4),
        desviacio_per_exposicio={f"{e:.9g}": round(d, 6) for e, d in desv.items()},
        pitjor_exposicio_s=pitjor_e, pitjor_desviacio=round(desv[pitjor_e], 6),
        rms_desviacio=round(rms, 6), n_esglaons=len(exps),
        terra_de_precisio=None if not math.isfinite(terra) else round(terra, 6),
        limit_derivat=round(limit, 6), factor=factor,
        criteri="rms entre esglaons <= 1,5 x la dispersió interna de la mesura")


def porta_f0_amplitud_flat(flat_domini: np.ndarray, *, maxim_ev: float = 0.25) -> dict:
    """F0' · fita d'amplitud del flat radial, que s'aplica com a CANDIDAT.

    El flat de la Vixen no es pot validar amb dades pròpies: no hi ha palanca.
    La decisió és aplicar-lo declarant-ho, i la porta que hi queda és que el
    que no es pot validar tampoc pugui fer gaire mal. Si l'amplitud dins el
    domini de la corona superés `maxim_ev`, aplicar-lo a cegues seria
    inadmissible i caldria aturar-se.
    """
    v = flat_domini[np.isfinite(flat_domini)]
    if v.size == 0:
        return _resultat("FAIL", motiu="cap valor finit")
    if v.min() <= 0:
        return _resultat("FAIL", motiu="flat amb valors no positius", minim=float(v.min()))
    amp_ev = float(np.log2(v.max() / v.min()))
    med = float(np.median(v))
    ok = amp_ev <= maxim_ev and 0.5 <= med <= 2.0
    return _resultat("PASS" if ok else "FAIL", amplitud_ev=round(amp_ev, 5),
                     amplitud_percent=round(100 * (v.max() / v.min() - 1), 4),
                     mediana=round(med, 6), minim=round(float(v.min()), 6),
                     maxim=round(float(v.max()), 6), maxim_ev_autoritzat=maxim_ev,
                     politica="CANDIDAT_DECLARAT_NO_VALIDAT_AMB_DADES_VIXEN")


# ---------------------------------------------------------------- F1
def _ajusta_deriva(t: np.ndarray, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Model lineal de deriva: retorna els coeficients (x0, vx) i (y0, vy)."""
    A = np.vstack([np.ones_like(t), t]).T
    cx, *_ = np.linalg.lstsq(A, x, rcond=None)
    cy, *_ = np.linalg.lstsq(A, y, rcond=None)
    return cx, cy


def _mad(v: np.ndarray) -> float:
    return float(1.4826 * np.median(np.abs(v - np.median(v))))


def _ruptura(t: np.ndarray, x: np.ndarray, y: np.ndarray, grau: int
             ) -> tuple[float, int | None, float]:
    """Millor ruptura: quant milloraria el model si hi afegíssim un graó.

    ⛔ No serveix mirar els residus de l'ajust sense graó: un ajust lineal
    **absorbeix** un graó del mig i el converteix en una V, o sigui que ni el
    salt de mitjanes de bloc ni la seva escala robusta veuen el que hi ha. Amb
    un salt de 750 px, permutar residus donava p = 0,26. El que sí que funciona
    és comparar dos MODELS: recta contra recta-més-graó, buscant el punt de
    ruptura, i calibrar amb el soroll que queda **després** de posar-hi el graó,
    que és l'única estimació neta de σ que hi ha.

    Retorna (magnitud del graó en px, índex de la ruptura, σ del soroll net).
    """
    n = t.size
    V = np.vander(t, grau + 1)
    millor = (np.inf, None, 0.0)
    for k in range(3, n - 3):
        pas = (np.arange(n) >= k).astype(float)[:, None]
        A = np.hstack([V, pas])
        cx, *_ = np.linalg.lstsq(A, x, rcond=None)
        cy, *_ = np.linalg.lstsq(A, y, rcond=None)
        rss = float(((x - A @ cx) ** 2).sum() + ((y - A @ cy) ** 2).sum())
        if rss < millor[0]:
            millor = (rss, k, math.hypot(cx[-1], cy[-1]))
    rss, k, salt = millor
    if k is None:
        return 0.0, None, 1e-9
    sigma = math.sqrt(rss / max(2 * n - 2 * (grau + 2), 1))
    return salt, k, max(sigma, 1e-9)


def porta_f1_registre(t: np.ndarray, x: np.ndarray, y: np.ndarray,
                      noms: list[str], *, limit_px: float = 0.3,
                      grau: int = 1, n_sim: int = 400) -> dict:
    """F1' · registre per model de deriva, amb dos oracles independents.

    Tres coses que la porta antiga barrejava:

    1. el residu de la SOLUCIÓ DE PLACA (0,424 px) és **comú** als 68
       fotogrames —n'hi ha una de sola— i desplaça, gira i escala el llenç
       sencer igual per a tothom: **no desenfoca l'apilat** i no entra aquí;
    2. el `sol_x, sol_y` del manifest **no és una mesura**: surt d'un model
       lineal exacte (residu 0,000000 px). Avaluar-hi un oracle és avaluar el
       model contra ell mateix, o sigui una porta vàcua;
    3. el que sí que és mesurat és `lluna_mes_x, lluna_mes_y`, el centre del
       limbe lunar, i n'hi ha a 42 dels 68 fotogrames.

    La mesura per fotograma té 0,55 px de dispersió, però la muntura no es mou
    a batzegades: la seva deriva és llisa i el que oscil·la és l'ajust del
    limbe. La posició adoptada és la del MODEL, i la porta mesura dues coses
    diferents que cap de les dues sola no basta:

    * **precisió** (split-half alternat): quant es mouria el model si les dades
      fossin unes altres. Un salt de muntura NO el veu, perquè totes dues
      meitats el pateixen igual —provat amb 6 px—;
    * **adequació** (ruptura): si un graó milloraria el model més del que el
      soroll permet. Això és el que la Sony hauria disparat el 12 d'agost.
    """
    t = np.asarray(t, float); x = np.asarray(x, float); y = np.asarray(y, float)
    mes = np.isfinite(x) & np.isfinite(y)
    if mes.sum() < 4 * (grau + 1):
        return _resultat("FAIL", motiu="massa poques posicions mesurades",
                         n_mesurats=int(mes.sum()))
    o = np.flatnonzero(mes)[np.argsort(t[np.flatnonzero(mes)])]

    def ajusta(idx):
        A = np.vander(t[idx], grau + 1)
        cx, *_ = np.linalg.lstsq(A, x[idx], rcond=None)
        cy, *_ = np.linalg.lstsq(A, y[idx], rcond=None)
        return cx, cy

    def prediu(c, tt):
        return np.vander(np.atleast_1d(tt), grau + 1) @ c

    cx, cy = ajusta(o)
    rx = x[o] - prediu(cx, t[o]); ry = y[o] - prediu(cy, t[o])
    d = np.hypot(rx, ry)

    A_, B_ = o[0::2], o[1::2]
    if min(len(A_), len(B_)) < 2 * (grau + 1):
        return _resultat("FAIL", motiu="meitats massa curtes per a l'oracle",
                         n_a=len(A_), n_b=len(B_))
    ca, cb = ajusta(A_), ajusta(B_)
    tt = np.linspace(float(t.min()), float(t.max()), 400)
    sep = np.hypot(prediu(ca[0], tt) - prediu(cb[0], tt),
                   prediu(ca[1], tt) - prediu(cb[1], tt))
    sep_max = float(sep.max())

    span = float(t.max() - t.min())
    cob_a = float(t[A_].max() - t[A_].min()) / span if span > 0 else 0.0
    cob_b = float(t[B_].max() - t[B_].min()) / span if span > 0 else 0.0

    salt, k_salt, sigma = _ruptura(t[o], x[o], y[o], grau)
    rng = np.random.default_rng(20260823)
    nul = np.empty(n_sim)
    for i in range(n_sim):
        nul[i] = _ruptura(t[o], prediu(cx, t[o]) + rng.normal(0, sigma, o.size),
                          prediu(cy, t[o]) + rng.normal(0, sigma, o.size), grau)[0]
    p_valor = float((1 + (nul >= salt).sum()) / (1 + n_sim))
    llindar_nul = float(np.percentile(nul, 99))
    salt_estructural = bool(p_valor < 0.01 and salt > limit_px)

    ok = (sep_max <= limit_px and min(cob_a, cob_b) >= 0.8 and not salt_estructural)
    return _resultat(
        "PASS" if ok else "FAIL", oracle="split_half_alternat_mes_ruptura_simulada",
        separacio_maxima_px=round(sep_max, 5),
        separacio_mediana_px=round(float(np.median(sep)), 5), limit_px=limit_px,
        salt_de_ruptura_px=round(salt, 5), salt_p_valor=round(p_valor, 5),
        salt_percentil99_del_nul_px=round(llindar_nul, 5),
        salt_es_estructural=salt_estructural,
        instant_de_la_ruptura_s=None if k_salt is None else round(float(t[o][k_salt]), 3),
        sigma_del_soroll_net_px=round(sigma, 5), n_simulacions=n_sim,
        n_mesurats=int(mes.sum()), n_sense_mesura=int((~mes).sum()),
        n_meitat_a=int(len(A_)), n_meitat_b=int(len(B_)),
        cobertura_meitat_a=round(cob_a, 4), cobertura_meitat_b=round(cob_b, 4),
        grau_del_model=grau,
        dispersio_per_fotograma_px=round(float(np.sqrt((d ** 2).mean())), 5),
        autocorrelacio_lag1={"x": round(float(np.corrcoef(rx[:-1], rx[1:])[0, 1]), 4),
                             "y": round(float(np.corrcoef(ry[:-1], ry[1:])[0, 1]), 4)},
        nota=("la dispersió per fotograma és soroll de la mesura del limbe, no "
              "moviment: el que es propaga a l'apilat és la separació split-half"))


def cota_gir_camp(residu_px: float, radi_px: float) -> float:
    """Gir equivalent, en graus, que un residu donat implicaria a aquell radi."""
    return math.degrees(residu_px / radi_px) if radi_px > 0 else math.inf


# ---------------------------------------------------------------- E
def porta_e_monotonia(radis: np.ndarray, perfil: np.ndarray, *,
                      tolerancia_relativa: float = 0.02) -> dict:
    """E · el perfil radial del compost ha de baixar.

    ⛔ S'avalua **abans** d'aplicar cap `k, q` per segment angular: amb 60
    segments i paràmetres lliures, l'ajust pot FABRICAR la monotonia. Aquest
    pilot no en té cap, o sigui que la porta mira el compost cru.
    """
    r = np.asarray(radis, float); p = np.asarray(perfil, float)
    bo = np.isfinite(p) & (p > 0)
    if bo.sum() < 8:
        return _resultat("FAIL", motiu="perfil massa curt", n=int(bo.sum()))
    r, p = r[bo], p[bo]
    pujades = p[1:] / p[:-1] - 1.0
    dolentes = np.flatnonzero(pujades > tolerancia_relativa)
    pitjor = float(pujades.max()) if pujades.size else 0.0
    ok = dolentes.size == 0
    return _resultat("PASS" if ok else "FAIL", n_anells=int(p.size),
                     pujada_maxima_relativa=round(pitjor, 6),
                     tolerancia_relativa=tolerancia_relativa,
                     n_anells_que_pugen=int(dolentes.size),
                     radis_que_pugen_rsol=[round(float(r[i + 1]), 4) for i in dolentes[:20]],
                     avaluada_abans_de_k_q=True)


# ---------------------------------------------------------------- F
def porta_f_mescla(mostres: list[dict], *, limit_relatiu: float = 1e-3) -> dict:
    """F · el compost ha de ser EXACTAMENT la mescla declarada.

    Cada mostra porta els pesos i els valors de tots els fotogrames que hi
    contribueixen més el valor que el compost hi té. Es recalcula Σ(wJ)/Σw i,
    a més, es torna a sumar amb els termes **barrejats**: una composició alfa
    de Photoshop depèn de l'ordre i aquí no ho pot fer.
    """
    if not mostres:
        return _resultat("FAIL", motiu="cap mostra")
    pitjor = 0.0; pitjor_id = None; pitjor_ordre = 0.0
    rng = np.random.default_rng(20260823)
    for m in mostres:
        w = np.asarray(m["pesos"], float); v = np.asarray(m["valors"], float)
        d = float(w.sum())
        if d <= 0:
            continue
        g = float((w * v).sum() / d)
        obs = float(m["compost"])
        rel = abs(g - obs) / max(abs(obs), 1e-30)
        k = rng.permutation(w.size)
        g2 = float((w[k] * v[k]).sum() / w[k].sum())
        rel_ordre = abs(g2 - g) / max(abs(g), 1e-30)
        if rel > pitjor:
            pitjor, pitjor_id = rel, m.get("id")
        pitjor_ordre = max(pitjor_ordre, rel_ordre)
    ok = pitjor < limit_relatiu and pitjor_ordre < limit_relatiu
    return _resultat("PASS" if ok else "FAIL", n_mostres=len(mostres),
                     desviacio_relativa_maxima=float(f"{pitjor:.6g}"),
                     mostra_pitjor=pitjor_id, limit_relatiu=limit_relatiu,
                     desviacio_per_ordre_maxima=float(f"{pitjor_ordre:.6g}"))


# ---------------------------------------------------------------- G
def envolupant_decreixent(v, w=None) -> np.ndarray:
    """Regressió isotònica DECREIXENT (pool adjacent violators), pesada."""
    v = np.asarray(v, float)
    w = np.ones_like(v) if w is None else np.asarray(w, float)
    val, pes, n = [], [], []
    for x, p in zip(v, w):
        val.append(x); pes.append(p); n.append(1)
        while len(val) > 1 and val[-2] < val[-1]:
            x2 = val.pop(); p2 = pes.pop(); n2 = n.pop()
            x1 = val.pop(); p1 = pes.pop(); n1 = n.pop()
            val.append((x1 * p1 + x2 * p2) / (p1 + p2))
            pes.append(p1 + p2); n.append(n1 + n2)
    return np.repeat(np.array(val), np.array(n))


def porta_g_envolupant(radis: np.ndarray, perfil: np.ndarray, pesos: np.ndarray | None = None,
                       *, limit: float = 1.30) -> dict:
    """G · l'excés sobre l'envolupant isotònica decreixent ha de ser < 1,30.

    Sense finestra triada a mà: una de curta segueix l'anell i el fa invisible,
    i una de llarga confon una pujada legítima amb un defecte.

    ⚠️ **AQUESTA PORTA ÉS PER AL PERFIL D'AMPLITUD D'UN PAS ALT, NO PER A LA
    LLUMINÀNCIA.** Mesurada el 23-08 sobre un perfil de corona `r^-2,5`, amb el
    límit d'1,30 deixa passar:

    | defecte injectat | excés que dona | veredicte |
    |---|---:|---|
    | anell d'1 a 9 anells, ×1,45 | 1,17–1,23 | PASS |
    | graó multiplicatiu ×1,40 | 1,15 | PASS |
    | anomalia ×2,00 | 1,35–1,55 | FAIL |

    El motiu és que el PAVA **absorbeix** una pujada agrupant-la amb els veïns,
    i com més fort baixa el perfil, més se n'hi amaga. O sigui que contra un
    graó de fusió de la lluminància **no té dents**: per a això hi ha
    `porta_e_graons_de_fusio`, que mira exactament els radis on canvia
    l'esglaó d'exposició dominant.
    """
    r = np.asarray(radis, float); p = np.asarray(perfil, float)
    bo = np.isfinite(p) & (p > 0)
    if bo.sum() < 8:
        return _resultat("FAIL", motiu="perfil massa curt", n=int(bo.sum()))
    r, p = r[bo], p[bo]
    w = None if pesos is None else np.asarray(pesos, float)[bo]
    env = envolupant_decreixent(p, w)
    exc = p / np.maximum(env, 1e-30)
    i = int(np.argmax(exc))
    ok = float(exc.max()) < limit
    return _resultat("PASS" if ok else "FAIL", exces_maxim=round(float(exc.max()), 5),
                     radi_de_l_exces_rsol=round(float(r[i]), 4), limit=limit,
                     n_anells=int(p.size))


def porta_rectangle(imatge: np.ndarray, centre: tuple[float, float] | None = None,
                    *, n_sectors: int = 24, minima_variacio: float = 0.15,
                    r_ocultador_px: float | None = None,
                    marge_ocultador: float = 1.10) -> dict:
    """NORMA DEL RECTANGLE · el que falti ha de faltar per COBERTURA, no per un cercle.

    ⛔ Cap filtre ni cap màscara no es retalla mai a una circumferència: queden
    halos. L'única cosa que pot deixar un píxel sense valor és que no hi hagi
    dada. Però «no hi ha dada» té una forma reconeixible: la petjada del sensor
    és un RECTANGLE, o sigui que el radi fins on arriba la dada **depèn de
    l'azimut** —d'un factor √2 entre el costat i la cantonada, com a mínim—.
    Un retall circular arriba igual de lluny a tots els azimuts.

    La porta no compta cantonades buides —n'hi pot haver de legítimes—: mesura
    la forma de la frontera. Si és una circumferència, l'ha posada algú.

    ⛔ **I la frontera INTERIOR també.** Fins al 24-08-2026 aquesta porta només
    mirava `rmax` per sector, o sigui que **no podia fallar** davant d'un tall
    circular interior ni d'una rampa de pes circular —hi donava `PASS` amb
    `variacio_del_radi_maxim = 0,523`—, contra la regla del capdamunt d'aquest
    mateix fitxer: una porta que no pot fallar no és una porta.

    La frontera interior té un cas legítim, i només un: **l'ocultador**, que és
    la Lluna i és un cercle de radi conegut. Per això es passa `r_ocultador_px`:
    un forat circular fins a `marge_ocultador` vegades aquell radi és la Lluna i
    passa; un forat circular **més enllà** l'ha posat algú. Sense
    `r_ocultador_px` la comprovació interior no s'executa i el rebut ho diu, per
    no convertir un silenci en un aprovat.
    """
    v = np.isfinite(imatge)
    h, w = v.shape
    cy, cx = ((h - 1) / 2.0, (w - 1) / 2.0) if centre is None else (centre[1], centre[0])
    frac = float(v.mean())
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - cx, yy - cy)
    aa = np.arctan2(yy - cy, xx - cx)
    ia = np.clip(((aa + math.pi) / (2 * math.pi) * n_sectors).astype(int), 0, n_sectors - 1)
    rmax = np.zeros(n_sectors)
    for k in range(n_sectors):
        m = (ia == k) & v
        rmax[k] = float(rr[m].max()) if m.any() else 0.0
    if rmax.max() <= 0:
        return _resultat("FAIL", motiu="cap píxel vàlid", mida=[int(h), int(w)])
    variacio = float((rmax.max() - rmax.min()) / rmax.max())
    circular = variacio < minima_variacio

    # ---- frontera interior
    interior = {"comprovada": False,
                "motiu": "no s'ha declarat r_ocultador_px; la comprovació interior no s'ha fet"}
    dolent_dins = False
    if r_ocultador_px is not None and r_ocultador_px > 0:
        rmin = np.full(n_sectors, np.nan)
        for k in range(n_sectors):
            m = (ia == k) & v
            rmin[k] = float(rr[m].min()) if m.any() else np.nan
        b = np.isfinite(rmin)
        if b.sum() >= n_sectors // 2:
            rm = rmin[b]
            var_int = float((rm.max() - rm.min()) / max(rm.max(), 1e-9))
            circ_int = var_int < minima_variacio
            fora = float(np.median(rm)) > marge_ocultador * r_ocultador_px
            dolent_dins = bool(circ_int and fora)
            interior = {"comprovada": True,
                        "radi_minim_px": [round(float(x), 1) for x in rmin],
                        "radi_minim_median_px": round(float(np.median(rm)), 1),
                        "r_ocultador_px": round(float(r_ocultador_px), 1),
                        "variacio_del_radi_minim": round(var_int, 4),
                        "es_circular": bool(circ_int),
                        "mes_enlla_de_l_ocultador": fora,
                        "frontera": ("CIRCULAR i MÉS ENLLÀ DE L'OCULTADOR: l'ha posada algú"
                                     if dolent_dins else
                                     "circular i a l'ocultador: és la Lluna" if circ_int else
                                     "depèn de l'azimut")}
    return _resultat("FAIL" if (circular or dolent_dins) else "PASS",
                     fraccio_valida=round(frac, 6),
                     variacio_del_radi_maxim=round(variacio, 4),
                     minima_exigida=minima_variacio,
                     radi_maxim_px=[round(float(x), 1) for x in rmax],
                     frontera=("CIRCULAR (algú ha retallat)" if circular
                               else "depèn de l'azimut: és la petjada del sensor"),
                     frontera_interior=interior,
                     mida=[int(h), int(w)])


def porta_e_graons_de_fusio(radis: np.ndarray, perfil: np.ndarray,
                            radis_transicio: list[float], *,
                            limit_relatiu: float = 0.02, ample_mediana: int = 21,
                            marge_dex: float = 0.012) -> dict:
    """E2 · cap graó multiplicatiu allà on canvia l'esglaó d'exposició dominant.

    Aquesta és la porta que la G no pot fer. Un compost HDR mal escalat —temps
    d'exposició nominals en lloc dels físics, un fosc mal restat, un factor de
    fusió inventat— no trenca la monotonia ni sobresurt de l'envolupant: hi
    posa un **salt multiplicatiu** exactament al radi on el fotograma que mana
    passa a ser un altre. Se sap on són aquests radis, o sigui que s'hi mira.

    ⛔ **Ni extrapolar rectes ni extrapolar polinomis serveix.** El perfil de la
    corona és brutalment corbat en log-log —mesurat a la Vixen, el pendent va de
    −11,1 a 1,09 R☉ fins a −1,2 a 2,1 R☉—, i extrapolar dos ajustos a banda i
    banda d'un punt llegeix aquella curvatura com un graó: amb rectes donava
    −20 % a TOTES les transicions i amb paràboles fins a +7 %, sempre del mateix
    signe, sobre un perfil net i sense cap defecte.

    El que sí que funciona: la **derivada logarítmica** d'un perfil llis també
    és llisa, i un graó hi posa una punta local. L'estadístic és la punta de la
    derivada respecte de la seva pròpia mediana mòbil, i **el nul no es tria:
    són els radis que NO són transicions**. La pregunta que la porta contesta és
    exactament la bona: *el perfil és menys llis a les transicions que a la
    resta de radis?*
    """
    r = np.asarray(radis, float); p = np.asarray(perfil, float)
    bo = np.isfinite(p) & (p > 0) & np.isfinite(r) & (r > 0)
    r, p = r[bo], p[bo]
    if r.size < 60 or not radis_transicio:
        return _resultat("FAIL", motiu="perfil massa curt o cap transició declarada",
                         n=int(r.size), n_transicions=len(radis_transicio))
    lr, lp = np.log10(r), np.log10(p)
    w = ample_mediana if ample_mediana % 2 else ample_mediana + 1
    k = w // 2
    # ⛔ El pas en log r és LOCAL, no un de sol. Amb calaixos uniformes en r,
    # `diff(log r)` va com 1/r i varia un factor 4,5 entre 1,15 i 5,2 R☉.
    # Multiplicar per la mediana convertia la punta de la derivada en graó amb
    # un error de fins a ×3,5, i la calibració per injecció, que també era una
    # sola mediana, no ho corregia. Mesurat el 24-08-2026 injectant un graó real
    # del +5 %: la porta en deia +1,42 % a 1,20 R☉ i +8,33 % a 5,00 —un factor
    # **5,9** de sensibilitat entre extrems— i les CINC transicions reals del
    # pilot (1,175 · 1,266 · 1,418 · 1,570 · 2,097 R☉) queien totes a la meitat
    # cega. El `pitjor_grao` de −0,49 % que es va publicar corresponia de veritat
    # a un graó d'aproximadament **−1,7 %**.
    dlr_local = np.gradient(lr)

    def punta(logp):
        st = np.gradient(logp, lr)
        llis = np.array([np.median(st[max(0, i - k):i + k + 1]) for i in range(st.size)])
        return (st - llis) * dlr_local * math.log(10.0)

    graó = punta(lp)

    prop = np.zeros(r.size, bool)
    for rt in radis_transicio:
        prop |= np.abs(lr - math.log10(rt)) <= marge_dex
    lluny = ~prop
    lluny[:k] = False
    lluny[-k:] = False
    if prop.sum() < 1 or lluny.sum() < 20:
        return _resultat("FAIL", motiu="mostra insuficient per calibrar el nul",
                         n_prop=int(prop.sum()), n_lluny=int(lluny.sum()))

    # ⛔ L'estadístic NO és el graó: és la punta que el graó deixa a la
    # derivada, i la mediana mòbil se'n menja una part. Es calibra INJECTANT un
    # graó conegut a radis sense transició i mirant què en surt. Mesurat: la
    # resposta és d'un factor ~0,22, o sigui que sense calibrar la porta
    # infravalorava els graons quatre vegades i mitja.
    # ⛔ I la resposta també és LOCAL: es mesura a molts radis i s'interpola,
    # perquè el que queda de dependència amb el radi (l'amplada de la mediana
    # mòbil en dex canvia amb r) no el tapa un sol número.
    prova = 0.05
    respostes = []
    idxs = []
    cand = np.flatnonzero(lluny)
    for j3 in cand[::max(1, cand.size // 24)]:
        q = lp.copy()
        q[j3:] += math.log10(1.0 + prova)
        respostes.append(abs(punta(q)[j3] - graó[j3]) / prova)
        idxs.append(j3)
    if respostes:
        resposta_arr = np.interp(np.arange(r.size), np.array(idxs, float),
                                 np.array(respostes, float))
    else:
        resposta_arr = np.ones(r.size)
    resposta_arr = np.maximum(resposta_arr, 1e-3)
    resposta = float(np.median(resposta_arr))

    graó_cal = graó / resposta_arr
    nul99 = float(np.percentile(np.abs(graó_cal[lluny]), 99))
    i_pitjor = int(np.flatnonzero(prop)[np.argmax(np.abs(graó_cal[prop]))])
    pitjor = float(graó_cal[i_pitjor])
    ok = abs(pitjor) <= max(limit_relatiu, nul99)
    detall = []
    for rt in radis_transicio:
        m = np.abs(lr - math.log10(rt)) <= marge_dex
        if not m.any():
            continue
        j2 = int(np.flatnonzero(m)[np.argmax(np.abs(graó_cal[m]))])
        detall.append({"radi_rsol": round(float(rt), 4),
                       "graó": round(float(graó_cal[j2]), 6),
                       "radi_del_maxim": round(float(r[j2]), 4)})
    return _resultat("PASS" if ok else "FAIL", n_transicions_avaluades=len(detall),
                     limit_relatiu=limit_relatiu,
                     nul_p99_sense_transicio=round(nul99, 6),
                     resposta_calibrada_per_injeccio=round(resposta, 5),
                     limit_efectiu=round(max(limit_relatiu, nul99), 6),
                     pitjor_radi_rsol=round(float(r[i_pitjor]), 4),
                     pitjor_grao=round(pitjor, 6), graons=detall,
                     criteri=("la punta de la derivada logarítmica a les transicions no pot "
                              "superar la que el mateix perfil té on no n'hi ha"))


# ---------------------------------------------------------------- H · artefactes de la fase 3
def porta_h_circular(rms_circ: float, rms_detall: float, *,
                     maxim_fraccio: float = 0.06) -> dict:
    """H1 · cap anell concèntric al detall.

    L'estadístic és el **rms de la mediana azimutal per anell** dividit pel rms
    del detall: quina fracció del detall que declarem és una circumferència
    centrada al Sol. Un anell concèntric és sempre un artefacte —la corona no
    té simetria circular més enllà de la caiguda radial, que el NRGF ja treu—,
    o sigui que el criteri és tan aprop de zero com la mesura permeti.

    ⛔ **El límit no es tria a ull.** El terra d'aquesta mesura és l'error típic
    de la mediana d'un anell: 1,25·σ/√n amb n ≈ 3.300 px per anell dona 0,022 σ,
    o sigui un 2,2 % del rms del detall. El límit va al **6 %**, prop de tres
    vegades el terra. Mesurat el 24-08-2026 abans d'arreglar-ho: **57 %**.
    """
    if not (math.isfinite(rms_circ) and math.isfinite(rms_detall)) or rms_detall <= 0:
        return _resultat("FAIL", motiu="mesura no finita",
                         rms_circular=rms_circ, rms_detall=rms_detall)
    frac = rms_circ / rms_detall
    return _resultat("PASS" if frac <= maxim_fraccio else "FAIL",
                     rms_circular=round(rms_circ, 8), rms_detall=round(rms_detall, 8),
                     fraccio=round(frac, 5), maxim_fraccio=maxim_fraccio,
                     terra_estimat=0.022,
                     criteri="rms de la mediana azimutal per anell <= 6 % del rms del detall")


def porta_h_costures(per_frontera: list[dict], *, maxim_sigmes: float = 3.0) -> dict:
    """H2 · cap vall al detall que segueixi una frontera de fusió HDR.

    Les costures **no són circulars** —segueixen isofotes, i per això la porta
    H1 no les veu i cap prova radial no les havia vist mai—. L'estadístic és el
    contrast del detall al llarg de cada isofota de frontera, en unitats de la
    dispersió entre sectors azimutals de la MATEIXA isofota.

    ⛔ I porta **controls**: isofotes que NO són fronteres de fusió. Si els
    controls surten igual de significatius que les fronteres, el que es mesura
    no és la costura sinó el mètode —això és exactament el que va passar el
    24-08-2026, quan quatre isofotes de control van donar de 2,7 a 3,8 σ, els
    mateixos valors que les fronteres, i van desmentir un «60 σ» que jo havia
    declarat—. La porta compara **frontera contra control**, mai una frontera
    contra zero.

    Cada element: `{"nom": str, "es_frontera": bool, "contrast": float,
    "sigma": float}` amb el contrast en fracció (negatiu = vall).
    """
    fr = [d for d in per_frontera if d.get("es_frontera")]
    ct = [d for d in per_frontera if not d.get("es_frontera")]
    if len(fr) < 1 or len(ct) < 2:
        return _resultat("FAIL", motiu="calen almenys una frontera i dos controls",
                         n_fronteres=len(fr), n_controls=len(ct))
    def _z(d):
        s = float(d.get("sigma", math.nan))
        return abs(float(d["contrast"])) / s if s > 0 and math.isfinite(s) else math.inf
    z_fr = {d["nom"]: _z(d) for d in fr}
    z_ct = {d["nom"]: _z(d) for d in ct}
    # el terra és el pitjor control: el mètode mateix ja dona això sense costura
    terra = max(z_ct.values())
    limit = max(maxim_sigmes, terra)
    pitjor = max(z_fr, key=lambda k: z_fr[k])
    ok = all(v <= limit for v in z_fr.values())
    return _resultat("PASS" if ok else "FAIL",
                     sigmes_per_frontera={k: round(v, 3) for k, v in z_fr.items()},
                     sigmes_per_control={k: round(v, 3) for k, v in z_ct.items()},
                     pitjor_frontera=pitjor, pitjor_sigmes=round(z_fr[pitjor], 3),
                     terra_dels_controls=round(terra, 3), limit_derivat=round(limit, 3),
                     criteri=("cap frontera de fusió pot destacar per damunt del pitjor "
                              "control; el límit se'l calibren els controls, no es tria"))


def porta_h_esglaons_px(ratios: dict[str, float], sigmes: dict[str, float], *,
                        maxim: float = 0.004) -> dict:
    """H3 · coherència entre esglaons d'exposició mesurada **píxel a píxel**.

    És la mateixa pregunta que F0 —dos esglaons han de mesurar la mateixa
    corona— amb un instrument mil vegades més fi. F0 compara **medianes d'anell
    sencer** amb dos a quatre fotogrames per esglaó i té un terra de precisió
    del 2,5 al 4,3 %; les costures que Pere va marcar el 24-08-2026 valen el
    0,2 %, **deu vegades per sota del que F0 pot resoldre**. Aquí es compara
    cada esglaó amb el veí als milions de píxels on tots dos són vàlids, i el
    terra baixa a ~0,01 %.

    ⛔ Aquesta és la mesura que faltava: el codi de la fase 2 ja deia des del
    23-08 que «l'amplitud del colze és proporcional al DESACORD entre esglaons»
    i que «la causa arrel va per la coherència entre esglaons, no per la
    rampa», però la porta que ho havia de vigilar no tenia potència per veure-ho.

    `ratios[parell] = mediana(J_llarg / J_curt) − 1` a la zona de solapament.
    """
    if not ratios:
        return _resultat("FAIL", motiu="cap parell d'esglaons mesurat")
    pitjor = max(ratios, key=lambda k: abs(ratios[k]))
    dolents = {k: round(v, 6) for k, v in ratios.items() if abs(v) > maxim}
    return _resultat("PASS" if not dolents else "FAIL",
                     desacord_per_parell={k: round(v, 6) for k, v in ratios.items()},
                     sigma_per_parell={k: round(v, 7) for k, v in sigmes.items()},
                     pitjor_parell=pitjor, pitjor_desacord=round(ratios[pitjor], 6),
                     parells_que_fallen=dolents, maxim=maxim, n_parells=len(ratios),
                     criteri=("|mediana(J_llarg/J_curt) − 1| <= 0,4 % a cada parell "
                              "d'esglaons veïns, mesurat píxel a píxel"))


def porta_h4_jutge_creuat(referencia: dict, candidat: dict, *,
                          minim_bandes: float = 0.8, tolerancia: float = 0.002) -> dict:
    """H4 · ⛔ **Cap correcció es declara bona sense l'altre tren.**

    És la porta que hauria evitat l'error recurrent del 24-08-2026: quatre
    vegades vaig declarar un artefacte arreglat i quatre vegades Pere el va veure
    a la imatge. Cada estadístic que em vaig inventar tenia un punt cec —cap
    control, finestra més gran que la separació entre costures, mediana azimutal
    que dilueix el que és local—, i el pitjor de tots va ser una resta per sector
    que **millorava el seu propi número ×8 mentre treia corona**.

    El jutge no comparteix els punts cecs perquè no comparteix l'instrument: la
    Sony i la Vixen veuen la mateixa corona amb una altra òptica, un altre
    sensor, un altre fosc, un altre flat, una altra escala d'exposicions i unes
    altres fronteres de fusió. Per tant:

    > una correcció que treu **artefacte** fa **pujar** la correlació entre trens;
    > una que treu **corona** la fa **baixar**.

    Mesurat: les dues passades globals 0,894 → 0,952 (PASS); la resta per sector
    0,930 → 0,849 (FAIL).

    ⚠️ **Límit**: els dos trens comparteixen llenç, warp, màscara lunar i filtre.
    Un artefacte d'aquelles etapes també correlacionaria i el jutge no el veuria.
    """
    claus = [k for k in referencia if k in candidat
             and math.isfinite(referencia[k]) and math.isfinite(candidat[k])]
    if len(claus) < 3:
        return _resultat("FAIL", motiu="calen almenys tres bandes comparables",
                         n_bandes=len(claus))
    delta = {k: candidat[k] - referencia[k] for k in claus}
    milloren = sum(1 for k in claus if delta[k] > -tolerancia)
    ok = milloren >= minim_bandes * len(claus) and sum(delta.values()) > 0
    return _resultat("PASS" if ok else "FAIL",
                     delta_per_banda={k: round(v, 5) for k, v in delta.items()},
                     delta_mitja=round(float(sum(delta.values()) / len(claus)), 5),
                     bandes_que_milloren=milloren, n_bandes=len(claus),
                     minim_bandes=minim_bandes, tolerancia=tolerancia,
                     criteri=("la correlació amb l'ALTRE TREN ha de pujar; si baixa, "
                              "la correcció treu corona i no artefacte"))
