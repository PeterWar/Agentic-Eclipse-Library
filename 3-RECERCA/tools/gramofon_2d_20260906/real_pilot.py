"""Sony-only native-window pilot; fixed original Vixen judge, no product changes."""
from experiment import *
from PIL import Image, ImageDraw
from scipy.signal.windows import tukey
import gc
sys.path.insert(0,str(ROOT/'research/tools/v31_purs'))
from local_filters import mgn

OLD=ROOT/'research/tools/v29/cau_final'
FIX=ROOT/'research/tools/v29_c03_fix'
CX,CY,RS=5361.768111973117,3775.747534140857,440.60304883027544
POINTS=[('NE_3.5R',5890,2326),('S_3.5R',5089,5294),
        ('NE_4R',5965,2120),('S_4R',5056,5511),
        ('pentagon_NE',6198,3638),('pentagon_Sony',6376,4342)]

def analysis_fft(a):
    a=np.asarray(a,float)
    assert np.isfinite(a).all()
    ny,nx=a.shape;y,x=np.mgrid[-1:1:complex(ny),-1:1:complex(nx)]
    X=np.stack([np.ones_like(x),x,y,x*x,x*y,y*y],axis=-1).reshape(-1,6)
    beta=np.linalg.lstsq(X,a.ravel(),rcond=None)[0]
    a=a-(X@beta).reshape(a.shape)
    w=tukey(ny,.25)[:,None]*tukey(nx,.25)[None,:]
    return np.fft.rfft2(a*w)

def band_metrics(a,judge):
    A=analysis_fft(a);J=analysis_fft(judge)
    ny,nx=a.shape;ky=np.fft.fftfreq(ny)[:,None];kx=np.fft.rfftfreq(nx)[None,:]
    k=np.hypot(kx,ky);rows=[]
    for lo,hi in [(4,8),(8,16),(16,32),(32,64),(64,128),(128,256)]:
        sel=(k>=1/hi)&(k<1/lo)
        aa=np.fft.irfft2(np.where(sel,A,0),s=a.shape)
        jj=np.fft.irfft2(np.where(sel,J,0),s=a.shape)
        corr=float(np.corrcoef(aa.ravel(),jj.ravel())[0,1])
        rows.append({'wavelength_px':[lo,hi],'correlation':corr,'RMS':rms(aa),
                    'judge_RMS':rms(jj)})
    return rows

