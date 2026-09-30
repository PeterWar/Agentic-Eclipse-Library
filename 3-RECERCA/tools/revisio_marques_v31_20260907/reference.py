"""Render matching unpainted original layers and mark/reference comparison atlases."""
from extract import *
def main():
    rep=json.loads(Path(RUN.rebut('marks_inventory.json')).read_text());assert 'source_sha256' in rep
    src=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_FiltresPurs.psb')
    s=PSDImage.open(src);byname={l.name:l for l in s};out=[]
    for row in rep['layers']:
        i=row['index'];l=byname[row['name']]
        if i==0:rgb=np.stack([channel(l,c) for c in [0,1,2]],axis=2);u=(rgb//257).astype('uint8');del rgb
        else:
            u=(channel(l,1)//257).astype('uint8');np.save(D/f'{i:02d}_original_G8.npy',u)
        alpha=channel(l,-1);mask=channel(l,-2)
        w=np.ones((s.height,s.width),np.float32)
        if alpha is not None:w*=alpha/65535
        if mask is not None:w*=mask/65535
        disp=np.round(u*w[...,None]+127*(1-w[...,None])).astype('uint8') if i==0 else np.round(u*w+127*(1-w)).astype('uint8')
        im=Image.fromarray(disp);im.thumbnail((1600,1600),Image.Resampling.LANCZOS);im.save(RUN.vista(f'L{i:02d}_original_sencera.png'))
        codes=np.load(D/f'{i:02d}_mark_codes.npy',mmap_mode='r');panels=[];pairs=[]
        for m in row['marks']:
            x0,y0,x1,y1=m['window_bbox'];clean=disp[y0:y1,x0:x1];marked=np.load(D/'windows'/(m['id']+'_marked.npy'))
            np.save(D/'windows'/(m['id']+'_original.npy'),clean)
            # Cosmetic stroke outlines are excluded only from the correspondence check.
            cm=np.asarray(codes[y0:y1,x0:x1])>0
            cm=cv2.dilate(cm.astype('uint8'),np.ones((13,13),np.uint8))>0
            z=np.median(marked.astype('int16'),axis=2);v=clean if clean.ndim==2 else np.median(clean,axis=2)
            dd=np.abs(z-v);valid=(~cm)&(w[y0:y1,x0:x1]>.999)
            stats={'id':m['id'],'unpainted_observed_samples':int(valid.sum()),
                'fraction_within_2_DN8':float(np.mean(dd[valid]<=2)) if valid.any() else None,
                'median_abs_DN8':float(np.median(dd[valid])) if valid.any() else None}
            pairs.append(stats)
            p=Image.new('RGB',(1060,568),(24,24,24));d=ImageDraw.Draw(p)
            d.text((8,5),f"{m['id']} | {row['name']} | r={m['radius_R']:.2f}R",font=font(15),fill='white')
            for j,(a,label) in enumerate([(marked,'Marcat per Pere'),(clean,'Original sense pintura; suport sobre gris')]):
                patch=Image.fromarray(a).convert('RGB');patch.thumbnail((520,510),Image.Resampling.LANCZOS)
                p.paste(patch,(j*530+(530-patch.width)//2,52));d.text((j*530+8,29),label,font=font(13),fill='#cccccc')
            panels.append(p)
        for k in range(0,len(panels),4):
            sub=panels[k:k+4];sheet=Image.new('RGB',(2120,568*((len(sub)+1)//2)),(24,24,24))
            for t,p in enumerate(sub):sheet.paste(p,((t%2)*1060,(t//2)*568))
            sheet.save(RUN.vista(f'L{i:02d}_comparacio_{k//4+1:02d}.png'))
        out.append({'index':i,'name':row['name'],'reference_bbox':list(l.bbox),'reference_mask_present':mask is not None,'pairs':pairs})
        write(RUN.rebut('reference_comparison.json'),{'original':str(src),'layers':out,'method':'original G8 or RGB8; alpha and layer mask composited over gray127; no inpainting; marked crops from annotation PSB'})
        print('REFERENCE',i,row['name'],len(pairs),flush=True);del disp,u,w,alpha,mask;gc.collect()
    print('REFERENCE COMPLETE',flush=True)
if __name__=='__main__':main()
