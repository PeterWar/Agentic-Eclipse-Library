import numpy as np, json
from scipy import ndimage as ndi
FR=[('572A2978',1.0),('572A2979',2.0),('572A2980',2.0),('572A2981',2.0),
    ('572A2982',10.3),('572A2983',10.3),('572A2984',10.3),('572A2996',1.0)]
SH=json.load(open('shifts_start.json'))
H,W=4638,6958
halves={'A':['572A2978','572A2980','572A2982','572A2984'],'B':['572A2979','572A2981','572A2983','572A2996']}
for hn,lst in halves.items():
    num=np.zeros((H,W),np.float32); den=np.zeros((H,W),np.float32)
    for f,exp in FR:
        if f not in lst: continue
        dt,dx,dy=SH[f]
        res=np.load('res_%s.npy'%f); sig=np.load('sig_%s.npy'%f); msk=np.load('msk_%s.npy'%f)
        res=np.where(msk,0.0,res).astype(np.float32); ok=(~msk).astype(np.float32)
        rs=ndi.shift(res,(-dy,-dx),order=1,mode='constant',cval=0.0,prefilter=False)
        os_=ndi.shift(ok,(-dy,-dx),order=1,mode='constant',cval=0.0,prefilter=False)
        ss=ndi.shift(sig,(-dy,-dx),order=1,mode='nearest',prefilter=False)
        good=os_>0.99
        w=np.where(good,(exp/np.maximum(ss,1e-3))**2,0.0).astype(np.float32)
        num+=w*np.where(good,rs/exp,0.0); den+=w
        del res,sig,msk,rs,os_,ss,w,good
    snr=np.where(den>0,num/np.maximum(den,1e-12)*np.sqrt(np.maximum(den,1e-12)),0.0).astype(np.float32)
    np.save('half%s_snr.npy'%hn,snr)
    print(hn,'done', np.percentile(snr[den>0],[50,99.9]), snr.max())
