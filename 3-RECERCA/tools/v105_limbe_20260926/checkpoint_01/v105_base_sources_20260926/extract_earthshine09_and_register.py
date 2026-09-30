from pathlib import Path
import json,numpy as np
O=Path('/private/tmp/v105_base_sources_20260926');src=Path('/Volumes/Crucial/Capes interiors/Earthshine_V56.psb')
p=Path('/Users/USUARI/Desktop/Eclipse 2026/3-RECERCA/tools/v71_marques_v69_20260916/psb69.py');code=p.read_text().replace('lid=int(r.tagged_blocks.get_data(Tag.LAYER_ID));','lid=int(r.tagged_blocks.get_data(Tag.LAYER_ID) or -1000-i);');ns={};exec(compile(code,'temporary_reader_allow_missing_group_id','exec'),ns);psb=ns['PSB'](src)
rgb=np.stack([psb.channel_box(10,c,[4677-2,3077-4,6077-2,4477-4]) for c in range(3)],-1);np.save(O/'EarthshineV56_09_shiftplus2plus4_ROI_RGB.npy',rgb)
p=O/'register_sources.py';ns={};exec(p.read_text().split('raw=q[\'E\']')[0],ns);globals().update(ns)
r,sx,sy=fit_sim(ref[...,1],rgb[...,1].astype(float)/65535,(d>25)&(d<150)&(ref[...,1]>.02)&(ref[...,1]<.90),[cx-bx,cy-by],[cx,cy],[0,0,0,1],[(-10,10),(-10,10),(-1,1),(.99,1.01)],'EarthshineV56_09_to_current303')
reg=np.stack([map_coordinates(rgb[...,c].astype(float)/65535,[sy,sx],order=1,mode='constant',cval=np.nan,prefilter=False) for c in range(3)],-1).astype(np.float32)
np.savez_compressed(O/'EarthshineV56_09_registered_to_current303.npz',RGB=reg,support_sampled=np.isfinite(reg).all(-1),box=box,metadata_json=json.dumps(r))
