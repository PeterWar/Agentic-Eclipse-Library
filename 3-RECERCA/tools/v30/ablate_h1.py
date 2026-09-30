"""Isolate H1 radial printing; compare coarser C2 profiles on identical detail."""
import os,sys,json
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
D=Path(__file__).parent;ROOT=D.parents[2]
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
from qa_rasters import h1,h1_setup
from scipy.interpolate import LSQUnivariateSpline
from PIL import Image,ImageDraw
FIX=ROOT/'research/tools/v29_c03_fix';OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v30_20260905')

def png(a,name):
    im=Image.fromarray(np.uint8(np.clip(a,0,1)*255));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(OUT/name)
def curve_fit(a,m,r,spacing):
    rr=r[m];lo=np.log(20.);hi=np.log(float(rr.max()));idx=np.clip(((np.log(np.maximum(rr,1))-lo)/(hi-lo)*200).astype(int),0,199)
    o=np.argsort(idx,kind='stable');n=np.bincount(idx,minlength=200);off=np.r_[0,np.cumsum(n)];sx=np.log(np.maximum(rr,1))[o];v=a[m][o];ks=np.flatnonzero(n>=400)
    nodes=np.array([np.median(sx[off[k]:off[k+1]]) for k in ks]);p=np.array([np.median(v[off[k]:off[k+1]]) for k in ks])
    # Fit global level with C2 cubic spline, substantially broader than the
    # diagnostic bins. Data and all support remain unchanged.
    knots=np.arange(nodes[0]+spacing,nodes[-1]-spacing*.5,spacing)
    f=LSQUnivariateSpline(nodes,p,knots,k=3,ext=3)
    bg=f(np.clip(np.log(np.maximum(r,1)),nodes[0],nodes[-1])).astype('float32')
    out=np.where(m,.5+a-bg,.5).astype('float32')
    return out,{'spacing_ln_r':spacing,'nodes_ln_px':nodes.tolist(),'observed_medians':p.tolist(),'knots_ln_px':knots.tolist(),'fit_at_nodes':f(nodes).tolist(),'max_node_residual':float(np.max(np.abs(p-f(nodes))))}

def main():
    r,t=coords();manifest=json.loads((D/'cau/input_manifest.json').read_text());rep={}
    old=np.load(FIX/'gran_u16.npy',mmap_mode='r').astype('float32')/65535;m=np.load(CAU/'gran_support.npy');sm=np.load(FIX/'gran_smoothed.npy',mmap_mode='r');ctx=h1_setup(r,m)
    no=np.where(m,.5+sm,.5);png(no,'ABLACIO_03_sense_H1_llenc_sencer.png')
    rep['no_H1']=h1(no,m,ctx)
    candidates={'original':old,'senseH1':no}
    for sp in (.10,.15,.20):
        a,q=curve_fit(sm,m,r,sp);q['H1']=h1(a,m,ctx);np.save(D/f'cau/gran_spline_{sp:.2f}.npy',a);png(a,f'PILOT_03_spline_{sp:.2f}_llenc_sencer.png');candidates[f'spline{sp:.2f}']=a;rep[f'spline{sp:.2f}']=q
        log(f'spline{sp:.2f} H1 '+str(q['H1']['worst']))
    comps=manifest['marks'][0]['components']
    # Largest/first components in four quadrants: native512px patches.
    selected=[]
    for xa,ya in [(1,-1),(-1,-1),(1,1),(-1,1)]:
        possible=[q for q in comps if (q['xy'][0]-CX)*xa>0 and (q['xy'][1]-CY)*ya>0]
        if possible:selected.append(max(possible,key=lambda q:q['pixels']))
    for j,q in enumerate(selected):
        x,y=np.round(q['xy']).astype(int);sl=(slice(y-256,y+256),slice(x-256,x+256));im=Image.new('RGB',(512*4,542));dr=ImageDraw.Draw(im)
        for i,key in enumerate(['original','senseH1','spline0.15','spline0.20']):
            z=np.uint8(np.clip(candidates[key][sl],0,1)*255);im.paste(Image.fromarray(z),(i*512,30));dr.text((i*512+8,8),key,fill='white')
        im.save(OUT/f'ABLACIO_03_100pct_{j}.png')
    # Confirm which delivered03 the supplied marks came from, away from blue.
    marked=np.load(D/'cau/marked_0_G16.npy',mmap_mode='r');blue=np.load(D/'cau/marked_0_blue.npy',mmap_mode='r');z=m[::8,::8]&~blue[::8,::8]
    rep['marks_vs_current03']={'max_DN':float(np.max(np.abs(marked[::8,::8][z].astype('float32')-np.round(old[::8,::8][z]*65535)))),'median_DN':float(np.median(np.abs(marked[::8,::8][z].astype('float32')-np.round(old[::8,::8][z]*65535))))}
    savejson(D/'cau/h1_ablation.json',rep)
if __name__=='__main__':main()
