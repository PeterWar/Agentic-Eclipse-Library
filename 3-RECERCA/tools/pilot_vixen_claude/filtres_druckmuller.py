"""Els filtres de la família de Brno, tots al RECTANGLE i tots amb pes.

## ⛔ Les tres regles que governen aquest fitxer

1. **Norma del rectangle.** Cap filtre no es retalla a una circumferència. Un
   filtre circular deixa halos, i si l'exterior surt lleig es repara aigües
   amunt —flat, cel, estrelles—, mai retallant. L'única cosa que atura un filtre
   és que **no hi hagi dada**, i això ho diu el mapa de pes.
2. **Convolució incompleta.** Tot suavitzat va com `G(w·I)/G(w)`, no com
   `G(I)`: on falta dada, el veí que hi ha mana i no s'hi inventa un zero. Sense
   això, cada vora del rectangle i cada forat de la Lluna es converteixen en una
   rampa fosca que el passa-alt torna a treure com si fos estructura.
3. **Porta de soroll suau, mai un llindar dur.** `d·erf(|d|/(n·σ))`, la de WOW:
   un llindar dur deixa vores i les vores són l'artefacte que estem perseguint.

## Els filtres i què fa cadascun

| filtre | què normalitza | quan serveix |
|---|---|---|
| `passa_alt` | res: treu la part suau | veure detall a una escala triada |
| `desenfoc_radial` | res: suavitza en polars | treure soroll SENSE matar els raigs |
| `nrgf` | mitjana i dispersió per ANELL | aplanar la caiguda radial |
| `fnrgf` | mitjana i dispersió per anell **i azimut** | corona molt asimètrica |
| `mgn` | dispersió local a cada escala | detall a totes les escales alhora |
| `wow` | dispersió per escala + porta | màxim detall amb soroll controlat |
| `nafe` | rang local difús | contrast local sense cremar |

⚠️ **Cap d'aquests filtres conserva la fotometria.** Serveixen per veure, no per
mesurar. El producte calibrat és el compost de la fase 2; això és la fase 3.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates
from scipy.special import erf

EPS = 1e-6


# ---------------------------------------------------------------- utilitats
def _suau(imatge: np.ndarray, pes: np.ndarray, sigma: float) -> np.ndarray:
    """Suavitzat de convolució INCOMPLETA: `G(w·I)/G(w)`.

    ⛔ Mai `gaussian_filter(I, σ)` a seques. Amb dada que falta —la Lluna, les
    vores del rectangle, els forats de saturació— la convolució normal hi posa
    zeros i el resultat és una rampa que després es llegeix com a estructura.
    """
    w = np.asarray(pes, np.float32)
    iw = np.where(w > 0, np.asarray(imatge, np.float32), 0.0)
    num = gaussian_filter(iw, sigma, mode="nearest")
    den = gaussian_filter(w, sigma, mode="nearest")
    return np.where(den > EPS, num / np.maximum(den, EPS), 0.0).astype(np.float32)


def _porta_de_soroll(d: np.ndarray, sigma_soroll, n: float) -> np.ndarray:
    """La porta suau de WOW. `sigma_soroll` pot ser escalar o mapa."""
    s = np.asarray(sigma_soroll, np.float32)
    return (d * erf(np.abs(d) / np.maximum(n * s, 1e-12))).astype(np.float32)


def soroll_per_diferencies(imatge: np.ndarray, pes: np.ndarray) -> float:
    """Soroll estimat de les diferències entre píxels VEÏNS.

    ⛔ Existeix perquè tots els filtres que **divideixen per una dispersió**
    exploten quan la dispersió és zero. Amb una entrada perfectament llisa, el
    NRGF donava `(residu d'arrodoniment)/(≈0)` = O(1) i el NAFE saturava a ±1 a
    tot el camp: inventaven estructura on no n'hi havia cap. El terra no pot ser
    un número triat a mà, o sigui que es **mesura**: la diferència entre veïns
    és senyal (suau, petita) més soroll (independent, ×√2), i la seva mediana
    absoluta escalada és l'estimador robust de sempre.
    """
    w = np.asarray(pes, np.float32) > 0
    d = np.asarray(imatge, np.float32)
    dif = np.diff(d, axis=1)
    bo = w[:, :-1] & w[:, 1:]
    if bo.sum() < 100:
        return 0.0
    mad = float(np.median(np.abs(dif[bo] - np.median(dif[bo]))))
    return float(1.4826 * mad / np.sqrt(2.0))


def _terra_de_dispersio(imatge: np.ndarray, pes: np.ndarray,
                        sigma_minim: float | None) -> float:
    """El terra per sota del qual no es pot dividir.

    És el soroll mesurat, i **mai menys** d'una part per milió de la dispersió
    de la mateixa imatge: si la dispersió local és zero de veritat, no hi ha
    contrast a equalitzar i el filtre s'ha de fer transparent en lloc de
    dividir per zero. Amb una entrada exactament constant, el NAFE saturava a
    ±1 a tot el camp i el NRGF donava O(1): inventaven un camp sencer.
    """
    if sigma_minim is None:
        sigma_minim = soroll_per_diferencies(imatge, pes)
    w = np.asarray(pes, np.float32) > 0
    escala = float(np.std(np.asarray(imatge, np.float32)[w])) if w.any() else 0.0
    return max(float(sigma_minim), 1e-6 * escala)


def _dispersio_local(d: np.ndarray, pes: np.ndarray, sigma: float) -> np.ndarray:
    """Desviació típica local, també amb convolució incompleta."""
    m = _suau(d, pes, sigma)
    m2 = _suau(d * d, pes, sigma)
    return np.sqrt(np.maximum(m2 - m * m, 0.0)).astype(np.float32)


# ---------------------------------------------------------------- 1 · passa-alt
def passa_alt(imatge: np.ndarray, pes: np.ndarray, sigma: float, *,
              sigma_soroll=None, n_soroll: float = 3.0) -> tuple[np.ndarray, dict]:
    """Passa-alt d'una sola escala: `I − G_σ(I)`, amb pes i porta opcional.

    És el filtre més simple de tots i el que Pere fa servir per veure si un
    artefacte hi és: un passa-alt **és un detector de defectes**, i qualsevol
    cosa que hi surti amb forma de circumferència o d'isofota és sospitosa.
    """
    imatge = np.asarray(imatge, np.float32)
    w = (np.asarray(pes, np.float32) > 0).astype(np.float32)
    d = np.where(w > 0, imatge - _suau(imatge, w, sigma), 0.0).astype(np.float32)
    passat = 1.0
    if sigma_soroll is not None:
        abans = float(np.std(d[w > 0])) if w.any() else 0.0
        d = np.where(w > 0, _porta_de_soroll(d, sigma_soroll, n_soroll), 0.0)
        despres = float(np.std(d[w > 0])) if w.any() else 0.0
        passat = despres / abans if abans > 0 else 1.0
    return d, {"filtre": "passa_alt", "sigma_px": float(sigma),
               "n_soroll": float(n_soroll) if sigma_soroll is not None else None,
               "fraccio_que_passa": round(float(passat), 5),
               "rms": float(np.std(d[w > 0])) if w.any() else 0.0}


# ------------------------------------------------------- polars, per als radials
def _reixa_polar(shape, centre, n_ang: int, r_max: float):
    h, w = shape
    cy, cx = centre
    ang = np.linspace(0.0, 2.0 * np.pi, n_ang, endpoint=False, dtype=np.float32)
    rad = np.arange(0.0, r_max, 1.0, dtype=np.float32)
    ca, sa = np.cos(ang)[:, None], np.sin(ang)[:, None]
    yy = cy + rad[None, :] * sa
    xx = cx + rad[None, :] * ca
    return yy, xx, ang, rad


def a_polar(imatge: np.ndarray, centre, n_ang: int, r_max: float) -> np.ndarray:
    yy, xx, _, _ = _reixa_polar(imatge.shape, centre, n_ang, r_max)
    return map_coordinates(np.asarray(imatge, np.float32), [yy, xx], order=1,
                           mode="constant", cval=0.0).astype(np.float32)


def de_polar(pol: np.ndarray, shape, centre, r_max: float) -> np.ndarray:
    """Torna de polars a cartesianes, amb l'angle circular."""
    h, w = shape
    cy, cx = centre
    n_ang = pol.shape[0]
    yy = np.arange(h, dtype=np.float32)[:, None] - cy
    xx = np.arange(w, dtype=np.float32)[None, :] - cx
    r = np.hypot(xx, yy)
    a = np.arctan2(yy, xx) % (2.0 * np.pi)
    ia = a * (n_ang / (2.0 * np.pi))
    # ⛔ l'eix de l'angle és CIRCULAR: sense `mode="grid-wrap"` surt una costura
    # radial a φ = 0, que és exactament la mena d'artefacte que perseguim.
    return map_coordinates(pol, [ia, np.clip(r, 0, r_max - 1)], order=1,
                           mode="grid-wrap").astype(np.float32)


