"""FASE 3 · Filtres — només presentació. Res que canviï el que la dada vol dir.

⛔⛔ **NORMA DEL RECTANGLE**: cap filtre es retalla a cap circumferència. L'única
cosa que l'atura és que no hi hagi dada.

⏭️ **El detall va per la MEDIANA de les tres realitzacions de canal**
(`research/107`): cada canal compon cada radi amb un joc de fotogrames diferent,
i la mediana mata l'anomalia que això fabrica sense matar l'estructura real.

⏭️ **La BASE va per la CADENA DE COLOR SENCERA** (`research/109`): matriu de
color de la càmera, UNA corba escalar sobre la lluminància, i el croma restituït
a baixa freqüència. ⛔ Tonificar canal a canal fa DERIVAR el color amb el radi
(R/G d'1,06 a 1,35 amb la dada plana a 1,76) i, amb àncora per canal, la imatge
surt directament MONOCROMA.

⏭️ **El cel es queda a la base visual** (Brno): el terra és cel, no negre. Els
FITS lineals amb el cel restat continuen sent el producte científic.
"""

from __future__ import annotations

import time

import numpy as np
import cv2
from astropy.io import fits

import comu

SNR_REF = 30.0


def gauss(a, s):
    k = int(6 * s) | 1
    return cv2.GaussianBlur(a, (k, k), s)


def suau_mask(a, m, s):
    num = gauss(np.where(m, a, 0.0).astype(np.float32), s)
    den = gauss(m.astype(np.float32), s)
    return np.where(den > 1e-6, num / np.maximum(den, 1e-9), 0.0).astype(np.float32)


# fuita del soroll BLANC de la banda fina (λ<5 px) a la banda mitjana, mesurada
# amb soroll sintètic sobre els mateixos nuclis (1,2 · 2,5 · 10):
BETA_FUITA_SOROLL = 0.0128


def suavitza_sn(F, m, rad=None, t=0.18, smax=16.0):
    """El detall es suavitza allà on el SOROLL mana — NORMA DE PERE (27-08).

    «Tots els filtres tenen encara un fons molt sorollós, molt diferent dels
    passa-alt que faig manualment.» Mesurat: a partir de ~3 R☉ la banda fina
    (λ<5 px, que a la corona només pot ser soroll) iguala o supera la banda
    estructurada (fina/mitjana 1,24 a 3-3,5 R☉ i 1,49 a 7-7,5). ⛔ L'atenuació
    per S/N no ho pot curar: atenua soroll i estructura PER IGUAL. L'única cosa
    que separa soroll blanc d'estructura és PROMITJAR: la resolució ha de
    seguir el senyal/soroll (la filosofia de l'ACHF de Druckmüller).

    Autocalibrat, sense cap mapa extern: n_loc = rms local de la banda fina;
    s_loc = rms local de la banda mitjana, neta de la fuita β del soroll blanc;
    σ(x) = n/(2√π·t·s), que és la σ exacta perquè el soroll blanc residual
    quedi a t vegades l'estructura (fórmula validada: la reducció mesurada del
    soroll blanc sota una gaussiana σ clava 1/(2σ√π)). S'aplica amb una
    piràmide gaussiana i barreja contínua per píxel — cap llindar dur, cap
    circumferència (norma del rectangle: el mapa és de DADA, no de radi).

    Calibrat al run 018: t=0,18 i una passada deixen el fons exterior a
    fina/mitjana 0,21-0,32 —el nivell de la corona interior— amb σ p90
    exterior de 5,8 px, per sota dels ~15 px de l'estructura real més fina
    (0,5° a 4 R☉, `research/82`). La zona amb senyal no es mou (0,21 → 0,20).
    """
    F0 = np.where(m, F, 0.0).astype(np.float32)
    fina = F0 - gauss(F0, 1.2)
    n2 = suau_mask(fina * fina, m, 24.0)
    mit = gauss(F0, 2.5) - gauss(F0, 10.0)
    m2 = suau_mask(mit * mit, m, 24.0)
    s2 = np.maximum(m2 - BETA_FUITA_SOROLL * n2, 1e-12)
    sig = np.clip(np.sqrt(n2) / (2.0 * np.sqrt(np.pi) * t * np.sqrt(s2)),
                  0.0, smax).astype(np.float32)
    sig[sig < 0.7] = 0.0
    nivells = [0.5, 1.0, 2.0, 4.0, 8.0, smax]
    pir = [F0] + [gauss(F0, s_) for s_ in nivells[1:]]
    ls = np.array([np.log2(s_ / 0.5) for s_ in nivells], np.float32)
    lev = np.where(sig > 0, np.log2(np.maximum(sig, 0.5) / 0.5), 0.0).astype(np.float32)
    li = np.clip(np.searchsorted(ls, lev) - 1, 0, len(nivells) - 2)
    frac = np.clip((lev - ls[li]) / np.maximum(ls[li + 1] - ls[li], 1e-9),
                   0, 1).astype(np.float32)
    out = np.zeros_like(F0)
    for i in range(len(nivells) - 1):
        k = li == i
        if k.any():
            out[k] = pir[i][k] * (1 - frac[k]) + pir[i + 1][k] * frac[k]
    out = np.where(sig > 0, out, F0)
    return out.astype(np.float32), sig


