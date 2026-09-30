"""Cloud geometry bound; no lunar albedo inferred and no photograph edited."""
from pathlib import Path
import numpy as np,json
R=Path.cwd();O=R/'output/earthshine_taca_source_20260914'
y,x=np.mgrid[:1400:2,:1400:2];nx=(x-699.568111973117)/453.5;ny=(y-699.6475341408573)/453.5
nz=np.sqrt(np.maximum(1-nx*nx-ny*ny,0));r=np.hypot(nx,ny)
valid=r<.9;mark=(x>=550)&(x<723)&(y>=902)&(y<1048);guard=(x>=500)&(x<773)&(y>=852)&(y<1098)
normal=np.stack([nx,ny,nz],-1);surface=1737.4*normal
# Conservative closest geocentric lunar distance; absolute cloud photocenter
# lies within Earth's apparent radius. Limb point source is an extreme, not
# a realistic cloud map. Smooth sphere, common surface reflectance assumed.
D=356500.;ER=6378.137
def irradiance(e):
 d=np.asarray(e)-surface;rr=np.linalg.norm(d,axis=-1);return np.sum(normal*d,axis=-1)/rr**3
center=irradiance([0,0,D]);fit=valid&~guard;design=np.stack([np.ones(nx.shape),nx/np.maximum(nz,1e-5),ny/np.maximum(nz,1e-5)],-1)
rows=[]
for angle in np.arange(0,360,30):
 a=np.deg2rad(angle);flux=irradiance([ER*np.cos(a),ER*np.sin(a),D]);ratio=flux/np.maximum(center,1e-20)
 coeff=np.linalg.lstsq(design[fit],ratio[fit],rcond=None)[0];res=ratio-design@coeff
 rows.append(dict(angle_deg=int(angle),mark_irradiance_ratio_range=np.percentile(ratio[mark],[0,50,100]).tolist(),mark_residual_after_global_incidence_gradient_max=float(abs(res[mark]).max())))
rep=dict(method=__doc__,earth_radius_km=ER,earth_moon_distance_km=D,earth_angular_radius_deg=float(np.rad2deg(np.arcsin(ER/D))),models=rows,scope='Irradiance on a smooth sphere, not lunar BRDF or albedo. Clouds change integrated source brightness and a smooth illumination gradient; they do not form a cloud image on lunar terrain.',source='https://arxiv.org/abs/1904.00236')
(O/'A1_cloud_geometry.json').write_text(json.dumps(rep,indent=2)+'\n')
print('angular radius',rep['earth_angular_radius_deg'],'worst local residual',max(q['mark_residual_after_global_incidence_gradient_max'] for q in rows))
