"""Read-only input assimilation; separate native coordinates from photo products."""
from pathlib import Path
import json, hashlib, subprocess, datetime
import numpy as np
import pandas as pd

R=Path(__file__).resolve().parents[3]
O=R/'output/relativitat_revisio_20260914'
V=R/'output/v65_pere_estrelles_20260914'
W=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17')
def dump(name,obj): (O/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)))

def main():
    assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_RELATIVITAT_REVISIO_20260914'
    j=json.loads((V/'S19_native_measure.json').read_text())
    old={tag:pd.read_csv(W/f'xmatch/final_match_{s}.csv') for tag,s in [('Sony','sony'),('Vixen','r6')]}
    refs={tag:dict(zip(x.det,x.TYC)) for tag,x in old.items()}
    cat=pd.read_csv(W/'xmatch/cat2_sony.csv').set_index('TYC')
    d={}
    for q in j['measurements']+j['references']:
        q=q.copy();tag='Sony' if q['source']=='extra' else q['source'];tyc=q['TYC'] or refs[tag].get(q['det'])
        if tyc not in cat.index:continue
        key=(q['frame'],tyc)
        # References have no catalogue positional seed; retain those over duplicate catalogue stamps.
        priority=0 if q['kind']=='psf_reference' else 1 if q['source']!='extra' else 2
        if key in d and d[key]['priority']<=priority:continue
        c=cat.loc[tyc];p=q['parameters'];s=np.exp(p[2:4]);th=p[4]
        rot=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
        cov=rot@np.diag(2*s*s/max(q['green_snr'],1e-6)**2)@rot.T
        d[key]=dict(source=tag,extraction=q['source'],frame=q['frame'],TYC=tyc,HIP=c.HIP_n if np.isfinite(c.HIP_n) else c.HIP,V=c.Vuse,BV=c.BVuse,
          x=q['xy'][0],y=q['xy'][1],SNR=q['green_snr'],refined=q['centroid_refined'],priority=priority,
          old=tyc in set(old[tag].TYC),blended=tyc in ['1403-1015-1','1403-1015-2','1403-1283-1','1403-1283-2'],
          cxx=cov[0,0],cxy=cov[0,1],cyy=cov[1,1],sigma_major=s.max(),sigma_minor=s.min(),index=q['index'])
    df=pd.DataFrame(d.values()).sort_values(['source','TYC','frame'])
    usable=df.refined & (df.SNR>=10) & ~df.blended
    count=df[usable].groupby(['source','TYC']).size()
    df['eligible']=usable & np.array([count.get((q.source,q.TYC),0)>=2 for q in df.itertuples()])
    df.to_csv(O/'A1_native_centroids.csv',index=False)
    manifests=[V/'S9_native_manifest.json',V/'S11_vixen_manifest.json']
    frames={q['name']:q for p in manifests for q in json.loads(p.read_text())['frames']}
    exif=json.loads(subprocess.check_output(['exiftool','-j','-DateTimeOriginal','-SubSecTimeOriginal','-OffsetTimeOriginal','-ExposureTime']+[v['path'] for v in frames.values()]))
    for e in exif:
        fr=frames[Path(e['SourceFile']).stem];t=datetime.datetime.strptime(e['DateTimeOriginal'],'%Y:%m:%d %H:%M:%S').replace(tzinfo=datetime.timezone(datetime.timedelta(hours=2)))
        sub=e.get('SubSecTimeOriginal',0);sub=float('0.'+str(sub)) if sub else 0
        t+=datetime.timedelta(seconds=sub+fr['exposure']/2)
        fr['utc_mid']=t.astimezone(datetime.timezone.utc).isoformat();fr['timing']='EXIF treated as exposure start; native Vixen duration 10.3s; absolute clock not independently certified.'
    dump('A1_frames.json',frames)
    paths=[V/'S19_native_measure.json',V/'S22_final_catalog.json',V/'S25_position_injections.json',V/'S26_evidence_summary.json',R/'research/77_PLA_RELATIVITAT_2027_QUE_CALDRIA.md',R/'research/tools/astrometria/deflexio/deflexio.py',R/'research/tools/astrometria/xmatch/cat2.py',W/'xmatch/cat2_sony.csv',W/'xmatch/cat2_r6.csv',W/'xmatch/final_match_sony.csv',W/'xmatch/final_match_r6.csv',O/'PROTOCOL.md',Path('/Users/USUARI/.cache/skyfield/de440s.bsp')]+manifests
    dump('A0_input_hashes.json',[dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()) for p in paths])
    summary={tag:dict(rows=len(a),unique=a.TYC.nunique(),eligible_rows=int(a.eligible.sum()),eligible_unique=a[a.eligible].TYC.nunique(),eligible_old=a[a.eligible&a.old].TYC.nunique(),unrefined=int((~a.refined).sum())) for tag,a in df.groupby('source')}
    dump('A1_summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':main()
