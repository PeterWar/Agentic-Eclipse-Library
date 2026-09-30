"""Reopen the delivered PSB, verify immutable channels and actual composite."""
from common import *
from package_psb import layer_signature
from inspect_inputs import channel,sha
from build_canvas import canvas_layer,over,png
from psd_tools import PSDImage

def main():
    p=CT/'V29.psb';s=PSDImage.open(p);ls=list(s);receipt=json.loads((CAU/'packaging_receipt.json').read_text());cfg=receipt['delivery_config']
    rep={'path':str(p),'size':s.size,'depth':s.depth,'layers':len(ls),'preserved':[],'new_layers':[],'composite':{}}
    assert tuple(s.size)==(FW,FH) and s.depth==16 and len(ls)==25
    for oi,ni in [(i,i) for i in range(18)]+[(24,23),(25,24)]:
        original=receipt['original_layers'][str(oi)];new=layer_signature(ls[ni]);ok=original==new
        rep['preserved'].append({'old_index':oi,'new_index':ni,'name':new['name'],'all_channels_mask_bbox_blend_opacity_identical':ok});assert ok,(oi,ni)
    for idx,name in [(18,'base_amb_cel'),(19,'base_cel4'),(20,'gran'),(21,'achf'),(22,'passalt24')]:
        l=ls[idx];a=np.load(CAU/f'{name}_final.npy',mmap_mode='r');is_detail=name in cfg['layers']
        if is_detail:a=.5+(a-.5)*cfg['layers'][name]['strength']
        mask=np.load(CAU/(f'{name}_mask_final.npy' if is_detail else 'base_mask_final.npy'),mmap_mode='r')
        expected_mask=np.round(np.clip(mask,0,1)*65535).astype(np.uint16)
        checks=[]
        for c in range(3):
            u=channel(l,c);expected=np.round(np.clip(a if is_detail else a[...,c],0,1)*65535).astype(np.uint16)
            checks.append(bool(np.array_equal(u,expected)));del u,expected
        mask_equal=np.array_equal(channel(l,-2),expected_mask)
        rep['new_layers'].append({'index':idx,'name':name,'RGB_exact':checks,'mask_exact':bool(mask_equal)});assert all(checks) and mask_equal
        del a,mask,expected_mask;log('verified pixels '+name)
    comp=np.zeros((FH,FW,3),np.float32)
    for idx in (0,1,17,19,20,21,22,23,24):
        l=ls[idx];a,mask=canvas_layer(l)
        mode='overlay' if idx in (20,21,22) else 'add' if idx in (23,24) else 'normal'
        comp=over(comp,a,mask,l.opacity/255,mode);del a,mask;log('recomposed '+str(idx))
    merged=s._record.image_data.get_data(s._record.header);expected=np.load(CAU/'composite_delivery.npy',mmap_mode='r')
    for c in range(3):
        actual=np.frombuffer(merged[c],'>u2').reshape(FH,FW);expect=np.round(np.clip(expected[...,c],0,1)*65535).astype(np.uint16)
        assert np.array_equal(actual,expect),'merged delivery mismatch'
        error=np.abs(actual.astype(np.float32)-np.round(np.clip(comp[...,c],0,1)*65535))
        rep['composite'][str(c)]={'merged_exact':True,'reopened_layers_max_DN':float(error.max()),'p99_DN':float(np.percentile(error,99))};assert error.max()<=4
    png(comp,'V29_VERIFICADA_llenc_sencer.png');rep['sha256']=sha(p);rep['bytes']=p.stat().st_size;rep['PASS']=True
    savejson(CAU/'psb_verification.json',rep);log('PSB verification PASS')

if __name__=='__main__':main()
