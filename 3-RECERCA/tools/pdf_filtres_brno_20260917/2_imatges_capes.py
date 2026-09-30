"""Pas 2. Portada (V80 de Pere), tires de cada capa (llenç sencer + zona central) i la parella abans/després. Píxels tal com són: cap estirament."""
import numpy as np, cv2, os
from comu import *
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"]=str(2**40)
a=cv2.imread(str(TIF_V80),cv2.IMREAD_UNCHANGED)[...,:3][...,::-1].astype(np.float32)/65535
jpg('portada_v80',redueix(a,3),q=90)
NOMS={3:'base',41:'nrgf',43:'rhef',44:'rhef_ups',45:'rhef_local60',47:'achf_azimutal',51:'achf_micro',53:'achf_estructura',54:'mgn',55:'wow',56:'wow_bilateral'}
for lid,nom in NOMS.items():
    jpg(f'{nom}_llenc',np.load(TREBALL/'capes'/f'L{lid}_full5.npy')/65535.0,w=1500)
    jpg(f'{nom}_centre',np.load(TREBALL/'capes'/f'L{lid}_centre2.npy')/65535.0,w=1100)
jpg('compost_llenc',np.load(TREBALL/'capes'/'compost_full5.npy')/65535.0,q=90,w=1500)
jpg('compost_centre',np.load(TREBALL/'capes'/'compost_centre2.npy')/65535.0,q=90,w=1100)
print('fet')
