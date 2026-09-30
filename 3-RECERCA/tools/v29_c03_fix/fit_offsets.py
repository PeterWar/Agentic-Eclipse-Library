"""Global additive native-channel offsets; independent angular validation.

No spatial correction, tone fit, selection from marks, or support mutation.
"""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
D=Path(__file__).parent

def main():
    out={'model':'one additive constant per native channel and frame, before existing HDR weights; original gain/k unchanged','fit':'alternate angular sectors; common unsaturated plateau, r1.08-4.5R','validation':'other angular sectors, not used to fit','groups':{}}
    for tag in ['vixen','sony']:
        meta=json.loads((D/f'{tag}_sample_meta.json').read_text());frames=meta['frames'];a=np.load(D/f'{tag}_samples.npy',mmap_mode='r');w=np.load(D/f'{tag}_confidence.npy',mmap_mode='r')
        yy,xx=np.meshgrid(meta['ys'],meta['xs'],indexing='ij');dx=xx-5361.768112;dy=yy-3775.747534;r=np.hypot(dx,dy)/440.60304883;ang=np.mod(np.arctan2(dy,dx),2*np.pi)
        sectors=np.floor(ang*16/(2*np.pi)).astype(int);phase=np.mod(ang,2*np.pi/16)
        safe=(r>1.08)&(r<4.5)&(phase>.035)&(phase<2*np.pi/16-.035)
        train=safe&(sectors%2==0);test=safe&(sectors%2==1)
        groups=[('vixen',list(range(len(frames))),'572A2979.CR3')] if tag=='vixen' else [('sony_A',[i for i,f in enumerate(frames) if int(f['name'][3:8])<=6987],'DSC06984.ARW'),('sony_B',[i for i,f in enumerate(frames) if int(f['name'][3:8])>=6991],'DSC06996.ARW')]
        for group,inds,anchorname in groups:
            anchor=next(i for i in inds if frames[i]['name']==anchorname);rep={'anchor':anchorname,'offsets':{},'edges':[]};allb=np.zeros((len(frames),3))
            for c in range(3):
                edges=[]
                for ix,i in enumerate(inds):
                    ai=np.asarray(a[i,...,c]);wi=np.asarray(w[i,...,c])
                    for j in inds[ix+1:]:
                        ei=frames[i]['exposure'];ej=frames[j]['exposure']
                        if max(ei,ej)/min(ei,ej)>8.01:continue
                        aj=np.asarray(a[j,...,c]);good=(wi>.995)&(w[j,...,c]>.995)&(ai>0)&(aj>0)
                        mt=good&train;mv=good&test
                        if mt.sum()<35 or mv.sum()<35:continue
                        diff=(ai[mt]-aj[mt]).astype(float);delta=float(np.median(diff));level=float(np.median((ai[mt]+aj[mt])/2));mad=1.4826*np.median(np.abs(diff-delta))
                        err=max(.003*level,mad/np.sqrt(len(diff)),.1)
                        edges.append((i,j,delta,err,good,level))
                connected={anchor}
                for _ in inds:
                    for i,j,*_ in edges:
                        if i in connected or j in connected:connected.update([i,j])
                unknown=sorted(connected-{anchor});lookup={j:i for i,j in enumerate(unknown)}
                es=[e for e in edges if e[0] in connected and e[1] in connected];A=np.zeros((len(es),len(unknown)));y=[]
                for k,(i,j,delta,err,good,level) in enumerate(es):
                    if i!=anchor:A[k,lookup[i]]=1/err
                    if j!=anchor:A[k,lookup[j]]=-1/err
                    y.append(-delta/err)
                y=np.array(y);initial=np.linalg.lstsq(A,y,rcond=None)[0]
                b=least_squares(lambda z:A@z-y,initial,jac=lambda z:A.copy(),loss='soft_l1',f_scale=1,ftol=1e-10,xtol=1e-10,gtol=1e-10).x
                for i,val in zip(unknown,b):allb[i,c]=val
                for i,j,delta,err,good,level in es:
                    mv=good&test;ai=a[i,...,c][mv].astype(float);aj=a[j,...,c][mv].astype(float);base=(ai+aj)/2;before=(ai-aj)/base;after=(ai+allb[i,c]-aj-allb[j,c])/base
                    rep['edges'].append({'channel':c,'i':frames[i]['name'],'j':frames[j]['name'],'heldout_samples':int(mv.sum()),'before_median_relative':float(np.median(before)),'after_median_relative':float(np.median(after)),'before_robust_scatter':float(1.4826*np.median(np.abs(before-np.median(before)))),'after_rms_relative':float(np.sqrt(np.mean(after**2))),'train_difference':delta,'level':level})
                rep.setdefault('unconnected',{})[str(c)]=[frames[i]['name'] for i in inds if i not in connected]
            for i in inds:rep['offsets'][frames[i]['name']]=allb[i].tolist()
            out['groups'][group]=rep
            print(group,'offsets',rep['offsets'],flush=True)
    (D/'offset_model.json').write_text(json.dumps(out,indent=2)+'\n')
    for g,d in out['groups'].items():
        focus=[x for x in d['edges'] if (x['i'].endswith(('2982.CR3','2983.CR3','2984.CR3','6993.ARW','6987.ARW')) or x['j'].endswith(('2982.CR3','2983.CR3','2984.CR3','6993.ARW','6987.ARW')))]
        print(g,'long exposures: median absolute heldout pair bias before/after',np.median([abs(x['before_median_relative']) for x in focus]),np.median([abs(x['after_median_relative']) for x in focus]),flush=True)
if __name__=='__main__':main()
