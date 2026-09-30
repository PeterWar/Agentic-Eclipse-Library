from filters58 import *
claim();C=O/'filters';S=O/'sources';radii=np.linspace(1.15,1.8,70).astype('float32');ref=np.load(S/'fusion_starless.npy',mmap_mode='r')[...,1];sony=np.load(S/'sony_starless.npy',mmap_mode='r')[...,1];Rpol=polar(np.log(np.maximum(ref,1e-6)),CX,CY,RS,radii);Spol=polar(np.log(np.maximum(sony,1e-6)),CX,CY,RS,radii);rep={};from PIL import Image,ImageDraw
for idx,tag in [(15,'P02c_RHEF_local60_fixed'),(16,'P02d_RHEF_local30_fixed')]:
 a=np.load(C/f'{tag}_u16.npy',mmap_mode='r');P=polar(a.astype('float32')/65535,CX,CY,RS,radii);old=roi(idx).astype('float32')/65535;op=polar(old,CX-ROI[0],CY-ROI[1],RS,radii);rep[tag]=dict(alignment=correlate(P,Rpol),old_independent_sony=correlate(op,Spol),independent_sony=correlate(P,Spol));print(tag,rep[tag],flush=True)
 # Native filter raster around lunar limb: compare without altering scale/contrast.
 new=np.asarray(a[2777:4777,4377:6377],np.float32)/65535;can=Image.new('RGB',(2000,1000))
 for i,img in enumerate([old,new]):can.paste(Image.fromarray(np.uint8(np.clip(img[500:1500,500:1500],0,1)*255)),(i*1000,0))
 ImageDraw.Draw(can).text((10,10),'V57',fill='red');ImageDraw.Draw(can).text((1010,10),'V58 fixed radius',fill='red');can.save(O/'vistes'/f'F1_{tag}_limb_compare.png')
 # Composite of accepted base/moon and this filter at 35% multiply, with physical lunar mask.
 base=roi(9).astype('float32')/65535;moon=roi(29).astype('float32')/65535;ma=roi(29,-2).astype('float32')/65535;bm=roi(9,-2).astype('float32')/65535;fm=(1-ma)*np.load(C/f'{tag}_support.npy',mmap_mode='r')[2777:4777,4377:6377];blend=base*(1-.35*fm*(1-new));out=moon*ma+blend*(1-ma);Image.fromarray(np.uint8(np.clip(out[300:1700,300:1700],0,1)*255)).save(O/'vistes'/f'F1_{tag}_composite_1a1.png')
save('F1_local_qa.json',rep)
