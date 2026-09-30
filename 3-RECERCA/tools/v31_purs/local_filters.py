from common import *
import gc
def mgn(a,m,sigmas=(1.25,2.5,5,10,20,40),k=.7,h=.7,gamma=3.2,limits=None):
 # Morgan & Druckmuller 2014 eqs1-5: variance of residual, NOT G(B^2)-G(B)^2.
 lo,hi=limits or (float(np.min(a[m])),float(np.max(a[m])))
 if hi<=lo:return np.zeros_like(a,dtype='float32')
 detail=np.zeros_like(a,dtype='float32')
 for s in sigmas:
  mu=ng(a,m,s);d=a-mu
  d[np.abs(d)<=8*np.finfo('float32').eps*np.maximum(np.abs(a),np.abs(mu))]=0
  den=np.sqrt(ng(d*d,m,s));z=np.divide(d,den,out=np.zeros_like(d),where=den>0)
  detail+=np.arctan(k*z)/len(sigmas);log('MGN sigma '+str(s))
 global_term=np.clip((a-lo)/(hi-lo),0,1)**(1/gamma) if hi>lo else np.zeros_like(a)
 return h*global_term+(1-h)*detail
def main():
 a,m=readbase();a=np.array(a);a_mgn=np.maximum(a,0);limits=[float(a_mgn[m].min()),float(a_mgn[m].max())]
 out=mgn(a_mgn,m,limits=limits)
 save_output('P03_MGN',out,m,{'paper':'Morgan & Druckmuller 2014, equations1-5','sigma_px':[1.25,2.5,5,10,20,40],'k':.7,'h':.7,'gamma':3.2,'weights':[1]*6,'input_limits':limits,'nonpositive_input':'49 native limb pixels clipped to0 as allowed in paper; base itself unchanged','boundary':'normalized observed support, truncate3 Gaussian; no radial normalizer, H1, or external high-pass'})
 del out;gc.collect()
 # These are NEW pure controls. Frozen legacy controls also remain in the PSB.
 out=a-ng(a,m,24)
 save_output('C01_Passa_alt24_lineal',out,m,{'role':'classic control','definition':'B-Gaussian24(B), linear G','boundary':'normalized physical support','external_processing':'none'})
if __name__=='__main__':main()
