"""Read annotated PSB, inventory color strokes and render all layers; never save PSD."""
from pathlib import Path
import sys,json,hashlib,gc,time,zlib
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
from psd_tools import PSDImage
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'research/tools/v29'));from inspect_inputs import channel as slow_channel,sha
sys.path.insert(0,str(ROOT/'research/tools/eclipse_determinista'));from comu import Run
RUN=Run('REVISIO_MARQUES_V31','20260907',str(ROOT/'output/revisio_marques_v31_20260907'))
for p in [RUN.vista(''),RUN.lliurable(''),RUN.rebut(''),D/'windows']:Path(p).mkdir(parents=True,exist_ok=True)
CX,CY,RS=5361.768111973117,3775.747534140857,440.60304883027544
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
cv2.setNumThreads(2)
def channel(l,cid):
    w,h=l.size
    if cid==-2:
        m=l._record.mask_data;w,h=m.right-m.left,m.bottom-m.top
    for ci,cd in zip(l._record.channel_info,l._channels):
        if int(ci.id)!=cid:continue
        if int(cd.compression)==3 and l._psd.depth==16:
            delta=np.frombuffer(zlib.decompress(cd.data),'>u2').reshape(h,w)
            return np.cumsum(delta,axis=1,dtype=np.uint16)
        return slow_channel(l,cid)
    return None
def font(n):return ImageFont.truetype(FONT,n)
def write(p,j):Path(p).write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
def main():
    src=D/'input_anotat.psb';s=PSDImage.open(src);rep={'path':str(src),'size':list(s.size),'depth':s.depth,'layers':[]}
    contact=Image.new('RGB',(4*480,5*384),(28,28,28));draw=ImageDraw.Draw(contact)
    for i,l in enumerate(s):
        rgb=np.stack([channel(l,c) for c in (0,1,2)],axis=2)
        u=(rgb//257).astype('uint8');del rgb
        hsv=cv2.cvtColor(u,cv2.COLOR_RGB2HSV);h,sat,val=(hsv[...,c] for c in range(3))
        vivid=(sat>25)&(val>20)
        # Base is genuinely colored. Color alone cannot identify painted marks;
        # reviewed separately against the unmarked base instead of calling corona paint.
        if i==0:vivid[:]=False
        colors={'groc':(h>=20)&(h<40),'verd':(h>=40)&(h<95),'blau':(h>=95)&(h<125),'lila':(h>=125)&(h<175)}
        codes=np.zeros(u.shape[:2],np.uint8);marks=[]
        for code,(name,hh) in enumerate(colors.items(),1):
            candidate=(vivid&hh).astype('uint8')
            # Join close brush fragments solely for indexing, never product masking.
            joined=cv2.morphologyEx(candidate,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
            n,lab,stats,cent=cv2.connectedComponentsWithStats(joined,8)
            for k in range(1,n):
                x,y,w,hh,area=map(int,stats[k])
                if area<80:continue
                local=(lab[y:y+hh,x:x+w]==k)&(candidate[y:y+hh,x:x+w]>0)
                count=int(local.sum())
                if count<60:continue
                codes[y:y+hh,x:x+w][local]=code
                cx,cy=map(float,cent[k]);ident=f'L{i:02d}-{name}-{len(marks)+1:02d}'
                marks.append({'id':ident,'color':name,'certainty_by_Pere':'dubtos' if name=='verd' else 'confirmat',
                    'bbox':[x,y,x+w,y+hh],'center_xy':[cx,cy],'radius_R':float(np.hypot(cx-CX,cy-CY)/RS),
                    'azimuth_image_deg':float(np.degrees(np.arctan2(cy-CY,cx-CX))), 'paint_pixels':count})
            del lab,joined,candidate
        del hsv,h,sat,val,colors,vivid
        np.save(D/f'{i:02d}_mark_codes.npy',codes)
        im=Image.fromarray(u);im.thumbnail((1600,1600),Image.Resampling.LANCZOS)
        full=Path(RUN.vista(f'L{i:02d}_anotada_sencera.png'));im.save(full)
        sm=im.copy();sm.thumbnail((480,342),Image.Resampling.LANCZOS);xx=(i%4)*480;yy=(i//4)*384
        contact.paste(sm,(xx,yy+42));draw.text((xx+6,yy+5),f'{i:02d} {l.name[:49]}',fill='white',font=font(14))
        draw.text((xx+6,yy+24),f'{len(marks)} components de pinzell',fill='#cccccc',font=font(12))
        # Per-layer detail atlas: bounding window preserves whole mark when feasible;
        # 1:1 native crops separately retained before diagnostic downscale.
        if marks:
            panels=[]
            for mark in marks:
                x0,y0,x1,y1=mark['bbox'];pad=40
                x0=max(0,x0-pad);y0=max(0,y0-pad);x1=min(u.shape[1],x1+pad);y1=min(u.shape[0],y1+pad)
                mark['window_bbox']=[x0,y0,x1,y1]
                np.save(D/'windows'/(mark['id']+'_marked.npy'),u[y0:y1,x0:x1])
                patch=Image.fromarray(u[y0:y1,x0:x1]);patch.thumbnail((510,510),Image.Resampling.LANCZOS)
                p=Image.new('RGB',(530,560),(24,24,24));p.paste(patch,((530-patch.width)//2,44))
                dd=ImageDraw.Draw(p);dd.text((8,5),f"{mark['id']} | r={mark['radius_R']:.2f} R",fill='white',font=font(15))
                dd.text((8,25),f'{x1-x0}x{y1-y0} px originals',fill='#bbbbbb',font=font(12));panels.append(p)
            for start in range(0,len(panels),8):
                sub=panels[start:start+8];sheet=Image.new('RGB',(4*530,((len(sub)+3)//4)*560),(24,24,24))
                for k,p in enumerate(sub):sheet.paste(p,((k%4)*530,(k//4)*560))
                sheet.save(RUN.vista(f'L{i:02d}_marques_{start//8+1:02d}.png'))
        row={'index':i,'name':l.name,'visible':l.visible,'opacity':l.opacity,'blend':str(l.blend_mode),'bbox':list(l.bbox),
            'marks':marks,'color_counts':{color:sum(m['color']==color for m in marks) for color in ['groc','blau','lila','verd']},
            'full_view':str(full)}
        rep['layers'].append(row);write(RUN.rebut('marks_inventory.json'),rep)
        print(i,l.name,row['color_counts'],flush=True);del u,codes,im;gc.collect()
    contact.save(RUN.vista('00_totes_les_capes_anotades.png'))
    rep['source_sha256']=sha(src);rep['source_original']='/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_FiltresPurs_Artefactes.psb'
    assert rep['source_sha256']==sha(rep['source_original'])
    rep['source_bytes']=src.stat().st_size
    rep['detection']='HSV color segmentation S>25,V>20 on monochrome filter layers; base excluded from color-only marking and reviewed separately; H yellow20..40,green40..95,blue95..125,purple125..175; 5px closing for index only; component>=80px, original paint>=60px; components are not necessarily separate defects'
    write(RUN.rebut('marks_inventory.json'),rep);print('COMPLETE',flush=True)
if __name__=='__main__':main()
