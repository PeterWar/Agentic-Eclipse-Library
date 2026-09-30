# Filtres «Druckmüller» per a la corona externa (18-08-2026)

Capes de detall al llenç de Pere (7648×5353) fetes amb els dos trens alhora. Detall del
mètode, números i QA a `research/82`; lliurables a
`~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Druckmuller_2026-08-18/`.

| Script | Què fa |
|---|---|
| `comu.py` | geometria del llenç (Sol a (4021,35, 2737,90) mesurat sobre `Aplicant_Filtres.tif`), del compost Vixen (RETALL, offset +542,35/+418,90) i de la Sony (placa, similitud); `SCR` per `FD_SCR` |
| `flat_sony_des_del_perfil.py` | reconstrueix `flat_a7r3a_rgb.npy` (5320×7968×3) del perfil radial CSV de `encaix_sony/` quan els intermedis no hi són |
| `prepara_lluminancia.py` | Vixen (HDR + var) i Sony (apilat ≥ 1 s de `encaix_sony/apila_sony.py`, aplanat) al llenç: registre per correlació creuada plana de la corona, aparellament fotomètric, costura de baixa freqüència, soroll per font, combinació 1/σ² → `lum_llenc.npz` + `lum_llenc_geometria.json` (30 s) |
| `filtre_corona_externa.py` | log-polar 8192×3072: fons de Fourier, bandes en graus, soroll sintètic per font i banda, porta de Wiener amb llindar per banda, ADD (additiu, γ_r) i WHITE (blanquejat per anell), COH (coherència entre trens), TOTCAMP; test d'anell, test de colors, NRGF de control, màscara de coherència → 11 TIFF (6,5 min) |

Ordre:

```bash
P=~/.venvs/eines-ia-py312/bin/python; SCR=<carpeta de treball>
mkdir -p $SCR/sony && cd $SCR/sony && $P research/tools/encaix_sony/apila_sony.py      # sony_stack_ref_rgb.npy (3 min)
$P research/tools/filtres_druckmuller/flat_sony_des_del_perfil.py flat_a7r3a_rgb.npy
cd $SCR && FD_SCR=$SCR/treball FD_SONY_DIR=$SCR/sony $P research/tools/filtres_druckmuller/prepara_lluminancia.py
FD_SCR=$SCR/treball FD_OUT=$SCR/capes $P research/tools/filtres_druckmuller/filtre_corona_externa.py   # NOMES=WHITE per depurar
```

Variables: `NA_POLAR`, `NR_POLAR` (8192, 3072), `NOMES` (subcadena de capa), `FD_OUT`.
