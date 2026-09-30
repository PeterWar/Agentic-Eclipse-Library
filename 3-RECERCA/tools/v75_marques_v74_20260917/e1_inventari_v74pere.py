"""E1: la V74 re-desada per Pere (17-09 vespre): (a) què ha canviat respecte de V71 i de la meva V74 (hash per canal; arrays de la ROI amb tolerància ±1 DN16 pel re-desat de Photoshop), (b) la capa de marques nova (222): components, colors, posició, (c) ROI del compost i de les capes → roi74p_L{id}.npz, índex v74pere_index_psb69.json."""
import sys, json, hashlib, numpy as np, time
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
sys.path.insert(0,NEW)
from psb69 import PSB
from scipy.ndimage import label, find_objects, binary_dilation
ROI=(4377,2777,6377,4777); x0,y0,x1,y1=ROI; CX,CY=5375.88,3775.41
p74=PSB('/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V74.psb'); p71=PSB('/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V71.psb')
json.dump({'layers':p74.layers,'width':p74.width,'height':p74.height},open(S4+'/v74pere_index_psb69.json','w'),default=str)
def h(path,off,n):
    hh=hashlib.sha256()
    with open(path,'rb') as f:
        f.seek(off); rem=n
        while rem>0: b=f.read(min(rem,64<<20)); hh.update(b); rem-=len(b)
    return hh.hexdigest()
meves={lid:['c0','c1','c2'] for lid in (3,41,42,45,46,47,49,51,53,55,56)}   # 57 esborrada per Pere
l71={l['id']:l for l in p71.layers}; rep=[]
for L in p74.layers:
    lid=L['id']; r=dict(id=lid,nom=L['name'],visible=L['visible'],op=L['opacity'],blend=L['blend'],bbox=[L['left'],L['top'],L['right'],L['bottom']])
    if lid in l71:
        a=l71[lid]; r['op_v71']=a['opacity']; r['vis_v71']=a['visible']; r['bbox_v71']=[a['left'],a['top'],a['right'],a['bottom']]; canv=[]
        for cid,(off,n) in L['chans'].items():
            key=f'c{cid}'
            if cid not in a['chans']: canv.append(f'{key}:nou'); continue
            offa,na=a['chans'][cid]
            if na==n and h(p71.path,offa,na)==h(p74.path,off,n): continue
            full,org=p74.channel(lid,cid); ox,oy=org; hh,ww=full.shape; xa,ya=max(x0,ox),max(y0,oy); xb,yb=min(x1,ox+ww),min(y1,oy+hh)
            ref=None
            if lid in meves and key in meves[lid]: ref=np.load(S4+f'/roi74_L{lid}.npz')[key][ya-y0:yb-y0,xa-x0:xb-x0]; nomref='meva V74'
            else:
                f71,o71=p71.channel(lid,cid)
                if f71.shape==full.shape and o71==org: ref=f71[ya-oy:yb-oy,xa-ox:xb-ox]; nomref='V71'
            if ref is None: canv.append(f'{key}:≠ V71 (forma/origen diferent: {org} {full.shape})'); continue
            d=np.abs(full[ya-oy:yb-oy,xa-ox:xb-ox].astype(np.int32)-ref.astype(np.int32)); big=(d>2)
            # fora de la ROI: compara amb V71 si mateixa forma
            fora=''
            if lid in meves:
                f71,o71=p71.channel(lid,cid)
                if f71.shape==full.shape and o71==org:
                    m=np.ones(full.shape,bool); m[ya-oy:yb-oy,xa-ox:xb-ox]=False; dd=np.abs(full.astype(np.int32)-f71.astype(np.int32))[m]; fora=f' fora ROI vs V71: màx {int(dd.max())} DN16, >2: {int((dd>2).sum())} px'
            if big.sum()==0: canv.append(f'{key}:= {nomref} (±{int(d.max())} DN16, re-desat){fora}')
            else:
                yy,xx=np.nonzero(big); canv.append(f'{key}:≠ {nomref} (PERE): {int(big.sum())} px >2 DN16, màx {int(d.max())}, caixa x {int(xx.min()+xa)}–{int(xx.max()+xa)} y {int(yy.min()+ya)}–{int(yy.max()+ya)}, r {np.hypot(xx.mean()+xa-CX,yy.mean()+ya-CY):.0f} az {np.rad2deg(np.arctan2(-(yy.mean()+ya-CY),xx.mean()+xa-CX))%360:.0f}{fora}')
        r['canals']=canv
    else: r['nova']=True
    rep.append(r); flag=' *' if (lid not in l71 or r.get('canals') or r.get('op_v71')!=r['op'] or r.get('vis_v71')!=r['visible']) else ''
    print(f"id {lid:>3} {'V' if L['visible'] else '-'} op {L['opacity']:3d} {L['blend']:12s} {L['name'][:44]:44s} {r.get('canals','NOVA')}{flag}",flush=True)
