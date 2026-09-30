"""Verify lack of clean independent Sony coverage without reading RGB."""
from a4_sources import *
from scipy.ndimage import map_coordinates

def main():
 rows=json.loads((O/'bias_component_R02/DECOMPOSITION.json').read_text())['coordinates'];points=np.asarray([next(p['xy'] for p in r['samples'] if p['label']=='minus4') for r in rows]);assert len(points)==80;report=[]
 for group in ['sony_A','sony_B']:
  z=np.load(O/'sony_clean_judge'/(group+'.npz'));y0,y1,x0,x1=map(int,z['box']);coords=np.stack([points[:,1]-y0,points[:,0]-x0]);den=z['den'];count=z['count'];valid=z['valid'];sample=np.stack([map_coordinates(den[...,c],coords,order=1,mode='constant',cval=0) for c in range(3)],-1);nc=map_coordinates(count.astype(float),coords,order=1,mode='constant',cval=0);va=map_coordinates(valid.astype(float),coords,order=1,mode='constant',cval=0);assert not sample.any() and not nc.any() and not va.any();report.append({'group':group,'inner_samples':80,'max_den_RGB':sample.max(axis=0).tolist(),'max_count':float(nc.max()),'valid_samples':int((va>.999).sum()),'loaded_fields':['box','den','count','valid'],'RGB_not_loaded':True})
 save(O/'SONY_INNER_SUPPORT_R02.json',{'root_verified_weights':report,'geometry_readonly_peer':'filter_sources','geometry_peer_maxD_sensorpx_quantiles':{'sony_A':[-.5848,.1744,1.0653],'sony_B':[-8.1406,-7.3109,-6.3436]},'geometry_peer_frame_counts':{'sony_A':9,'sony_B':12},'clean_rule':'A12 D>15 sensor pixels at both native CFA samples and mapped output','scope':'No clean independent measurement in the21 Sony frames admitted by current pipeline; Vixen and Brno limitations are separately recorded','implication':'Using these Sony pixels would require a new independently validated response model, not merely an available clean judge','heldout_radiance_not_read':True});print('SONY_NO_CLEAN_INNER_COVERAGE_CONFIRMED')

if __name__=='__main__':guard();main()
