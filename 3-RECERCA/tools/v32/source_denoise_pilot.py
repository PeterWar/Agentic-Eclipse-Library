"""Local discriminating test of denoising ln radiance before the high-pass.

Diagnostic only: a noise proxy is not a calibrated RAW variance model.
No generated patch is used as a deliverable or inpainting source.
"""
from sn_pilots import *
from skimage.restoration import denoise_nl_means,estimate_sigma
from fuse_and_filter import achf
def main():
    total=np.load(CAU/'fusion_total.npy',mmap_mode='r');m=np.load(CAU/'fusion_support.npy',mmap_mode='r');sigma=np.load(CAU/'resolution_sigma.npy',mmap_mode='r')
    prof=json.loads((CAU/'refined_detail_receipt.json').read_text());scale_tanh=prof['filters']['achf']['scale_tanh'];p=prof['profiles']['1'];rep={'status':'DIAGNOSTIC_ONLY','operator':'nonlocal-means on lnG before ACHF, fixed subsequent scales; no generative fill','noise_proxy':'wavelet estimate_sigma; not RAW variance and possibly biased for correlated noise','rois':{}}
    # Whole canvas context accompanies the local diagnostic comparisons.
    source=np.log(np.maximum(total[::4,::4,1],1e-8));lo,hi=np.percentile(source[np.isfinite(source)],(1,99));png((source-lo)/(hi-lo),OUT/'SOURCE_lnG_llenc_sencer.png')
    for name,(cx,cy) in ROIS.items():
        n=768;yy,xx=np.mgrid[cy-n//2:cy+n//2,cx-n//2:cx+n//2];r=np.hypot(xx-CX,yy-CY);sl=(slice(cy-n//2,cy+n//2),slice(cx-n//2,cx+n//2));w=m[sl].astype('float32');x=np.log(np.maximum(total[sl][...,1],1e-8));sc=np.interp(np.log(np.maximum(r/RS,1e-5)),p['lnr_centres'],p['robust_contrast']).astype('float32');ss=sigma[sl];noise=float(estimate_sigma(x,channel_axis=None,average_sigmas=True))
        arrays=[];labels=[]
        for factor in (0,1,1.5):
            z=x if factor==0 else denoise_nl_means(x,h=noise*factor,sigma=noise,fast_mode=True,patch_size=5,patch_distance=9,preserve_range=True,channel_axis=None).astype('float32')
            d=achf(z,w,[2,4,8,16,32])/sc;a,_=sn_smooth(.5*np.tanh(d/scale_tanh),w>0,sigma=ss)
            np.save(D/f'cau/source_{name}_h{factor:g}_detail.npy',a)
            arrays.append(a[128:-128,128:-128]+.5);labels.append('source h'+str(factor))
        im=Image.new('RGB',(1536,542));draw=ImageDraw.Draw(im)
        for j,(a,label) in enumerate(zip(arrays,labels)):
            im.paste(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('RGB'),(j*512,30));draw.text((j*512+8,8),label,fill='white')
        im.save(OUT/f'SOURCE_NLM_{name}_100.png');rep['rois'][name]={'noise_lnG_proxy':noise,'center':[cx,cy],'note':'same unchanged H1 omitted from all displayed differences; G-only, not final medianRGB'};log('source pilot '+name)
    savejson(D/'source_denoise_pilot.json',rep)
if __name__=='__main__':main()