def main():
    sony=np.load(FIX/'sony_corrected_G.npy',mmap_mode='r')
    old=np.load(OLD/'sony_corrected_total.npy',mmap_mode='r')
    vixen=np.load(OLD/'vixen_total.npy',mmap_mode='r')
    ms=np.load(OLD/'sony_support.npy',mmap_mode='r')
    mv=np.load(OLD/'vixen_support.npy',mmap_mode='r')
    # Overview is the complete existing native canvas, only display reduced.
    a=np.asarray(sony[::6,::6],float);m=ms[::6,::6]
    disp=np.where(m,np.clip((np.log(np.maximum(a,1))-np.log(1000))/np.log(1000),0,1),0)
    im=Image.fromarray(np.uint8(disp*255)).convert('RGB');dr=ImageDraw.Draw(im)
    for name,x,y in POINTS:
        dr.rectangle(((x-256)/6,(y-256)/6,(x+256)/6,(y+256)/6),outline='cyan',width=2)
        dr.text((x/6+5,y/6),name,fill='yellow')
    im.save(RUN.vista('03_context_Sony_llenc_sencer.png'))
    rows=[];injections=[];ranges=[];cache=D/'native_pilots';cache.mkdir(exist_ok=True)
    limit=float(np.max(sony))
    for name,cx,cy in POINTS:
        log('real '+name)
        sl=np.s_[cy-512:cy+512,cx-512:cx+512];core=np.s_[256:768,256:768]
        s=np.array(sony[sl],float);o=np.array(old[sl][...,1],float);v=np.array(vixen[sl][...,1],float)
        mask=ms[sl]&(s>0)&(o>0);vm=mv[sl]&(v>0)
        if not mask[core].all() or not vm[core].all():
            rows.append({'ROI':name,'status':'not all core pixels valid; no global metric'})
            continue
        y,x=np.mgrid[cy-512:cy+512,cx-512:cx+512]
        qr=np.log(np.maximum(np.hypot(x-CX,y-CY)/RS,1e-10))
        l=np.log(np.maximum(s,1e-20));lo=np.log(np.maximum(o,1e-20));j=np.log(np.maximum(v,1e-20))[core]
        outputs={};models={}
        for kind in ['mean','quadratic','lograd']:
            mod=LocalModel(mask,160,kind,qr);models[kind]=mod
            outputs[kind]=mod.apply(l)[0]
            outputs[kind+'_old_source']=mod.apply(lo)[0]
        # Published comparison has its own units; never used for amplitude gating.
        mg=mgn(s.astype('float32'),mask,limits=[0,limit])
        metrics={key:band_metrics(a[core],j) for key,a in outputs.items()}
        metrics['MGN_published']=band_metrics(mg[core],j)
        metrics['input_log']=band_metrics(l[core],j)
        metrics['null_Vixen_local_rot180']=band_metrics(outputs['quadratic'][core],j[::-1,::-1])
        rows.append({'ROI':name,'center_xy':[cx,cy],'core_bbox':[cx-256,cy-256,cx+256,cy+256],
                     'input':'Sony only; original Vixen immutable judge','metrics':metrics})
        ranges.append({'ROI':name,'log_detail_Q2_rms':rms(outputs['quadratic'][core]),
                       'log_detail_LR_rms':rms(outputs['lograd'][core]),
                       'source_delta_log_rms':rms((l-lo)[core])})
        # Fixed-amplitude probes on actual Sony data; no fit against Vixen.
        eps=.0001
        for kind in ['quadratic','lograd']:
            for wave in [16,32,64,128]:
                phi=2*np.pi*(.6*x+.8*y)/wave+.371
                q=np.cos(phi);qs=np.sin(phi)
                delta=(models[kind].apply(l+eps*q)[0]-models[kind].apply(l-eps*q)[0])/(2*eps)
                good=np.zeros(mask.shape,bool);good[core]=True;good&=models[kind].valid
                z=coefficients(delta,q,qs,good)
                z.update(ROI=name,method=kind,wavelength_px=wave,epsilon_log=eps,
                         PASS_gain=.9<=z['gain']<=1.1)
                injections.append(z)
        # Display log details with identical fixed gain32, no per-image stretching.
        ims=[]
        for key in ['mean_old_source','mean','quadratic_old_source','quadratic','lograd_old_source','lograd']:
            a=outputs[key][core];u=np.uint8(np.clip(.5+32*a,0,1)*255)
            ims.append((key,Image.fromarray(u).convert('RGB')))
            np.save(cache/(name+'_'+key+'.npy'),np.asarray(a,np.float32))
        plate=Image.new('RGB',(512*3,542*2),(24,24,24));draw=ImageDraw.Draw(plate)
        for i,(key,im) in enumerate(ims):
            xx=(i%3)*512;yy=(i//3)*542
            plate.paste(im,(xx,yy+30));draw.text((xx+8,yy+8),name+' | '+key+' | 1px=1px',fill='white')
        plate.save(RUN.vista('04_'+name+'_100percent.png'))
        np.save(cache/(name+'_judge_log.npy'),np.asarray(j,np.float32))
        # Save intermediate receipts after every independent window.
        save('real_pilot',{'rows':rows,'injections':injections,'ranges':ranges,
              'analysis':'same quadratic detrend, Tukey0.25 and exact Fourier annuli on each512core',
              'display':'log detail: grey=.5+32D, fixed for all source/candidate/ROI; clipping display only',
              'external_scope':'morphological coherence; not radiance equality or proof all texture is coronal',
              'no_blended_input':True,'calibration':'no Sony/Vixen scalar needed: log residual invariant to constant scaling',
              'full_canvas_shape':list(sony.shape),'product_modified':False})
        del models,outputs;gc.collect()
    log('real pilot COMPLETE')

if __name__=='__main__':main()