# ------------------------------------------------------- 2 · desenfoc radial
def desenfoc_radial(imatge: np.ndarray, pes: np.ndarray, centre, *,
                    sigma_r_px: float = 0.0, sigma_az_graus: float = 0.0,
                    n_ang: int = 4096, r_max: float | None = None
                    ) -> tuple[np.ndarray, dict]:
    """Desenfoc separable en POLARS: radial (zoom) i/o azimutal (spin).

    ⚠️ Els dos serveixen per a coses oposades i no s'han de confondre:

    - **azimutal** (`sigma_az_graus`) suavitza *al llarg dels anells*. Allarga
      el que és radial —els raigs polars, els filaments— i mata el soroll que
      no ho és. És el que a Photoshop es diu «radial blur · zoom».
    - **radial** (`sigma_r_px`) suavitza *al llarg dels radis*. Allarga el que
      és circular. ⛔ A la corona això sol ser **el contrari del que vols**:
      reforça justament els anells i les costures de fusió. Hi és perquè és
      la manera de MESURAR quanta senyal circular hi ha.

    ⛔ Es fa amb convolució incompleta també en polars, o sigui que el forat de
    la Lluna i les vores del rectangle no s'escampen cap endins.
    """
    imatge = np.asarray(imatge, np.float32)
    w = (np.asarray(pes, np.float32) > 0).astype(np.float32)
    h, wd = imatge.shape
    cy, cx = centre
    if r_max is None:                       # ⛔ fins al CANTÓ, no fins al costat
        r_max = float(np.ceil(max(np.hypot(y - cy, x - cx)
                                  for y in (0, h - 1) for x in (0, wd - 1)))) + 2
    pi = a_polar(np.where(w > 0, imatge, 0.0), centre, n_ang, r_max)
    pw = a_polar(w, centre, n_ang, r_max)
    if sigma_az_graus > 0:
        s = sigma_az_graus * n_ang / 360.0
        pi = gaussian_filter1d(pi, s, axis=0, mode="wrap")
        pw = gaussian_filter1d(pw, s, axis=0, mode="wrap")
    if sigma_r_px > 0:
        pi = gaussian_filter1d(pi, sigma_r_px, axis=1, mode="nearest")
        pw = gaussian_filter1d(pw, sigma_r_px, axis=1, mode="nearest")
    pol = np.where(pw > EPS, pi / np.maximum(pw, EPS), 0.0).astype(np.float32)
    out = de_polar(pol, imatge.shape, centre, r_max)
    return (np.where(w > 0, out, 0.0).astype(np.float32),
            {"filtre": "desenfoc_radial", "sigma_r_px": float(sigma_r_px),
             "sigma_az_graus": float(sigma_az_graus), "n_angles": int(n_ang),
             "r_max_px": float(r_max),
             "rms": float(np.std(out[w > 0])) if w.any() else 0.0,
             "arc_per_angle_a_r_max_px": round(2 * np.pi * r_max / n_ang, 3)})


