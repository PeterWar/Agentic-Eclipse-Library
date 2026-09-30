"""19-source RGB pilot, calibrated individual CFA samples and detector crops.
Single ordinary bilinear interpolation, identical frozen source geometry.
G must reproduce earlier ordinary source. No legacy campaign imports.
"""
from common import *
import sys,math,ast,types,time
import cv2,rawpy
from scipy.ndimage import maximum_filter
sys.path.insert(0,str(ROOT/'research/tools/eclipse_determinista'))
import comu,f2
cv2.setNumThreads(2)
claim()
class ReadOnlyRun(comu.Run):
    def fase(self,n,*parts):
        p=Path(self.dir)/comu.FASES[n]
        for part in parts:p=p/part
        assert p.exists(),p
        return str(p)
    def desa_rebut(self,*args):raise RuntimeError('Frozen run')

# Extract the already-audited pure function only; never execute top-level
# legacy imports, mkdirs, monkeypatches or old claim statements.
path=ROOT/'research/tools/v32_arcs_20260907/comu32.py'
tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='flat_ripple_correction')
ns={'np':np,'FLAT_CENTRE_YX':{'sony':(2660.,4000.)},'FLAT_SIGMA_PX':32.}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'),ns)
flat_ripple=ns['flat_ripple_correction']
lut=json.loads((ROOT/'output/revisio_marques_v33_20260907/4-rebuts/R33_linealitat_sensor.json').read_text())['sony']
lx=np.array(lut['x_centres']);ly=np.array([0 if v is None else v/100 for v in lut['mediana_pct']]);ly[lx<=.425]=0
def sony_lut(raw,ped,sat):
    x=(raw-ped)/(sat-ped);a=np.interp(x,lx,ly,left=0,right=ly[-1]);over=x>lx[-1]
    if over.any():a=np.where(over,ly[-1]+(ly[-1]-ly[-2])/(lx[-1]-lx[-2])*(x-lx[-1]),a)
    return np.exp(-a).astype(np.float32)
def upsample(p):
    h,w=p.shape;a=cv2.resize(np.asarray(p,np.float32),(w*4,h*4),interpolation=cv2.INTER_LINEAR)
    out=np.empty((7506,10551),np.float32);out[:h*4,:w*4]=a;out[h*4:,:w*4]=a[-1:,:];out[:,w*4:]=out[:,w*4-1:w*4]
    return out
def footprint(mx,my,bad):
    ix=np.floor(mx).astype(int);iy=np.floor(my).astype(int)
    inside=(ix>=0)&(iy>=0)&(ix+1<bad.shape[1])&(iy+1<bad.shape[0]);sx=np.clip(ix,0,bad.shape[1]-2);sy=np.clip(iy,0,bad.shape[0]-2)
    invalid=bad[:-1,:-1]|bad[1:,:-1]|bad[:-1,1:]|bad[1:,1:];strict=inside&~invalid[sy,sx]
    near=maximum_filter(invalid,size=5,mode='constant',cval=1)[sy,sx]&strict;dist=np.ones_like(mx,dtype=float)
    dd=np.ones(int(near.sum()));qx=mx[near];qy=my[near];ix0=ix[near];iy0=iy[near]
    for di in range(-2,3):
        for dj in range(-2,3):
            xi=ix0+dj;yi=iy0+di;ok=(xi>=0)&(yi>=0)&(xi<invalid.shape[1])&(yi<invalid.shape[0])
            bc=~ok|invalid[np.clip(yi,0,invalid.shape[0]-1),np.clip(xi,0,invalid.shape[1]-1)]
            dx=np.maximum(np.maximum(xi-qx,qx-xi-1),0);dy=np.maximum(np.maximum(yi-qy,qy-yi-1),0)
            dd=np.minimum(dd,np.where(bc,np.hypot(dx,dy),1.))
    dist[near]=dd;dist[~strict]=0
    return strict,dist*dist*(3-2*dist)

