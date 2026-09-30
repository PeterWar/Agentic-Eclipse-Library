"""Persist/reproduce independent read-only weight audit at mark246, no RAW radiance."""
from a4_sources import *

def main():
 out=O/'weight_bound_R02';out.mkdir();meta=json.loads((O/'limb_frames/METADATA.json').read_text());frames=meta['frames'];z=np.load(O/'ROI_L246.npz');my,mx=np.where(z['c-1']>0);alpha=z['c-1'][my,mx].astype(np.float64);gx=mx+z['box'][0];gy=my+z['box'][1];x=gx-meta['box_y0y1x0x1'][2];y=gy-meta['box_y0y1x0x1'][0];D=np.load(O/'limb_frames/distance_model.npy',mmap_mode='r');W=np.load(O/'limb_frames/weight.npy',mmap_mode='r')
 b2=json.loads((H/'v38_limb_round1/cau/correccio_vora_lunar.json').read_text())['taula'];a1=json.loads((H/'v38_limb_round1/receipts/A1_franja_font.json').read_text())['perfil_biaix_vs_distancia_vora'];cl={'curts':'curts (≤1/800)','mitjans':'mitjans (1/800–1/50)','llargs':'llargs (>1/50)'};tables={}
 for c,t in b2.items():
  q=a1[cl[c]]['perfil'];dd=np.array([a['d'] for a in q]);bb=np.array([a['mediana_ln'] for a in q]);lo=dd<t['d_px'][0];tables[c]=(np.r_[dd[lo],t['d_px']].astype(np.float32),np.r_[bb[lo],t['B_ln']].astype(np.float32))
 tiers=[{'curts':0.,'mitjans':.5,'llargs':1.5},{'curts':-2.,'mitjans':-.5,'llargs':None},{'curts':-4.,'mitjans':None,'llargs':None}];gt=[.02,4e-4,8e-6];den={k:np.zeros((len(x),3),np.float32) for k in ['old','full']};num={run:{grp:np.zeros((len(x),3),np.float32) for grp in ['late_all_Dlt4','late_train_Dlt4','late_all_Dlt0','late_all_D0to2','late_all_D2to4']} for run in den};nf=0;nt=0
 for j,f in enumerate(frames):
  d=D[j,y,x];w=W[j,y,x,:];e=f['exposure'];c='curts' if e<=1/800 else ('mitjans' if e<=1/50 else 'llargs');dd,bb=tables[c];cn=np.exp(-np.interp(d,dd,bb,right=0).astype(np.float32),dtype=np.float32);fl=np.clip((d-2)/2,0,1).astype(np.float32);we=np.zeros_like(d)
  for tier,g in zip(tiers,gt):
   d0=tier[c]
   if d0 is not None:we+=g*np.clip(d-d0,0,1)/np.maximum(cn,1e-6)**2
  coeff={'old':fl,'full':fl+we};late=f['time']>100 and e==.0003125;nf+=int(late);nt+=int(late and not f['holdout'])
  for run,k in coeff.items():
   dw=w*k[:,None];den[run]+=dw
   if late:
    for grp,sel in [('late_all_Dlt4',d<4),('late_train_Dlt4',(d<4)&(not f['holdout'])),('late_all_Dlt0',d<0),('late_all_D0to2',(d>=0)&(d<2)),('late_all_D2to4',(d>=2)&(d<4))]:num[run][grp]+=dw*sel[:,None]
 s4=np.load(O/'s4_baseline/cau/s4_recomposicio_box.npz');sy0,sy1,sx0,sx1=s4['box'];sx=gx-sx0;sy=gy-sy0;assert ((sx>=0)&(sy>=0)&(sx<sx1-sx0)&(sy<sy1-sy0)).all();old_support=np.load(O/'b3_baseline/cau/support_v42.npy',mmap_mode='r')[gy,gx];new_support=np.load(O/'s4_baseline/cau/s4_support_new_box.npy',mmap_mode='r')[sy,sx];dm=s4['Dmin'][sy,sx];use=new_support&((~old_support)|(dm<6));rows=[]
 for run in ['old','full','actual']:
  dn=np.where(use[:,None],den['full'],den['old']) if run=='actual' else den[run]
  for grp in num['old']:
   nn=np.where(use[:,None],num['full'][grp],num['old'][grp]) if run=='actual' else num[run][grp];f=np.divide(nn,dn,out=np.zeros_like(nn),where=dn>0)
   for ch in [0,1,2]:
    if ch!=1 and grp!='late_all_Dlt4':continue
    a=f[:,ch];rows.append({'run':run,'group':grp,'channel':ch,'supported_marks':int((dn[:,ch]>0).sum()),'nonzero_marks':int((a>0).sum()),'fraction_percentiles_0_25_50_75_95_99_100':np.percentile(a,[0,25,50,75,95,99,100]).tolist(),'alpha_weighted_mean_fraction':float(np.sum(a*alpha)/alpha.sum()),'pooled_weight_fraction':float(nn[:,ch].sum()/dn[:,ch].sum()),'conditional_deficit_36pct_median_max':[float(.36*np.median(a)),float(.36*np.max(a))]})
 assert len(x)==1016 and nf==17 and nt==13 and use.sum()==1016 and old_support.sum()==980
 actual=next(v for v in rows if v['run']=='actual' and v['group']=='late_all_Dlt0' and v['channel']==1);assert abs(actual['fraction_percentiles_0_25_50_75_95_99_100'][-1]-9.1938352398e-7)<1e-16
 save(out/'RECEIPT.json',{'PASS':True,'scope':'denominator weights only; does not read holdout radiance','reproduced_independent_readonly_peer':'limb_diagnosis; same frame/sum order','marks':len(x),'late_all':nf,'late_train':nt,'actual_uses_full':int(use.sum()),'old_supported':int(old_support.sum()),'Dmin_percentiles_0_50_100':np.percentile(dm,[0,50,100]).tolist(),'rows':rows,'caveats':['D<0 includes strong-deficit band of a42; D2..4 dominates maximum weight but not the strong deficit','36pct is conditional scenario, not empirical per-frame upper bound','common true radiance assumed; weights are CFA before color matrix/star subtraction/filters','old unsupported36 marks represented0 by protected division, not measured zero weight fraction','no direct bound on final AdobeRGB or filtered image; nonlinear amplification possible']});print('WEIGHT_BOUND_REPRODUCED',actual['conditional_deficit_36pct_median_max'])
if __name__=='__main__':guard();main()