# ------------------------------------------------------------------ 3 · NRGF
def nrgf(imatge: np.ndarray, pes: np.ndarray, radis: np.ndarray, *,
         n_anells: int = 400, suavitza_anells: float = 2.0,
         sigma_minim: float | None = None) -> tuple[np.ndarray, dict]:
    """Normalizing Radial Graded Filter: `(I − ⟨I⟩_r) / σ_r`.

    ⛔ Els perfils d'anell es **suavitzen en log r** abans de restar-los. Amb la
    resta per calaix crua, el 54 % del detall que declaràvem el 24-08-2026 era
    el serrell dels calaixos: a la corona interior el quocient serrell/senyal
    valia 1,00-1,13, o sigui que el «detall» ERA el serrell.
    """
    imatge = np.asarray(imatge, np.float32)
    w = (np.asarray(pes, np.float32) > 0)
    r = np.asarray(radis, np.float32)
    rv = r[w]
    if rv.size == 0:
        return np.zeros_like(imatge), {"filtre": "nrgf", "n_anells": 0}
    vores = np.quantile(rv, np.linspace(0, 1, n_anells + 1))
    vores = np.unique(vores)
    idx = np.clip(np.searchsorted(vores, r, "right") - 1, 0, len(vores) - 2)
    nb = len(vores) - 1
    mitj = np.zeros(nb, np.float64); disp = np.ones(nb, np.float64)
    iv, ix = imatge[w], idx[w]
    for k in range(nb):
        m = ix == k
        if m.sum() >= 20:
            v = iv[m]
            mitj[k] = np.median(v)
            disp[k] = max(np.std(v), 1e-12)
    # ⛔ suavitzat en LOG del radi, no en radi: els anells de fora són molt més
    # amples i un suavitzat uniforme els barreja amb els de dins.
    centres = 0.5 * (vores[:-1] + vores[1:])
    lr = np.log(np.maximum(centres, 1e-6))
    if suavitza_anells > 0 and nb > 5:
        pas = float(np.median(np.diff(lr))) or 1e-6
        s = max(suavitza_anells * pas / max(pas, 1e-9), suavitza_anells)
        mitj = gaussian_filter1d(mitj, s, mode="nearest")
        disp = np.maximum(gaussian_filter1d(disp, s, mode="nearest"), 1e-12)
    # ⛔ terra de dispersió: sense ell, una entrada llisa surt normalitzada a
    # O(1) perquè es divideix pel residu d'arrodoniment. Es MESURA de la imatge.
    sigma_minim = _terra_de_dispersio(imatge, w, sigma_minim)
    if sigma_minim <= 0.0:                 # entrada exactament constant
        return np.zeros_like(imatge), {"filtre": "nrgf", "n_anells": int(nb),
                                       "sigma_minim": 0.0, "rms": 0.0,
                                       "nota": "entrada sense contrast"}
    disp = np.maximum(disp, sigma_minim)
    out = np.where(w, (imatge - mitj[idx]) / disp[idx], 0.0).astype(np.float32)
    return out, {"filtre": "nrgf", "n_anells": int(nb),
                 "sigma_minim": float(sigma_minim),
                 "suavitzat_en_log_r": float(suavitza_anells),
                 "rms": float(np.std(out[w])) if w.any() else 0.0}


