"""x6 (verificador adversari, 27-09) · La «línia» horitzontal a l'altura del centre de la Lluna que es veu al mapa ln(N/V107) ±5 %:
¿és un graó/plec (costura) o només el pas per zero d'un gradient suau? Perfil vertical de ln(V108/V107) i de ln V108 (mitjana de columnes,
fora de 3 R☉), amb la primera i la segona derivada. Sortida: text (x6.log)."""
from pathlib import Path
import numpy as np
R0 = Path('/Users/USUARI/Desktop/Eclipse 2026'); CO = R0 / '4-RESULTATS/v108_20260926/verifica_v108_final/composts'
L7 = np.load(CO / 'L_V107.npy', mmap_mode='r'); L8 = np.load(CO / 'L_V108.npy', mmap_mode='r'); CY = 3776
for nom, (xa, xb) in {'esquerra x 1400-2400': (1400, 2400), 'dreta x 8300-9300': (8300, 9300)}.items():
    a7 = np.asarray(L7[CY - 700:CY + 700, xa:xb], np.float64); a8 = np.asarray(L8[CY - 700:CY + 700, xa:xb], np.float64)
    ok = (a7 > 1e-3) & (a8 > 1e-3); d = np.where(ok, np.log(np.maximum(a8, 1e-4)) - np.log(np.maximum(a7, 1e-4)), np.nan); l8 = np.where(ok, np.log(np.maximum(a8, 1e-4)), np.nan)
    pd = np.nanmedian(d, 1); p8 = np.nanmedian(l8, 1)
    k = np.ones(9) / 9; sd = np.convolve(pd, k, 'same'); s8 = np.convolve(p8, k, 'same')
    g = np.gradient(sd); g8 = np.gradient(s8); c = np.gradient(g)
    print(nom)
    for y in range(-600, 601, 50): i = y + 700; print(f'   y−CY={y:+5d}: ln V108/V107 {100*sd[i]:+6.2f} %   pendent {1e4*g[i]:+6.2f} ‱/px   ln V108 pendent {1e4*g8[i]:+6.2f} ‱/px')
    core = slice(50, -50); print(f'   |2a derivada| màxima {1e4*np.nanmax(np.abs(c[core])):.3f} ‱/px² a y−CY={int(np.nanargmax(np.abs(c[core])))+50-700}; p99 {1e4*np.nanpercentile(np.abs(c[core]),99):.3f}')
    j = np.abs(np.diff(pd[core])); print(f'   salt màxim entre files (sense suavitzar) {100*np.nanmax(j):.3f} % a y−CY={int(np.nanargmax(j))+50-700}; p99 {100*np.nanpercentile(j,99):.3f} %')
