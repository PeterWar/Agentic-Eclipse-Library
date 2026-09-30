"""B1: la V71 desada per Pere: (a) què ha canviat respecte de V69 i de la meva V71 (hash per canal), (b) les dues capes de marques (219, 220): components, colors, posició, (c) ROI del compost i de les capes."""
import sys, json, hashlib, numpy as np, time
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
sys.path.insert(0,NEW)
from psb69 import PSB
from scipy.ndimage import label, find_objects, binary_dilation
ROI=(4377,2777,6377,4777); x0,y0,x1,y1=ROI
p71=PSB('/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V71.psb'); p69=PSB('/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V69.psb')
def h(path,off,n):
    hh=hashlib.sha256()
    with open(path,'rb') as f:
        f.seek(off); rem=n
        while rem>0: b=f.read(min(rem,64<<20)); hh.update(b); rem-=len(b)
    return hh.hexdigest()
# (a) canvis per capa respecte de V69 (bytes) i respecte de la meva intenció V71 (arrays ROI)
meves={3:['c-2'],30:['c0','c1','c2','c-2'],41:['c-2'],42:['c-2'],45:['c-2'],46:['c-2'],47:['c0','c1','c2'],49:['c0','c1','c2'],51:['c0','c1','c2'],53:['c0','c1','c2'],55:['c0','c1','c2'],56:['c0','c1','c2']}
fonts={3:OLD+'/roi_L3_v71.npz',30:OLD+'/roi_L30_v71.npz',41:OLD+'/roi_L41_v70.npz',42:OLD+'/roi_L42_v70.npz',45:OLD+'/roi_L45_v70.npz',46:OLD+'/roi_L46_v70.npz',47:OLD+'/roi_L47_v70.npz',49:OLD+'/roi_L49_v70.npz',51:OLD+'/roi_L51_v70.npz',53:OLD+'/roi_L53_v70.npz',55:OLD+'/roi_L55_v70.npz',56:OLD+'/roi_L56_v70.npz'}
l69={l['id']:l for l in p69.layers}; rep=[]
for L in p71.layers:
    lid=L['id']; r=dict(id=lid,nom=L['name'],visible=L['visible'],op=L['opacity'],blend=L['blend'],bbox=[L['left'],L['top'],L['right'],L['bottom']])
    if lid in l69:
        a=l69[lid]; r['op_v69']=a['opacity']; r['vis_v69']=a['visible']; r['blend_v69']=a['blend']; r['bbox_v69']=[a['left'],a['top'],a['right'],a['bottom']]
        canv=[]
        for cid,(off,n) in L['chans'].items():
            if cid not in a['chans']: canv.append(f'c{cid}:nou'); continue
            offa,na=a['chans'][cid]
            if na==n and h(p69.path,offa,na)==h(p71.path,off,n): continue
            # difereix de V69: és la meva intenció?
            key=f'c{cid}'
            if lid in meves and key in meves[lid]:
                full,org=p71.channel(lid,cid); v=np.load(fonts[lid])[key]; ox,oy=org; hh,ww=full.shape; xa,ya=max(x0,ox),max(y0,oy); xb,yb=min(x1,ox+ww),min(y1,oy+hh)
                same=np.array_equal(full[ya-oy:yb-oy,xa-ox:xb-ox],v[ya-y0:yb-y0,xa-x0:xb-x0]); canv.append(f'{key}:{"= meva V71" if same else "≠ meva V71 (Pere)"}')
            else: canv.append(f'{key}:≠ V69 (Pere)')
        r['canals']=canv
    else: r['nou']=True
    rep.append(r); flag=' *' if (lid not in l69 or r.get('canals') or r.get('op_v69')!=r['op'] or r.get('vis_v69')!=r['visible']) else ''
    print(f"id {lid:>3} {'V' if L['visible'] else '-'} op {L['opacity']:3d}{('/'+str(r.get('op_v69'))) if lid in l69 and r.get('op_v69')!=L['opacity'] else ''} {L['blend']:12s} {L['name'][:50]:50s} {r.get('canals','NOVA')}{flag}")
json.dump(rep,open(NEW+'/b1_canvis_pere.json','w'),indent=1,ensure_ascii=False)
# (b) capes de marques
marks={}
for lid in (219,220):
    L=p71.layer(lid); A,_=p71.channel(lid,-1); R,_=p71.channel(lid,0); G,_=p71.channel(lid,1); B,_=p71.channel(lid,2); xo,yo=L['left'],L['top']
    np.savez_compressed(NEW+f'/marques_{lid}.npz',A=A,R=R,G=G,B=B,x0=xo,y0=yo)
    sel=A>0; lab,n=label(binary_dilation(sel,iterations=3)); rows=[]
    for j,sl in enumerate(find_objects(lab),1):
        k=(lab[sl]==j)&sel[sl]
        if k.sum()<4: continue
        yy,xx=np.nonzero(k); yy=yy+sl[0].start; xx=xx+sl[1].start; rgb=np.stack([R[yy,xx],G[yy,xx],B[yy,xx]],1).astype(float); med=np.median(rgb,0); a=A[yy,xx].astype(float)/65535
        rows.append(dict(id=len(rows)+1,capa=lid,n=int(len(xx)),alfa_mitjana=round(float(a.mean()),3),bbox=[int(xx.min()+xo),int(yy.min()+yo),int(xx.max()+xo+1),int(yy.max()+yo+1)],centre=[round(float(xx.mean()+xo),1),round(float(yy.mean()+yo),1)],rgb8=[int(v/257) for v in med],r_lluna=round(float(np.hypot(xx.mean()+xo-5375.88,yy.mean()+yo-3775.41)),0),az=round(float(np.rad2deg(np.arctan2(-(yy.mean()+yo-3775.41),xx.mean()+xo-5375.88))%360),0)))
    marks[lid]=rows; print(f'\ncapa {lid} «{L["name"]}»: {len(rows)} components, alfa>0: {int(sel.sum())} px')
    for r in rows: print('  ',r)
json.dump(marks,open(NEW+'/b1_marques.json','w'),indent=1,ensure_ascii=False)
# (c) ROI del compost i capes
t=time.time(); C=p71.composite(); np.savez_compressed(NEW+'/roi71_compost.npz',C=C[y0:y1,x0:x1]); np.savez_compressed(NEW+'/compost71_x6.npz',C=C[::6,::6,:3].copy()); del C
for L in p71.layers:
    if not L['visible'] and L['id']!=62: continue
    d={}
    for cid in L['chans']:
        a=p71.channel_box(L['id'],cid,ROI,fill=(L['mask']['background']*257 if (cid==-2 and L['mask']) else 0))
        if a is not None: d['c%d'%cid]=a
    np.savez_compressed(NEW+f"/roi71_L{L['id']}.npz",**d)
print('ROI extreta (%.0fs)'%(time.time()-t))
