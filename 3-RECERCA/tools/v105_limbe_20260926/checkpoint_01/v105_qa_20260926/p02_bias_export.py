"""Export frozen P02 constants and reserved-sector G/L diagnostics, no product."""
from pathlib import Path
import json,numpy as np
path=Path('/private/tmp/v105_qa_20260926/factorial_frozen_corrections.py')
text=path.read_text();prefix=text.split("report={'scope':",1)[0]
ns={'__name__':'qa_context','__file__':str(path)};exec(compile(prefix,str(path),'exec'),ns)
out=Path('/private/tmp/v105_qa_20260926');report=json.loads((out/'factorial_frozen_corrections.json').read_text())
q=report['cases']['remove_phi']['16']['572A2969.CR3']
gfull=np.array([q['camera_channels'][c]['constant']['full_fit']['gain'] for c in 'RGB'])
cfg={'pilot':'P02 observed photographic pilot; scientific calibration remains partial',
 'input':'/private/tmp/v105_raw_pilot_20260926/no_floor_all67',
 'source_policy':'remove frozen phi consistently for ALL67; retain frozen additive b and frozen k already present in N',
 'phi_source':'/Users/USUARI/Desktop/Eclipse 2026/4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v36/cau/vixen_{R,G,B}_phi.npy',
 'phi_upsample_helper':'/private/tmp/v105_qa_20260926/p02_phi_helpers.py:phi_crop',
 'box_y0y1x0x1':ns['meta']['box_y0y1x0x1'],'phi_Q':ns['Q'],
 'short_frames':['572A'+str(i)+'.CR3' for i in range(2959,2967)],
 'short_camera_RGB_gains':gfull.tolist(),'other_frame_camera_RGB_gains':[1.,1.,1.],
 'new_additive_offsets':[0.,0.,0.],
 'formula':'N_p02=(N_cached*exp(phi))*g_camera; W_p02=W_original*smoothstep(dreal,0.6,2); E_camera=sum(N_p02*ramp)/sum(W_original*ramp)',
 'units':'N/W is calibrated CAMERA RGB after frozen exposure normalization, k and b, before fixed AM0 color gains and matrix; g_camera dimensionless',
 'color_gain_after_stack':ns['gain'].tolist(),'color_matrix_after_stack':ns['matrix'].tolist(),
 'do_not_apply_twice':['k','frozen additive b','camera calibration g','AM0 gains/color matrix'],
 'keep_negative_noisy_numerators':True,'no_T_or_PSF_correction':True,
 'weights':'original per-camera-channel weights retained; W/g^2 is a separate variance policy, not silently introduced here',
 'physical_limit':'dreal ramp is modeled support, not a certificate of pure corona; keep presentation Moon and Pere geometry intact',
 'normalization':'no percentile/display scaling in this packet; caller declares existing tone curve',
 'scientific_status':'No global 2% claim. Blue fails sector validation even though removing floor and phi improves other channels.',
 'join_to_old_look':'Any 12..25 px join to the old-phi input must be explicit, observed-support-only, inspected and transfer-tested; not included by this helper.'}
(out/'P02_FROZEN_CONFIG.json').write_text(json.dumps(cfg,indent=2)+'\n')
inp=ns['inputs'];correct=ns['corrected_n'];cells=ns['cells'];M=ns['matrix'];color_gain=ns['gain']
pooledN=sum(correct(j,True,False) for j in range(8));pooledW=sum(inp[j]['w'] for j in range(8))
a,sec=cells(pooledN,pooledW,16);b,_=cells(correct(10,True,False),inp[10]['w'],16)
valid=np.isfinite(a).all(-1)&np.isfinite(b).all(-1)&(b>0).all(-1)
er=np.einsum('ij,...j->...i',M,b*color_gain)
applied=np.einsum('ij,...j->...i',M,(a*gfull)*color_gain)
heldout=np.full_like(a,np.nan)
for fold in [0,1]:
    g=np.array([q['camera_channels'][c]['constant']['cv'][fold]['fit']['gain'] for c in 'RGB'])
    te=sec%2!=fold;heldout[te]=np.einsum('ij,...j->...i',M,(a[te]*g)*color_gain)
def channel(v,name):return v[:,1] if name=='G' else ((v[:,0]+2*v[:,1]+v[:,2])/4 if name=='L' else v[:,2])
def desc(z):
    z=np.sort(z[np.isfinite(z)]);n=len(z)
    if not n:return {'n_cells':0}
    k=int(.1*n);trim=z[k:n-k] if k else z
    return {'n_cells':n,'median_bias_pct':float(100*np.median(z)),
      'trimmed_mean_bias_pct':float(100*trim.mean()),'trim_fraction_each_tail':.1,
      'spatial_p16_p84_pct':(100*np.percentile(z,[16,84])).tolist(),'spatial_sd_pct':float(100*np.std(z,ddof=1))}
bias={'scope':'Fixed 16px spatial cells at25..100px; all source and reference phi removed, b retained.',
 'heldout':'Each 30deg sector uses coefficients trained on the opposite parity sectors; frozen full-fit columns are descriptive only.',
 'uncertainty':'p16/p84 and SD measure spatial dispersion, not an independent confidence interval. Separate4+4-frame QA requested from sibling agent; common calibration/reference error is not covered.',
 'sectors':{}}
for ss in range(12):
    z=valid&(sec==ss);row={}
    for name in ['G','L','B']:
        target=channel(er,name);ok=z&(target>0)
        row[name]={'heldout':desc((channel(heldout,name)[ok]-target[ok])/target[ok]),
                   'frozen_fullfit_applied':desc((channel(applied,name)[ok]-target[ok])/target[ok])}
    bias['sectors'][f'{30*ss}..{30*(ss+1)}']=row
(out/'P02_G_L_B_HELDOUT_BIAS.json').write_text(json.dumps(bias,indent=2,allow_nan=False)+'\n')
print('CONFIG',cfg['short_camera_RGB_gains'])
for sector in ['60..90','90..120','120..150','150..180','210..240','240..270']:
 print(sector,{c:bias['sectors'][sector][c]['heldout'] for c in ['G','L','B']})
