"""Full-amplitude editable filters; presentation strength in opacity only."""
from common import *
from build_canvas import over,png
from PIL import Image,ImageDraw

def main():
    assert json.loads((CAU/'raster_qa.json').read_text())['PASS']
    cfg={'accepted_for_packaging':False,'candidate':'full_amplitude_layers_natural_opacities','layers':{'achf':{'strength':1,'opacity_u8':36},'passalt24':{'strength':1,'opacity_u8':20},'gran':{'strength':1,'opacity_u8':38}},'support':'actual observed temporal union; wideG uses positivefiniteG; physicalouterkernel taper only'}
    comp=np.load(CAU/'composite_base.npy');states=[comp]
    for name in ('gran','achf','passalt24'):
        a=np.load(CAU/f'{name}_final.npy',mmap_mode='r');m=np.load(CAU/f'{name}_mask_final.npy',mmap_mode='r');m=np.round(m*65535)/65535
        comp=over(comp,a[...,None],m,cfg['layers'][name]['opacity_u8']/255,'overlay');states.append(comp)
    comp=np.clip(comp+np.load(CAU/'foreground_add.npy',mmap_mode='r'),0,1)
    np.save(CAU/'composite_delivery.npy',comp);savejson(CAU/'delivery_config.json',cfg);png(comp,'V29_COMPOST_llenc_sencer.png')
    for label,cx,cy,n in [('ghost',4879,2549,512),('arcs_SE',6078,4998,640),('arcs_NE',5743,2374,512),('limb',4900,3776,512),('outer_NW',3700,2400,512)]:
        sl=(slice(cy-n//2,cy+n//2),slice(cx-n//2,cx+n//2));Image.fromarray(np.round(comp[sl]*255).astype(np.uint8)).save(OUT/f'V29_1a1_{label}.png')
    n=512;sl=(slice(3520,4032),slice(4644,5156));panel=Image.new('RGB',(n*4,n+30));dr=ImageDraw.Draw(panel)
    for j,a in enumerate(states):
        panel.paste(Image.fromarray(np.round(np.clip(a[sl],0,1)*255).astype(np.uint8)),(j*n,30));dr.text((j*n+10,8),['base','+ azimutal','+ ACHF fi','+ passa-alt'][j],fill='white')
    panel.save(OUT/'V29_QA_limb_acumulat_1a1.png');log('delivery preview ready')

if __name__=='__main__':main()
