"""Balance angular detail with measured radial regularization before display.

Scientific support is preserved; the radial convolution is normalized only by
the original physical/positive source support. No rings or marked areas masked.
"""
import os,sys,json
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
D=Path(__file__).parent;ROOT=D.parents[2]
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
from fuse_and_filter import sn_smooth,centre_rings
from qa_rasters import h1,h1_setup
from PIL import Image,ImageDraw
FIX=ROOT/'research/tools/v29_c03_fix';OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v30_20260905')
SIGMAS=(2.,4.,8.)

def angular_pilots(x,m,r,t,tag):
    x=np.where(m,x,0).astype('float32');mf=m.astype('float32');r0=400;nr=int(np.ceil(r.max()))-r0+2;nt=16384
    theta=np.arange(nt,dtype='float32')*2*np.pi/nt;freq=np.fft.rfftfreq(nt)[None,:];p=np.empty((nr,nt),'float32');valid=np.empty_like(p)
    for start in range(0,nr,64):
        rr=(r0+np.arange(start,min(start+64,nr),dtype='float32'))[:,None];mx=(CX+rr*np.cos(theta)).astype('float32');my=(CY+rr*np.sin(theta)).astype('float32')
        wm=cv2.remap(mf,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);xp=cv2.remap(x,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        fx=np.fft.rfft(xp,axis=1);fw=np.fft.rfft(wm,axis=1);bands=[]
        for sigma in (8,32,64,128):
            sp=sigma*nt/(2*np.pi*rr);g=np.exp(-2*np.pi**2*sp**2*freq**2);den=np.fft.irfft(fw*g,n=nt,axis=1);num=np.fft.irfft(fx*g,n=nt,axis=1)
            bands.append(np.where(den>1e-5,num/np.maximum(den,1e-5),0).astype('float32'))
        p[start:start+len(rr)]=bands[0]-(bands[1]+bands[2]+bands[3])/3;valid[start:start+len(rr)]=wm
    mx=(np.mod(t,2*np.pi)*nt/(2*np.pi)+1).astype('float32');my=(r-r0).astype('float32')
    def back(a):
        ext=np.concatenate([a[:,-1:],a,a[:,:1]],axis=1)
        return np.where(m,cv2.remap(ext,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT),0)
    # Zero regularization must reproduce the exact V29 operator, not merely
    # look similar. This guards the only geometric evaluation involved here.
    if not tag.startswith('inj_'):
        zero=back(p);old=np.load(FIX/f'angular_{tag}_raw.npy',mmap_mode='r');assert np.array_equal(zero,old),float(np.max(np.abs(zero-old)));del zero,old
    for s in SIGMAS:
        q=p if s==0 else gaussian_filter1d(p*valid,s,axis=0,mode='constant',cval=0)/np.maximum(gaussian_filter1d(valid,s,axis=0,mode='constant',cval=0),1e-8)
        a=back(q);np.save(D/f'cau/angular_{tag}_r{s:g}.npy',a);log(f'angular {tag} radial sigma{s:g}');del q,a

def png(a,name):
    im=Image.fromarray(np.uint8(np.clip(a,0,1)*255));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(OUT/name)

def main():
    r,t=coords();oldrep=json.loads((CAU/'gran_azimuthal_receipt.json').read_text());profiles=oldrep['post_contrast_profiles'];masks={}
    for tag in ('vixen','sony'):
        old=np.load(CAU/f'{tag}_total.npy' if tag=='vixen' else CAU/'sony_corrected_total.npy',mmap_mode='r')[...,1];masks[tag]=np.load(CAU/f'{tag}_support.npy')&np.isfinite(old)&(old>0)
    m=masks['vixen']|masks['sony'];assert np.array_equal(m,np.load(CAU/'gran_support.npy'));wv=(1-smooth(r/RS,2,2.65))*masks['vixen'];wv=np.where(masks['sony'],wv,masks['vixen'].astype('float32'));ws=(1-wv)*masks['sony']
    if '--presentation-only' not in sys.argv:
        for tag in ('vixen','sony'):
            a=np.load(FIX/f'{tag}_corrected_G.npy',mmap_mode='r');angular_pilots(np.log(np.maximum(a,1e-8)),masks[tag],r,t,tag)
    scale=np.zeros_like(r)
    for tag,w in [('vixen',wv),('sony',ws)]:
        p=profiles[tag];scale+=w*np.interp(np.log(np.maximum(r/RS,1e-5)),p['lnr_centres'],p['robust_contrast']).astype('float32')
    rep={'operator':'same angular8/32/64/128 plus radial normalized Gaussian before nonlinear mapping; sigma0 exact original','tanh_scale':oldrep['scale_tanh'],'pilots':{}};ctx=h1_setup(r,m)
    originals=np.load(FIX/'gran_u16.npy',mmap_mode='r');marks=json.loads((D/'cau/input_manifest.json').read_text())['marks'][0]['components'];selected=[]
    def cardinal(q):
        dx=q['xy'][0]-CX;dy=q['xy'][1]-CY
        return ('E' if dx>0 else 'W') if abs(dx)>abs(dy) else ('S' if dy>0 else 'N')
    for tag in ['N','W','E','S']:
        qq=[q for q in marks if cardinal(q)==tag]
        if qq:selected.append(max(qq,key=lambda q:q['pixels']))
    for s in SIGMAS:
        d=wv*np.load(D/f'cau/angular_vixen_r{s:g}.npy',mmap_mode='r')+ws*np.load(D/f'cau/angular_sony_r{s:g}.npy',mmap_mode='r');d=np.where(m,d/np.maximum(scale,.002),0).astype('float32')
        mapped=.5*np.tanh(d/oldrep['scale_tanh']);sm,_=sn_smooth(mapped,m);centered,hist=centre_rings(sm,m,r);a=np.clip(.5+centered,0,1);a[~m]=.5
        np.save(D/f'cau/gran_r{s:g}_raw.npy',d);np.save(D/f'cau/gran_r{s:g}_smoothed.npy',sm);np.save(D/f'cau/gran_r{s:g}_u16.npy',np.round(a*65535).astype('uint16'));png(a,f'PILOT_03_radial{s:g}_llenc_sencer.png')
        rep['pilots'][str(s)]={'radial_sigma_px':s,'H1':h1(a,m,ctx),'H1_history':hist}
        log(f'presentation radial{s:g} ready')
    for j,q in enumerate(selected):
        x,y=np.round(q['xy']).astype(int);sl=(slice(y-256,y+256),slice(x-256,x+256));im=Image.new('RGB',(2048,542));dr=ImageDraw.Draw(im)
        for i,s in enumerate([0,*SIGMAS]):
            a=originals[sl] if not s else np.load(D/f'cau/gran_r{s:g}_u16.npy',mmap_mode='r')[sl];im.paste(Image.fromarray(np.uint8(a/257)),(i*512,30));dr.text((i*512+8,8),f'03 radial sigma{s:g} px',fill='white')
        im.save(OUT/f'PILOT_03_radial_100pct_{j}.png')
    savejson(D/'cau/angular_pilot_receipt.json',rep)
if __name__=='__main__':main()
