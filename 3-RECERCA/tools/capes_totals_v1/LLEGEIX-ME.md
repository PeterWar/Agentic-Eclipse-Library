# CapesTotalsV1: codi de la sessió (20-08-2026, matinada)

Nota canònica: `research/86`. Lliurable: `~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint
Capes/Capes Totals/CapesTotalsV1.psb`. Tot sobre `~/.venvs/eines-ia-py312`; els scripts assumeixen el
scratchpad de la sessió com a directori de treball (rutes relatives al costat del codi:
`ext/`, `sf10/`, `v5/`, npz de capes) — per re-executar-los en un directori nou, primer les
tres extraccions.

| Script | Què fa |
|---|---|
| `extreu_exteriors/sf10/v5.py` | bolquen capes+màscares de CapesExteriors, FiltresSEMIFINAL10 i CapesInteriorsV5 a npy |
| `compon_exteriors.py` | prova que el compost de CapesExteriors == Aplicant_Filtres (≤3/65535) |
| `sanitat_sf10.py` | prova que base + filtres SF10 == Benchmark20Agost (màx 11/65535): valida el compositor |
| `analitza_mascares_ext.py`, `analitza_mask03.py` | perfils i estructura de les màscares; el vel de 04/03 sobre les zones sagrades |
| `acaba_mask0403.py` | l'acabat de màscares (ordre de Pere): màscara × (1−P), P = anell lunar + el·lipse de protuberància |
| `capa_vora*.py` | la capa VORA (v1 → v3: iterada fins a mediana per anell = benchmark des de 452 px) |
| `prototip_ct1.py` | el compost sencer (V5+VORA via CT1_V5 → PONT → exterior amb porta → filtres SF10 → ANELL) |
| `perfil_trim.py` | la capa PERFIL (perfil radial del compost → el del benchmark, 1,28–3,0 R☉) |
| `qa_ct1.py`, `test_acceptacio_limbe.py`, `tests_opus.py` | QA: anells, guardes, perfil lunar ±5 %, sectors azimutals, passa-alt per anell |
| `retalls_ct1.py`, `retalls_panel.py`, `or_vision.py` | retalls comparatius i consultes de visió per OpenRouter |
| `construeix_capestotals.py` | el PSB final (36 capes; variant per env CT1_*) |
| `verifica_ct1.py` | rellegeix el PSB i recompon finestres contra la fusionada |
