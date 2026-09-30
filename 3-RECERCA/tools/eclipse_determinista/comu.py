"""Nucli de la cadena determinista de l'eclipsi del 12-08-2026.

## Les tres regles que governen aquest mòdul

1. **Un run és IMMUTABLE.** Tot s'escriu dins de `1-RUNS/<TREN>_<segell>/` i cap
   run no pot arribar al directori d'un altre. No hi ha `overwrite` enlloc.
2. **Cap ruta a mà.** Tot passa per l'objecte `Run`. Si un script escriu una
   ruta literal, ha entrat un defecte.
3. **Zero estat amagat.** Cap variable d'entorn, cap valor per defecte que
   canviï el resultat. El que decideix, decideix al manifest.

## Les quatre cures del 26-08 que viuen aquí

- ⛔ **El balanç de blancs s'aplica a `calibra_pla()`**, o sigui a l'ÚNIC lloc
  per on passa tota la dada. Abans anava al final de la composició i qualsevol
  script que refés la imatge des dels RAW se'l deixava: restar-hi després un
  mapa de cel balancejat treia 2,17x massa vermell.
- ⛔ **La corba de to porta l'àncora com a ARGUMENT, i és COMUNA als tres
  canals.** Amb una àncora per canal, la mediana és homogènia i **qualsevol
  constant per canal s'anul·la**: la imatge surt monocroma.
- ⛔ **L'àncora no pot ser `nan`.** `np.nanmedian([])` dona `nan` i
  `np.maximum(x, nan)` l'escampa a TOT el llenç.
- ⛔ **La zona EMMASCARADA del sensor no pot entrar al llenç.** Es remapeja una
  màscara de validesa al costat de la dada i es talla.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, field

import numpy as np
import cv2
import rawpy

# ------------------------------------------------------------------ arrel

ARREL = os.path.expanduser("~/Desktop/Eclipse determinista")
ENTRADES = os.path.join(ARREL, "0-ENTRADES")
RUNS = os.path.join(ARREL, "1-RUNS")
OUTPUT = os.path.join(ARREL, "2-OUTPUT")

TRENS = {
    "VIXEN": {
        "cos": "Canon EOS R6 Mark III",
        "dir": os.path.join(ENTRADES, "VIXEN-R6III"),
        "ext": ".CR3",
        "escala_arcsec_px": 2.1494813525884373,   # placa r6_radial, 22 estrelles
        "pa_north_deg": 57.194988546068025,
        "rsol_arcsec": 947.068,                   # radi solar aparent del dia
        "pedestal_dn": 512.0,                     # MESURAT, no de libraw
        "saturacio_dn": 16382.0,                  # MESURAT: no 16383
        "pedestal_font": "marge",                 # té marge esquerre emmascarat
        # fotogrames de fora de la totalitat que ensenyen el limbe solar
        "prot_ingress": ("572A2963.CR3", "572A2964.CR3", "572A2965.CR3",
                         "572A2966.CR3"),
        "prot_egress": ("572A3014.CR3", "572A3015.CR3", "572A3016.CR3",
                        "572A3017.CR3", "572A3018.CR3"),
    },
    # ⏭️ SONY A7RIIIA + FE 300 mm f/2,8 GM sobre Skywatcher (27-08-2026).
    #    Segon tren. Entra al MATEIX llenç que la Vixen (`llenc_de`) perquè
    #    pugui fer de JUTGE INDEPENDENT: per comparar estructura, els dos han
    #    d'estar exactament a la mateixa graella.
    "SONY": {
        "cos": "Sony ILCE-7RM3A",
        "dir": os.path.join(ENTRADES, "SONY-A7RIIIA"),
        "ext": ".ARW",
        # ⛔ 3,2020 i no 3,234: l'astrometria de `research/75` §5.1 (38 estrelles,
        #    residu 0,71 px) mana sobre l'ajust del diàmetre lunar, que en dona
        #    3,234. La discrepància de l'1 % queda OBERTA i declarada.
        "escala_arcsec_px": 3.2020,
        "pa_north_deg": 90.27,                    # research/75 §5.1
        "rsol_arcsec": 947.068,                   # el mateix dia
        # ⛔ MESURAT als 378 darks (mediana 512,00 als quatre canals, dispersió
        #    0,00 DN). ⚠️ Aquest cos NO TÉ ZONA EMMASCARADA: `raw_width` 8000
        #    contra `width` 7968, i les 32 columnes que sobren VEUEN LLUM
        #    (a 8 s marquen 3436 DN). El camí del marge de la R6 III no s'hi
        #    pot fer servir.
        "pedestal_dn": 512.0,
        "pedestal_font": "darks",
        # MESURAT: retalla al valor declarat, 1.034.049 px exactes a 16383 amb
        # els veïns a ~75. (La R6 III retalla a 16382 i aquesta no.)
        "saturacio_dn": 16383.0,
        "llenc_de": "VIXEN",
        # ⏭️ CORRECCIÓ DEL FLAT MESURADA AMB EL SALT DE MUNTURA (27-08, §11 del
        #    `research/115`). Aquest cos no té flats invertits i el seu flat
        #    radial arrossegava un error del 7 al 9 % pel camp. El salt de
        #    749 px és un dither i el mesura: `sony_entrada/flat_pel_salt.py`.
        #    ⚠️ Gauge lnF(0)=0 → NO toca l'escala absoluta, només la forma.
        "flat_dither": "flat_dither_SONY.json",
        # ⚠️ Amb nomes els 14 de `totalitat` no hi ha cap fotograma d'INGRESS:
        #    el bloc de contacte de C2 es a `descentrats`. D'egress hi ha els
        #    dos del bloc de C3, que cauen a C3-0,7 s (1/800 i 1/6400).
        "prot_ingress": (),
        "prot_egress": ("DSC07003.ARW", "DSC07004.ARW"),
    },
}

# ⏭️ REORGANITZACIO DE `0-ENTRADES`, 27-08-2026, per decisio de Pere despres de
#    mirar els cinc exclosos un per un (`research/116` §8):
#
#      `quarantena/`   -> DESAPAREIX. El nom deia «sospitosos» i no ho eren:
#                         era el PRIMER APUNTAMENT.
#      `descentrats/`  -> els 15 del primer apuntament (DSC06973-06987). Estan
#                         bé; nomes miren cap a un altre lloc.
#      `inservibles/`  -> NOMES DSC06988, 06989 i 06990, moguts durant el salt.
#                         No els llegeix ningu, pero hi son i el manifest els
#                         hasheja: un fotograma no s'esborra mai.
#
#    ⏭️ I 06991 i 06993 TORNEN A ENTRAR. Pere: «de DSC06991 en endavant jo els
#    veig tots perfectament be i es una pena que no els aprofitem, pensa que
#    cada foto compta». Tenen ovalitat de limbe 2,56 i 3,60 px sobre una
#    mediana d'1,1, o sigui una mica escombrats, i el filtre d'rms de `f1` ja
#    decideix sol si entren al model d'apuntament.
#    ⚠️ Amb el 06991 dins del compost, `control_testimoni_DSC06991` deixa de
#    ser independent del producte. Continua valent com a control de
#    consistencia —igual que `tancament_hdr`, que sempre ha comparat el compost
#    amb un fotograma que hi es a dins— i aixo queda dit al rebut.
TRENS["SONYTOT"] = dict(
    TRENS["SONY"],
    cos="Sony ILCE-7RM3A (dos apuntaments)",
    carpetes_llum=("totalitat", "descentrats"),
    exclou=(),
    # amb els descentrats dins ja hi ha el bloc de contacte de C2 sencer
    prot_ingress=("DSC06973.ARW", "DSC06974.ARW", "DSC06975.ARW",
                  "DSC06976.ARW", "DSC06977.ARW", "DSC06978.ARW"),
)

# ⏭️ EL LLENÇ COMÚ (27-08). Perquè un tren pugui fer de JUTGE de l'altre, els
#    dos han d'estar a la MATEIXA graella: mateixa mida, mateixa escala, Sol al
#    centre per efemèride i nord amunt. Aquests números són els que la Vixen va
#    derivar de la seva pròpia cobertura (run 20260827T012038Z) i ara es
#    DECLAREN, perquè un llenç que depèn de quins fotogrames entren no és una
#    graella comuna. Un tren amb `llenc_de` l'hereta tal qual.
#    ⚠️ La Sony hi entra remostrejada ×1,49 (3,2020 → 2,1495 ''/px) i el seu
#    camp NO omple el llenç en vertical (±8,99 R☉ contra ±10,16): és correcte i
#    els pesos ja ho porten.
LLENC_COMU = {
    "W": 8096, "H": 8960,
    "escala_arcsec_px": 2.1494813525884373,
    "font": "VIXEN, run 20260827T012038Z (cobertura pròpia), ara DECLARAT",
}

# ⛔ QUINS CONTACTES ENTREN AL PRODUCTE. Decisió de Pere del 27-08-2026:
#    «oblidem-nos del requisit de fer la simetria amb els dos contactes,
#    treballarem només en C2; no m'agrada el resultat de posar C2 i C3 i
#    deformar la Lluna».
#    ⏭️ El motiu és geomètric i estava escrit al codi des del primer dia: el
#    llenç va centrat al SOL i la Lluna hi llisca ~28,5 px entre C2 i C3, o
#    sigui que unir els dos extrems deixa com a negre la **intersecció dels dos
#    discos lunars** —una llentia, no un cercle—. Amb només C2, la Lluna torna
#    a ser rodona.
#    ⚠️ El preu: les protuberàncies de just abans de C3 no surten al producte.
#    Es continuen calculant i desant al rebut, i la capa de contactes de C3
#    (segon anell de diamant) no es toca: viu al seu propi PSB.
CONTACTES_AL_PRODUCTE = ("ingress",)          # C2. Per als dos: ("ingress", "egress")

LLOC = (42.299407, -5.02503, 798.0)   # MIRADOR FINAL 2
UTC_OFF_H = 2.0
DIA = (2026, 8, 12)
EFEM = "/Users/USUARI/Downloads/Eclipse 2026/de421.bsp"

FASES = ("0-calibracio", "1-registre", "2-ldic", "3-filtres", "4-rebuts")


# ------------------------------------------------------ numeració dels runs

# ⏭️ 27-08-2026, per Pere: «pots fer que cada run tingui un número cronològic?
#    així ordeno les carpetes i m'és més fàcil trobar els outputs». El nom d'un
#    run passa a ser `NNN_<TREN>_<MODE>_<segell>`, amb NNN **cronològic i comú
#    a tots els trens**, o sigui que ordenar per nom és ordenar per temps.
#    ⛔ El segell no marxa: és el que lliga el run amb els documents que el
#    citen. El número és per a l'ull; el segell és la identitat.
_PREFIX = re.compile(r"^(\d{3,})_")
_SEGELL = re.compile(r"(\d{8}T\d{6}Z)")


def sense_prefix(nom: str) -> str:
    """El nom d'un run sense el número: `012_SONY_...` -> `SONY_...`."""
    return _PREFIX.sub("", os.path.basename(nom.rstrip("/")))


