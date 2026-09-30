"""f2 (V97) · La linealitzada de la V97: les fonts sense estrelles de la d4 amb la franja d'un sol instant (A3A) posada a la caixa lunar,
exactament com la fan servir els filtres. Així la base (capa 3) i els filtres parteixen de LA MATEIXA dada (a la V96 la base venia de la
fusió V42 amb les correccions del limbe de la V53–V56, i els filtres de la d4 amb l'A3A).
Escriu a <sortida>: fusion_starless.npy (RGB, amb F de l'A3A), base_G.npy (G de l'A3A), vixen_starless.npy (G de la Vixen amb V de l'A3A),
sony_starless.npy i support.npy (clons de la d4), star_footprints.npy, i LINEAL_REBUT.json.
Ús: f2_lineal_v97.py <d4 sources> <A3A.npz> <sortida>"""
import sys, json, subprocess, hashlib
from pathlib import Path
import numpy as np
D4, A3A, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
Q = np.load(A3A); y0, y1, x0, x1 = Q['box']; B = (slice(y0, y1), slice(x0, x1))
for nom in ('sony_starless.npy', 'support.npy', 'star_footprints.npy'):
    if not (OUT / nom).exists(): subprocess.run(['cp', '-c', str(D4 / nom), str(OUT / nom)], check=True)
F = np.array(np.load(D4 / 'fusion_starless.npy', mmap_mode='r')); F[B] = Q['F']; np.save(OUT / 'fusion_starless.npy', F)
G = np.array(np.load(D4 / 'base_G.npy', mmap_mode='r')); G[B] = Q['G']; np.save(OUT / 'base_G.npy', G)
V = np.array(np.load(D4 / 'vixen_starless.npy', mmap_mode='r')); V[B + (1,)] = Q['V']; np.save(OUT / 'vixen_starless.npy', V)
rep = dict(d4=str(D4), a3a=str(A3A), caixa=[int(y0), int(y1), int(x0), int(x1)], nota='franja A3A dins de la caixa lunar (G, F, V); la resta, la d4 tal qual',
           sha256={p.name: sha(p) for p in sorted(OUT.glob('*.npy'))})
(OUT / 'LINEAL_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); print('FET', OUT)
