"""Rutes del PDF «Els filtres de la corona». Tot és relatiu a l'arrel del projecte (la carpeta que conté CLAUDE.md): cap ruta absoluta."""
import os, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image

def _arrel():
    for a in Path(__file__).resolve().parents:
        if (a/'CLAUDE.md').exists() and (a/'1-PHOTOSHOP').is_dir(): return a
    raise SystemExit("No trobo l'arrel del projecte (la carpeta amb CLAUDE.md i 1-PHOTOSHOP).")
ARREL=_arrel()
PSB_V77=ARREL/'1-PHOTOSHOP'/'V77.psb'            # només lectura
TIF_V80=ARREL/'1-PHOTOSHOP'/'V80.tif'            # només lectura
RES=ARREL/'4-RESULTATS'/'pdf_filtres_brno_20260917'
IMG=RES/'font'/'img'; REBUTS=RES/'rebuts'
for d in (IMG,REBUTS): d.mkdir(parents=True,exist_ok=True)
# intermedis (uns 0,9 GB de .npy): fora del projecte; es poden esborrar en acabar
TREBALL=Path(os.environ.get('PDF_FILTRES_TREBALL',Path(tempfile.gettempdir())/'pdf_filtres_brno_treball')); (TREBALL/'capes').mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ARREL/'3-RECERCA'/'tools'/'v73_marques_v71_20260917'))   # psb69.py, el lector lleuger de PSB
CX,CY=5375.88,3775.41          # centre de la Lluna al llenç de la V77 (px)
RLLUNA=455.5                   # radi lunar (px) = 1 radi solar a l'escala d'aquest document

def jpg(nom,arr,q=88,w=None):
    """Desa un array 0..1 com a JPEG a la carpeta d'imatges del document."""
    im=Image.fromarray((np.clip(arr,0,1)*255+0.5).astype(np.uint8))
    if w and im.width!=w: im=im.resize((w,int(round(im.height*w/im.width))),Image.LANCZOS)
    im.save(IMG/f'{nom}.jpg',quality=q,optimize=True,progressive=True)
def png(nom,arr):
    Image.fromarray((np.clip(arr,0,1)*255+0.5).astype(np.uint8)).save(IMG/f'{nom}.png')
def redueix(a,f):
    h,w=a.shape[:2]; a=a[:h//f*f,:w//f*f]
    return a.reshape(h//f,f,w//f,f,-1).mean((1,3)) if a.ndim==3 else a.reshape(h//f,f,w//f,f).mean((1,3))
