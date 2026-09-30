"""Desa la vista de banda (18–240 px, blocs 6×6) d'un render natiu com a .npy, per retallar-la després. Ús: v0c_banda_npy.py TIFF SORTIDA.npy"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from v0b_vista_realcada import realca
hp, val = realca(sys.argv[1])
np.save(sys.argv[2], np.where(val, hp, np.nan).astype(np.float32))
