"""Numerical and preservation checks; a PASS here is explicitly not a GR detection."""
from a3_inference import *
import hashlib,subprocess,sys,importlib.metadata

def main():
    checks=[]
    def check(name,condition,value=None):
        checks.append(dict(name=name,pass_=bool(condition),value=value))
        if not condition:raise AssertionError((name,value))
    for q in json.loads((O/'A0_input_hashes.json').read_text()):
        h=hashlib.file_digest(Path(q['path']).open('rb'),'sha256').hexdigest();check('source exact: '+q['path'],h==q['sha256'])
    raw=json.loads((V/'S26_evidence_summary.json').read_text())['selected_RAW']
    for q in raw:check('RAW SHA256 exact: '+Path(q['path']).name,hashlib.file_digest(Path(q['path']).open('rb'),'sha256').hexdigest()==q['sha256'])
    df=pd.read_csv(O/'A3_analysis_sample.csv');check('unique frame/source/star rows',not df.duplicated(['frame','TYC']).any());check('no unrefined or blended selected',bool((df[df.use5].refined&~df[df.use5].blended).all()))
    for threshold,n in [(5,51),(10,23),(20,8)]:check(f'census SNR{threshold}',df[df[f'use{threshold}']].TYC.nunique()==n,n)
    g=pd.read_csv(O/'A3_geometry_forecasts.csv');pick=lambda sample,kind:float(g[(g.source=='combined_conditional')&(g['sample']==sample)&(g.kind==kind)].sigma_epsilon.iloc[0])
    for sample,kind,value in [('old_literal','similarity',.528870),('old_literal','radial',.844511),('old_identified','similarity',.574227),('V65_eligible5','similarity',.488703),('V65_eligible5','radial',.844707)]:check('forecast '+sample+'/'+kind,abs(pick(sample,kind)-value)<2e-6,pick(sample,kind))
    ep=json.loads((O/'A2_ephemeris_check.json').read_text());check('legacy ephemeris reproduction',ep['catalog_old_max_abs_difference_arcsec']<1e-5);check('finite-angle deflection',ep['finite_angle_gnomonic_relative_difference_max']<2e-4)
    for c in json.loads((O/'A3_controls.json').read_text()):
        for v in c['coordinate_injections']:check('conditional coordinate injection '+c['kind']+'/'+str(v['injected']),abs(v['error'])<1e-8)
    out=[]
    for snr in [5,10]:
      for kind in ['radial','affine']:
       for tag in ['Sony','Vixen']:
        frames=sorted(df[df.source==tag].frame.unique())
        for half,fr in {'A':frames[::2],'B':frames[1::2]}.items():
         a=df[(df.source==tag)&df[f'use{snr}']&df.frame.isin(fr)];parts=[frame_part(x,kind,'equal') for _,x in a.groupby('frame')];parts=[p for p in parts if p is not None];q=combine(parts,f'{tag}/{half}/SNR{snr}/{kind}')
         if q:out.append(q)
    dump('A5_frame_halves.json',out)
    sc=pd.read_csv(O/'A4_2027_conditional_scenarios.csv')
    for tag,n,v in [('Sony',41,.07092598748),('Vixen',12,.11884543812)]:
        q=sc[(sc.source==tag)&(sc.V_limit==8)&(sc.kind=='radial')&(sc.per_star_sigma_arcsec==.1)].iloc[0];check('2027 conditional '+tag,int(q.n)==n and abs(q.sigma_epsilon-v)<1e-8)
    versions={m:importlib.metadata.version(m) for m in ['numpy','scipy','pandas','skyfield','matplotlib']};dump('VERIFICACIO.json',dict(status='NUMERICAL_REPRODUCTION_AND_SOURCE_PRESERVATION_PASS',GR_measurement_status='NOT_QUALIFIED',checks=checks,nchecks=len(checks),python=sys.version,versions=versions,visual_QA='All ten final PDF pages inspected individually; no clipping or unreadable figures observed. PDF logical QA in QA_PDF.json.',note='No clean RAW-to-centroid reconstruction or blind end-to-end GR validation was run; pre-existing S19 centroids are the frozen measurement input.'))
    extra=[W.parent/'catalegs/hip_main.dat',W.parent/'estrelles_sony.csv',W.parent/'estrelles_r6.csv']
    dump('A5_additional_source_hashes.json',[dict(path=str(p),sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()) for p in extra])
    print('PASS',len(checks),'checks; GR remains NOT_QUALIFIED')
if __name__=='__main__':main()