# ----------------------------------------------------------------- 4 · FNRGF
def fnrgf(imatge: np.ndarray, pes: np.ndarray, radis: np.ndarray,
          azimuts: np.ndarray, *, n_anells: int = 300, ordre: int = 6,
          suavitza_anells: float = 2.0) -> tuple[np.ndarray, dict]:
    """NRGF de Fourier: la mitjana i la dispersió depenen també de l'AZIMUT.

    A cada anell s'ajusta una sèrie de Fourier d'ordre `ordre` a la intensitat
    —això és el fons `A(φ)`— i una altra a `|I − A|` —això és l'amplitud
    `B(φ)`—; la sortida és `(I − A)/B`.

    ⛔ **No és l'equació que surt a l'ApJ.** Aquella barreja els coeficients de
    la mitjana amb els de l'amplitud i, amb una corona asimètrica, la
    normalització surt negativa a les serpentines. Aquí les dues sèries
    s'ajusten **per separat** i `B` es força positiva.

    ⚠️ `ordre` és el nombre de graus de llibertat per anell i és el perill
    d'aquest filtre: amb l'ordre prou alt s'hi pot dibuixar el que es vulgui.
    Per damunt de ~10 deixa de ser un filtre i passa a ser un ajust.
    """
    imatge = np.asarray(imatge, np.float32)
    w = (np.asarray(pes, np.float32) > 0)
    r = np.asarray(radis, np.float32)
    phi = np.asarray(azimuts, np.float32)
    if not w.any():
        return np.zeros_like(imatge), {"filtre": "fnrgf", "n_anells": 0}
    vores = np.unique(np.quantile(r[w], np.linspace(0, 1, n_anells + 1)))
    idx = np.clip(np.searchsorted(vores, r, "right") - 1, 0, len(vores) - 2)
    nb = len(vores) - 1
    nc = 2 * ordre + 1
    A = np.zeros((nb, nc)); B = np.zeros((nb, nc))
    B[:, 0] = 1.0
    iv, ix, pv = imatge[w], idx[w], phi[w]

    def _base(p):
        col = [np.ones_like(p)]
        for k in range(1, ordre + 1):
            col += [np.cos(k * p), np.sin(k * p)]
        return np.stack(col, 1)

    for k in range(nb):
        m = ix == k
        if m.sum() < max(60, 6 * nc):
            continue
        X = _base(pv[m]); y = iv[m].astype(np.float64)
        ca, *_ = np.linalg.lstsq(X, y, rcond=None)
        A[k] = ca
        res = np.abs(y - X @ ca)
        cb, *_ = np.linalg.lstsq(X, res, rcond=None)
        B[k] = cb
    if suavitza_anells > 0 and nb > 5:
        A = gaussian_filter1d(A, suavitza_anells, axis=0, mode="nearest")
        B = gaussian_filter1d(B, suavitza_anells, axis=0, mode="nearest")
    # ⛔ `ix` i `pv` ja són els valors DINS del pes: tornar-los a indexar amb
    # la màscara 2-D és l'error que la prova del FNRGF va enxampar.
    Xt = _base(pv.astype(np.float64))
    a = np.einsum("ij,ij->i", Xt, A[ix])
    b = np.einsum("ij,ij->i", Xt, B[ix])
    # ⛔ l'amplitud ha de ser positiva: una sèrie truncada pot passar per zero
    # i allà la normalització explota amb el signe canviat.
    b = np.maximum(b, np.percentile(np.abs(b), 5) if b.size else 1.0)
    out = np.zeros_like(imatge)
    out[w] = ((iv - a) / np.maximum(b, 1e-12)).astype(np.float32)
    return out, {"filtre": "fnrgf", "n_anells": int(nb), "ordre": int(ordre),
                 "graus_de_llibertat_per_anell": int(2 * nc),
                 "rms": float(np.std(out[w]))}


