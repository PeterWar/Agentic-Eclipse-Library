"""Read-only lineage audit, exact replay and diagnostic stage comparisons.
No legacy imports or writes; derivatives live only in this campaign.
"""
from pathlib import Path
import ast, json, hashlib
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter, gaussian_filter1d
from scipy.optimize import isotonic_regression
from scipy.interpolate import PchipInterpolator
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/earthshine_upstream_tone_20260914'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_UPSTREAM_TONE_20260914'
N=1400; CXT=699.568111973117; CYT=699.6475341408573; RL=455.5018
YY,XX=np.mgrid[:N,:N].astype(np.float32)
R=np.hypot(XX-CXT,YY-CYT); PHI=np.arctan2(YY-CYT,XX-CXT)
MARK=(XX>=550)&(XX<723)&(YY>=902)&(YY<1048)
GUARD=(XX>=500)&(XX<773)&(YY>=852)&(YY<1098)
SECTOR=np.floor((PHI%(2*np.pi))*24/(2*np.pi)).astype(int)
FIT=(R<410)&(R>30)&~GUARD&(SECTOR%2==0)
HELD=(R<410)&(R>30)&~GUARD&(SECTOR%2==1)

def save(name,d):
    (OUT/name).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')

def q(a,m):return np.percentile(a[m],[1,50,95,99]).tolist()

def relation(a,b):
    edges=np.unique(np.quantile(a[FIT],np.linspace(0,1,257)))
    xx=[]; yy=[]; ww=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        m=FIT&(a>=lo)&(a<hi)
        if m.sum()<20:continue
        xx.append(float(np.median(a[m]))); yy.append(float(np.median(b[m])));ww.append(int(m.sum()))
    yy=isotonic_regression(yy,weights=ww).x
    f=PchipInterpolator(xx,yy,extrapolate=False)
    pred=f(np.clip(a,xx[0],xx[-1]));res=b-pred
    return pred,dict(x=xx,y=yy.tolist(),held_residual=q(res,HELD),mark_residual=q(res,MARK),mark_outside_fit_range=int((MARK&((a<xx[0])|(a>xx[-1]))).sum())),res

def main():
    c44=ROOT/'research/tools/v44_earthshine_20260910/cau'
    c45=ROOT/'research/tools/v45_earthshine_20260910/cau'
    # Replay the suspect old operator exactly, without executing old main/imports.
    tree=ast.parse((c44.parent/'f5_render.py').read_text())
    pure=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['smooth','veil']],type_ignores=[])
    env=dict(np=np,cv2=cv2,gaussian_filter1d=gaussian_filter1d,RL=RL,CXT=CXT,CYT=CYT,R=R,XX=XX,YY=YY,PHI=PHI)
    exec(compile(pure,'legacy_f5_pure','exec'),env)
    source=np.load(c44/'surface_clean_rgb.npy')[...,1]
    replay=env['veil'](source);cached=np.load(c44/'veil_clean.npy')
    assert np.array_equal(replay,cached)
    g=np.load(c45/'combined_reference.npy'); disp=np.load(c45/'combined_reference_display_u16.npy')[...,1]
    tone=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F7_fonts.json').read_text())['tone']
    du=np.rint(np.clip(tone['anchor']+tone['scale']*np.arcsinh((np.nan_to_num(g,nan=tone['mid'])-tone['mid'])/tone['soft']),0,1)*65535).astype('uint16')
    assert np.array_equal(du,disp)
    live=np.load(ROOT/'research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy').mean(-1)
    precr=np.load(ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta/C0_pre_camera_raw_rgb.npy').mean(-1)
    p49=np.load(ROOT/'output/earthshine_v49_pere_reveal_20260912/A0_Pere_moon_RGB16.npy').mean(-1)
    post=np.load(ROOT/'research/tools/earthshine_v50_temporal_20260912/cau/lun_rgb_vel_u16.npy').mean(-1)
    v68=np.load(ROOT/'output/v68_artefactes_20260914/arrays/B10_photo_pilot.npz')['candidate'].mean(-1)
    arrays={'V45 observed G':g,'V45 initial global tone':disp.astype(float),'V45 user saved pixels':live,'V48 pre CR':precr,'V49 user tone':p49,'S8 output':post,'V68':v68}
    rows=[];preds={};resids={}
    items=list(arrays.items())
    for (na,a),(nb,b) in zip(items[:-1],items[1:]):
        pred,j,res=relation(a,b);j.update(before=na,after=nb);rows.append(j);preds[nb]=pred;resids[nb]=res
    save('A1_lineage.json',dict(old_V44_veil_replay_exact=True,V45_global_asinh_replay_exact=True,V44_background_enters_V45_source_RGB=False,V44_inheritance='Join/mask only; V45 replacement source itself is raw native G through one global asinh curve. Do not correct V44 polynomial in current V68 without proving another dependency.',historical_user_baked_V45_RGB=True,relations=rows,tone=tone))
    np.savez_compressed(OUT/'arrays/A1_trace.npz',**{k.replace(' ','_'):v.astype(np.float32) for k,v in arrays.items()},**{('res_'+k.replace(' ','_')):v.astype(np.float32) for k,v in resids.items()})
    # Whole lunar rectangle shown for every stage; normalized thumbnails diagnostic only.
    panel=Image.new('RGB',(700*4,750*2),(22,22,22));draw=ImageDraw.Draw(panel)
    for i,(name,a) in enumerate(arrays.items()):
        lo,hi=np.percentile(a[R<410],[2,98]);u=np.clip((a-lo)/(hi-lo),0,1);u=np.where(R<454,u,0)
        im=Image.fromarray(np.uint8(u*255)).convert('RGB').resize((700,700))
        x=(i%4)*700;y=(i//4)*750;panel.paste(im,(x,y+30));draw.text((x+8,y+8),name,fill='white');draw.rectangle((x+275,y+30+451,x+361,y+30+524),outline='orange',width=2)
    panel.save(OUT/'vistes/A1_entire_lunar_stages.png')
    print(json.dumps(dict(replays='EXACT',V44_background_not_in_current_source=True,relations=[{k:v for k,v in j.items() if k not in ['x','y']} for j in rows]),indent=2),flush=True)

if __name__=='__main__':main()
