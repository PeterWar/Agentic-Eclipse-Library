from common58 import *
claim();prep=json.loads((O/'G0_prepared_layers.json').read_text());y,x=np.mgrid[:2000,:2000];mc=(999.5681,999.6475);mr=np.hypot(x-mc[0],y-mc[1]);mt=np.mod(np.arctan2(y-mc[1],x-mc[0]),2*np.pi);sec=(mt/(np.pi/4)).astype(int);rep={}
def edited(i):
 bb=prep[str(i)]['bbox'];a=np.load(O/'prepared_layers'/f'L{i:02d}_C1.npy',mmap_mode='r');out=np.zeros((2000,2000),np.uint16);xa=max(bb[0],ROI[0]);ya=max(bb[1],ROI[1]);xb=min(bb[2],ROI[2]);yb=min(bb[3],ROI[3]);out[ya-ROI[1]:yb-ROI[1],xa-ROI[0]:xb-ROI[0]]=a[ya-bb[1]:yb-bb[1],xa-bb[0]:xb-bb[0]];return out.astype('float32')/65535
lunar=roi(29).astype('float32')/65535;old=roi(28).astype('float32')/65535;new=edited(28);good=(mr>60)&(mr<.8*453.5)
for ln in [False,True]:
 for sig in [(3,12),(5,16)]:
  fs=[]
  for a in [lunar,old,new]:
   if ln:a=np.log(np.maximum(a,.005))
   fs.append(gaussian_filter(a,sig[0])-gaussian_filter(a,sig[1]))
  before=[];after=[]
  for k in range(8):
   m=good&(sec==k);before.append(ncc(fs[0][m],fs[1][m]));after.append(ncc(fs[0][m],fs[2][m]))
  rep[f'LROC_log{ln}_{sig}']=dict(before=before,after=after,heldout_before=float(np.mean(np.array(before)[1::2])),heldout_after=float(np.mean(np.array(after)[1::2])));print(rep[f'LROC_log{ln}_{sig}'],flush=True)
# Newly transformed exposures, independent region partition inherited from B2.
sr=np.hypot(x+ROI[0]-CX,y+ROI[1]-CY);st=np.mod(np.arctan2(y+ROI[1]-CY,x+ROI[0]-CX),2*np.pi);ss=(st/(np.pi/4)).astype(int);base=roi(9).astype('float32')/65535;B=gaussian_filter(np.log(np.maximum(base,.001)),4)-gaussian_filter(np.log(np.maximum(base,.001)),16)
for i in range(1,7):
 a=roi(i).astype('float32')/65535;new=edited(i);good=(sr>1.25*RS)&(sr<1.85*RS)&(a>.025)&(a<.92)&(base>.025)&(base<.96)&(roi(i,-1)>65000);oldf=gaussian_filter(np.log(np.maximum(a,.001)),4)-gaussian_filter(np.log(np.maximum(a,.001)),16);newf=gaussian_filter(np.log(np.maximum(new,.001)),4)-gaussian_filter(np.log(np.maximum(new,.001)),16);before=[];after=[]
 for k in [1,3,5,7]:
  m=good&(ss==k)
  if m.sum()>720:before.append(ncc(B[m],oldf[m]));after.append(ncc(B[m],newf[m]))
 rep[str(i)]=dict(heldout_before=float(np.mean(before)),heldout_after=float(np.mean(after)));print(i,rep[str(i)],flush=True)
rep['PASS']=all(v['heldout_after']>=v['heldout_before'] for v in rep.values());save('B10_alignment_readback.json',rep);assert rep['PASS']
