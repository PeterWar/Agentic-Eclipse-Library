from comu45 import *
import subprocess,os

def main():
    claim45();fr=json.loads((REB44/'B2_inputs.json').read_text())['frames'];rows=[]
    # Longest exposures first to make useful independent diagnostics available early.
    fr.sort(key=lambda m:-m['exp'])
    for m in fr:
        report=REB45/f"B1_{m['tren']}_{m['stem']}.json"
        overfile=REB45/'A2_native_registration.json'
        overrides=json.loads(overfile.read_text()).get('applied',{}) if overfile.exists() else {}
        desired=overrides.get(m['stem'],m['shift'])
        if not report.exists() or not json.loads(report.read_text()).get('no_brightness_floor',False) or np.max(abs(np.array(json.loads(report.read_text())['shift'])-desired))>1e-7:
            d=desired;cmd=[sys.executable,str(HERE45/'b1_native.py'),m['tren'],m['nom'],f'sx={d[0]:.12f}',f'sy={d[1]:.12f}']
            if m['grup']=='sony_B':cmd+=['delta_arcmin=8.10',f'corr={HERE42}/cau/correccions_B.json']
            subprocess.run(cmd,check=True,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'})
        r=json.loads(report.read_text());rows.append({**m,'native':r,'shift':r['shift']})
    savejson(REB45/'B1_inputs.json',dict(frames=rows,source='88 calibrated registered V44 inventory, all times, independent native green support; five additional nominal contact frames lack fine registration and weak-surface evidence'))
    print('COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