# ------------------------------------------------------------------- 5 · MGN
def mgn(imatge: np.ndarray, pes: np.ndarray, sigmes=(1.25, 2.5, 5, 10, 20, 40),
        *, h: float = 0.7, k_arctan: float = 0.7, pes_global: float = 0.3
        ) -> tuple[np.ndarray, dict]:
    """Multi-scale Gaussian Normalization (Morgan & Druckmüller 2014).

    A cada escala: es treu la mitjana local, es divideix per la dispersió local
    i es passa per `arctan`, que és el que impedeix que el soroll de les zones
    fosques exploti. La sortida és la mitjana de les escales més una part de la
    imatge original comprimida.
    """
    imatge = np.asarray(imatge, np.float32)
    w = (np.asarray(pes, np.float32) > 0).astype(np.float32)
    acc = np.zeros_like(imatge)
    diag = []
    for s in sigmes:
        m = _suau(imatge, w, s)
        sd = _dispersio_local(imatge, w, s)
        terra = _terra_de_dispersio(imatge, w, None)
        c = (np.where((w > 0) & (sd > terra), (imatge - m) / np.maximum(sd, terra), 0.0)
             if terra > 0 else np.zeros_like(imatge))
        c = np.arctan(k_arctan * c).astype(np.float32)
        acc += c
        diag.append({"sigma_px": float(s), "rms": float(np.std(c[w > 0]))})
    acc /= len(sigmes)
    # part global: la imatge sencera comprimida amb el mateix arctan
    vw = imatge[w > 0]
    if vw.size:
        g = (imatge - np.mean(vw)) / max(np.std(vw), EPS)
        glob = np.arctan(k_arctan * g).astype(np.float32)
    else:
        glob = np.zeros_like(imatge)
    out = np.where(w > 0, h * acc + pes_global * glob, 0.0).astype(np.float32)
    return out, {"filtre": "mgn", "sigmes": [float(x) for x in sigmes],
                 "h": float(h), "k_arctan": float(k_arctan),
                 "pes_global": float(pes_global), "per_escala": diag,
                 "rms": float(np.std(out[w > 0])) if w.any() else 0.0}