print('capes de V71 que ja no hi són:',[lid for lid in l71 if lid not in {L['id'] for L in p74.layers}])
json.dump(rep,open(S4+'/e1_canvis_pere_v74.json','w'),indent=1,ensure_ascii=False)
# (b) capa de marques 222
L=p74.layer(222); A,_=p74.channel(222,-1); R,_=p74.channel(222,0); G,_=p74.channel(222,1); B,_=p74.channel(222,2); xo,yo=L['left'],L['top']
np.savez_compressed(S4+'/marques_222.npz',A=A,R=R,G=G,B=B,x0=xo,y0=yo)
sel=A>0; lab,n=label(binary_dilation(sel,iterations=3)); rows=[]
for j,sl in enumerate(find_objects(lab),1):
    k=(lab[sl]==j)&sel[sl]
    if k.sum()<4: continue
    yy,xx=np.nonzero(k); yy=yy+sl[0].start; xx=xx+sl[1].start; rgb=np.stack([R[yy,xx],G[yy,xx],B[yy,xx]],1).astype(float); med=np.median(rgb,0); a=A[yy,xx].astype(float)/65535
    rows.append(dict(id=len(rows)+1,n=int(len(xx)),alfa_mitjana=round(float(a.mean()),3),bbox=[int(xx.min()+xo),int(yy.min()+yo),int(xx.max()+xo+1),int(yy.max()+yo+1)],centre=[round(float(xx.mean()+xo),1),round(float(yy.mean()+yo),1)],rgb8=[int(v/257) for v in med],r_lluna=round(float(np.hypot(xx.mean()+xo-CX,yy.mean()+yo-CY)),0),az=round(float(np.rad2deg(np.arctan2(-(yy.mean()+yo-CY),xx.mean()+xo-CX))%360),0),r_min=round(float(np.hypot(xx+xo-CX,yy+yo-CY).min()),0),r_max=round(float(np.hypot(xx+xo-CX,yy+yo-CY).max()),0)))
print(f'\ncapa 222 «{L["name"]}»: {len(rows)} components, alfa>0: {int(sel.sum())} px')
for r in rows: print('  ',r)
json.dump(rows,open(S4+'/e1_marques_222.json','w'),indent=1,ensure_ascii=False)
# (c) ROI del compost i capes
t=time.time(); C=p74.composite(); np.savez_compressed(S4+'/roi74p_compost.npz',C=C[y0:y1,x0:x1]); np.savez_compressed(S4+'/compost74p_x6.npz',C=C[::6,::6,:3].copy()); del C
for L in p74.layers:
    if not L['visible'] and L['id']!=62: continue
    d={}
    for cid in L['chans']:
        a=p74.channel_box(L['id'],cid,ROI,fill=(L['mask']['background']*257 if (cid==-2 and L['mask']) else 0))
        if a is not None: d['c%d'%cid]=a
    np.savez_compressed(S4+f"/roi74p_L{L['id']}.npz",**d)
print('ROI extreta (%.0fs)'%(time.time()-t))