def numero_de(nom: str) -> int:
    m = _PREFIX.match(os.path.basename(nom.rstrip("/")))
    return int(m.group(1)) if m else -1


def runs_llista(tren: str | None = None, mode: str | None = None,
                acabats: bool = True) -> list[str]:
    """Els runs, ORDENATS pel seu número (i, per tant, en el temps).

    ⛔ Un sol lloc que sap com es diu un run. Abans cada eina en tenia la seva
    còpia amb `startswith(f"{tren}_{mode}_")`, i posar-hi un número al davant
    les hauria trencat totes alhora.
    """
    out = []
    for d in os.listdir(RUNS):
        p = os.path.join(RUNS, d)
        if not os.path.isdir(p):
            continue
        if acabats and (d.endswith("_FALLIT") or d.endswith("_AVORTAT")):
            continue
        n = sense_prefix(d)
        if tren and not n.startswith(f"{tren}_"):
            continue
        if mode and f"_{mode}_" not in n:
            continue
        out.append(p)
    return sorted(out, key=lambda q: (numero_de(q), os.path.basename(q)))


def darrer_run(tren: str, mode: str = "CIENCIA", exigeix: str | None = None) -> str:
    """L'últim run acabat d'un tren. `exigeix` és una ruta relativa que hi ha
    de ser (per exemple `2-ldic/CORONA_G.fits`), perquè un run que va caure a
    mig camí no serveix de font."""
    ds = [d for d in runs_llista(tren, mode)
          if exigeix is None or os.path.exists(os.path.join(d, exigeix))]
    if not ds:
        raise SystemExit(f"cap run acabat de {tren}_{mode}")
    return ds[-1]


def carpeta_sortida(run: "Run") -> str:
    """Com es diu la carpeta de `2-OUTPUT` d'un run: `NNN_TREN_COLOR`.

    ⏭️ 27-08, per Pere: «enumera també les carpetes dins output, així sé sempre
    quina és l'última». El número és **el del run**, no un comptador a part: la
    sortida i el run que l'ha feta queden lligats pel nom.
    ⛔ Amb això desapareix el sufix `_anterior`: la còpia d'abans es queda amb
    el SEU número, que ja diu que és més vella.
    """
    return f"{numero_de(run.dir):03d}_{run.tren}_{run.mode}"


def sortides_de(tren: str, mode: str) -> list[str]:
    """Les carpetes de sortida d'un tren+color, de la més vella a la més nova."""
    suf = f"_{tren}_{mode}"
    out = [os.path.join(OUTPUT, d) for d in os.listdir(OUTPUT)
           if _PREFIX.match(d) and d.endswith(suf)
           and os.path.isdir(os.path.join(OUTPUT, d))]
    return sorted(out, key=numero_de)


def run_per_segell(segell: str) -> str:
    """Troba un run pel seu SEGELL, tant si porta número com si no.

    Els documents citen els runs pel segell (`VIXEN_CIENCIA_20260827T012038Z`);
    aquesta funció els continua trobant després de numerar les carpetes.
    """
    m = _SEGELL.search(segell)
    clau = m.group(1) if m else segell
    for d in sorted(os.listdir(RUNS)):
        if clau in d:
            return os.path.join(RUNS, d)
    raise SystemExit(f"no trobo cap run amb el segell {clau}")


# -------------------------------------------------------------------- run


