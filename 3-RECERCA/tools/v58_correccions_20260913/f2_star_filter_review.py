from common58 import *
from PIL import Image,ImageDraw
claim();F=O/'filters';sources=json.loads((O/'D4_sources.json').read_text());oldStars=json.loads((V42/'cau/estrelles_v42.json').read_text())['estrelles'];stars=[r['star'] for r in sources['selected'] if all(np.hypot(r['star']['x']-s['x'],r['star']['y']-s['y'])>12 for s in oldStars)];stars=stars[:12];names=['P01_NRGF','P01_NRGF_extrap','P02_RHEF','P02b_RHEF_ups0.35','P02c_RHEF_local60_native','P02d_RHEF_local30_native','03','03v30','07','01','04','05','06','P03_MGN','P04_WOW','P05_WOW_bilateral'];can=Image.new('RGB',(160+len(stars)*100,len(names)*118+30),(24,24,24));draw=ImageDraw.Draw(can);rep={}
for row,tag in enumerate(names):
 a=np.load(F/f'{tag}_u16.npy',mmap_mode='r');draw.text((3,row*118+35),tag[:24],fill='white');rrs=[]
 for col,s in enumerate(stars):
  x,y=int(s['x']),int(s['y']);q=np.array(a[y-24:y+25,x-24:x+25],float)/65535;yy,xx=np.mgrid[-24:25,-24:25];r=np.hypot(xx,yy);ann=(r>14)&(r<23);bg=np.median(q[ann]);sd=1.4826*np.median(np.abs(q[ann]-bg))+1e-8;z=(q-bg)/sd;tile=Image.fromarray(np.uint8(np.clip(.5+z/10,0,1)*255)).resize((98,98));can.paste(tile,(160+col*100,row*118+20));draw.text((160+col*100,row*118+4),str(col),fill='white');rrs.append(dict(x=x,y=y,star=s.get('TYC'),core_mean_sigma=float(z[r<5].mean()),core_max_sigma=float(z[r<5].max())))
 rep[tag]=rrs
can.save(O/'vistes/F2_stars_all_filters_1a1.png');save('F2_star_filter_review.json',dict(stars=stars,rows=rep,note='Native49x49 patches displayed2x, each standardized only for diagnostic display using its own14..23pxannulus. Includes12 stars newly removed beyond the previous21 list.'))
