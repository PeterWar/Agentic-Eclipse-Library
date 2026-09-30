"""Build full-canvas V29 previews and rasters before packaging a PSB."""
from common import *
from inspect_inputs import channel
from psd_tools import PSDImage
from PIL import Image

def canvas_layer(l):
    rgb=np.stack([channel(l,c) for c in range(3)],axis=2).astype(np.float32)/65535
    alpha=channel(l,-1);alpha=np.ones(l.size[::-1],np.float32) if alpha is None else alpha.astype(np.float32)/65535
    out=np.zeros((FH,FW,3),np.float32);a=np.zeros((FH,FW),np.float32)
    x0,y0,x1,y1=l.bbox;X0,Y0,X1,Y1=max(x0,0),max(y0,0),min(x1,FW),min(y1,FH)
    out[Y0:Y1,X0:X1]=rgb[Y0-y0:Y1-y0,X0-x0:X1-x0];a[Y0:Y1,X0:X1]=alpha[Y0-y0:Y1-y0,X0-x0:X1-x0]
    mask=channel(l,-2)
    if mask is not None and not l._record.mask_data.flags.mask_disabled:
        md=l._record.mask_data;mk=np.full((FH,FW),md.background_color/255,np.float32)
        mx0,my0,mx1,my1=md.left,md.top,md.right,md.bottom;X0,Y0,X1,Y1=max(mx0,0),max(my0,0),min(mx1,FW),min(my1,FH)
        mk[Y0:Y1,X0:X1]=mask[Y0-my0:Y1-my0,X0-mx0:X1-mx0]/65535;a*=mk
    return out,a

def over(b,f,a=1.,op=1.,mode='normal'):
    weight=a*op
    if isinstance(weight,np.ndarray):weight=weight[...,None]
    if mode=='overlay':f=np.where(b<=.5,2*b*f,1-2*(1-b)*(1-f))
    elif mode=='add':return np.clip(b+f*weight,0,1)
    return b*(1-weight)+f*weight

def png(a,name):
    im=Image.fromarray(np.round(np.clip(a[::4,::4],0,1)*255).astype(np.uint8));im.save(OUT/name)

def new_tone(k):
    m=np.load(CAU/'fusion_support.npy');u=np.load(CAU/'fusion_total.npy',mmap_mode='r');c=np.load(CAU/'fusion_corona.npy',mmap_mode='r')
    data=np.maximum(k*u+(1-k)*c,0);L=(data[...,0]+2*data[...,1]+data[...,2])/4
    va=float(json.loads((OLD/'rebut_etapa1.json').read_text())['base']['ancora_va'])
    tone=comu.corba_to(L,m,va,pend=.22,anc=.74,terra=.045)
    den=gauss(m.astype(np.float32),24); ls=gauss(L*m,24)/np.maximum(den,1e-8)
    q=np.stack([gauss(data[...,i]*m,24)/np.maximum(den,1e-8)/np.maximum(ls,1e-8) for i in range(3)],axis=2)
    ylin=comu.a_lineal(tone);qmax=q.max(axis=2)
    with np.errstate(divide='ignore',invalid='ignore'):wmax=np.where(qmax>1,(1/np.maximum(ylin,1e-8)-1)/(qmax-1),1)
    wg=np.clip(np.nan_to_num(wmax,nan=0,posinf=1),0,1)
    return comu.a_srgb(ylin[...,None]*(1+wg[...,None]*(q-1)))*m[...,None]

def main():
    assert 'resolution' in json.loads((CAU/'filter_receipt.json').read_text()), 'filter generation incomplete'
    psd=PSDImage.open(HERE/'cau/input_V28.psb');ls=list(psd)
    m=np.load(CAU/'fusion_support.npy');al=np.clip(warp(m.astype(np.float32),True),0,1)
    # Common interpolator and common support for base and all detail layers.
    den=warp(m.astype(np.float32),True);valid=al>1e-6
    y,x=np.ogrid[:FH,:FW];r=np.hypot(y-CY,x-CX)/RS
    base_mask=np.where(r<1.12,al,1).astype(np.float32)
    np.save(CAU/'base_mask_final.npy',base_mask);np.save(CAU/'detail_mask_final.npy',al)
    rep={'final_size':[FW,FH],'sun_xy':[CX,CY],'base_changes':'only temporal limb and marked ghost; V28 exterior base retained','opacities':{'achf':.70,'passalt24':.40,'gran':.35},'omitted':'04 ACHF ample 9R; redundant broad azimuthal blur'}
    # All regenerated detail starts neutral outside observed support; never
    # interpolate the neutral level against black at a footprint boundary.
    for name in ('achf','passalt24','gran'):
        if '--base-only' in sys.argv:continue
        log('warp '+name);d=np.load(CAU/f'{name}_u16.npy').astype(np.float32)/65535-.5
        f=warp(d*m,True)/np.maximum(den,1e-6);f=np.where(valid,f,0)
        f=np.clip(f+.5,0,1).astype(np.float32);np.save(CAU/f'{name}_final.npy',f);png(f,f'V29_{name}_llenc_sencer.png')
    # Only areas whose science/input changed are rebuilt in the base.
    gxy=M@np.array([*GHOST_XY,1]);ghost=1-smooth(np.hypot(x-gxy[0],y-gxy[1]),210,280)
    inner=1-smooth(r,1.08,1.16);changed=np.maximum(inner,ghost).astype(np.float32)
    for k,idx,name in [(.25,19,'base_cel4'),(1.,18,'base_amb_cel')]:
        if '--reuse-base' in sys.argv and (CAU/f'{name}_final.npy').exists():continue
        log('tone '+name);old,_=canvas_layer(ls[idx]);fresh=new_tone(k)
        fresh=np.stack([warp(fresh[...,i],True)/np.maximum(den,1e-6) for i in range(3)],axis=2)
        base=old*(1-changed[...,None])+fresh*changed[...,None]
        np.save(CAU/f'{name}_final.npy',base.astype(np.float32));del old,fresh,base
    # Compose the actual delivery state, with alpha and mask metadata honored.
    comp=np.zeros((FH,FW,3),np.float32)
    for i in (0,1,17):
        a,mask=canvas_layer(ls[i]);comp=over(comp,a,mask,ls[i].opacity/255);del a,mask
    base=np.load(CAU/'base_cel4_final.npy',mmap_mode='r');comp=over(comp,base,base_mask)
    np.save(CAU/'composite_base.npy',comp);png(comp,'V29_BASE_llenc_sencer.png')
    if '--base-only' in sys.argv:
        fg=np.zeros_like(comp)
        for i in (24,25):
            a,mask=canvas_layer(ls[i]);fg+=a*mask[...,None]*ls[i].opacity/255;del a,mask
        np.save(CAU/'foreground_add.npy',fg);savejson(CAU/'canvas_receipt.json',rep);log('base and foreground ready');return
    for name,op in [('gran',.35),('achf',.70),('passalt24',.40)]:
        f=np.load(CAU/f'{name}_final.npy',mmap_mode='r');comp=over(comp,f[...,None],al,op,'overlay')
    for i in (24,25):
        a,mask=canvas_layer(ls[i]);mode='add' if 'LINEAR_DODGE' in str(ls[i].blend_mode) else 'normal';comp=over(comp,a,mask,ls[i].opacity/255,mode);del a,mask
    np.save(CAU/'composite_final.npy',comp);png(comp,'V29_PROPOSTA_llenc_sencer.png')
    savejson(CAU/'canvas_receipt.json',rep);log('full canvas ready')

if __name__=='__main__':main()
