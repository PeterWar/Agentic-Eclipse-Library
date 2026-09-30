import numpy as np, itertools, json
FR=['572A2978','572A2979','572A2980','572A2981','572A2982','572A2983','572A2984','572A2996']
C={f:np.load('cat_%s.npy'%f) for f in FR}
for f in FR:
    a=C[f]; print(f,'n=%d  peak p50=%.2f p99=%.2f max=%.2f'%(len(a),np.percentile(a[:,2],50),np.percentile(a[:,2],99),a[:,2].max()))
def top(f,n=6000,pmin=4.5):
    a=C[f]; a=a[a[:,2]>=pmin]
    o=np.argsort(-a[:,2])[:n]; return a[o]
REF='572A2982'
R=top(REF)
print('ref n',len(R))
res={}
for f in FR:
    T=top(f)
    dx=(T[:,0][None,:]-R[:,0][:,None]).ravel()
    dy=(T[:,1][None,:]-R[:,1][:,None]).ravel()
    k=(np.abs(dx)<45)&(np.abs(dy)<45)
    dx=dx[k]; dy=dy[k]
    Hh,xe,ye=np.histogram2d(dx,dy,bins=[np.arange(-45,46,1),np.arange(-45,46,1)])
    i,j=np.unravel_index(np.argmax(Hh),Hh.shape)
    # refine with 3x3 centroid
    sl=Hh[max(0,i-2):i+3,max(0,j-2):j+3]
    xs=xe[max(0,i-2):i+3]+0.5; ys=ye[max(0,j-2):j+3]+0.5
    wx=(sl.sum(1)*xs).sum()/sl.sum(); wy=(sl.sum(0)*ys).sum()/sl.sum()
    med=np.median(Hh); mad=np.median(np.abs(Hh-med))*1.4826
    print('%s  peak=%d at dx=%.1f dy=%.1f  refined (%.2f,%.2f)  bg=%.1f sig=%.1f  signif=%.1f'%(
        f,Hh.max(),xe[i]+0.5,ye[j]+0.5,wx,wy,med,mad,(Hh.max()-med)/max(mad,1)))
    res[f]=[float(wx),float(wy)]
json.dump(res,open('shifts0.json','w'))