M=np.array(json.loads((ROOT/'research/tools/v25_lineal/cau_v25/geometria_v27.json').read_text())['M_llenc_a_v23'])
inv=cv2.invertAffineTransform(M);MC=(X0+CX,Y0+CY);yy,xx=np.mgrid[Y0:Y0+N,X0:X0+N].astype(np.float32)
fr=json.loads((OUT/'A0_freeze.json').read_text())['pilot_frames'];fr.sort(key=lambda m:(m['tren']!='vixen',-m['exp'],m['stem']))
if '--all' in sys.argv:fr=sorted(frames(),key=lambda m:(m['tren']!='vixen',-m['exp'],m['stem']))
rows=[];last=None;deps={};tic=time.time()
for count,m in enumerate(fr):
    tag=m['tren'];stem=m['stem'];nom=m['nom'];target=OUT/'native'/f'{tag}_{stem}.npz';rpout=target.with_suffix('.json')
    if target.exists():
        row=json.loads(rpout.read_text());assert row['sha256']==sha(target);rows.append(row);continue
    if tag!=last:
        ctx=f2.Ctx(ReadOnlyRun.obre(str(RUNS[tag])))
        pos=json.loads((RUNS[tag]/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((RUNS[tag]/'4-rebuts/F2.2_coherencia.json').read_text())['k']
        meta=json.loads((CAU36/(tag+'_meta.json')).read_text())['frames'];fcorr,frep=flat_ripple(ctx,tag);last=tag
    group=m['grup'];gm=[a for a in meta if tag=='vixen' or a['group']==group];j=next(i for i,a in enumerate(gm) if a['name']==nom);mm=gm[j];v=pos[nom]
    sx,sy=m['native']['shift'];xm=xx-sx;ym=yy-sy;qx=inv[0,0]*xm+inv[0,1]*ym+inv[0,2];qy=inv[1,0]*xm+inv[1,1]*ym+inv[1,2]
    dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k;qmx=inv[0,0]*MC[0]+inv[0,1]*MC[1]+inv[0,2];qmy=inv[1,0]*MC[0]+inv[1,1]*MC[1]+inv[1,2]
    dmx=(qmx-ctx.CX)*ctx.k;dmy=(qmy-ctx.CY)*ctx.k;cxy=(0.,0.)
    if group=='sony_B':
        delta=math.radians(8.10/60);ca,sa=math.cos(delta),math.sin(delta);dx,dy=ca*dx-sa*dy,sa*dx+ca*dy;dmx,dmy=ca*dmx-sa*dmy,sa*dmx+ca*dmy
        cxy=json.loads((ROOT/'research/tools/v42_20260910/cau/correccions_B.json').read_text()).get(nom,(0.,0.))
    offx=v['lluna_dx']-(ctx.ca*dmx+ctx.sa*dmy);offy=v['lluna_dy']-(-ctx.sa*dmx+ctx.ca*dmy)
    rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']+cxy[0]+offx).astype(np.float32);ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']+cxy[1]+offy).astype(np.float32)
    # Numerical affine from far-separated grid points avoids float32 local difference loss.
    A=np.array([[(rx[0,-1]-rx[0,0])/(N-1),(rx[-1,0]-rx[0,0])/(N-1),rx[0,0]],[(ry[0,-1]-ry[0,0])/(N-1),(ry[-1,0]-ry[0,0])/(N-1),ry[0,0]]],float)
    with rawpy.imread(ctx.ruta[nom]) as rr:raw=rr.raw_image.astype(np.float32)
    dark=ctx.dark(v['exp']);fields={};arr={};det={};cov=[];equiv={}
    for ci,cname in enumerate(['R','G','B']):
        ppath=CAU36/(group+'_'+cname+'_phi.npy');phis=np.load(ppath,mmap_mode='r');phi_full=upsample(phis[j])
        fields[ci]=np.exp(-cv2.remap(phi_full,xm,ym,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE));del phi_full
        if str(ppath) not in deps:deps[str(ppath)]=sha(ppath)
    for i in range(4):
        ci=comu.IDX_CANAL[i];label=comu.NOMS[i];oy,ox=ctx.orig[i];rp=raw[oy::2,ox::2];ds=dark[oy::2,ox::2];flat=ctx.flat[oy::2,ox::2]
        rs=ds+(rp-ds)*sony_lut(rp,ctx.cfg['pedestal_dn'],ctx.cfg['saturacio_dn']) if tag=='sony' else rp
        pl=comu.calibra_pla(rs,ds,flat,v['exp'],ctx.wb,ctx.mc,i)
        if fcorr is not None:pl=pl*fcorr[i]
        mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32)
        ped=ctx.cfg['pedestal_dn'];sat=ctx.cfg['saturacio_dn'];rn=(rp-ped)/(sat-ped);u=np.clip((rn-.35)/.5,0,1);quality=(1-u*u*(3-2*u)).astype(np.float32)
        bad=(rn>=.85)|(ctx.valid[oy::2,ox::2]<=0)|~np.isfinite(pl);strict,taper=footprint(mx,my,bad)
        q=cv2.remap(quality,mx,my,cv2.INTER_LINEAR)*strict*taper
        field=fields[ci];g=(cv2.remap(pl*kq.get(nom,1),mx,my,cv2.INTER_LINEAR)+mm['offset_RGB'][ci])*field
        read=(1.05 if v['exp']>=1 else 2.72) if tag=='vixen' else 1.22
        rnvar=np.maximum(rp-ped,0)/(5.08 if tag=='vixen' else 3.41)+2*read**2
        if tag=='sony':
            derivative=(rp+.5-ds)*sony_lut(rp+.5,ped,sat)-(rp-.5-ds)*sony_lut(rp-.5,ped,sat);rnvar*=derivative**2
        scale=kq.get(nom,1)/(np.maximum(flat,1e-12)*v['exp'])*ctx.wb[ci]
        if fcorr is not None:scale*=fcorr[i]
        rnvar*=scale**2;qx1=np.rint(mx*32)/32;qy1=np.rint(my*32)/32;vx=np.clip(np.floor(qx1).astype(int),0,rp.shape[1]-2);vy=np.clip(np.floor(qy1).astype(int),0,rp.shape[0]-2)
        fx=qx1-vx;fy=qy1-vy;var=np.zeros_like(xx,dtype=float)
        for di,dj,b in [(0,0,(1-fy)*(1-fx)),(0,1,(1-fy)*fx),(1,0,fy*(1-fx)),(1,1,fy*fx)]:var+=b*b*rnvar[vy+di,vx+dj]
        var*=field**2
        arr[label]=np.where(q>0,g,np.nan).astype(np.float32);arr[label+'_q']=q.astype(np.float32);arr[label+'_var']=np.where(q>0,var,np.nan).astype(np.float32)
        # Detector crop: no spatial interpolation, fields or offset applied.
        xa=max(0,int(np.floor(mx.min()))-3);xb=min(rp.shape[1],int(np.ceil(mx.max()))+4);ya=max(0,int(np.floor(my.min()))-3);yb=min(rp.shape[0],int(np.ceil(my.max()))+4)
        sl=np.s_[ya:yb,xa:xb];det[label]=pl[sl].copy();det[label+'_q']=(quality*(~bad))[sl].copy();det[label+'_var']=(rnvar/kq.get(nom,1)**2)[sl].astype(np.float32)
        det[label+'_origin']=np.array([2*xa+ox,2*ya+oy]);cov.append(dict(channel=label,CFAindex=i,valid_pixels=int((q>0).sum()),native_origin=det[label+'_origin'].tolist(),WB=float(ctx.wb[ci])))
        if ci==1:
            old=np.load(ROOT/'output/earthshine_detail_20260911/native'/f'{tag}_{stem}.npz');k='1' if i==1 else '2';ok=np.isfinite(old['g'+k]);assert np.array_equal(ok,np.isfinite(arr[label]))
            diff=np.abs(arr[label][ok]-old['g'+k][ok]);equiv[label]=float(diff.max());assert diff.max()==0,(stem,label,diff.max())
        del pl,rnvar,rs,var
    arr['roi_to_native']=A;det['roi_to_native']=A
    np.savez_compressed(target,**arr)
    dt=OUT/'native'/f'{tag}_{stem}_detector.npz';np.savez_compressed(dt,**det)
    row=dict(stem=stem,tren=tag,group=group,exp=m['exp'],time_C2=m['t_mid_C2'],file=str(target),sha256=sha(target),detector_file=str(dt),detector_sha256=sha(dt),raw_path=ctx.ruta[nom],raw_sha256=sha(ctx.ruta[nom]),roi_to_native=A,shift=[sx,sy],WB=ctx.wb,offset_RGB=mm['offset_RGB'],k=kq.get(nom,1),coverage=cov,G_exact=equiv,variance_limit='Conditional photon/read variance; shared masters, flat uncertainty and spectral CFA differences not included. R/B WB squared applied.',flat_ripple=frep)
    save(str(rpout.relative_to(OUT)),row);rows.append(row)
    print(count+1,len(fr),tag,stem,'G EXACT',equiv,'elapsed',round(time.time()-tic),flush=True)
save('A1_native_rgb_all.json' if '--all' in sys.argv else 'A1_native_rgb_pilot.json',dict(frames=rows,channel_field_sha256=deps,method=__doc__))
print('A1 COMPLETE',len(rows),flush=True)
