from common58 import *
from PIL import Image,ImageDraw
claim();ang=np.arange(0,360,15);rad=np.arange(440,475,.25);xx=999.5681+rad[:,None]*np.cos(np.deg2rad(ang));yy=999.6475+rad[:,None]*np.sin(np.deg2rad(ang));rep={}
for i in [0,1,9,10,29]:
 rep[str(i)]={}
 for c in [1,-2]:
  a=roi(i,c).astype(float)/65535;v=map_coordinates(a,[yy,xx],order=1);rep[str(i)][str(c)]=v.tolist()
can=Image.new('RGB',(1800,900),(25,25,25));draw=ImageDraw.Draw(can)
for k,theta in enumerate(ang):
 ox=(k%6)*300;oy=(k//6)*225;draw.text((ox+8,oy+4),str(theta)+' deg; 440..475px',fill='white')
 for idx,col in [(0,'red'),(1,'yellow'),(9,'cyan'),(29,'green')]:
  v=np.array(rep[str(idx)]['1'])[:,k];draw.line([(ox+(r-440)*8,oy+210-y*180) for r,y in zip(rad,v)],fill=col,width=1)
can.save(O/'vistes/B4_limb_profiles.png');save('B4_limb_profiles.json',dict(rad=rad,angles=ang,profiles=rep))
