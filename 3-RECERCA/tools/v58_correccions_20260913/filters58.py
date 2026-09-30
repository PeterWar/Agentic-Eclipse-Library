from common58 import *
import ast,sys,time,gc,cv2,ctypes
import numexpr as ne
from scipy.ndimage import gaussian_filter1d
H,W=7506,10551;CAUF=R/'research/tools/v29/cau_final';cv2.setNumThreads(4)
def log(s):print(time.strftime('%H:%M:%S'),s,flush=True)
def coords():
 y,x=np.ogrid[:H,:W];return np.hypot(y-CY,x-CX).astype('float32'),np.arctan2(y-CY,x-CX).astype('float32')
def gauss(a,s):return cv2.GaussianBlur(np.asarray(a,np.float32),(0,0),s,borderType=cv2.BORDER_REFLECT_101)
def normgauss(a,w,s):return gauss(np.where(w>0,a,0)*w,s)/np.maximum(gauss(w,s),1e-8)
def gaussian(a,s,truncate=3):return cv2.GaussianBlur(np.asarray(a,np.float32),(2*int(truncate*s+.5)+1,)*2,s,borderType=cv2.BORDER_REPLICATE)
def ng(a,m,s,truncate=3):return gaussian(np.where(m,a,0),s,truncate)/np.maximum(gaussian(m.astype('float32'),s,truncate),1e-20)
def smooth(a,lo,hi):
 q=np.clip((a-lo)/(hi-lo),0,1);return q*q*(3-2*q)
def defs(path,names=None):
 tree=ast.parse(Path(path).read_text());fs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!='main' and (names is None or n.name in names)];exec(compile(ast.Module(body=fs,type_ignores=[]),str(path),'exec'),globals())
defs(R/'research/tools/v29/fuse_and_filter.py',['sn_smooth','centre_rings','achf'])
defs(R/'research/tools/v37_20260908/comu37.py',['farcit_perfil_ln_A'])
defs(V42/'b4b_capes_azimutals_v42.py',['angular_polar','back'])
defs(V42/'b4c_purs_v42.py',['farcit_perfil','farcit_perfil_A'])
defs(V42/'b4d_radial_vora_v42.py',['ring_stats','complete_from_partial','radial_v36'])
defs(V42/'b4f_rhef_variants_v42.py',['upsilon','rhef_local'])
defs(R/'research/tools/v29/audit_geometry.py',['polar','features','correlate'])
defs(R/'research/tools/v29/qa_rasters.py',['h1_setup','h1'])
defs(R/'research/tools/v31_purs/local_filters.py',['mgn'])
K=np.array([1,4,6,4,1],np.float32)/16;lib=ctypes.CDLL(str(R/'research/tools/v31_purs/sparse_conv.dylib'));lib.sparse_b3.argtypes=[ctypes.c_void_p]*3+[ctypes.c_int]*4;lib.sparse_b3.restype=None
defs(R/'research/tools/v31_purs/wow_filters.py',['conv','nconv','bilateral_conv','wow'])
L_PX=60.;PUJADA_MAX=5.;BLEND=64.;NB=720;DR=1.