# ------------------------------------------------------------------- 6 · WOW
def wow(imatge: np.ndarray, pes: np.ndarray, *, n_escales: int = 6,
        sigma_soroll=None, n_soroll: float = 3.0, pes_gamma: float = 1.0
        ) -> tuple[np.ndarray, dict]:
    """Wavelet Optimized Whitening (Auchère et al. 2023), amb à trous.

    Cada escala es blanqueja per la seva pròpia dispersió local i passa per la
    porta suau; després es tornen a sumar. El resultat ensenya el detall feble
    de fora sense cremar el de dins.

    ⛔ La porta és `erf`, no un llindar: un llindar dur deixa vores i les vores
    són l'artefacte que estem perseguint.
    """
    imatge = np.asarray(imatge, np.float32)
    w = (np.asarray(pes, np.float32) > 0).astype(np.float32)
    resta = imatge.copy()
    out = np.zeros_like(imatge)
    diag = []
    for k in range(n_escales):
        s = 2.0 ** k
        suau = _suau(resta, w, s)
        det = np.where(w > 0, resta - suau, 0.0).astype(np.float32)
        # ⛔ el mateix terra que al NRGF i al NAFE. Sense ell, a la vora del
        # rectangle la dispersió local cau i el blanquejament hi fa un marc
        # brillant: al full de contacte del 25-08-2026 es veia com un requadre.
        sd = _dispersio_local(det, w, 4.0 * s)
        terra = _terra_de_dispersio(det, w, None)
        sd = np.maximum(sd, max(terra, EPS))
        blanc = np.where(sd > terra, det / sd, 0.0).astype(np.float32)
        if sigma_soroll is not None:
            blanc = _porta_de_soroll(blanc, np.asarray(sigma_soroll) / np.maximum(sd, EPS),
                                     n_soroll)
        out += (s ** -pes_gamma) * blanc
        diag.append({"escala_px": float(s), "rms": float(np.std(blanc[w > 0]))})
        resta = suau
    out = np.where(w > 0, out, 0.0).astype(np.float32)
    return out, {"filtre": "wow", "n_escales": int(n_escales),
                 "pes_gamma": float(pes_gamma), "per_escala": diag,
                 "rms": float(np.std(out[w > 0])) if w.any() else 0.0}


# ------------------------------------------------------------------ 7 · NAFE
def nafe(imatge: np.ndarray, pes: np.ndarray, *, sigma: float = 30.0,
         sigma_soroll=None, n_soroll: float = 2.0, gamma: float = 0.5,
         sigma_minim: float | None = None) -> tuple[np.ndarray, dict]:
    """Noise Adaptive Fuzzy Equalization (Druckmüller 2013), versió gaussiana.

    L'equalització local exacta demana un histograma per píxel. Aquí el rang
    local es fa amb la **funció d'error sobre la distribució local**, que és el
    mateix si la distribució local és aproximadament gaussiana i costa dues
    convolucions en lloc d'un histograma:

        rang(x) = ½·(1 + erf((I − m_local) / (√2 · σ_local)))

    La part «adaptativa al soroll» és que el contrast s'atenua allà on la
    dispersió local **és** el soroll: si `σ_local ≈ σ_soroll`, no hi ha res a
    equalitzar i el filtre es fa transparent.
    """
    imatge = np.asarray(imatge, np.float32)
    w = (np.asarray(pes, np.float32) > 0).astype(np.float32)
    m = _suau(imatge, w, sigma)
    sd = _dispersio_local(imatge, w, sigma)
    # ⛔ el mateix terra que al NRGF, i pel mateix motiu: amb dispersió local
    # nul·la, `erf(ε/0)` saturava a ±1 i el filtre pintava el camp sencer.
    sigma_minim = _terra_de_dispersio(imatge, w, sigma_minim)
    if sigma_minim <= 0.0:                 # entrada exactament constant
        return np.zeros_like(imatge), {"filtre": "nafe", "sigma_px": float(sigma),
                                       "sigma_minim": 0.0, "rms": 0.0,
                                       "nota": "entrada sense contrast"}
    sd = np.maximum(sd, sigma_minim)
    rang = 0.5 * (1.0 + erf((imatge - m) / (np.sqrt(2.0) * sd)))
    out = (2.0 * rang - 1.0).astype(np.float32)          # a [−1, 1]
    if sigma_soroll is not None:
        ss = np.asarray(sigma_soroll, np.float32)
        # fracció de la dispersió local que NO és soroll
        real = np.clip(1.0 - (ss / np.maximum(sd, 1e-12)) ** 2, 0.0, 1.0)
        out = (out * real ** gamma).astype(np.float32)
    out = np.where(w > 0, out, 0.0).astype(np.float32)
    return out, {"filtre": "nafe", "sigma_px": float(sigma),
                 "sigma_minim": float(sigma_minim),
                 "n_soroll": float(n_soroll), "gamma": float(gamma),
                 "rms": float(np.std(out[w > 0])) if w.any() else 0.0}


CATALEG = {"passa_alt": passa_alt, "desenfoc_radial": desenfoc_radial,
           "nrgf": nrgf, "fnrgf": fnrgf, "mgn": mgn, "wow": wow, "nafe": nafe}