def perfil_azimutal(a, rad, m, nb=900):
    """Perfil robust: log r + pes de COBERTURA + suavitzat.

    ⛔ Sense això l'NRGF fabrica un disc amb vora dura: més enllà del radi on
    l'anell deixa de caure sencer dins del rectangle (5,21 R☉), la mitjana
    azimutal es calcula només amb els CANTONS —azimuts fixos, a la diagonal— i
    salta. La cura no és retallar (norma del rectangle) sinó fer el perfil
    incapaç de saltar.

    ⛔ **ES TORNA INTERPOLAT, NO PER CALAIX** (27-08). Tornant `mu[idx]` el
    perfil és una **escala de 900 graons en radi** i, en restar-lo, cada graó
    queda com un **anell de vora dura** al camp aplanat. El passa-alt i l'MGN
    en viuen: són justament els filtres que conserven les vores. Pere els va
    marcar mirant el PSB de prop —a 4,5 R☉ l'anell hi passa a 45° i semblen
    ratlles diagonals—. Mesurat: λ creix amb el radi com mana el calaix
    logarítmic (4,8 px a 1,8 R☉, 25,8 px a 7 R☉) i la seva raó amb la predicció
    de 1200 calaixos era **1,33 = 1200/900**, que és el que va identificar
    aquesta funció i no `anivella`.
    ⚠️ El perfil ja es SUAVITZAVA (nucli de 14 calaixos), i no servia de res:
    suavitzar el perfil no treu els graons de com s'APLICA.
    """
    rmax = float(rad[m].max())
    lo = float(np.log10(20.0 / rmax))
    lr = np.log10(np.maximum(rad, 1.0) / rmax)
    idx = np.clip(((lr - lo) / (0.0 - lo) * nb).astype(np.int32), 0, nb - 1)
    c = np.bincount(idx[m], None, nb); s1 = np.bincount(idx[m], a[m], nb)
    mu = np.where(c > 30, s1 / np.maximum(c, 1), np.nan)
    s2 = np.bincount(idx[m], (a[m] - mu[idx[m]]) ** 2, nb)
    sd = np.sqrt(np.where(c > 30, s2 / np.maximum(c, 1), np.nan))
    ctot = np.bincount(idx.ravel(), None, nb)
    cob = c / np.maximum(ctot, 1)
    w = np.where(np.isfinite(mu), np.clip(cob, 0.02, 1.0) ** 2, 0.0)
    ker = np.exp(-0.5 * (np.arange(-60, 61) / 14.0) ** 2)

    def suau(v):
        x = np.where(np.isfinite(v), v, 0.0) * w
        return np.where(np.convolve(w, ker, "same") > 1e-6,
                        np.convolve(x, ker, "same") / np.maximum(np.convolve(w, ker, "same"), 1e-9),
                        np.nan)
    mu = suau(mu); sd = suau(sd)
    for v in (mu, sd):
        bo = np.isfinite(v)
        if bo.any():
            v[~bo] = np.interp(np.flatnonzero(~bo), np.flatnonzero(bo), v[bo])
    # ⛔ CONTINU: interpolació lineal entre centres de calaix. Exacte al centre
    #    i sense cap graó entremig.
    pos = np.clip((lr - lo) / (0.0 - lo) * nb - 0.5, 0.0, nb - 1.0).astype(np.float32)
    xb = np.arange(nb, dtype=np.float32)
    muc = np.interp(pos, xb, mu).astype(np.float32)
    sdc = np.interp(pos, xb, sd).astype(np.float32)
    return muc, np.maximum(sdc, 1e-9), cob, idx


