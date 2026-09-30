"""Three-frame native green and positive quincunx interpolation pilot.
Same V48 calibration, texture geometry and output1400 grid; no deconvolution,
no borrowed red/blue data, no mask or Photoshop changes. Original arrays frozen.
"""
from native_common import *
import sys,time,argparse
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from b1_native import f2,comu,RUNS,COMMON_TO_FINAL,CAU36,B,MC,rawpy,cv2
from quincunx import interpolate,elementary_checks

parser=argparse.ArgumentParser();parser.add_argument('--all-vixen',action='store_true');args=parser.parse_args()
checks=elementary_checks()
if not args.all_vixen:save('A0_lattice_checks.json',checks)
frames=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'];names=['572A2973','572A2976','572A2978'];frames=[m for m in frames if m['tren']=='vixen'] if args.all_vixen else [next(m for m in frames if m['stem']==name) for name in names]
reportname='A2_all_native.json' if args.all_vixen else 'A0_native_and_quincunx.json'
previous={m['stem']:m for m in json.loads((OUT/'A0_native_and_quincunx.json').read_text())['frames']} if args.all_vixen else {}
source_meta=json.loads((SRC/'B0_all_native.json').read_text())['frames'];source_meta={m['stem']:m for m in source_meta if m['tren']=='vixen'}
ctx=f2.Ctx(comu.Run.obre(str(RUNS['vixen'])));pos=json.loads((RUNS['vixen']/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((RUNS['vixen']/'4-rebuts/F2.2_coherencia.json').read_text())['k'];meta=json.loads((CAU36/'vixen_meta.json').read_text())['frames'];fcorr,frep=B.flat_ripple_correction(ctx,'vixen');phis=np.load(CAU36/'vixen_G_phi.npy',mmap_mode='r')
assert sorted(ctx.orig[i] for i in ctx.orig if comu.IDX_CANAL[i]==1)==[(0,1),(1,0)]
inv=cv2.invertAffineTransform(COMMON_TO_FINAL);yy,xx=np.mgrid[Y0:Y0+N,X0:X0+N].astype(np.float32);rrworld=np.hypot(xx-(X0+CX),yy-(Y0+CY));reports=[]

for m in frames:
    if m['stem'] in previous:
        row=previous[m['stem']]
        assert Path(row['output']).exists() and Path(row['native_samples']).exists()
        reports.append(row);continue
    start=time.time();nom=m['nom'];stem=m['stem'];output=OUT/f'A0_quincunx_{stem}.npz';nativeout=OUT/f'A0_native_samples_{stem}.npz';assert not nativeout.exists()
    v=pos[nom];j=next(i for i,a in enumerate(meta) if a['name']==nom);mm=meta[j];sx,sy=m['native']['shift'];xm=xx-sx;ym=yy-sy
    # Match the V48 affine arithmetic and coordinate precision before changing
    # only the interpolation lattice and its fractions.
    qx=inv[0,0]*xm+inv[0,1]*ym+inv[0,2];qy=inv[1,0]*xm+inv[1,1]*ym+inv[1,2];dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
    qmx=inv[0,0]*MC[0]+inv[0,1]*MC[1]+inv[0,2];qmy=inv[1,0]*MC[0]+inv[1,1]*MC[1]+inv[1,2];dmx=(qmx-ctx.CX)*ctx.k;dmy=(qmy-ctx.CY)*ctx.k
    offx=v['lluna_dx']-(ctx.ca*dmx+ctx.sa*dmy);offy=v['lluna_dy']-(-ctx.sa*dmx+ctx.ca*dmy)
    rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']+offx).astype(np.float32);ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']+offy).astype(np.float32)
    u=(rx.astype(float)+ry-1)/2;vv=(rx.astype(float)-ry-1)/2
    u0=int(np.floor(u.min()))-4;u1=int(np.ceil(u.max()))+4;v0=int(np.floor(vv.min()))-4;v1=int(np.ceil(vv.max()))+4
    V,U=np.mgrid[v0:v1+1,u0:u1+1];nx=1+U+V;ny=U-V
    with rawpy.imread(ctx.ruta[nom]) as a:raw=a.raw_image.astype(np.float32)
    inside=(nx>=0)&(ny>=0)&(nx<raw.shape[1])&(ny<raw.shape[0]);assert np.all((nx[inside]+ny[inside])%2==1)
    plans=ctx.plans(nom,v['exp']);g=np.zeros(U.shape);quality=g.copy();var=g.copy();rn=np.ones(U.shape);bad=np.ones(U.shape,dtype=bool);assigned=np.zeros(U.shape,dtype=bool);plane=np.full(U.shape,-1,dtype=np.int8)
    for i in ctx.orig:
        if comu.IDX_CANAL[i]!=1:continue
        oy,ox=ctx.orig[i];sel=inside&((ny-oy)%2==0)&((nx-ox)%2==0);iy=(ny[sel]-oy)//2;ix=(nx[sel]-ox)//2;rp=raw[oy::2,ox::2];pl=plans[i][0]
        corr=fcorr[i][iy,ix] if fcorr is not None else 1.;cal=pl[iy,ix]*corr;k=kq.get(nom,1.);g[sel]=cal*k;rn[sel]=(rp[iy,ix]-ctx.cfg['pedestal_dn'])/(ctx.cfg['saturacio_dn']-ctx.cfg['pedestal_dn'])
        z=np.clip((rn[sel]-.35)/.5,0,1);quality[sel]=1-z*z*(3-2*z)
        bad[sel]=(rn[sel]>=.85)|(ctx.valid[oy::2,ox::2][iy,ix]<=0)|~np.isfinite(cal);assigned[sel]=True;plane[sel]=i
        read=1.05 if v['exp']>=1 else 2.72;noise=np.maximum(rp[iy,ix]-ctx.cfg['pedestal_dn'],0)/5.08+2*read*read
        scale=k/(np.maximum(ctx.flat[oy::2,ox::2][iy,ix],1e-12)*v['exp'])*corr;var[sel]=noise*scale*scale
    assert np.array_equal(assigned,inside)
    result,receipt=interpolate(g,quality,var,bad,u,vv,u0,v0)
    phi_full=B.upsample(phis[j]);field=np.exp(-cv2.remap(phi_full,xm,ym,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE))
    result['g']=((result['g']+mm['offset_RGB'][1])*field).astype(np.float32);result['q']=result['q'].astype(np.float32);result['variance']=(result['variance']*field**2).astype(np.float32)
    if output.exists():
        # Recover the recorded OpenCV vector-size failure without overwriting
        # its completed source checkpoint; require identical regeneration.
        with np.load(output) as checkpoint:
            assert set(checkpoint.files)==set(result)
            for key in result:assert np.array_equal(checkpoint[key],result[key],equal_nan=True),key
    else:np.savez_compressed(output,**result)
    # Save actual calibrated green samples, without interpolating radiance.
    D=np.array([[ctx.ca,ctx.sa],[-ctx.sa,ctx.ca]])@inv[:2,:2]*ctx.k;J=np.linalg.inv(D);nxc=v['sol_x']+v['lluna_dx'];nyc=v['sol_y']+v['lluna_dy']
    wx=MC[0]+sx+J[0,0]*(nx-nxc)+J[0,1]*(ny-nyc);wy=MC[1]+sy+J[1,0]*(nx-nxc)+J[1,1]*(ny-nyc);radius=np.hypot(wx-MC[0],wy-MC[1]);band=inside&(radius>=415)&(radius<=495)
    fx=(wx[band]-sx).astype(np.float32);fy=(wy[band]-sy).astype(np.float32)
    nativefield=np.concatenate([np.exp(-cv2.remap(phi_full,fx[a:a+16000][None,:],fy[a:a+16000][None,:],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE))[0] for a in range(0,len(fx),16000)])
    np.savez_compressed(nativeout,x=wx[band]-X0,y=wy[band]-Y0,native_x=nx[band],native_y=ny[band],g=(g[band]+mm['offset_RGB'][1])*nativefield,variance=var[band]*nativefield**2,q=np.where(~bad[band],quality[band],0),raw_relative=rn[band],valid=~bad[band],green_plane=plane[band],native_to_world=J)
    with Path(ctx.ruta[nom]).open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    assert sha==source_meta[stem]['raw_sha256']
    old=np.load(source_meta[stem]['file']);comparisons=[]
    for lo,hi in [(0,350),(435,449),(449,458)]:
        area=(rrworld>=lo)&(rrworld<hi);common=area&(old['q']>0)&(result['q']>0)
        comparisons.append(dict(radius=[lo,hi],old_valid=int((area&(old['q']>0)).sum()),new_valid=int((area&(result['q']>0)).sum()),common=int(common.sum()),median_variance_ratio=float(np.median(result['variance'][common]/old['variance'][common])),median_delta_G=float(np.median(result['g'][common]-old['g'][common]))))
    row=dict(stem=stem,exp=v['exp'],raw_path=str(ctx.ruta[nom]),raw_sha256=sha,output=str(output),native_samples=str(nativeout),shift=[sx,sy],native_to_world_pixel_scale=float(np.sqrt(abs(np.linalg.det(J)))),lattice_shape=list(g.shape),validity=receipt,comparisons=comparisons,seconds=time.time()-start,method=__doc__);reports.append(row);save(reportname,dict(method=__doc__,frames=reports,lattice_checks=checks,status='Source interpolation candidate only; noise and independent detail qualification pending',all_vixen=args.all_vixen))
    print(stem,'DONE',row['seconds'],'valid',receipt['valid'],'variance_ratio',comparisons[0]['median_variance_ratio'],flush=True)
    del raw,plans,g,quality,var,rn,bad,phi_full,old,result,U,V,nx,ny,wx,wy
print('DONE',len(reports),flush=True)
