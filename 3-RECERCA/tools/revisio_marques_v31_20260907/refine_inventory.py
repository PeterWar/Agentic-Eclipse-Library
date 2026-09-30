"""Refine brush color labels using measured hues; retain stable neutral mark IDs."""
from extract import *
def main():
    p=Path(RUN.rebut('marks_inventory.json'));rep=json.loads(p.read_text())
    if rep.get('color_refinement_complete'):return
    write(D/'inventory_before_color_refinement.json',rep)
    comparisons=json.loads(Path(RUN.rebut('reference_comparison.json')).read_text());mapping={}
    for row in rep['layers']:
        i=row['index'];codes=np.load(D/f'{i:02d}_mark_codes.npy')
        for n,m in enumerate(row['marks'],1):
            old=m['id'];new=f'L{i:02d}-M{n:02d}';mapping[old]=new
            marked=np.load(D/'windows'/(old+'_marked.npy'));hsv=cv2.cvtColor(marked,cv2.COLOR_RGB2HSV)
            x0,y0,x1,y1=m['window_bbox'];sub=codes[y0:y1,x0:x1]
            oldblue=(sub==3);sub[oldblue&(hsv[...,0]>=116)]=4
            a,b,c,d=m['bbox'];cut=codes[b:d,a:c]
            target={'groc':1,'verd':2,'blau':3,'lila':4}[m['color']]
            if target==3:
                nb=int(np.sum(cut==3));nl=int(np.sum(cut==4));m['color']='lila' if nl>nb else 'blau'
                m['color_parts']={'blau':nb,'lila':nl}
                target=4 if nl>nb else 3
            yy,xx=np.where((cut==target)|((cut==3)|(cut==4) if m.get('color_parts') else False))
            rad=np.hypot(xx+a-CX,yy+b-CY)/RS
            m['paint_radius_R_p05_p50_p95']=[float(t) for t in np.percentile(rad,[5,50,95])]
            m['centroid_radius_is_not_arc_radius']=True
            m['legacy_id']=old;m['id']=new
            for suffix in ['_marked.npy','_original.npy']:(D/'windows'/(old+suffix)).rename(D/'windows'/(new+suffix))
        np.save(D/f'{i:02d}_mark_codes.npy',codes)
        row['color_counts']={c:sum(m['color']==c for m in row['marks']) for c in ['groc','blau','lila','verd']}
    for row in comparisons['layers']:
        for pair in row['pairs']:pair['id']=mapping[pair['id']]
    rep['color_refinement_complete']=True
    rep['color_refinement']='Measured brush hue modes: yellow H30-31, green H66, blue H108-109, lilac H119-123. Blue/lilac boundary116; overlapping strokes retained as same component with color_parts, dominant hue label. Neutral IDs avoid encoding a provisional hue.'
    write(p,rep);write(RUN.rebut('reference_comparison.json'),comparisons)
    # Replace diagnostic atlas labels, preserving original native windows.
    for row in rep['layers']:
        i=row['index'];panels=[]
        for m in row['marks']:
            p=Image.new('RGB',(1060,568),(24,24,24));d=ImageDraw.Draw(p)
            rr=m['paint_radius_R_p05_p50_p95'];d.text((8,5),f"{m['id']} · {m['color']} · traç {rr[0]:.2f}–{rr[2]:.2f} R",font=font(16),fill='white')
            for j,(suffix,label) in enumerate([('_marked.npy','Marcat per Pere'),('_original.npy','Original sense pintura')]):
                a=np.load(D/'windows'/(m['id']+suffix));im=Image.fromarray(a).convert('RGB');im.thumbnail((520,510),Image.Resampling.LANCZOS)
                p.paste(im,(j*530+(530-im.width)//2,52));d.text((j*530+8,29),label,font=font(13),fill='#cccccc')
            panels.append(p)
        for k in range(0,len(panels),4):
            sub=panels[k:k+4];sheet=Image.new('RGB',(2120,568*((len(sub)+1)//2)),(24,24,24))
            for t,p in enumerate(sub):sheet.paste(p,((t%2)*1060,(t//2)*568))
            sheet.save(RUN.vista(f'L{i:02d}_comparacio_{k//4+1:02d}.png'))
        print(i,row['color_counts'],flush=True)
    # Old one-sided atlases used provisional hue/centroid labels; final pairs supersede them.
    hist=Path(RUN.vista('provisional_SUPERSEDED'));hist.mkdir(exist_ok=True)
    for p in Path(RUN.vista('')).glob('L*_marques_*.png'):p.rename(hist/p.name)
if __name__=='__main__':main()
