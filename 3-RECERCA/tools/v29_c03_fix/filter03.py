"""Recompute only 03, freezing its operator, display scale, support and opacity."""
import os,sys,json
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026');D=Path(__file__).parent
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
from gran_azimuthal import angular
from fuse_and_filter import sn_smooth,centre_rings
from build_canvas import over
from PIL import Image,ImageDraw
OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v29_c03_fix_20260905')

def png(a,name):
    im=Image.fromarray(np.uint8(np.clip(a,0,1)*255));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(OUT/name)
def main():
    r,t=coords();oldrep=json.loads((CAU/'gran_azimuthal_receipt.json').read_text());profiles=oldrep['post_contrast_profiles']
    masks={n:np.load(CAU/f'{n}_support.npy') for n in ['vixen','sony']}
    # Match the original03 validity before train weights and Sony fallback.
    for tag in ('vixen','sony'):
        old=np.load(CAU/f'{tag}_total.npy' if tag=='vixen' else CAU/'sony_corrected_total.npy',mmap_mode='r')[...,1]
        masks[tag]&=np.isfinite(old)&(old>0)
    m=np.load(CAU/'gran_support.npy');wv=(1-smooth(r/RS,2,2.65))*masks['vixen'];wv=np.where(masks['sony'],wv,masks['vixen'].astype('float32'));ws=(1-wv)*masks['sony']
    assert np.array_equal(m,masks['vixen']|masks['sony'])
    d=np.zeros((H,W),np.float32);scale=np.zeros_like(d);rep={'unchanged':['angular operator8/32/64/128','post-contrast profiles','tanh scale','resolution map','support','PSB layer mask','opacity38/255'],'source_change':'global native-channel additive offsets through original weights'}
    for tag,weight in [('vixen',wv),('sony',ws)]:
        a=np.load(D/f'{tag}_corrected_G.npy',mmap_mode='r');mask=masks[tag];old=np.load(CAU/f'{tag}_total.npy' if tag=='vixen' else CAU/'sony_corrected_total.npy',mmap_mode='r')[...,1]
        valid=mask&np.isfinite(old)&(old>0);bad=valid&(~np.isfinite(a)|(a<=0));assert not bad.any(),(tag,int(bad.sum()))
        band=angular(np.log(np.maximum(a,1e-8)),valid,r,t);np.save(D/f'angular_{tag}_raw.npy',band)
        profile=profiles[tag];sc=np.interp(np.log(np.maximum(r/RS,1e-5)),profile['lnr_centres'],profile['robust_contrast']).astype('float32')
        d+=weight*band;scale+=weight*sc;log('corrected angular '+tag)
        del band,sc,a,old,valid,bad
    d=np.where(m,d/np.maximum(scale,.002),0).astype('float32');np.save(D/'gran_raw.npy',d)
    mapped=(.5*np.tanh(d/oldrep['scale_tanh'])).astype('float32');sm,_=sn_smooth(mapped,m);centered,hist=centre_rings(sm,m,r)
    u=np.round(np.clip(.5+centered,0,1)*65535).astype('uint16');u[~m]=32768;np.save(D/'gran_u16.npy',u);np.save(D/'gran_smoothed.npy',sm)
    rep['H1_history']=hist;rep['display_tanh_scale']=oldrep['scale_tanh'];savejson(D/'filter_receipt.json',rep)
    final=u.astype('float32')/65535;png(final,'CANDIDATA_03_llenc_sencer.png')
    sl=(slice(2350,5200),slice(3935,6785));old=np.load(CAU/'gran_final.npy',mmap_mode='r');panel=Image.new('RGB',(1800,935));dr=ImageDraw.Draw(panel)
    for i,(a,label) in enumerate([(old,'03 V29 abans'),(final,'03 corregida: mateixa forca i mateixa mascara')]):
        im=Image.fromarray(np.uint8(np.clip(a[sl],0,1)*255)).resize((900,900),Image.Resampling.LANCZOS);panel.paste(im,(i*900,35));dr.text((i*900+10,10),label,fill='white')
    panel.save(OUT/'AB_03_zona_pentagonals.png')
    comp=np.load(CAU/'composite_base.npy');cfg=json.loads((CAU/'delivery_config.json').read_text())
    for name in ['gran','achf','passalt24']:
        a=final if name=='gran' else np.load(CAU/f'{name}_final.npy',mmap_mode='r');mask=np.load(CAU/f'{name}_mask_final.npy',mmap_mode='r')
        comp=over(comp,a[...,None],mask,cfg['layers'][name]['opacity_u8']/255,'overlay')
    comp=np.clip(comp+np.load(CAU/'foreground_add.npy',mmap_mode='r'),0,1);np.save(D/'composite.npy',comp);png(comp,'CANDIDATA_V29_llenc_sencer.png')
    log('layer03 candidate ready')
if __name__=='__main__':main()