def anivella(y, rad, m, passades=3, nb=1200, ks=3.0):
    """H1 · el NIVELL de cada anell ha de ser 0,5.

    ⛔ En Superposar, un nivell diferent de 0,5 **enfosqueix o aclareix un anell
    sencer**. Mesurat al run del 26-08: l'NRGF baixava a 0,249 a 2 R☉ (el bol
    fosc que es veia) i l'MGN feia anell clar → fosc → clar. Res que sigui
    funció NOMÉS del radi no pot sobreviure a la capa de detall.

    ⚠️ Sobre dades RETALLADES no funciona: la massa retallada no es mou i la
    cura divergeix. Per això va SEMPRE després de la compressió suau.

    ⚠️ **La resolució ha de poder seguir la vora més estreta.** Amb la corona
    interior recuperada (des d'1,013 R☉), el nivell del passa-alt cau de
    **0,931 a 1,07 R☉ a 0,331 a 1,15**: amb 600 calaixos i nucli σ=4 el
    resultat es quedava a 0,067 i **no passava**; amb **1200 i σ=3** cau a
    **0,0084**. Cada calaix és un 0,19 % en radi i hi caben ~20.000 píxels,
    o sigui que la mediana azimutal hi continua sent robusta.

    ⛔ **LA CORRECCIÓ S'APLICA INTERPOLADA, NO PER CALAIX** (27-08). Restant
    `sm[idx]` —el valor del calaix— la cura és una **escala de 1200 graons en
    radi**, i cada graó és un **anell de vora dura**. En Superposar, i sobretot
    al passa-alt i a l'MGN, aquells anells es veuen: Pere els va marcar mirant
    el PSB de prop, on a 4,5 R☉ semblen ratlles diagonals perquè allà l'anell
    passa a 45°. Mesurat: λ creix amb el radi tal com mana el calaix logarítmic
    —4,8 px a 1,8 R☉ i 25,8 px a 7 R☉—, sempre en direcció RADIAL.
    ⚠️ **La porta H1 no ho podia veure**: mesura el NIVELL de cada anell i una
    escala de graons petits el compleix perfectament. Un anell és una FORMA i
    la porta mirava un NIVELL — la mateixa lliçó del `research/111`.
    La cura no canvia què corregeix la funció, només com ho reparteix: en lloc
    del valor del calaix, la **interpolació lineal entre centres de calaix**,
    que és exacta al centre i contínua a tot arreu.
    """
    rmax = float(rad[m].max())
    lo = np.log10(20.0 / rmax)
    lr = np.log10(np.maximum(rad, 1.0) / rmax)
    # posició CONTÍNUA en calaixos (per a la correcció) i índex enter (per a
    # la mediana de cada calaix, que sí que és una estadística per calaix)
    pos = np.clip((lr - lo) / (0.0 - lo) * nb - 0.5, 0.0, nb - 1.0).astype(np.float32)
    idx = np.clip(((lr - lo) / (0.0 - lo) * nb).astype(np.int32), 0, nb - 1)
    tot = np.bincount(idx.ravel(), None, nb)
    ordre = np.argsort(idx[m], kind="stable")
    k2 = int(4 * ks)
    ker = np.exp(-0.5 * (np.arange(-k2, k2 + 1) / ks) ** 2); ker /= ker.sum()
    y = y.copy()
    for _ in range(passades):
        ss = y[m][ordre]; bb = idx[m][ordre]
        n = np.bincount(bb, None, nb); off = np.concatenate([[0], np.cumsum(n)])
        med = np.full(nb, np.nan)
        for k in np.flatnonzero(n > 400):
            med[k] = np.median(ss[off[k]:off[k + 1]])
        w = np.where(np.isfinite(med), np.clip(n / np.maximum(tot, 1), 0.02, 1.0) ** 2, 0.0)
        num = np.convolve(np.where(np.isfinite(med), med, 0.0) * w, ker, "same")
        den = np.convolve(w, ker, "same")
        sm = np.where(den > 1e-9, num / np.maximum(den, 1e-9), np.nan)
        bo = np.isfinite(sm) & (w > 0)
        if not bo.any():
            break
        sm[~bo] = np.interp(np.flatnonzero(~bo), np.flatnonzero(bo), sm[bo])
        # ⛔ CONTÍNUA, no per calaix: `sm[idx]` seria una escala de graons i
        #    cada graó, un anell de vora dura.
        corr = np.interp(pos, np.arange(nb, dtype=np.float32), sm).astype(np.float32)
        y = np.where(m, y - (corr - 0.5), 0.0).astype(np.float32)
    return y


