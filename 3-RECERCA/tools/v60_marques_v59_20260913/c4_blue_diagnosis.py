from composite60 import *
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw
claim();items=[]
for n in ['fusion','vixen','sony']:
 a=np.load(PREV/'sources'/f'{n}_starless.npy',mmap_mode='r')[2777:4777,4377:6377,1].astype(float);items.append((n,np.log(np.maximum(np.nan_to_num(a),1e-10))))
items.append(('base RGB',np.log(np.maximum(read(9,1),1e-10))))
for i in [11,12,13,14,17,19,21,22,23,26]:items.append((str(i)+' '+rows[i]['name'][:28],read(i,1)))
can=Image.new('RGB',(210*7,320*2),(25,25,25));d=ImageDraw.Draw(can);xy=np.load(O/'arrays/mark_blau_1_xy.npy');rep={}
for k,(n,a) in enumerate(items):
 residual=a-gaussian_filter(a,5);b=residual[3500-2777:3770-2777,4850-4377:5060-4377];v=np.quantile(abs(b),.99);im=Image.fromarray(np.uint8(np.clip(.5+.45*b/max(v,1e-10),0,1)*255)).convert('RGB');can.paste(im,((k%7)*210,(k//7)*320+40));d.text(((k%7)*210+2,(k//7)*320+3),n,fill='white');rep[n]={'contrast_scale':float(v)}
can.save(O/'vistes/C4_blue_source_channels.png');save('C4_blue_diagnosis.json',rep);print('BLUE CHANNELS')