@dataclass
class Run:
    """Un run. Immutable un cop escrit; cap ruta surt d'aquí a fora."""

    tren: str
    segell: str
    dir: str
    mode: str = "CIENCIA"          # clau de MODES_COLOR
    rebuts: dict = field(default_factory=dict)

    @classmethod
    def nou(cls, tren: str, segell: str, mode: str = "CIENCIA") -> "Run":
        if mode in MODES_DEPRECATS:
            raise SystemExit(
                f"⛔ el mode de color {mode} està DEPRECAT des del 27-08-2026 "
                f"(decisió de Pere: el projecte segueix amb CIENCIA). Els runs "
                f"vells es continuen podent llegir, però no se'n fan de nous. "
                f"Modes vius: {list(MODES_COLOR)}")
        if mode not in MODES_COLOR:
            raise SystemExit(f"mode de color desconegut: {mode} (n'hi ha {list(MODES_COLOR)})")
        n = max([numero_de(x) for x in os.listdir(RUNS)] + [0]) + 1
        d = os.path.join(RUNS, f"{n:03d}_{tren}_{mode}_{segell}")
        if os.path.exists(d):
            raise SystemExit(f"el run ja existeix i un run no es toca mai: {d}")
        for f in FASES:
            os.makedirs(os.path.join(d, f), exist_ok=False)
        os.makedirs(os.path.join(d, "codi"))
        os.makedirs(os.path.join(d, "lliurables", "vistes"))
        return cls(tren=tren, segell=segell, dir=d, mode=mode)

    @classmethod
    def obre(cls, d: str) -> "Run":
        b = sense_prefix(d)
        tren, _, resta = b.partition("_")
        mode, _, segell = resta.partition("_")
        return cls(tren=tren, segell=segell, dir=d, mode=mode)

    # rutes
    def fase(self, n: int, *parts: str) -> str:
        p = os.path.join(self.dir, FASES[n], *parts)
        os.makedirs(os.path.dirname(p) if parts else p, exist_ok=True)
        return p

    def rebut(self, nom: str) -> str:
        return os.path.join(self.dir, "4-rebuts", nom)

    def lliurable(self, nom: str) -> str:
        return os.path.join(self.dir, "lliurables", nom)

    def vista(self, nom: str) -> str:
        return os.path.join(self.dir, "lliurables", "vistes", nom)

    def desa_rebut(self, nom: str, dades: dict) -> None:
        with open(self.rebut(nom), "w") as fh:
            json.dump(dades, fh, indent=1, ensure_ascii=False, sort_keys=True)
        self.rebuts[nom] = dades

    def llegeix_rebut(self, nom: str) -> dict:
        with open(self.rebut(nom)) as fh:
            return json.load(fh)

    @property
    def cfg(self) -> dict:
        return TRENS[self.tren]

    @property
    def color(self) -> dict:
        # ⏭️ els runs DEPRECATS es continuen podent obrir i llegir: un run és
        #    immutable i el seu rebut ha de continuar tenint sentit.
        return MODES_COLOR.get(self.mode) or MODES_DEPRECATS[self.mode]

    @property
    def matriu(self) -> np.ndarray:
        if getattr(self, "_M", None) is None:
            self._M = matriu_srgb(entrades(self.tren, "totalitat")[0])
        return self._M


def sha256(ruta: str) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def llista(carpeta: str, ext: str) -> list[str]:
    """Fitxers d'una extensió, ORDENATS. ⛔ Mai `glob`, que no garanteix ordre."""
    if not os.path.isdir(carpeta):
        raise SystemExit(f"no hi ha la carpeta: {carpeta}")
    return [os.path.join(carpeta, n) for n in sorted(os.listdir(carpeta))
            if n.upper().endswith(ext.upper())]


def entrades(tren: str, quin: str) -> list[str]:
    cfg = TRENS[tren]
    if quin == "totalitat":
        return llums(tren)
    return llista(os.path.join(cfg["dir"], quin), cfg["ext"])


def llums(tren: str) -> list[str]:
    """Els fotogrames de totalitat, que poden venir de MES D'UNA CARPETA.

    La Sony te els seus 32 partits en `totalitat` (14, segon apuntament),
    `descentrats` (15, primer apuntament) i `inservibles` (3, moguts durant el
    salt de muntura). El tall entre els dos primers **no separa bo de dolent**:
    separa els DOS APUNTAMENTS (research/115 §1, research/116 §8).

    Un tren declara `carpetes_llum` per dir quines llegeix. `exclou` continua
    existint per deixar fora un fotograma concret sense moure'l de lloc, pero
    ⏭️ **des del 27-08 no s'usa**: el que no serveix viu a `inservibles/`, que
    simplement no es llegeix. Un nom de carpeta que menteix costa mes que una
    llista d'exclusions.
    """
    cfg = TRENS[tren]
    fora = set(cfg.get("exclou", ()))
    out = []
    for c in cfg.get("carpetes_llum", ("totalitat",)):
        out += [p for p in llista(os.path.join(cfg["dir"], c), cfg["ext"])
                if os.path.basename(p) not in fora]
    return sorted(out, key=os.path.basename)


def ruta_llum(tren: str, nom: str) -> str:
    """La ruta d'un fotograma de llum pel seu nom, sigui a la carpeta que sigui."""
    for p in llums(tren):
        if os.path.basename(p) == nom:
            return p
    raise SystemExit(f"{tren}: no trobo el fotograma {nom}")


# -------------------------------------------------------- geometria i CFA


@dataclass(frozen=True)
class Geo:
    alt: int
    ample: int
    marge_dalt: int
    marge_esq: int
    marge_dreta: int
    marge_baix: int
    desc: str

    @property
    def visible(self):
        return (slice(self.marge_dalt, self.alt - self.marge_baix),
                slice(self.marge_esq, self.ample - self.marge_dreta))


def geometria(r: rawpy.RawPy) -> Geo:
    s = r.sizes
    h, w = r.raw_image.shape
    return Geo(alt=h, ample=w, marge_dalt=s.top_margin, marge_esq=s.left_margin,
               marge_dreta=w - s.left_margin - s.width,
               marge_baix=h - s.top_margin - s.height,
               desc=r.color_desc.decode() if isinstance(r.color_desc, bytes)
               else str(r.color_desc))


def mapa_colors(r: rawpy.RawPy) -> np.ndarray:
    """Índex CFA de cada píxel de `raw_image`, marges inclosos.

    ⚠️ Es construeix amb la MATEIXA convenció que rawpy i es COMPROVA contra
    `raw_colors_visible`: la versió anterior feia servir la convenció contrària
    i només sortia bé perquè els dos marges són parells.
    """
    h, w = r.raw_image.shape
    s = r.sizes
    pat = np.asarray(r.raw_pattern)
    fil = (np.arange(h) - s.top_margin) % 2
    col = (np.arange(w) - s.left_margin) % 2
    mc = pat[fil[:, None], col[None, :]]
    vis = mc[s.top_margin:s.top_margin + s.height,
             s.left_margin:s.left_margin + s.width]
    if not np.array_equal(vis, r.raw_colors_visible):
        raise SystemExit("el mapa CFA no coincideix amb rawpy: no segueixis")
    return mc


NOMS = ("R", "G1", "B", "G2")
IDX_CANAL = {0: 0, 1: 1, 2: 2, 3: 1}     # R, G1, B, G2  ->  R, G, B, G
CANALS = ("R", "G", "B")


def nom_canal(i: int, desc: str = "RGBG") -> str:
    l = desc[i] if i < len(desc) else "?"
    return ("G1" if i == 1 else "G2") if l == "G" else l


