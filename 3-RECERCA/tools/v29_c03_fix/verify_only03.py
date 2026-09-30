"""Reopen, compare all25 complete layer records/channels, and recompose."""
from package_only03 import *
from build_canvas import canvas_layer,over
from PIL import Image
OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v29_c03_fix_20260905')

def main():
    rep0=json.loads((D/'packaging_receipt.json').read_text());s=PSDImage.open(TARGET);ls=list(s)
    assert len(ls)==25 and s.depth==16 and s.size==(FW,FH)
    rep={'size':s.size,'depth':s.depth,'layers':len(ls),'unchanged_layers':[],'changed_layer':{},'global_metadata_exact':global_signature(s)==rep0['original_global']}
    assert rep['global_metadata_exact']
    for i,l in enumerate(ls):
        new=signature(l);old=rep0['original_layers'][i]
        if i!=20:
            assert new==old,('unintended layer change',i);rep['unchanged_layers'].append({'index':i,'name':l.name,'all_record_metadata_and_compressed_channels_identical':True})
        else:
            assert new['record_without_color_lengths_sha256']==old['record_without_color_lengths_sha256']
            assert all(v==old['channels'][k] for k,v in new['channels'].items() if k not in ('0','1','2'))
            u=np.load(D/'gran_u16.npy',mmap_mode='r');checks=[bool(np.array_equal(channel(l,c),u)) for c in (0,1,2)];assert all(checks)
            rep['changed_layer']={'index':20,'name':l.name,'color_channels_exact_candidate':checks,'alpha_mask_visibility_blend_opacity_all_other_record_metadata_identical':True}
    log('24 layers byte-identical;03 pixels and preserved metadata verified')
    comp=np.zeros((FH,FW,3),np.float32)
    for i,l in enumerate(ls):
        if not l.visible:continue
        a,m=canvas_layer(l);mode='overlay' if str(l.blend_mode).endswith('OVERLAY') else 'add' if i in (23,24) else 'normal'
        comp=over(comp,a,m,l.opacity/255,mode);del a,m;log('recomposed '+str(i))
    merged=s._record.image_data.get_data(s._record.header);expected=np.load(D/'composite.npy',mmap_mode='r');rep['composite']={}
    for c in range(3):
        actual=np.frombuffer(merged[c],'>u2').reshape(FH,FW);u=np.round(np.clip(expected[...,c],0,1)*65535).astype('uint16');assert np.array_equal(actual,u)
        error=np.abs(actual.astype('float32')-np.round(np.clip(comp[...,c],0,1)*65535));mx=float(error.max());assert mx<=4,(c,mx)
        rep['composite'][str(c)]={'merged_exact':True,'max_reopened_layers_DN':mx,'p99_DN':float(np.percentile(error,99))}
    assert [digest(b) for b in merged[3:]]==rep0['expected_extra_merged_channels']
    im=Image.fromarray(np.uint8(np.clip(comp,0,1)*255));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(OUT/'V29_CORREGIDA_VERIFICADA.png')
    rep['sha256']=sha(TARGET);rep['bytes']=TARGET.stat().st_size;rep['PASS']=True;savejson(D/'psb_verification.json',rep);log('PSB verification PASS')
if __name__=='__main__':main()
