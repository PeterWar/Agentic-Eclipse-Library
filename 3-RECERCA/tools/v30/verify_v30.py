"""Read actual PSB pixels, original-layer signatures and visible recomposition."""
from package_v30 import *
from build_canvas import canvas_layer,over
from PIL import Image
OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v30_20260905')

def main():
    r=json.loads((D/'packaging_receipt.json').read_text());s=PSDImage.open(TARGET);ls=list(s)
    assert len(ls)==30 and s.depth==16 and s.size==(FW,FH)
    assert global_signature(s)==r['original_global']
    names=[n[0] for n in NEW];old=[l for l in ls if l.name not in names]
    assert [signature(l) for l in old]==r['expected_preserved_layers']
    # Only original03 visibility is permitted to differ from the original PSB.
    old[20].visible=True;assert [signature(l) for l in old]==r['original_layers'];old[20].visible=False
    rep={'original25_pixels_alpha_masks_compressed_channels_identical':True,'original24_complete_records_identical':True,'original03_only_visibility_changed':True,'global_metadata_exact':True,'new_layers':[]}
    for x in r['new']:
        l=next(l for l in ls if l.name==x['name']);assert signature(l)==x['signature'];u=np.load(C/f"{x['tag']}_u16.npy",mmap_mode='r')
        for c in (0,1,2):assert np.array_equal(channel(l,c),u)
        expected=channel(old[20],-2) if x['tag'].startswith('gran_') else np.load(C/f"{x['tag']}_mask_u16.npy",mmap_mode='r')
        assert np.array_equal(channel(l,-2),expected)
        rep['new_layers'].append({'name':l.name,'pixels_and_mask_exact':True,'visible':l.visible,'opacity':l.opacity})
    log('all original layers preserved; new rasters exact')
    comp=np.zeros((FH,FW,3),np.float32)
    fg_names={old[23].name,old[24].name}
    for l in ls:
        if not l.visible:continue
        a,m=canvas_layer(l);mode='overlay' if l.blend_mode==BlendMode.OVERLAY else 'add' if l.name in fg_names else 'normal'
        comp=over(comp,a,m,l.opacity/255,mode);del a,m;log('recomposed '+l.name)
    merged=s._record.image_data.get_data(s._record.header);expected=np.load(C/'composite_default_r4.npy',mmap_mode='r');rep['composite']={}
    for c in range(3):
        actual=np.frombuffer(merged[c],'>u2').reshape(FH,FW);u=np.round(np.clip(expected[...,c],0,1)*65535).astype('uint16');assert np.array_equal(actual,u)
        error=np.abs(actual.astype('float32')-np.round(np.clip(comp[...,c],0,1)*65535));mx=float(error.max());assert mx<=4,(c,mx)
        rep['composite'][str(c)]={'merged_exact':True,'max_reopened_layers_DN':mx,'p99_DN':float(np.percentile(error,99))}
    assert [digest(b) for b in merged[3:]]==r['expected_extra_merged_channels']
    im=Image.fromarray(np.uint8(np.clip(comp,0,1)*255));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(OUT/'V30_VERIFICADA.png')
    rep.update(size=list(s.size),depth=s.depth,layers=len(ls),sha256=sha(TARGET),bytes=TARGET.stat().st_size,PASS=True)
    savejson(D/'psb_verification.json',rep);log('V30 PSB verification PASS')
if __name__=='__main__':main()
