# Rescat dels scratchpads de sessió — 17 d'agost de 2026

Aquest directori és una **còpia de seguretat**, no codi revisat. Fins avui, una
part gran del codi del postprocessat vivia només al scratchpad de cada sessió
de Claude (`/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/
<sessió>/scratchpad/`), que és volàtil: un reinici del Mac se'l pot endur. Les
eines de `research/tools/` en depenien amb rutes escrites a pèl.

S'han copiat només els fitxers de text petits (`.py`, `.jsx`, `.md`, `.json`,
`.csv`, `.tsv`, `.log`, < 400 KB), sense `__pycache__`, sense PDF ni textos de
papers, sense cap `.npy`/`.tif`. **Els resultats intermedis grossos (16 GB a la
sessió d'estrelles) no s'han copiat**: es regeneren.

| Carpeta | Sessió | Què hi ha |
|---|---|---|
| `estrelles_placa_flats_16-08/` | `ea55df18` «Solar eclipse image alignment algorithms» (16-08) | predicció d'estrelles amb skyfield + Hipparcos/Tycho-2 (`estrelles.py`, `combina.py`, `final.py` de l'arrel: **només predicció i PTC, cap número de placa**), detecció cega (`sony_stars/` → `catalog_sony.txt`, `vixen/` → `catalog_vixen_fonts.csv`), **creuament, placa i calibratge absolut a `xmatch/`** (`solve.py`, `final_solve.py`, `zp2.py`, `corona2.py`…), auditoria escèptica de la placa (`skeptic2/`; `skeptic/` i `audit/` són foscos i difuminat), resolució/ESF (`sony/`), flats sintètics (`flats/`), síntesis (`sintesi_estrelles.md`, `sintesi_mesures.md`, `LLEGEIX-ME.md`, `pla.md`). ⚠️ `hip_main.dat` (53 MB) és a `~/Desktop/Eclipse 2026/Estrelles/catalegs/`. **La cadena canònica ja està promoguda a `research/tools/astrometria/` (vegeu-ne el `MAPA.md`).** |
| `deflexio_apod_2027_16-08/` | `604fa71e` «APOD submission: eclipse alignment» (16-08) | ajust de deflexió (`deflexio.py`, `fit.py`, `validate*.py`), animació de l'APOD (`animacio.py`, `munta.py`, `render_net.py`), pla del 2027 (`model2027.py`, `forecast2027.py`, `eclipsi2027.py`, `requisits*.py`, `bruns_check.py`). |
| `hdr_vixen_diagnostics_16-17-08/` | `8222da38` «Apilat corona solar VIXEN» (16/17-08) | els diagnòstics de `research/76`: `test_anell.py`, `creuament_trens.py`, `corba*.py`, `diag_*.py`, `escala_check.py`, `taules.py`, `snr_bandes.json`, `corba_fit.json`. |
| `earthshine_halo_15-08/` | `bd892f38` «Eina de calibratge d'imatges d'eclipsi» (15-08) | el model de halo **sense LROC** (`halo_sony2_noLROC.py`, que és el que va fer el producte final i no era al repositori), `halo_sony.py`, `halo_sony2*.py`, `final_rgb_body.py`, `exif_*.json`, `lot_calibratge_vixen.py`. |
| `hdr4_dng_photoshop_17-08/` | `d71d9c5e` «HDR4 corona image stacking» (17-08) | `ps_test/prova_pila.jsx` (prova que `Load Files into Stack` posa la primera de la llista a la capa de dalt) i `prova2.jsx`. |

Regles:

- **No executis res d'aquí sense llegir-ho**: molts scripts tenen rutes de la
  disposició antiga de l'Escriptori (`~/Desktop/Eclipse Vixen Unfiltered`,
  `~/Desktop/Eclipse 2026 300mm`) i rutes al scratchpad d'origen.
- El codi viu i mantingut és el de `research/tools/*.py`. Si una peça d'aquí
  es torna a necessitar, es promou a `research/tools/` amb rutes bones i
  s'anota a `research/README.md`.
- Índex del que hi ha i per què: `research/79_VALIDACIO_PASSOS_POSTPROCESSAT_2026-08-17.md`.
