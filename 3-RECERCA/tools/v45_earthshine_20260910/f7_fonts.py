"""Editable observed sources. A single invertible tone curve, no spatial filter.
This is not a clean, recovered lunar albedo product. Glare remains visible.
"""
from comu45 import *
from f2_temporal import SURFACE
import tifffile

SOURCES=[('vixen_C2_11s','V45 font G · Vixen C2+11,4 s · 1/2 s'),
         ('vixen_C2_73s','V45 font G · Vixen C2+73,1 s · 1/2 s'),
         ('sony_reference','V45 font G · Sony · selecció temporal'),
         ('vixen_reference','V45 font G · Vixen · selecció temporal'),
         ('combined_all','V45 font G · dos trens · tots els epochs'),
         ('combined_reference','V45 font G · dos trens · preferència temporal · vel present')]
FILES=OUT45/'lliurables/fonts'

def main():
    claim45();FILES.mkdir(exist_ok=True)
    # No current frame is re-interpolated for this display/export stage.
    gref=np.load(CAU45/'combined_reference.npy');mid=float(np.median(gref[R<.7*RL]));soft=20.;scale=.045;anchor=.20
    edge=np.load(CAU44/'vixen_optical_edge.npy');geometric=np.zeros_like(R,dtype=float)
    for oy in [-.375,-.125,.125,.375]:
        for ox in [-.375,-.125,.125,.375]:
            ph=np.arctan2(YY+oy-CYT,XX+ox-CXT)%(2*np.pi);lim=np.interp(ph*len(edge)/(2*np.pi),np.arange(len(edge)),edge,period=len(edge))
            geometric+=(np.hypot(XX+ox-CXT,YY+oy-CYT)<lim)/16
    # The PSB only displays through the inherited join. Full valid samples
    # stay in each layer; disabling its mask exposes them without a new crop.
    join=np.load(CAU44/'join_coverage.npy');rows=[]
    for key,label in SOURCES:
        if key.startswith('vixen_C2_'):
            stem='572A2972' if key.endswith('11s') else '572A2990';p=CAU45/f'native_vixen_{stem}.npz';d=np.load(p);g=d['g'];valid=np.isfinite(g)&(d['q']>0)
        else:
            p=CAU45/(key+'.npy');g=np.load(p);valid=np.isfinite(g)
        display=anchor+scale*np.arcsinh((np.nan_to_num(g,nan=mid)-mid)/soft)
        good=valid&(geometric>0);clipped=int(((display<=0)|(display>=1))[good].sum());assert clipped==0,(key,clipped)
        u=np.round(np.clip(display,0,1)*65535).astype(np.uint16);rgb=np.repeat(u[...,None],3,axis=2)
        mask=np.round(join*valid*65535).astype(np.uint16)
        np.save(CAU45/(key+'_display_u16.npy'),rgb);np.save(CAU45/(key+'_mask_u16.npy'),mask)
        png45('F7_'+key+'.png',np.repeat(np.where(good,display,0)[...,None],3,axis=2))
        rows.append(dict(key=key,label=label,source=str(p),source_sha256=sha(p),display_sha256=sha(CAU45/(key+'_display_u16.npy')),mask_sha256=sha(CAU45/(key+'_mask_u16.npy')),clipped_lunar_samples=clipped,valid_lunar_samples=int(good.sum()),missing_at_lunar_centres=int((SURFACE&~valid).sum())))
    # Full original canvas,32-bit float, unassociated alpha. Unit conversion
    # G/65535 is fixed; G is calibrated native green, NOT absolute radiance.
    out=FILES/'Earthshine_V45_HDR_G_lineal.tif';assert not out.exists()
    rgba=np.zeros((H,W,4),np.float32);roi=rgba[Y0:Y0+N,X0:X0+N]
    roi[...,:3]=np.repeat(np.nan_to_num(gref)[...,None]/65535,3,axis=2);roi[...,3]=geometric*np.isfinite(gref)
    tifffile.imwrite(out,rgba,photometric='rgb',extrasamples=['unassalpha'],compression='deflate',predictor=True,metadata={'axes':'YXS','description':'Measured nativeG1+G2 /65535. Single global gain, no spatial tone/filter/background subtraction. Original10551x7506 grid. Alpha=observed Vixen geometry. Includes residual corona/PSF light.'})
    del rgba
    with tifffile.TiffFile(out) as tf:
        arr=tf.asarray();assert arr.shape==(H,W,4) and arr.dtype==np.float32 and list(map(int,tf.pages[0].extrasamples))==[2]
    assert np.array_equal(arr[Y0:Y0+N,X0:X0+N,0],np.nan_to_num(gref)/65535)
    assert np.array_equal(arr[Y0:Y0+N,X0:X0+N,3],(geometric*np.isfinite(gref)).astype(np.float32))
    del arr
    # Lossless original numerical arrays and masks retain every observed pixel,
    # including the exterior diagnostic context that the Photoshop mask hides.
    raw=FILES/'Earthshine_V45_font_i_pesos.npz';assert not raw.exists()
    np.savez_compressed(raw,G=gref,vixen=np.load(CAU45/'vixen_reference.npy'),sony=np.load(CAU45/'sony_reference.npy'),all_epochs=np.load(CAU45/'combined_all.npy'),epoch_weights=np.load(CAU45/'combined_epoch_ref_weights.npy'),geometric_alpha=geometric.astype(np.float32),display_join=join,origin_xy=np.array([X0,Y0]),canvas_wh=np.array([W,H]))
    rep=dict(status='OBSERVED_SOURCE_ONLY; no recovered-all-limb or clean-albedo claim',sources=rows,F2_sha256=sha(REB45/'F2_temporal.json'),B1_sha256=sha(REB45/'B1_inputs.json'),tone=dict(formula='display=anchor+scale*asinh((G-mid)/soft)',anchor=anchor,scale=scale,mid=mid,soft=soft,spatial_filter='NONE',invertible_before_uint16_quantization=True),canvas=[W,H],depth=16,source_color='nativeG1+G2 repeated inRGB; monochrome, not recoveredRGB',join='exact stored V44 geometry/09 protection, removable layer mask; not a texture or quality fade',linear_float32=dict(path=str(out),sha256=sha(out),scale='G/65535',readback_exact=True),numerical_sources=dict(path=str(raw),sha256=sha(raw)))
    savejson(REB45/'F7_fonts.json',rep);print(json.dumps(rep),flush=True)
if __name__=='__main__':main()
