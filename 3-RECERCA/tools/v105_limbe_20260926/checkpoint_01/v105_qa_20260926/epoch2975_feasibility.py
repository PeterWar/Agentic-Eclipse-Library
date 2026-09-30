"""Geometry-only feasibility: no PSB/Photoshop changes, no lunar raster resampling.
Figures annotate an already registered observed source, never a proposed final.
"""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares
import cv2
from PIL import Image,ImageCms
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path('/Users/USUARI/Desktop/Eclipse 2026');O=Path('/private/tmp/v105_qa_20260926');S=Path('/private/tmp/v105_base_sources_20260926')
frames={};meta={}
for stem in ['572A2969','572A2975','572A2993']:
    z=np.load(S/(stem+'.npz'));frames[stem]=z['dreal'];meta[stem]=json.loads(str(z['metadata_json']))
y0,y1,x0,x1=meta['572A2975']['box_y0y1x0x1']
g=json.loads((ROOT/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']
alpha=np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L258.npz')['c-1'][y0-3000:y1-3000,x0-4600:x1-4600]/65535.
angles=np.arange(0,360,.25);th=np.deg2rad(angles);radii=np.arange(g['R']-20,g['R']+20,.025)
coords=np.array([g['cy']-radii[:,None]*np.sin(th)[None]-y0,g['cx']+radii[:,None]*np.cos(th)[None]-x0])
ap=map_coordinates(alpha,coords,order=1,mode='constant',cval=1,prefilter=False)
edges={str(t):radii[np.argmin(abs(ap-t),axis=0)] for t in [.05,.5,.95]}
points=np.column_stack([g['cx']+edges['0.5']*np.cos(th),g['cy']-edges['0.5']*np.sin(th)])
def sample(a,points):return map_coordinates(a,[points[:,1]-y0,points[:,0]-x0],order=1,mode='constant',cval=np.nan,prefilter=False)
def stat(v):return {'min':float(np.min(v)),'p05_p50_p95':np.percentile(v,[5,50,95]).tolist(),'max':float(np.max(v)),
                     'rms':float(np.sqrt(np.mean(v*v))),'fraction_abs_le_0p5':float(np.mean(abs(v)<=.5))}
circle=least_squares(lambda p:np.hypot(points[:,0]-p[0],points[:,1]-p[1])-p[2],[g['cx'],g['cy'],g['R']],loss='soft_l1',f_scale=.5)
ellipse=cv2.fitEllipse(points.astype(np.float32)[:,None,:])
rigid=least_squares(lambda p:sample(frames['572A2975'],points+p),[0.,0.],loss='soft_l1',f_scale=.5)
rigid_l2=least_squares(lambda p:sample(frames['572A2975'],points+p),[0.,0.])
shift_epoch=np.array(meta['572A2975']['model_center_final_xy'])-np.array([g['cx'],g['cy']])
shift_69_75=np.array(meta['572A2975']['model_center_final_xy'])-np.array(meta['572A2969']['model_center_final_xy'])
trials=[]
for dx in range(int(np.floor(rigid.x[0]))-2,int(np.ceil(rigid.x[0]))+3):
    for dy in range(int(np.floor(rigid.x[1]))-2,int(np.ceil(rigid.x[1]))+3):
        r=sample(frames['572A2975'],points+np.array([dx,dy]));trials.append((float(np.mean(r*r)),dx,dy))
best=sorted(trials)[0];integer=np.array(best[1:],float)
sectors=[('top',60,120),('upper_left',120,150),('prominence',150,180),('left',180,210),
         ('lower_left',210,240),('lower_left_exception',240,270),('bottom',270,300),('right',300,60)]
report={'scope':'Geometry feasibility only. Alpha258 is an edited display/earthshine alpha, not a measured physical lunar silhouette.',
 'frame_geometry':{k:{'time_s':v['time'],'exposure_s':v['exposure'],'frozen_model_center_xy':v['model_center_final_xy']} for k,v in meta.items()},
 'presentation':g,'center_delta_2969_to_2975_xy':shift_69_75.tolist(),'center_delta_presentation_to_2975_xy':shift_epoch.tolist(),
 'center_delta_2975_to_2993_xy':(np.array(meta['572A2993']['model_center_final_xy'])-np.array(meta['572A2975']['model_center_final_xy'])).tolist(),
 'alpha05_edge_note':'alpha0.05 means95%transparent, not an absolute physical lunar edge',
 'native_alpha05_radii':stat(edges['0.05']-g['R']),
 'native_alpha50_circle_fit':{'center_xy':circle.x[:2].tolist(),'radius':float(circle.x[2]),'residual_px':stat(circle.fun)},
 'native_alpha50_ellipse_fit':{'center_xy':list(ellipse[0]),'full_axis_lengths_px':list(ellipse[1]),'angle_deg':ellipse[2]},
 'rigid_alignment_to_dreal2975_zero':{'robust_shift_xy':rigid.x.tolist(),'robust_residual':stat(rigid.fun),
     'l2_shift_xy':rigid_l2.x.tolist(),'l2_residual':stat(rigid_l2.fun),'best_integer_shift_xy':integer.tolist(),
     'best_integer_residual':stat(sample(frames['572A2975'],points+integer)),
     'sign':'positive residual means display alpha50 falls outside physical2975model, covering observed corona; negative exposes geometrically lunar pixels'},
 'sectors':{},'coverage_new_epoch':{},
 'limitations':['Physical contour here uses the existing D21 silhouette model, with subpixel uncertainty; not external limb truth.',
   'A rigid move of bitmap layer by integer pixels adds no raster interpolation; exact fractional motion needs interpolation or deferred transform.',
   'Rigid movement cannot remove non-translational native-alpha shape residuals. Lunar texture is not resampled or edited in this probe.',
   'The historical09 source is2975+2993, anchored at2975 with later own-Moon exclusion; its registered edge is a separate observation, not declared exact from dreal2975.',
   'Holding one physical photographic epoch avoids temporal support gaps at its own limb but does not deconvolve the optical PSF.']}
for name,lo,hi in sectors:
    z=((angles>=lo)&(angles<hi)) if lo<hi else ((angles>=lo)|(angles<hi))
    report['sectors'][name]={case:stat(sample(frames['572A2975'],points+shift)[z]) for case,shift in [
       ('native',np.zeros(2)),('model_epoch_shift',shift_epoch),('best_robust_translation',rigid.x),('best_integer_translation',integer)]}

# All67 no-floor measured channel support, classified relative to each frame's own silhouette.
raw=Path('/private/tmp/v105_raw_pilot_20260926/no_floor_all67');rm=json.loads((raw/'METADATA.json').read_text());W=np.load(raw/'weight.npy',mmap_mode='r');N=np.load(raw/'numerator.npy',mmap_mode='r')
valid={}
for stem in ['572A2975','572A2993']:
    j=next(i for i,f in enumerate(rm['frames']) if f['name']==stem+'.CR3')
    valid[stem]=(np.asarray(W[j])>0).all(-1)&np.isfinite(N[j]).all(-1)
yy,xx=np.mgrid[y0:y1,x0:x1];c75=meta['572A2975']['model_center_final_xy'];pa=np.degrees(np.arctan2(-(yy-c75[1]),xx-c75[0]))%360;dr75=frames['572A2975'];dr93=frames['572A2993']
for name,lo,hi in sectors:
    sec=((pa>=lo)&(pa<hi)) if lo<hi else ((pa>=lo)|(pa<hi));rows=[]
    for a,b in [(0,.6),(.6,1),(1,2),(2,3),(3,5),(5,10)]:
        z=sec&(dr75>=a)&(dr75<b);nn=int(z.sum())
        rows.append({'distance_from_2975_own_model_limb_px':[a,b],'pixels':nn,
             '2975_observed_rgb_fraction':float(valid['572A2975'][z].mean()) if nn else None,
             '2993_observed_and_own_dreal_ge0_fraction':float((valid['572A2993']&(dr93>=0))[z].mean()) if nn else None,
             '2993_own_distance_p05_p50_p95':np.percentile(dr93[z],[5,50,95]).tolist() if nn else None})
    report['coverage_new_epoch'][name]=rows

(O/'EPOCH2975_FEASIBILITY.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
# Annotated source only. Same observational RGB in all panels; no compositing change.
z=np.load(S/'09_original_AdobeRGB1998_registered_to_E2975.npz');rgb=z['RGB'];img=Image.fromarray(np.rint(np.clip(rgb,0,1)*255).astype(np.uint8),'RGB')
img=ImageCms.profileToProfile(img,str(S/'V104_embedded.icc'),ImageCms.createProfile('sRGB'),outputMode='RGB');srgb=np.array(img)
fig,axs=plt.subplots(2,2,figsize=(11,8.4));cuts=[]
for row,ang in enumerate([130,230]):
    cx=int(round(c75[0]+g['R']*np.cos(np.deg2rad(ang))))-x0;cy=int(round(c75[1]-g['R']*np.sin(np.deg2rad(ang))))-y0
    cut=(slice(cy-50,cy+50),slice(cx-65,cx+65));cuts.append({'angle_deg':ang,'box_xyxy':[x0+cx-65,y0+cy-50,x0+cx+65,y0+cy+50]})
    yy0,xx0=np.mgrid[cy-50:cy+50,cx-65:cx+65]
    for col in range(2):
        ax=axs[row,col];ax.imshow(srgb[cut],origin='upper',interpolation='nearest',extent=[x0+cx-65,x0+cx+65,y0+cy+50,y0+cy-50])
        ax.contour(xx0+x0,yy0+y0,dr75[cut],levels=[0],colors=['cyan'],linewidths=.8)
        if col==0:
            mask=alpha[cut];color='red';title='09 observada + alfa258 actual (vermell)'
        else:
            mask=map_coordinates(alpha,[yy0-rigid.x[1],xx0-rigid.x[0]],order=1,mode='constant',cval=0,prefilter=False);color='lime';title='09 mateixa + alfa258 traslladada (verd)'
        ax.contour(xx0+x0,yy0+y0,mask,levels=[.5],colors=[color],linewidths=.9)
        ax.set_title(title,fontsize=10);ax.tick_params(labelsize=7)
fig.suptitle('Viabilitat geometrica: limbe modelat2975 en cian. Cap PSB modificat.',fontsize=12)
fig.tight_layout();fig.savefig(O/'EPOCH2975_CONTOUR_COMPARISON.png',dpi=170);plt.close(fig)
report['comparison_crops']=cuts;(O/'EPOCH2975_FEASIBILITY.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({'delta69to75':shift_69_75.tolist(),'deltaepoch':shift_epoch.tolist(),'rigid':report['rigid_alignment_to_dreal2975_zero'],'circle':report['native_alpha50_circle_fit']},indent=2))