def anells_de_calaix(y, rad, m, nb=(900, 1200), ks=3.0, mostra=200000):
    """PORTA H1b (27-08): queda estructura a la freqüència dels CALAIXOS?

    ⛔ `nivell_per_radi` mesura el nivell mitjà de cada anell, i una escala de
    graons petits el compleix perfectament: per això els anells de `anivella`
    van sobreviure fins que Pere els va veure al PSB. Aquesta mesura mira una
    altra cosa: la **potència del senyal a la freqüència dels calaixos**, que és
    on viuria una escala de graons, contra el fons a freqüències veïnes.

    Torna la raó potència(calaix)/potència(veïnes). 1 = res; >2 = hi ha graons.
    """
    rmax = float(rad[m].max())
    lo = np.log10(20.0 / rmax)
    lr = np.log10(np.maximum(rad, 1.0) / rmax)
    pitjor = 0.0
    for n_ in (nb if isinstance(nb, (tuple, list)) else (nb,)):
        pos = (lr - lo) / (0.0 - lo) * n_
        k = m & (pos > 1) & (pos < n_ - 1)
        ii = np.flatnonzero(k.ravel())
        if len(ii) < 10000:
            continue
        if len(ii) > mostra:
            ii = ii[:: max(1, len(ii) // mostra)]
        v = y.ravel()[ii].astype(np.float64); u = pos.ravel()[ii].astype(np.float64)
        v = v - v.mean()
        pot = lambda f: abs(np.mean(v * np.exp(-2j * np.pi * f * u))) ** 2
        fons = np.median([pot(f) for f in (0.31, 0.37, 0.43, 0.59, 0.67, 0.71)])
        pitjor = max(pitjor, float(pot(1.0) / max(fons, 1e-30)))
    return pitjor


def nivell_per_radi(y, rad, m, r_sol_px, nb=200):
    """Porta H1: la desviació màxima del nivell respecte de 0,5."""
    rmax = float(rad[m].max())
    lo = np.log10(20.0 / rmax)
    idx = np.clip(((np.log10(np.maximum(rad, 1.0) / rmax) - lo) / (0.0 - lo) * nb).astype(np.int32), 0, nb - 1)
    tot = np.bincount(idx.ravel(), None, nb)
    ordre = np.argsort(idx[m], kind="stable")
    ss = y[m][ordre]; bb = idx[m][ordre]
    n = np.bincount(bb, None, nb); off = np.concatenate([[0], np.cumsum(n)])
    pit, rr = 0.0, float("nan")
    r = 10 ** (lo + (np.arange(nb) + 0.5) / nb * (0.0 - lo)) * rmax / r_sol_px
    for k in np.flatnonzero(n > 400):
        if n[k] / max(tot[k], 1) < 0.999:      # anell sencer dins del rectangle
            continue
        v = ss[off[k]:off[k + 1]]
        me = float(np.median(v))
        di = 1.4826 * float(np.median(np.abs(v - me)))
        if di <= 0.02:                          # sense estructura, no hi ha res a jutjar
            continue
        if abs(me - 0.5) > pit:
            pit, rr = abs(me - 0.5), float(r[k])
    return pit, rr


def filtres(run: comu.Run) -> dict:
    t0 = time.time()
    S = run.llegeix_rebut("F1.2_sol_llenc.json")
    LL = S["llenc"]; W, H = LL["W"], LL["H"]; RS = LL["R_sol_px"]
    C = {c: fits.getdata(run.fase(2, f"CORONA_{c}.fits")).astype(np.float32)
         for c in comu.CANALS}
    P = fits.getdata(run.fase(2, "PES_G.fits")).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - H / 2.0, xx - W / 2.0); del yy, xx
    m = comu.mascara_dada(P, rad)
    for c in comu.CANALS:
        m &= np.isfinite(C[c])
    # ⛔ Els filtres de detall NO travessen el limbe lunar. Allà hi ha un esglaó
    #    de diversos ordres de magnitud i el desenfoc s'hi calcula amb el forat
    #    a dins —una mostra d'un sol costat—: el residu es dispara i surt un
    #    ANELL SATURAT que abraça la Lluna. Mesurat el 26-08: el nivell per radi
    #    del passa-alt es disparava a r < 1,02 R☉, o sigui DINS de la Lluna.
    #    ⚠️ Això NO és un filtre circular al camp exterior (norma del rectangle):
    #    és excloure un objecte que ÉS un cercle i que no és corona.
    #    ⚠️ La BASE sí que arriba fins a 1,013 R☉ gràcies a la màscara lunar
    #    per fotograma; el DETALL, no. Entre 1,013 i 1,05 la cobertura és
    #    PARCIAL (del 46 al 99 %) i cada píxel surt d'un joc de fotogrames
    #    diferent: això és una excursió de nivell que depèn NOMÉS del radi, i
    #    la porta H1 la va enxampar (passa-alt 0,358 → 0,053 > 0,05).
    #    ⛔ La cobertura per PES no serveix de vara: està barrejada amb la
    #    brillantor —els plomalls saturen més i tenen menys pes—, i exigir el
    #    50 % del pes assolible deixava fora el 90 % de l'anell d'1,2 R☉.
    #    A 1,05 R☉ la cobertura mesurada és del 99,4 %.
    md = m & (rad > 1.050 * RS)
    # ⏭️ Els filtres es CALCULEN amb `m` (tota la dada, fins a 1,013 R☉) i
    #    només s'ENSENYEN amb `md`. Calcular-los amb `md` posa una vora dura
    #    ENMIG de dada vàlida i el passa-alt s'hi desborda (mesurat: nivell
    #    0,475). Amb el desenfoc omplint de zero fora de la màscara, la vora
    #    real de la dada no esbiaixa res.

    # ⏭️ la base visual porta el CEL posat (el terra ha de ser cel, no negre)
    CEL = {c: fits.getdata(run.fase(2, f"CEL_{c}.fits")).astype(np.float32)
           for c in comu.CANALS}
    u_cam = np.dstack([C[c] + CEL[c] for c in comu.CANALS])
    M = run.matriu; guany = run.color["guany"]
    L, _ = comu.lluminancia(u_cam, M, guany)
    va = comu.ancora(L, rad, m, RS)
    base, ren = comu.render_visual(u_cam, m, va, M, guany)
    del u_cam
    col_dada = comu.mesura_color(C, rad, m, RS)
    col_base = comu.mesura_color({c: base[..., i].astype(np.float64)
                                  for i, c in enumerate(comu.CANALS)}, rad, m, RS)
    # el color RENDERITZAT, en sRGB LINEAL, que és el que es pot comparar amb
    # Brno, amb el DSC06991 i amb la predicció d'extinció
    bl = comu.a_lineal(base)
    col_srgb = comu.mesura_color({c: bl[..., i].astype(np.float64)
                                  for i, c in enumerate(comu.CANALS)}, rad, m, RS)
    del bl
    # ⏭️ CONTROL de tancament HDR (Codex, 26-08): el compost contra un
    # fotograma solt del mateix tren, als MATEIXOS anells.
    # ⛔ guany UNITAT: el control comprova la dada, no el mode de presentació
    _, u_srgb = comu.lluminancia(np.dstack([C[c] + CEL[c] for c in comu.CANALS]),
                                 M, (1.0, 1.0, 1.0))
    rRS = (rad / RS).astype(np.float32)
    # pedestal declarat quan el cos no té marge emmascarat (A7RIIIA)
    pedd = (run.cfg["pedestal_dn"] if run.cfg.get("pedestal_font") == "darks" else None)
    # ⛔ EL CONTROL HA DE SER UNA MITJANA TEMPORAL, com el compost. Amb UN sol
    #    fotograma, la porta mesurava tambe el canvi del cel durant la
    #    totalitat: a la Sony amb els dos apuntaments (104 s de recorregut) el
    #    B/G d'un fotograma va de 0,579 a 0,507 i torna a 0,535 —un 12 %— i la
    #    porta queia al 7,3 % contra un control de t=18 s mentre donava 1,4 %
    #    contra un de t=28 s. Ara jutja la MEDIANA sobre controls repartits en
    #    el temps i DECLARA la dispersio, que es informacio: si es gran, el cel
    #    va canviar. (27-08-2026, research/115.)
    thdr, provats, tots = None, [], []
    for cand in comu.controls_repartits(run)[:8]:
        t = comu.tancament_hdr(u_srgb, m, rRS, cand, M, ped_declarat=pedd)
        provats.append({"fotograma": t["fotograma"], "veredicte": t["veredicte"],
                        "anells": t.get("anells_valids", len(t.get("anells", {})))})
        if t["veredicte"] != "SENSE DADA":
            tots.append(t)
        if len(tots) >= 6:
            break
    if tots:
        sis = [x["sistematic_pct"] for x in tots]
        med = float(np.median(sis))
        thdr = dict(tots[int(np.argmin(np.abs(np.array(sis) - med)))])
        thdr["n_controls"] = len(tots)
        thdr["sistematic_per_control"] = [
            {"fotograma": x["fotograma"], "pct": x["sistematic_pct"]} for x in tots]
        thdr["sistematic_pct"] = med
        thdr["dispersio_entre_controls_pct"] = float(max(sis) - min(sis))
        thdr["jutja"] = ("la MEDIANA sobre controls repartits en el temps "
                         "(el compost es una mitjana temporal)")
        thdr["veredicte"] = "PASSA" if med <= thdr["llindar_pct"] else "NO PASSA"
    # ⏭️ PORTA F3.2 (27-08, de l'auditoria contra Brno): el mateix tancament
    #    però contra la BRILLANTOR. La porta de dalt compara MEDIANES d'anell i
    #    no pot veure un error que depengui del nivell del píxel, que és
    #    justament la forma d'un defecte de fusió HDR: la frontera entre
    #    exposicions és una ISOFOTA, o sigui que viu a un nivell, no a un radi.
    lumA = (u_srgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)).astype(np.float64)
    # ⛔ Mateix tracte que la porta de color: el compost es una mitjana temporal
    #    i el control ha de ser-ho tambe. Amb UN sol fotograma aquesta porta
    #    donava 7,65 % al Run 2 de la Sony —just per sota del llindar— contra un
    #    control de t=18 s, i el cel havia canviat un 12 % de B/G en 100 s.
    tbri, brits = None, []
    for cand in comu.controls_repartits(run)[:8]:
        t = comu.tancament_hdr_brillantor(lumA, m, rRS, cand, M, ped_declarat=pedd)
        if t["veredicte"] != "SENSE DADA":
            brits.append(t)
        if len(brits) >= 6:
            break
    if brits:
        sb = [x["sistematic_pct"] for x in brits]
        mb = float(np.median(sb))
        tbri = dict(brits[int(np.argmin(np.abs(np.array(sb) - mb)))])
        tbri["n_controls"] = len(brits)
        tbri["sistematic_per_control"] = [
            {"fotograma": x["fotograma"], "pct": x["sistematic_pct"]} for x in brits]
        tbri["sistematic_pct"] = mb
        tbri["dispersio_entre_controls_pct"] = float(max(sb) - min(sb))
        tbri["jutja"] = ("la MEDIANA sobre controls repartits, I la DISPERSIO "
                         "entre ells: si el compost no representa cap dels "
                         "controls, la mediana no el salva")
        # ⛔ AQUI LA MEDIANA SOLA NO SERVEIX. Al Run 2 de la Sony els sis
        #    controls surten BIMODALS per apuntament (7,7/9,7/8,5 % els de l'A i
        #    2,0/2,7/2,9 % els del B), i aquells 7-9 % coincideixen amb l'error
        #    de flat mesurat pel dither (research/115 §11): amb dos apuntaments
        #    el compost barreja dues vistes amb calibratges diferents, i aixo es
        #    REAL. Prendre la mediana ho amagaria (5,27 %, passa). Amb la guarda
        #    de dispersio, el senyal es queda a la vista.
        tbri["veredicte"] = ("PASSA" if (mb <= tbri["llindar_pct"]
                                         and tbri["dispersio_entre_controls_pct"]
                                         <= tbri["llindar_pct"])
                             else "NO PASSA")
    del lumA, u_srgb
    if tbri is None:
        raise SystemExit("PORTA F3.2: el tancament per brillantor no s'ha pogut "
                         "computar amb cap fotograma coronal")
    print(f"    tancament HDR per BRILLANTOR: mediana de {tbri.get('n_controls', 1)} "
          f"controls {tbri['sistematic_pct']:.2f} % · dispersió entre ells "
          f"{tbri.get('dispersio_entre_controls_pct', 0):.2f} % · {tbri['veredicte']}",
          flush=True)
    if tbri["veredicte"] != "PASSA":
        raise SystemExit(f"PORTA F3.2: el compost depèn de la BRILLANTOR respecte "
                         f"del fotograma solt ({tbri['sistematic_pct']:.2f} % > "
                         f"{tbri['llindar_pct']:.1f} %)")
    if thdr is None:
        raise SystemExit("PORTA F3: el tancament HDR no s'ha pogut computar amb cap "
                         f"fotograma coronal. Provats: {provats}")
    thdr["candidats_provats"] = provats
    thdr["brillantor"] = tbri
    if thdr.get("dispersio_entre_controls_pct", 0) > 4.0:
        print(f"    ⚠️ els {thdr['n_controls']} controls discrepen entre ells "
              f"{thdr['dispersio_entre_controls_pct']:.1f} %: el cel va canviar "
              f"durant la totalitat", flush=True)
    print(f"    tancament HDR contra {thdr['fotograma']}: mediana R/G "
          f"{thdr['mediana_R/G_pct']:+.1f} % B/G {thdr['mediana_B/G_pct']:+.1f} % · "
          f"sistemàtic {thdr['sistematic_pct']:.1f} % · pitjor {thdr['pitjor_pct']:.1f} % "
          f"· {thdr['veredicte']}", flush=True)
    if thdr["veredicte"] != "PASSA":
        raise SystemExit(f"PORTA F3: el color del compost NO TANCA amb el fotograma solt "
                         f"(sistemàtic {thdr['sistematic_pct']:.1f} % > "
                         f"{thdr['llindar_pct']} %).")
    croma = float(np.percentile((base[..., 0] - base[..., 1])[m], 99)
                  - np.percentile((base[..., 0] - base[..., 1])[m], 1))
    print(f"    mode {run.mode} · guany {tuple(round(g,4) for g in guany)} · "
          f"àncora L = {va:.4g} · croma p1-p99 de R−G = {croma:.4f} · "
          f"gamut acotat al {ren['gamut_acotat_pct']:.2f} %", flush=True)
    if croma < 0.02:
        raise SystemExit(f"PORTA F3: la base és MONOCROMA (croma {croma:.4f} < 0,02).")

    lg = {c: np.where(m & (C[c] > 0), np.log10(np.maximum(C[c], 1e-6)), 0.0).astype(np.float32)
          for c in comu.CANALS}
    # ⛔ El passa-alt i l'MGN es fan sobre el camp APLANAT en radi. Sense això,
    #    a 1,02-1,15 R☉ el desenfoc es calcula amb el forat de la Lluna a dins
    #    —una mostra d'un sol costat—, el residu es dispara i surt un ANELL
    #    SATURAT que abraça la Lluna (mesurat: el passa-alt hi valia exactament
    #    1,000). És el mateix parany que el `distanceTransform` sobre un mapa de
    #    cobertura amb el forat de la Lluna.
    lgp = {}
    for c in comu.CANALS:
        mu, _, _, _ = perfil_azimutal(lg[c], rad, m)
        lgp[c] = np.where(m, lg[c] - mu, 0.0).astype(np.float32)
    F = {}

    def mediana_canals(fn):
        return np.median(np.dstack([fn(c) for c in comu.CANALS]), axis=2).astype(np.float32)

    def nrgf(c):
        mu, sd, _, _ = perfil_azimutal(C[c], rad, m)
        return np.where(m, (C[c] - mu) / sd, 0.0).astype(np.float32)
    F["NRGF"] = mediana_canals(nrgf); print(f"    NRGF [{time.time()-t0:.0f}s]", flush=True)

    def passalt(c):
        # ⛔ `suau_mask` divideix per la màscara, i prop de la vora el nucli és
        #    d'UN SOL COSTAT: el residu s'hi dispara. Com que `lgp` té mitjana
        #    azimutal zero per construcció, omplir de ZERO fora de la màscara
        #    és l'extrapolació correcta i el desenfoc no queda esbiaixat.
        #    Amb `suau_mask` el nivell del passa-alt arribava a 0,475 a la vora
        #    de la màscara; és el mateix mecanisme que al limbe lunar.
        return np.where(m, lgp[c] - gauss(np.where(m, lgp[c], 0.0).astype(np.float32), 24.0),
                        0.0).astype(np.float32)
    F["PASSA_ALT"] = mediana_canals(passalt)

    def mgn(c):
        o = np.zeros((H, W), np.float32)
        for s in (6.0, 12.0, 24.0, 48.0, 96.0):
            z = np.where(m, lgp[c], 0.0).astype(np.float32)
            mu = gauss(z, s); d = np.where(m, lgp[c] - mu, 0.0).astype(np.float32)
            sd = np.sqrt(np.maximum(suau_mask(d * d, m, s), 1e-12))
            o += np.arctan(3.0 * d / sd)
        return np.where(m, o / 5.0, 0.0).astype(np.float32)
    F["MGN"] = mediana_canals(mgn); print(f"    MGN [{time.time()-t0:.0f}s]", flush=True)

    def radial(c):
        nr, na = 1400, 2048
        rr = np.linspace(0, float(rad[m].max()), nr, dtype=np.float32)
        aa = np.linspace(0, 2 * np.pi, na, endpoint=False, dtype=np.float32)
        X = (W / 2.0 + rr[None, :] * np.sin(aa)[:, None]).astype(np.float32)
        Y = (H / 2.0 - rr[None, :] * np.cos(aa)[:, None]).astype(np.float32)
        pol = cv2.remap(lgp[c], X, Y, cv2.INTER_LINEAR, borderValue=0.0)
        pm = cv2.remap(m.astype(np.float32), X, Y, cv2.INTER_LINEAR, borderValue=0.0)
        sm = cv2.GaussianBlur(pol * pm, (1, 61), 0, sigmaY=10.0)
        sd = cv2.GaussianBlur(pm, (1, 61), 0, sigmaY=10.0)
        det = pol - np.where(sd > 1e-6, sm / np.maximum(sd, 1e-9), 0.0)
        y2, x2 = np.mgrid[0:H, 0:W].astype(np.float32)
        r2 = np.hypot(y2 - H / 2.0, x2 - W / 2.0)
        a2 = np.arctan2(x2 - W / 2.0, H / 2.0 - y2) % (2 * np.pi)
        mx = (r2 / rr[-1] * (nr - 1)).astype(np.float32); my = (a2 / (2 * np.pi) * na).astype(np.float32)
        return np.where(m, cv2.remap(det, mx, my, cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_WRAP), 0.0).astype(np.float32)
    F["RADIAL"] = mediana_canals(radial); print(f"    radial [{time.time()-t0:.0f}s]", flush=True)

    # ⏭️ NORMA DE PERE (27-08): el fons dels filtres no pot ser estàtica.
    #    Cada camp de detall es suavitza allà on el soroll mana, ABANS de la
    #    compressió i de mesurar-ne la σ (si no, la σ seria la del soroll).
    print(f"    suavitzat pel S/N (t=0,18):", flush=True)
    sn_info = {}
    for k in sorted(F):
        F[k], sig_ = suavitza_sn(F[k], m)
        ext = m & (rad > 3.0 * RS)
        sn_info[k] = {"t": 0.18, "sigma_mediana_ext_px": float(np.median(sig_[ext])),
                      "sigma_p90_ext_px": float(np.percentile(sig_[ext], 90)),
                      "pct_tocat": float(100 * (sig_[m] > 0).mean())}
        print(f"      {k:10s} σ ext mediana {sn_info[k]['sigma_mediana_ext_px']:4.1f} px · "
              f"p90 {sn_info[k]['sigma_p90_ext_px']:4.1f} px · "
              f"tocat el {sn_info[k]['pct_tocat']:.0f} % del camp", flush=True)
        del sig_

    # atenuació per S/N: segueix la DADA, no cap circumferència
    Pn = P / float(np.nanmax(P))
    snr = np.where(m, C["G"] * np.sqrt(np.maximum(Pn, 0)) / SNR_REF, 0.0)
    aten = (snr ** 2 / (snr ** 2 + 1.0)).astype(np.float32)

    info = {"mode_color": run.mode,
            "color_titol": run.color["titol"],
            "color_per_que": run.color["per_que"],
            "guany": list(guany),
            "matriu_cam_a_sRGB": [[float(x) for x in f] for f in M],
            "corba_to": dict(ren, valor_ancora_L=va,
                             sobre="LLUMINÀNCIA (una sola corba escalar)"),
            "extincio_declarada": comu.EXTINCIO,
            "croma_p1_p99_RmenysG": croma,
            "color_dada": col_dada, "color_base": col_base,
            "color_renderitzat_sRGB_lineal": col_srgb,
            "control_testimoni_DSC06991": comu.control_testimoni(col_srgb),
            "control_tancament_HDR": thdr,
            "veredicte_color_dada": comu.veredicte_color(col_dada),
            "atenuacio_SN": {"ref_DN": SNR_REF,
                             "mediana": float(np.median(aten[md])),
                             "p5": float(np.percentile(aten[md], 5))},
            "mascara_detall": {"r_min_Rsol": 1.050,
                               "pct_de_la_dada": float(100 * md.sum() / max(int(m.sum()), 1)),
                               "per_que": "els filtres no travessen el limbe lunar"},
            "norma_rectangle": "cap filtre retallat a cap circumferència",
            "detall": "mediana de les tres realitzacions de canal (research/107)",
            "suavitzat_SN": dict(sn_info,
                                 per_que="norma de Pere 27-08: el fons no pot ser estàtica; "
                                         "la resolució segueix el S/N mesurat al camp"),
            "filtres": {}}
    np.save(run.fase(3, "BASE_rgb.npy"), base)
    np.save(run.fase(3, "MASCARA.npy"), m)
    np.save(run.fase(3, "MASCARA_DETALL.npy"), md)
    h1_pitjor = 0.0
    for k in sorted(F):
        # ⛔ la σ es mesura ABANS d'atenuar. Mesurant-la després, l'atenuació es
        #    realimenta al guany de pantalla i el retallat passa del 0,4 % al
        #    8,3 %: un píxel retallat no té estructura, és un pegat pla.
        sg = 1.4826 * float(np.median(np.abs(F[k][m] - np.median(F[k][m]))))
        v = (F[k] * aten).astype(np.float32)
        # ⏭️ compressió SUAU: mai un retall dur, que fabrica anells plans
        y = np.where(m, 0.5 + 0.5 * np.tanh(v / (3.0 * max(sg, 1e-9))), 0.5).astype(np.float32)
        n0, r0 = nivell_per_radi(y, rad, md, RS)
        y = np.clip(anivella(y, rad, md), 0, 1).astype(np.float32)
        y = np.where(md, y, 0.5).astype(np.float32)   # 0,5 = neutre en Superposar
        n1, r1 = nivell_per_radi(y, rad, md, RS)
        ret = float(100 * (md & ((y <= 1e-6) | (y >= 1 - 1e-6))).sum() / max(int(md.sum()), 1))
        h1_pitjor = max(h1_pitjor, n1)
        h1b = anells_de_calaix(y, rad, md)
        np.save(run.fase(3, f"DETALL_{k}.npy"), y)
        info["filtres"][k] = {"sigma_robust": sg, "retallats_pct": ret,
                              "H1_nivell_abans": n0, "H1_r_abans": r0,
                              "H1_nivell_despres": n1, "H1_r_despres": r1,
                              "H1b_anells_de_calaix": h1b}
        print(f"    {k:10s} retallats {ret:5.2f} % · nivell per radi "
              f"{n0:.3f} → {n1:.3f} · anells de calaix ×{h1b:.2f}", flush=True)
        # dispersió per anell: si creix cap enfora, és soroll i no estructura
        disp = {}
        for a_, b_ in ((1.2, 1.6), (3.0, 3.5), (5.0, 5.5), (7.0, 7.5), (9.0, 9.5)):
            s_ = md & (rad > a_ * RS) & (rad < b_ * RS)
            if s_.sum() > 1000:
                disp[f"{a_:g}-{b_:g}"] = float(v[s_].std())
        info["filtres"][k]["dispersio_per_anell"] = disp
    info["porta_H1"] = {"pitjor": h1_pitjor, "llindar": 0.05,
                        "que_mesura": "màxim |nivell de l'anell − 0,5| als anells "
                                      "sencers amb estructura; en Superposar, un "
                                      "nivell diferent de 0,5 pinta un anell",
                        "veredicte": "PASSA" if h1_pitjor <= 0.05 else "NO PASSA"}
    if h1_pitjor > 0.05:
        raise SystemExit(f"PORTA H1: hi ha anells als filtres "
                         f"(|nivell−0,5| = {h1_pitjor:.3f} > 0,05).")
    info["porta"] = "PASSA"
    run.desa_rebut("F3_filtres.json", info)
    print(f"    color de la DADA: " + " · ".join(
        f"{k} R/G={v['R/G']:.3f} B/G={v['B/G']:.3f}" for k, v in sorted(col_dada.items())),
        flush=True)
    print(f"    veredicte: {info['veredicte_color_dada']}", flush=True)
    ct = info["control_testimoni_DSC06991"]
    if "_pitjor_pct" in ct:
        print(f"    contra el DSC06991 de Pere: mediana {ct['_mediana_pct']:.1f} % · "
              f"pitjor {ct['_pitjor_pct']:.1f} %", flush=True)
    return info