def zona_fosca(g: Geo, guarda: int = 16) -> tuple[np.ndarray, str]:
    """Zona emmascarada FIABLE: només el marge ESQUERRE.

    ⛔ El marge SUPERIOR queda fora: les files 0-40 porten lluïssor
    d'amplificador que depèn de la TEMPERATURA (514 DN a 39 °C, 617 a 44 °C,
    píxels de fins a 6.684). La zona activa no se n'assabenta.
    """
    if g.marge_esq <= 2 * guarda:
        raise SystemExit("marge esquerre massa prim: aquest cos no té zona "
                         "emmascarada i el pedestal ha de sortir dels darks "
                         "(TRENS[...]['pedestal_font'] = 'darks')")
    m = np.zeros((g.alt, g.ample), bool)
    m[48:g.alt - 48, guarda:g.marge_esq - guarda] = True
    return m, f"esq col[{guarda}:{g.marge_esq-guarda}] fila[48:{g.alt-48}]"


# --------------------------------------------------- calibració per canal


def balanc_dia(ruta_raw: str) -> np.ndarray:
    """Multiplicadors de llum de dia normalitzats a G. L'escena ÉS el Sol."""
    with rawpy.imread(ruta_raw) as r:
        w = list(r.daylight_whitebalance)
    return np.array([w[0] / w[1], 1.0, w[2] / w[1]], np.float64)


def calibra_pla(raw: np.ndarray, dark: np.ndarray, flat: np.ndarray,
                exposicio: float, wb: np.ndarray, mc: np.ndarray,
                idx_cfa: int) -> np.ndarray:
    """Un subpla CFA calibrat, per SEGON i JA BALANCEJAT.

    ⛔ **El balanç de blancs viu aquí i enlloc més.** És l'únic lloc per on
    passa tota la dada, i posar-l'hi fa impossible l'error del 26-08: refer la
    imatge des dels RAW sense balanç i restar-hi després un mapa de cel que sí
    que en portava (2,17x massa vermell tret, 88 % del canal R a zero).
    """
    return ((raw - dark) / flat / exposicio * wb[IDX_CANAL[idx_cfa]]).astype(np.float32)


# ------------------------------------------------------------ corba de to


def ancora(v: np.ndarray, rad: np.ndarray, m: np.ndarray, r_sol_px: float,
           lo: float = 1.05, hi: float = 1.15) -> float:
    """Mediana de l'anell d'àncora. ⛔ Falla tancat si l'anell és buit."""
    a = m & (rad >= lo * r_sol_px) & (rad <= hi * r_sol_px) & np.isfinite(v) & (v > 0)
    if a.sum() < 500:
        raise ValueError(f"anell d'àncora {lo}-{hi} R☉ amb només {int(a.sum())} px")
    return float(np.median(v[a]))


