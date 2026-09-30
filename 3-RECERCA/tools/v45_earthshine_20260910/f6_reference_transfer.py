"""Weak additive signal BEFORE temporal reference selection, weights recalculated.
Conditional post-CFA experiment, not a RAW/optical resolution measurement.
"""
from comu45 import *
from f2_temporal import combine_epochs,SURFACE

def main():
    claim45();receipt=json.loads((REB45/'F2_temporal.json').read_text());keys=receipt['groups']['combined']['keys'];data=[]
    for key in keys:
        d=np.load(CAU45/f'epoch_{key}.npz');data.append((d['g'].astype(float),d['variance'].astype(float),d['weight'].astype(float)))
    base=combine_epochs(data,'qa',return_reference=True);rows=[]
    for name,rad,theta in [('cyan_nord',414,-np.pi/2),('lila',440,np.radians(185)),('last_nord',451,-np.pi/2)]:
        cx=CXT+rad*np.cos(theta);cy=CYT+rad*np.sin(theta);x=XX-cx;y=YY-cy
        envelope=np.exp(-(x*x+y*y)/(2*20**2));mask=SURFACE&(x*x+y*y<40**2)
        for wavelength in [16.,24.]:
            for direction in ['radial','tangent']:
                angle=theta+(np.pi/2 if direction=='tangent' else 0)
                signal=envelope*np.sin(2*np.pi*(x*np.cos(angle)+y*np.sin(angle))/wavelength+.73)*SURFACE
                injected=[(g+.05*signal,v,w) for g,v,w in data]
                result=combine_epochs(injected,'qa',return_reference=True)
                delta=(result-base)/.05;gain=float(np.sum(delta[mask]*signal[mask])/np.sum(signal[mask]**2))
                relative=float(np.linalg.norm((delta-signal)[mask])/np.linalg.norm(signal[mask]))
                row=dict(region=name,radius=rad,angle_degrees=float(np.degrees(theta)),wavelength=wavelength,direction=direction,amplitude=.05,envelope_sigma=20,coherent_gain=gain,relative_error=relative,passes=.9<=gain<=1.1)
                rows.append(row);print(row,flush=True)
                savejson(REB45/'F6_reference_transfer.json',dict(B1_sha256=sha(REB45/'B1_inputs.json'),F2_receipt_sha256=sha(REB45/'F2_temporal.json'),scope='source perturbation after registered CFA/variance; temporal means,CDF,preferences recalculated; no RAW injection or optical resolution claim',rows=rows,complete=False))
    savejson(REB45/'F6_reference_transfer.json',dict(B1_sha256=sha(REB45/'B1_inputs.json'),F2_receipt_sha256=sha(REB45/'F2_temporal.json'),scope='source perturbation after registered CFA/variance; temporal means,CDF,preferences recalculated; no RAW injection or optical resolution claim',rows=rows,complete=True))
if __name__=='__main__':main()
