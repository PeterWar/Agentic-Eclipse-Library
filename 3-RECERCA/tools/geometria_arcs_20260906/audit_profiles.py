"""Qualify heldout predictions against the training support of spline knots."""
from geometry import *
rows=[]
for path in sorted(Path(RUN.rebut('')).glob('*_fine.json'))+sorted(Path(RUN.rebut('')).glob('*_wide.json')):
    rep=json.loads(path.read_text());name=rep['name']
    data=np.load(D/(name+'_samples.npz'));z=data['z']
    s=Samples(center=rep['reference_center'],radial=rep['radial_selection_px'],step=4,nsectors=rep['sector_count'],margin_deg=rep['sector_margin_degrees'])
    for row in rep['fits']:
        fit=Fit(s,z,row['training_parity']);j,f=s.basis(row['parameters']);sel=fit.train;n=len(s.knots)
        info=np.bincount(j[sel],weights=(1-f[sel])**2,minlength=n)+np.bincount(j[sel]+1,weights=f[sel]**2,minlength=n)
        left=((1-f)>1e-6)&(info[j]<=1e-4);right=(f>1e-6)&(info[j+1]<=1e-4)
        weak=(left|right)&fit.valid
        p=np.load(D/(name+f"_{row['training_parity']}_{row['model']}_profile.npz"))
        pred=prediction(j,f,p['profile'])
        record={'case':name,'model':row['model'],'training_parity':row['training_parity'],
            'heldout_count':int(fit.valid.sum()),'weak_or_zero_knot_support_predictions':int(weak.sum()),
            'weak_fraction':float(weak.sum()/fit.valid.sum()),
            'max_abs_prediction':float(np.max(np.abs(pred[fit.valid]))),
            'data_RMS':float(np.sqrt(np.mean(z[fit.valid]**2))),
            'status':'PARTIAL_PROFILE_SUPPORT; raw CV cannot by itself reject geometry' if weak.any() else 'FULL_PREDICTION_SUPPORT',
            'threshold':'quadratic training basis support<=1e-4 with active basis weight>1e-6',
            'limitation':'diagonal knot support only; FULL means no weak knot detected at this threshold, not full rank or conditioning qualification'}
        row['prediction_support_qualification']=record;rows.append(record)
    save(name,rep)
save('profile_support_audit',{'rows':rows,'conclusion':'do not interpret extreme heldout errors from unsupported knots as noncircularity; no geometry is accepted on that basis'})
print(json.dumps([r for r in rows if r['weak_or_zero_knot_support_predictions']],indent=2))