def corba_to(v: np.ndarray, m: np.ndarray, va: float,
             pend: float = 0.17, anc: float = 0.68, terra: float = 0.045) -> np.ndarray:
    """Corba DECLARADA de `research/108`, amb l'àncora COMUNA als tres canals.

        y = anc + pend * log10(v / va)

    ⛔ `va` és un ARGUMENT i ha de ser el MATEIX per als tres canals. Si cada
    canal s'ancora al seu propi valor, la mediana és homogènia, qualsevol
    constant per canal s'anul·la i **la imatge surt monocroma** (mesurat: la
    corona té R/G d'1,84 i arribava a pantalla amb R−G = ±0,002).
    """
    if not np.isfinite(va) or va <= 0:
        raise ValueError(f"àncora invàlida: {va}")
    x = np.where(m & np.isfinite(v) & (v > 0), v, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        y = anc + pend * np.log10(x / va)
    return np.clip(np.where(np.isfinite(y), y, terra), terra, 1.0).astype(np.float32)


# ----------------------------------------------- la porta del color (Pere)


# ---------------------------------------------------- la cadena de COLOR

XYZ_SRGB = np.array([[ 3.24096994, -1.53738318, -0.49861076],
                     [-0.96924364,  1.87596750,  0.04155506],
                     [ 0.05563008, -0.20397696,  1.05697151]])


def matriu_srgb(ruta_raw: str) -> np.ndarray:
    """Matriu càmera → sRGB, convenció dcraw.

    ⛔ Els multiplicadors del balanç de blancs SOLS no són colorimetria. Sense
    la matriu la corona surt **2,6 vegades massa blava** (B/G 0,498 en lloc de
    0,194) i per això els lliuraments sortien «tirant a cafè» (`research/109`).
    ⚠️ Es normalitzen les files de la matriu **ENDAVANT** (sRGB→cam) i després
    s'inverteix, que és el que fa dcraw. Normalitzant la d'enrere el cel surt
    VERDÓS: és un error silenciós i fàcil.
    """
    with rawpy.imread(ruta_raw) as r:
        Mx = np.asarray(r.rgb_xyz_matrix)[:3, :3].astype(np.float64)
    cam_rgb = Mx @ np.linalg.inv(XYZ_SRGB)
    su = cam_rgb.sum(axis=1, keepdims=True)
    if not np.all(np.isfinite(su)) or np.any(np.abs(su) < 1e-6):
        raise SystemExit(f"matriu de color degenerada a {ruta_raw}")
    M = np.linalg.inv(cam_rgb / su)
    n = M @ np.ones(3)
    if float(np.max(np.abs(n - 1.0))) > 1e-6:      # el neutre ha de sortir neutre
        raise SystemExit(f"la matriu no conserva el neutre: {n}")
    return M.astype(np.float32)


def a_lineal(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def a_srgb(c):
    c = np.clip(np.asarray(c, np.float32), 0.0, 1.0)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


# ⏭️ Corba de to: la MATEIXA als dos modes, perquè la comparació aïlli el color.
#    0,22/dècada és dins la banda de Brno (0,202-0,240 mesurats sobre els seus
#    quatre composts del NOSTRE eclipsi) i entre la maqueta de Pere (0,166) i
#    `estira_log` (0,524, que cremava 1,67 dècades).
CORBA = {"pendent": 0.22, "ancora": 0.74, "terra": 0.045}

# ⏭️ PROCEDÈNCIA (27-08, per una pregunta de Pere: «què passa si Brno s'equivoca
#    i nosaltres ho propaguem?»). Aquesta taula va al rebut de CADA run perquè
#    la dependència quedi auditable sola i no depengui que ningú se'n recordi.
#    ⛔ Cap píxel ni cap correcció de Brno no entra al producte: a l'auditoria
#    del `research/114` hi van fer de JUTGE, i l'única correcció que hauria
#    pujat l'acord amb ells (el model de halo) es va REFUSAR.
#    ⚠️ I els seus quatre composts NO són quatre jutges independents: mateix
#    equip i mateix pipeline. «Brno×Brno» és un SOSTRE, no un control.
PROCEDENCIA = [
    ("MESURAT AQUÍ", "pedestal, saturació, flat radial, efemèride i llenç, "
     "registre fi, coherència per fotograma, cel per color, matriu de color de "
     "la càmera, model d'extinció, i totes les portes",
     "no depèn de ningú de fora"),
    ("TRIA DE PERE", "mode de color: CIENCIA, blanc sobre el Sol (AM0). El mode "
     "MEMORIA queda DEPRECAT el 27-08-2026",
     "declarat al rebut; es canvia sense refer la dada"),
    ("DE BRNO · número", "corba de to: pendent 0,22/dècada i àncora 0,74",
     "dins la banda mesurada als seus 4 composts (0,202-0,240; cim 0,72-0,76). "
     "És PRESENTACIÓ i està declarada: la maqueta de Pere en deia 0,166 i "
     "`estira_log` 0,524. Canviar-la és canviar un número"),
    ("DE BRNO · convenció", "capa 08 CORONA NEUTRA (blanquejar sobre la corona "
     "mesurada)", "viatja AL COSTAT de la capa 07, que surt del nostre model "
     "d'extinció: la diferència entre les dues és visible, no amagada"),
    ("DE BRNO · mètode", "LDIC (una sola suma ponderada), croma a baixa "
     "freqüència, cel al terra en lloc de negre, màscara lunar per fotograma",
     "són mètodes, i cadascun té la seva porta sobre la NOSTRA dada"),
    ("VERIFICAT TRES VEGADES", "l'estructura de la corona",
     "la nostra propia dada (dos fotogrames a 60 s: 0,984 a 4,5°), l'ALTRE TREN "
     "(Vixen x Sony 0,989 a 4,5°, per damunt del 0,976 de Brno amb ell mateix) "
     "i Brno (0,943). Les dues primeres cames no el coneixen. research/114 i 115"),
]

# ⏭️ L'EXTINCIÓ DECLARADA. Amb això al rebut, el groc deixa de ser una opinió:
#    qualsevol pot desfer-lo i obtenir la corona de sobre l'atmosfera, que és
#    la que lliura Brno. `research/109` §12.
EXTINCIO = {
    "lloc": "MIRADOR FINAL 2 · 42,299407 N · −5,02503 E · 798 m",
    "instant_utc": "2026-08-12T18:29:40Z",
    "alcada_sol_graus": 9.07,
    "massa_aire_X": 6.12,
    "model": "Planck 5772 K × (Rayleigh a 921 hPa + aerosol Ångström + ozó "
             "Chappuis), integrat contra les CIE 1931, blanc D65",
    "k_V_mag_per_X": 0.40,
    "AOD_550": 0.237,
    "angstrom_alpha": 1.3,
    "color_del_Sol_a_X": [1.818, 1.0, 0.250],
    "color_del_Sol_sense_atmosfera": [1.075, 1.0, 0.888],
    "nomes_extincio": [1.691, 1.0, 0.2815],
    "com_desfer_ho": ("divideix el sRGB LINEAL per `nomes_extincio` i tindràs la "
                      "corona tal com es veuria sobre l'atmosfera; per la "
                      "neutralitat total de Brno, divideix pel color mesurat de "
                      "la corona mateixa, que és `color_renderitzat_sRGB_lineal`"),
    "control": ("predit 1,818 · 0,250 contra 1,796 · 0,243 mesurats al fotograma "
                "572A2996 a 1,70 R☉ → 1,2 % i 2,8 %"),
    "font": "research/109 §12",
}

# ⛔ MODE DEPRECAT — decisió de Pere del 27-08-2026: «depreca el mode de color
#    MEMORIA, seguim amb ciència». Es conserva SENCER i no s'esborra per tres
#    motius, i cap és sentimental:
#      1. el run `VIXEN_MEMORIA_20260826T155138Z` existeix i és immutable;
#         `Run.obre()` l'ha de poder llegir per sempre;
#      2. el guany és una MESURA (el terme de càmera i vidre entre els dos
#         trens, 1,3 % i 2,2 % de dispersió) i esborrar-la seria perdre-la;
#      3. la comparativa dels dos modes és la proveniència de la decisió.
#    ⛔ El que NO es pot fer és arrencar un run nou amb ell: `Run.nou` el refusa.
MODES_DEPRECATS = {
    "MEMORIA": {
        "guany": (1.1528, 1.0, 1.0249),
        "titol": "el color del DSC06991 (testimoni de Pere)",
        "deprecat": "27-08-2026, per decisió de Pere: el projecte segueix amb CIENCIA",
        "per_que": ("guany mesurat perquè el Vixen es renderitzi com el fotograma "
                    "Sony DSC06991.ARW, que és el que Pere recorda d'haver viscut. "
                    "Mesurat sobre 2,18-4,82 R☉ amb 1,3 % i 2,2 % de dispersió; "
                    "és el terme de càmera i vidre entre els dos trens."),
    },
}

MODES_COLOR = {
    "CIENCIA": {
        # blanc = ESPECTRE SOLAR EXTRATERRESTRE (AM0), no D65
        "guany": (1.0 / 1.075, 1.0, 1.0 / 0.888),
        "titol": "blanc sobre el Sol de sobre l'atmosfera (AM0)",
        "per_que": ("el blanc adoptat és el SOL, no D65. D65 és llum diürna "
                    "mitjana i no és el blanc al qual l'ull de Pere estava "
                    "adaptat, o sigui que «D65 = tal com es veia» seria fals. "
                    "Amb el Sol com a blanc, el que queda a la imatge és "
                    "l'extinció de León —més l'enrogiment propi de la corona F, "
                    "les línies E i els residus instrumentals—, i això sí que és "
                    "una afirmació física. La corona hi surt R/G 1,793 · B/G "
                    "0,218 i la predicció d'extinció sola en fa 1,691 · 0,282. "
                    "Contrast de Codex, 26-08."),
    },
}


# ⏭️ El TESTIMONI de Pere: el perfil de color del DSC06991.ARW (Sony A7RIIIA,
#    300 mm, 1 s, 20:29:44), revelat amb la cadena sencera —pedestal mesurat,
#    balanç de dia, matriu de color, primàries sRGB lineals—. Era la referència
#    del mode MEMORIA, que des del 27-08-2026 està DEPRECAT.
#    ⏭️ **No es retira**: continua sent el CONTROL extern del color, a
#    `F3.control_testimoni_DSC06991`, i allà mesura, no afirma. El que s'ha
#    deprecat és renderitzar CONTRA ell, no comparar-s'hi.
REFERENCIA_SONY = {
    1.46: (2.143, 0.318), 1.67: (2.034, 0.348), 1.91: (1.960, 0.367),
    2.18: (1.817, 0.431), 2.49: (1.654, 0.503), 2.84: (1.514, 0.565),
    3.24: (1.398, 0.615), 3.70: (1.305, 0.655), 4.23: (1.230, 0.687),
    4.82: (1.171, 0.711), 5.51: (1.124, 0.731), 6.29: (1.087, 0.747),
    7.18: (1.057, 0.759), 8.20: (1.032, 0.769),
}


def revela_frame(ruta: str, M: np.ndarray, ped_declarat=None):
    """Un RAW solt per la MATEIXA cadena de color, per fer-lo servir de control.

    ⛔ Pedestal MESURAT al marge emmascarat: el declarat de la R6 III és fals
    ([0, 29, 94, 61] contra 512 pla) i amb ell el color de la corona externa
    s'ensorra (`research/71`, confirmat el 26-08).
    ⏭️ Binning 2×2 del mosaic, sense cap interpolació: no volem que el demosaic
    inventi color a un control de color.
    """
    with rawpy.imread(ruta) as r:
        raw = r.raw_image.astype(np.float64)
        vis = r.raw_image_visible.astype(np.float64)
        pat = np.asarray(r.raw_pattern)
        tm, lm = r.sizes.top_margin, r.sizes.left_margin
        dw = np.asarray(r.daylight_whitebalance, float)[:3]
        sat = float(r.white_level)
    # ⏭️ Amb marge emmascarat el pedestal es mesura AQUÍ, fotograma a fotograma
    #    (segueix la temperatura). ⛔ L'A7RIIIA no en té: allà arriba DECLARAT,
    #    mesurat als 378 darks (512,00 pla, dispersió 0,00 DN).
    if ped_declarat is not None:
        ped = np.full(4, float(ped_declarat))
    elif lm < 16:
        raise SystemExit(f"{ruta}: sense marge fosc per mesurar el pedestal i "
                         f"cap pedestal declarat (passa `ped_declarat`)")
    else:
        fosc = raw[tm:tm + vis.shape[0], 4:lm - 4]
        ped = np.array([np.median(fosc[i::2, j::2]) for i in range(2) for j in range(2)])
    h, w = (vis.shape[0] // 2) * 2, (vis.shape[1] // 2) * 2
    vis = vis[:h, :w]
    P = {}
    for i in range(2):
        for j in range(2):
            P.setdefault(int(pat[i, j]), []).append(vis[i::2, j::2] - ped[pat[i, j]])
    cub = np.stack([P[0][0], 0.5 * (P[1][0] + P[3][0]), P[2][0]], -1).astype(np.float32)
    # ⛔ La saturació es mesura al MOSAIC CRU, no al binat i no després del
    #    balanç. Al binat, un píxel saturat promitjat amb un que no ho és baixa
    #    del llindar i la saturació s'hi cola: amb el fotograma de 10 s això
    #    donava −42,7 % de B/G a 1,8-2,0 R☉. I el balanç multiplica el vermell
    #    per 2,17, o sigui que aplicat abans movia el llindar per canal.
    llind = 0.90 * (sat - float(np.median(ped)))
    viu = np.ones(cub.shape[:2], bool)
    for i in range(2):
        for j in range(2):
            viu &= (vis[i::2, j::2] - ped[pat[i, j]]) < llind
    cub *= (dw / dw[1])[None, None, :].astype(np.float32)
    u = np.einsum("ij,hwj->hwi", M, cub)
    lum = u @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    ys, xs = np.nonzero(lum >= np.percentile(lum, 99.9))
    cy, cx = float(ys.mean()), float(xs.mean())
    for _ in range(8):
        th = np.linspace(0, 2 * np.pi, 720, endpoint=False)
        rs = np.arange(4.0, min(cy, cx, lum.shape[0] - cy, lum.shape[1] - cx), 0.5)
        rad = []
        for t in th:
            Y = np.clip((cy + rs * np.sin(t)).astype(int), 0, lum.shape[0] - 1)
            X = np.clip((cx + rs * np.cos(t)).astype(int), 0, lum.shape[1] - 1)
            v = lum[Y, X]; kp = int(np.argmax(v))
            rad.append(rs[int(np.argmax(np.gradient(v)[:max(kp, 3)]))])
        rad = np.asarray(rad); md = np.median(rad); bo = np.abs(rad - md) < 0.06 * md
        A = np.column_stack([np.cos(th[bo]), np.sin(th[bo]), np.ones(int(bo.sum()))])
        dx, dy, Rr = np.linalg.lstsq(A, rad[bo], rcond=None)[0]
        cx += dx; cy += dy
        if abs(dx) < 0.05 and abs(dy) < 0.05:
            break
    yy, xx = np.mgrid[0:lum.shape[0], 0:lum.shape[1]]
    rr = np.hypot(yy - cy, xx - cx) / (Rr / 1.0335)
    return u, rr.astype(np.float32), viu


ANELLS_CONTROL = ((1.8, 2.0), (2.0, 2.3), (2.3, 2.7), (2.7, 3.1),
                  (3.1, 3.6), (3.6, 4.2), (4.2, 4.9))

# anells per a la porta de BRILLANTOR: han d'arribar a la corona interior, que
# és on el joc d'exposicions canvia i on una porta per mediana no veu res
ANELLS_BRILLANTOR = ((1.15, 1.30), (1.30, 1.50), (1.50, 1.80), (1.80, 2.10),
                     (2.10, 2.50), (2.50, 3.00), (3.00, 3.60))
PERCENTILS_BRILLANTOR = (10, 25, 50, 75, 90)


def tancament_hdr_brillantor(lumA, mA, rA, ruta_frame: str, M: np.ndarray,
                             llindar_pct=8.0, ped_declarat=None) -> dict:
    """PORTA NOVA (27-08): el tancament HDR **contra la BRILLANTOR**.

    `tancament_hdr` compara MEDIANES d'anell, i una mediana no pot veure un
    error que depengui del nivell del píxel —que és exactament la forma que té
    un defecte de fusió HDR, perquè la frontera entre exposicions és una
    ISOFOTA—. Aquí, dins de cada anell, es comparen els PERCENTILS del compost
    amb els del fotograma solt: si la fusió fos neutra, el quocient ha de ser
    el mateix a tots els percentils, i qualsevol dependència amb la brillantor
    hi surt encara que la mediana quadri.

    No cal correspondència píxel a píxel: dins d'un anell tots dos veuen la
    mateixa corona, o sigui que les seves distribucions han de coincidir tret
    d'una constant. Un guany global es cancel·la perquè cada anell es
    normalitza a la seva pròpia mediana de quocients.

    ⏭️ Mesurat el 27-08 al run VIXEN_CIENCIA_20260827T012038Z píxel a píxel amb
    tres fotogrames: la desviació real va de ±1 a ±3 %, o sigui que un llindar
    del 8 % deixa passar el que hi ha i atrapa un defecte de debò.
    """
    uB, rB, mB = revela_frame(ruta_frame, M, ped_declarat)
    lumB = uB @ np.array([0.2126, 0.7152, 0.0722], np.float64)
    files, desv = {}, []
    for a, b in ANELLS_BRILLANTOR:
        sA = mA & (rA >= a) & (rA < b) & np.isfinite(lumA) & (lumA > 0)
        anB = (rB >= a) & (rB < b)
        sB = mB & anB & (lumB > 0)
        if anB.sum() < 3000 or sB.sum() / max(int(anB.sum()), 1) < 0.80:
            continue
        if sA.sum() < 5000 or sB.sum() < 3000:
            continue
        pA = np.percentile(lumA[sA], PERCENTILS_BRILLANTOR)
        pB = np.percentile(lumB[sB], PERCENTILS_BRILLANTOR)
        q = pA / np.maximum(pB, 1e-30)
        rel = q / np.median(q) - 1.0
        files[f"{a:g}-{b:g}"] = {"percentils": list(PERCENTILS_BRILLANTOR),
                                 "quocient": [float(x) for x in q],
                                 "desviacio_pct": [float(x * 100) for x in rel]}
        desv.append(float(np.max(np.abs(rel)) * 100))
    if len(files) < 4:
        return {"veredicte": "SENSE DADA", "fotograma": os.path.basename(ruta_frame),
                "anells_valids": len(files)}
    sis = float(np.median(desv)); pit = float(np.max(desv))
    return {"fotograma": os.path.basename(ruta_frame), "anells": files,
            "sistematic_pct": sis, "pitjor_pct": pit, "llindar_pct": llindar_pct,
            "jutja": "la dependència del quocient compost/fotograma amb la BRILLANTOR",
            "veredicte": "PASSA" if sis <= llindar_pct else "NO PASSA"}


def controls_repartits(run, n=5) -> list[str]:
    """Fotogrames de control REPARTITS EN EL TEMPS.

    ⛔ El compost es una MITJANA TEMPORAL i la porta el comparava amb UN SOL
    INSTANT. Mesurat el 27-08 a la Sony: el B/G d'un fotograma a 1,8-3,6 R☉ va
    de 0,579 (t=16 s) a 0,507 (t=62 s) i torna a 0,535 (t=88 s) — un **12 %**
    en 100 s, que es el cel canviant (research/100 hi va mesurar un 8 % de
    transparencia). Amb un apuntament el recorregut era de 46 s i la porta
    passava; amb els dos, de 104 s, i queia. El defecte era del CONTROL.
    """
    S = run.llegeix_rebut("F1.2_sol_llenc.json")["fotogrames"]
    cor = {k: v for k, v in S.items() if v.get("coronal")}
    if not cor:
        raise SystemExit("PORTA: cap fotograma coronal per al control de tancament")
    # de mes llarga a mes curta, i dins de cada exposicio repartits en el temps
    exps = sorted({round(v["exp"], 8) for v in cor.values()}, reverse=True)
    fora = []
    for e in exps:
        ns = sorted((v["t"], k) for k, v in cor.items() if round(v["exp"], 8) == e)
        if not ns:
            continue
        idx = np.unique(np.linspace(0, len(ns) - 1, min(n, len(ns))).round().astype(int))
        fora += [ruta_llum(run.tren, ns[i][1]) for i in idx]
    return fora


def candidats_control(run) -> list[str]:
    """Fotogrames CORONALS per al tancament HDR, del més probable al menys.

    ⛔ NO pot ser el primer fitxer de la carpeta: el 572A2936 és de 1/3200 s
    —un fotograma de CONTACTE— i no té corona a 2-5 R☉, o sigui que el control
    tornava «SENSE DADA» i la porta el deixava passar. **Un control que no es
    pot computar és un control que no s'està fent.** (Defecte trobat al primer
    run del 26-08, vespre.)
    """
    S = run.llegeix_rebut("F1.2_sol_llenc.json")["fotogrames"]
    cor = {n: v for n, v in S.items() if v.get("coronal")}
    if not cor:
        raise SystemExit("PORTA: cap fotograma coronal per al control de tancament")
    # ⏭️ de MÉS LLARGA a més curta: el control necessita senyal a 2-5 R☉, i
    #    les que cremen la corona interior ja les rebutja el propi control
    #    (exigeix 4 anells sencers sense saturar).
    exps = sorted({round(v["exp"], 8) for v in cor.values()}, reverse=True)
    fora = []
    for e in exps:
        noms = sorted(n for n, v in cor.items() if round(v["exp"], 8) == e)
        if noms:
            # la ruta surt de `llums`, que sap de quina carpeta ve cada fotograma
            fora.append(ruta_llum(run.tren, noms[0]))
    return fora


def cfg_dir(run) -> str:
    return run.cfg["dir"]


def tancament_hdr(uA, mA, rA, ruta_frame: str, M: np.ndarray, llindar_pct=5.0,
                  ped_declarat=None) -> dict:
    """CONTROL de Codex (26-08): el compost contra un fotograma SOLT del mateix
    tren, als MATEIXOS anells. Si no tanca, el color del compost no queda
    aprovat encara que la predicció d'extinció quadri.

    ⚠️ Els anells han de ser els MATEIXOS: comparar agregats a radis diferents
    barreja proporcions K/F distintes i dona un fals negatiu (a Codex li va
    donar −20 % en B/G; amb els anells igualats surt −4 %).
    ⛔ `uA` ha d'arribar SENSE el guany del mode: això comprova la DADA, no la
    presentació. Amb el guany posat, el control mesurava el guany (−5,1 % i
    +8,4 % de mediana al mode CIENCIA, que són exactament 0,9302 i 1,1261).
    """
    uB, rB, mB = revela_frame(ruta_frame, M, ped_declarat)
    files, er, eb = {}, [], []
    for a, b in ANELLS_CONTROL:
        sA = mA & (rA >= a) & (rA < b)
        anB = (rB >= a) & (rB < b)
        sB = mB & anB
        # ⛔ Si al fotograma l'anell està mig saturat, els píxels que hi
        #    sobreviuen són els MÉS FOSCOS de l'anell: una mostra esbiaixada
        #    amb una barreja K/F que no és la de l'anell sencer. Amb el
        #    fotograma de 10 s això donava −42,7 % a 1,8-2,0 R☉ sense que hi
        #    hagués res malament al compost.
        if anB.sum() < 3000 or sB.sum() / max(int(anB.sum()), 1) < 0.80:
            continue
        if sA.sum() < 5000 or sB.sum() < 3000:
            continue
        A_, B_ = uA[sA], uB[sB]
        ar = float(np.median(A_[:, 0] / A_[:, 1])); ab = float(np.median(A_[:, 2] / A_[:, 1]))
        br = float(np.median(B_[:, 0] / B_[:, 1])); bb = float(np.median(B_[:, 2] / B_[:, 1]))
        er.append(ar / br - 1); eb.append(ab / bb - 1)
        files[f"{a:g}-{b:g}"] = {"compost_R/G": ar, "foto_R/G": br, "error_R/G_pct": 100*(ar/br-1),
                                 "compost_B/G": ab, "foto_B/G": bb, "error_B/G_pct": 100*(ab/bb-1)}
    if len(files) < 4:
        return {"veredicte": "SENSE DADA", "fotograma": os.path.basename(ruta_frame),
                "anells_valids": len(files)}
    pit = float(max(max(abs(x) for x in er), max(abs(x) for x in eb)) * 100)
    # ⏭️ La porta jutja el SISTEMÀTIC (mediana sobre els anells), no l'anell
    #    pitjor: l'anell interior és on la saturació i la llum dispersa piquen
    #    més fort i no descriu el color del compost. El pitjor es declara.
    sis = float(max(abs(np.median(er)), abs(np.median(eb))) * 100)
    return {"fotograma": os.path.basename(ruta_frame), "anells": files,
            "mediana_R/G_pct": float(np.median(er) * 100),
            "mediana_B/G_pct": float(np.median(eb) * 100),
            "sistematic_pct": sis, "pitjor_pct": pit, "llindar_pct": llindar_pct,
            "jutja": "el sistemàtic (mediana sobre els anells)",
            "veredicte": "PASSA" if sis < llindar_pct else "NO PASSA"}


def control_testimoni(col_srgb: dict) -> dict:
    """Quant s'assembla el que lliurem al fotograma que Pere recorda."""
    rr = np.array(sorted(REFERENCIA_SONY))
    sr = np.array([REFERENCIA_SONY[k][0] for k in rr])
    sb = np.array([REFERENCIA_SONY[k][1] for k in rr])
    out = {}
    for k, v in sorted(col_srgb.items()):
        r0 = float(k.replace("Rsol", ""))
        if r0 < rr.min() or r0 > rr.max():
            continue
        er = v["R/G"] / float(np.interp(r0, rr, sr)) - 1.0
        eb = v["B/G"] / float(np.interp(r0, rr, sb)) - 1.0
        out[k] = {"R/G_nostre": v["R/G"], "R/G_sony": float(np.interp(r0, rr, sr)),
                  "B/G_nostre": v["B/G"], "B/G_sony": float(np.interp(r0, rr, sb)),
                  "error_R/G_pct": 100 * er, "error_B/G_pct": 100 * eb}
    if out:
        e = [max(abs(v["error_R/G_pct"]), abs(v["error_B/G_pct"])) for v in out.values()]
        out["_pitjor_pct"] = float(max(e))
        out["_mediana_pct"] = float(np.median(e))
    return out


def mascara_dada(den: np.ndarray, rad_px: np.ndarray, frac: float = 0.02,
                 nb: int = 400) -> np.ndarray:
    """Hi ha mesura útil? Es compara amb el que és ASSOLIBLE AL MATEIX RADI.

    ⛔ Un llindar sobre el MÀXIM GLOBAL del pes no serveix. Prop del limbe
    només hi contribueixen les exposicions CURTES —la resta hi està saturada—
    i el pes hi cau dos ordres de magnitud de manera legítima. Amb el màxim
    global, la corona interior es perdia sencera: mesurat el 27-08, a 1,05 R☉
    el «2 % del màxim» deixava fora el **75 %** de l'anell, i el màxim mateix
    queia **DINS de la Lluna** (r = 1,020 R☉), perquè els píxels foscos rebien
    pes ple de tots els fotogrames.

    ⏭️ Aquesta funció l'han de fer servir TOTS els llocs que decideixen on hi
    ha dada, o divergeixen (la lliçó de `f2.mascara_lluna`).
    """
    r = np.asarray(rad_px, np.float32)
    rmax = float(r.max())
    idx = np.clip((r / max(rmax, 1e-6) * nb).astype(np.int32), 0, nb - 1)
    top = np.zeros(nb, np.float64)
    hi = den > 0
    if hi.any():
        ordre = np.argsort(idx[hi], kind="stable")
        bb = idx[hi][ordre]; vv = den[hi][ordre]
        n = np.bincount(bb, None, nb); off = np.concatenate([[0], np.cumsum(n)])
        for k in np.flatnonzero(n > 50):
            top[k] = np.percentile(vv[off[k]:off[k + 1]], 99.0)
    ker = np.exp(-0.5 * (np.arange(-8, 9) / 3.0) ** 2); ker /= ker.sum()
    w = (top > 0).astype(np.float64)
    sm = np.convolve(top * w, ker, "same") / np.maximum(np.convolve(w, ker, "same"), 1e-12)
    bo = sm > 0
    if bo.any():
        sm[~bo] = np.interp(np.flatnonzero(~bo), np.flatnonzero(bo), sm[bo])
    return (den > frac * sm[idx].astype(np.float32)) & (den > 0)


def _suau(a, s):
    k = int(6 * s) | 1
    return cv2.GaussianBlur(np.asarray(a, np.float32), (k, k), s)


def lluminancia(u_cam: np.ndarray, M: np.ndarray, guany) -> np.ndarray:
    """(H,W,3) en espai de càmera amb balanç de dia → lluminància sRGB lineal."""
    u = np.einsum("ij,hwj->hwi", M, u_cam.astype(np.float32)) * np.asarray(guany, np.float32)
    return ((u[..., 0] + 2.0 * u[..., 1] + u[..., 2]) / 4.0).astype(np.float32), u


def render_visual(u_cam, m, va, M, guany, pend=None, anc=None, terra=None, sigma=24.0):
    """Una sola corba sobre la LLUMINÀNCIA i el croma restituït.

    ⛔ Tonificar cada canal per separat afegeix un desplaçament CONSTANT en
    logaritme; com que el nivell cau amb el radi, el quocient de pantalla es
    dispara i el color DERIVA (mesurat: R/G d'1,06 a 1,35 amb la dada plana a
    1,76). Era el defecte que Pere veia a les capes externes.
    ⏭️ El croma va a BAIXA FREQÜÈNCIA (Brno): el residu útil val 0,4 % contra
    un soroll cromàtic per píxel del 2 al 5 %.
    ⛔ El gamut s'acota amb el pes `w`, MAI retallant per canal: retallar un
    canal canvia el color (avís de Codex).
    """
    pend = CORBA["pendent"] if pend is None else pend
    anc = CORBA["ancora"] if anc is None else anc
    terra = CORBA["terra"] if terra is None else terra
    L, u = lluminancia(u_cam, M, guany)
    mf = m.astype(np.float32)
    den = np.maximum(_suau(mf, sigma), 1e-6)
    LS = _suau(np.where(m, L, 0.0), sigma) / den
    q = np.empty_like(u)
    for i in range(3):
        q[..., i] = (_suau(np.where(m, u[..., i], 0.0), sigma) / den) / np.maximum(LS, 1e-9)
    y = corba_to(L, m, va, pend=pend, anc=anc, terra=terra)
    ylin = a_lineal(y)
    qmax = q.max(axis=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        wmax = np.where(qmax > 1.0, (1.0 / np.maximum(ylin, 1e-9) - 1.0) / (qmax - 1.0), np.inf)
    w = np.clip(np.nan_to_num(wmax, nan=0.0, posinf=1.0), 0.0, 1.0).astype(np.float32)
    rgb = a_srgb(ylin[..., None] * (1.0 + w[..., None] * (q - 1.0)))
    rgb = np.where(m[..., None], rgb, 0.0).astype(np.float32)
    fora = float((w < 0.999)[m].mean()) if m.any() else 0.0
    return rgb, {"gamut_acotat_pct": 100.0 * fora, "valor_ancora_L": float(va),
                 "pendent": pend, "ancora": anc, "terra": terra, "sigma_croma_px": sigma}


def mesura_color(C: dict, rad: np.ndarray, m: np.ndarray, r_sol_px: float,
                 radis=(1.1, 2.0, 3.0, 5.0)) -> dict:
    """R/G i B/G per anell. NORMA DE PERE (26-08): a cada resultat, i al rebut.

    Un producte verd vol dir que el verd del Bayer —el doble de píxels i el
    doble de sensible— no s'ha equilibrat. I algun «artefacte» pot ser això.
    """
    out = {}
    for r0 in radis:
        s = m & (rad > r0 * r_sol_px) & (rad < (r0 + 0.06) * r_sol_px)
        for c in CANALS:
            s = s & np.isfinite(C[c])
        if s.sum() < 200:
            continue
        g = np.median(C["G"][s])
        if not np.isfinite(g) or g == 0:
            continue
        out[f"{r0:g}Rsol"] = {"R/G": float(np.median(C["R"][s]) / g),
                              "B/G": float(np.median(C["B"][s]) / g),
                              "n": int(s.sum())}
    return out


def veredicte_color(mc_: dict) -> str:
    """Un sol mot per al rebut, perquè es vegi sense llegir números."""
    if not mc_:
        return "SENSE DADA"
    rg = [v["R/G"] for v in mc_.values()]
    bg = [v["B/G"] for v in mc_.values()]
    if min(rg) < 0.5 and min(bg) < 0.5:
        return "⛔ VERD (R i B ensorrats)"
    if max(abs(np.log10(np.array(rg))).tolist()) < 0.02 and \
       max(abs(np.log10(np.array(bg))).tolist()) < 0.02:
        return "⚠️ NEUTRE — comprova que el balanç i la matriu s'han aplicat"
    return "OK"
