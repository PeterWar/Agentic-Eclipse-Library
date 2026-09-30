# revelat_normalitzat — re-revelat ACR amb escala d'exposició comuna (CapesTotals V4)

Eina del pas §6.1 de `PROPOSTA_Normalitzacio_Exposicio_CapesTotalsV4.md` (Opció A,
signada per Pere el 21-08-2026). Cada fotograma font d'HDR4 es revela amb
compensació −log₂(t/t_ref), t_ref = 1/15 s (capa 07), corba lineal, WB «As Shot»
(idèntic als 12 fitxers: neutral 0,514573 1 0,602707, Dia 5200 K), NR/sharpening
zero, sortida 16 bits Display P3. Cada revelat porta `RENDER_RECEIPT` (hash de la
font, EV aplicat, XMP, eina, data).

- **No toca cap original**: es treballa sobre còpies a `work/`.
- La capa 01 usa **10,08 s fotomètric** (decisió §8.3, research/76), no l'EXIF.
- `revelat.py probe` → test de linealitat §5.1 (DNG 07 a +0,00 i +1,00 EV).
- `revelat.py render-all` → els 12 revelats + rebuts.
- `test_linealitat.py` → veredicte del test §5.1 sobre els dos TIFF del probe.

Sortides: `~/Desktop/Eclipse 2026/Derivats/Vixen/HDR4/revelat_v4/`
(`work/` còpies+XMP, `out/` TIFF, `receipts/` JSON).
