"""Verify reopened rasters, all unaffected layers, masks and merged pixels."""
from package_v31 import *
def main():
    r=json.loads((D/'packaging_receipt.json').read_text());s=PSDImage.open(TARGET);ls=list(s)
    assert len(ls)==30 and s.depth==16 and s.size==(FW,FH)
    assert global_signature(s)==r['original_global']
    changed={x['index']:x for x in r['changed']}
    for i,l in enumerate(ls):
        if i not in changed:assert signature(l)==r['original_layers'][i]
        else:
            x=changed[i];assert signature(l)==x['signature'];u=np.load(C/f"{x['tag']}_final_u16.npy",mmap_mode='r')
            for c in (0,1,2):assert np.array_equal(channel(l,c),u)
            l.name=x['old_name'];sig=signature(l);old=r['original_layers'][i]
            assert sig['record_without_color_lengths_sha256']==old['record_without_color_lengths_sha256']
            assert all(v==old['channels'][k] for k,v in sig['channels'].items() if k not in ('0','1','2'))
            l.name=x['new_name']
    rep={'unaffected25_complete_records_and_channels_identical':True,'changed5_only_RGB_and_version_name':True,'all30_alpha_masks_opacities_visibility_order_preserved':True,'azimuthal03_and07_identical':True,'global_metadata_exact':True,'composite':{}}
    log('reopened layer preservation PASS');comp=compose(s);merged=s._record.image_data.get_data(s._record.header)
    for c in range(3):
        a=np.frombuffer(merged[c],'>u2').reshape(FH,FW);b=np.round(np.clip(comp[...,c],0,1)*65535).astype('uint16');e=np.abs(a.astype('int32')-b.astype('int32'));mx=int(e.max());assert mx<=1
        rep['composite'][str(c)]={'max_DN16':mx,'p99_DN16':float(np.percentile(e,99))}
    assert [digest(b) for b in merged[3:]]==r['expected_extra_merged_channels']
    rep.update(size=list(s.size),depth=s.depth,layers=len(ls),sha256=sha(TARGET),bytes=TARGET.stat().st_size,PASS=True)
    savejson(D/'psb_verification.json',rep);log('V31 verification PASS')
if __name__=='__main__':main()
