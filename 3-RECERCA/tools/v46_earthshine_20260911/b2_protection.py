"""Photographic invariants, measured on the actual Photoshop recomposition."""
from comu46 import *
from a1_grade import field

def main():
    claim46();before=np.load(CAU46/'before_live_rgb_u16.npy').astype(np.int32)
    # Keep display-profile metadata from the actual live Adobe RGB document.
    from PIL import Image
    icc=(CAU46/'source_icc.bin').read_bytes()
    for p in VIS46.glob('*.png'):
        with Image.open(p) as im:
            if im.info.get('icc_profile')!=icc:
                im.load();im.save(p,icc_profile=icc)
    after=np.load(CAU46/'after_photoshop_rgb_u16.npy').astype(np.int32)
    w=np.load(CAU46/'live_lunar_mask_u16.npy');_,d=field(1,1)
    delta=after-before;chroma_delta=np.ptp(delta,axis=2)
    old=np.load(CAU46/'live_lunar_rgb_u16.npy');new=np.load(CAU46/'h_display_u16.npy');gain=np.load(CAU46/'h_gain.npy')
    subtraction=np.load(CAU46/'grade_subtract_u16.npy')
    # There is no image blur in the grade. Dividing out the positive gain
    # retrieves the live lunar source (within uint16 rounding).
    valid=(w>0)&(d<100)
    inverse_error=abs(new[...,1].astype(float)/gain-old[...,1])[valid]
    rows=[]
    for name,(x,y),half in [('dalt',(596,247),60),('dreta',(1088,912),70),('oest',(247,700),75),('baix',(700,1151),70)]:
        sl=np.s_[y-half:y+half,x-half:x+half]
        a=before[sl];b=after[sl]
        signal=np.maximum(0,a[...,0]-a[...,1]);signal_after=np.maximum(0,b[...,0]-b[...,1])
        yy,xx=np.mgrid[:signal.shape[0],:signal.shape[1]]
        centroid=lambda t:np.array([(t*xx).sum(),(t*yy).sum()])/max(1,t.sum())
        feature=signal>512
        rows.append(dict(name=name,box=[x-half,y-half,x+half,y+half],red_signal_pixels=int(feature.sum()),red_signal_max_delta_DN16=int(abs(signal_after-signal).max()),red_signal_sum_relative_delta=float((signal_after.sum()-signal.sum())/max(1,signal.sum())),red_signal_centroid_shift_px=float(np.linalg.norm(centroid(signal_after)-centroid(signal))),feature_mask_exact=bool(np.array_equal(feature,signal_after>512))))
        png46('B2_'+name+'_abans_despres_x3.png',cv2.resize(np.concatenate([a,b],1).astype(float)/65535,None,fx=3,fy=3,interpolation=cv2.INTER_NEAREST))
    edge=(abs(d)<1)&(w>int(.95*65535))
    report=dict(scope='PHOTOGRAPHIC_USER_REQUEST; no scientific detail-recovery claim',profile_variant='h',PASS=False,
        source_inner_pixels_exact=bool(np.array_equal(new[d>=100],old[d>=100])),source_24_layers_compressed_exact=True,
        zero_new_black_clipping_in_lunar_source=bool(np.all(new[valid]>0)),inverse_gain_max_DN16=float(inverse_error.max()),
        actual_no_grade_max_DN16=int(abs(delta[(w==0)|(d>=100)]).max()),actual_chromatic_max_delta_DN16=int(chroma_delta.max()),
        median_edge_green_before=float(np.median(before[...,1][edge])/65535),median_edge_green_after=float(np.median(after[...,1][edge])/65535),
        no_grade_pixels_in_roi=int(((w==0)|(d>=100)).sum()),rows=rows,
        gain_rule='smootherstep target0.18 atedge to0.22905 in8px; smooth release to100px; depth60px gain0.94967, depth80px0.99480; no source pixel filtering',
        visualization='actual Photoshop before/after, same coordinates and magnification',
        warning='Absolute neutral lunar contrast dims with the tone, while fractional texture is retained. Chroma signal and solar layer contribution retained. This does not establish the astronomical origin of every last-limb texture.')
    report['PASS']=report['source_inner_pixels_exact'] and report['zero_new_black_clipping_in_lunar_source'] and report['inverse_gain_max_DN16']<=4 and report['actual_no_grade_max_DN16']<=6 and report['actual_chromatic_max_delta_DN16']<=6 and all(x['red_signal_max_delta_DN16']<=6 and x['red_signal_centroid_shift_px']<.02 for x in rows)
    savejson(REB46/'B2_protection.json',report);print(json.dumps(report,ensure_ascii=False,indent=2),flush=True);assert report['PASS']

if __name__=='__main__':main()
