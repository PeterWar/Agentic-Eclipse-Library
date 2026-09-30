"""Regenerate only frames whose final fine mapping changes; reuse untouched B2
tiles byte for byte. Every regenerated frame starts from calibrated CFA planes.
"""
from comu44 import *
import subprocess, os

def main():
    prepare();fr,contacts=frames();regs=json.loads((REB44/'A2_registre.json').read_text())['registre']; rows=[]
    for m in fr:
        s=m['stem'];d=regs.get(s,{}).get('applied',[0.,0.]);changed=any(d)
        p=CAU44 if changed else CAU43;ver='v44' if changed else 'v43'
        if changed:
            cmd=[sys.executable,str(HERE44/'b2_lluna_v44.py'),m['tren'],m['nom'],f'sx={d[0]:.12f}',f'sy={d[1]:.12f}']
            if m['grup']=='sony_B':cmd+=['delta_arcmin=8.10',f'corr={HERE42}/cau/correccions_B.json']
            subprocess.run(cmd,check=True)
        a=p/f"lluna_{m['tren']}_{s}_{ver}.npy";w=p/f"lluna_{m['tren']}_{s}_{ver}_pes.npy"
        assert a.exists() and w.exists()
        rows.append(dict(**m,path=str(a),weight=str(w),regenerated=changed,shift=d,sha256=sha(a),weight_sha256=sha(w)))
    savejson(REB44/'B2_inputs.json',dict(frames=rows,contacts=contacts,n_regenerated=sum(r['regenerated'] for r in rows)))
    print('COMPLETE',len(rows),'frames',flush=True)

if __name__=='__main__':main()
