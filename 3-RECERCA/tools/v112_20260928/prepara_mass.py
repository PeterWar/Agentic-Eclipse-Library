from pathlib import Path
import json
T=Path(__file__).parent;R=T.parents[2];O=R/'4-RESULTATS/v112_20260928'
p=O/'ADDENDUM_MASS_PREVI.json';assert not p.exists()
p.write_text(json.dumps(dict(candidate='sensor_nominal_mass',formula='F=.5+sum_j wj*(H(q-vj)-.5)/N_nominal; wj=bilinear_valid_j*bilinear_valid_mirror; equal ties half; four original radial-angular interpolation weights. No nmin cutoff or detrending in partial-FOV route.',meaning='Support-attenuated contrast, not full empirical CDF or recovered radiance. Missing comparisons contribute neutral rank only. No changed data samples, no painted mask.',scope='Only sensor-FOV partial cells; same enclosed-hole topology classification. Legacy route exact where all contributing cells have complete sensor support; lunar operation exact.',dependencies='Recompute41/42 using frozen producer8, retain manual display31. Raw inputs mean pre-Photoshop generator rasters, not cameraRAW reconstruction.',quality='All original fixed thresholds and windows unchanged; sensor01 and sensor_recipe8_raw native wedge failures retained. Candidate must be independently judged.',source='8a607e75967b4ef0d8a52eedabbedd986742781ecf3622b12c6e2630faba0da3'),indent=2)+'\n')
s=(T/'rhef_sensor.py').read_text()
s=s.replace('if detrend and partial_sensor and v.size >= nmin:', 'if False: # nominal-mass operator never detrends')
s=s.replace('beta, dmax, partial_sensor))','beta, dmax, partial_sensor, ix))').replace('float(S_deg / 2), partial_sensor))','float(S_deg / 2), partial_sensor, ix))')
s=s.replace('return res\n', '''# Continuous symmetric paired validity. This is comparison mass, never a radiance fill.
        outcells=[]
        for vals,vdet,beta,dmax,partial,ix in res:
            if partial:
                pair=(wm[ix]*wm[ix][::-1]).astype(np.float64); vv=p[ix]; take=pair>0; vv=vv[take]; pair=pair[take]
                oo=np.argsort(vv,kind='stable'); vv=vv[oo]; pair=pair[oo]; prefix=np.concatenate(([0.],np.cumsum(pair,dtype=np.float64)))
                outcells.append((vals,partial,vv,prefix,float(len(ix))))
            else: outcells.append((vals,partial,None,None,float(len(ix))))
        return outcells
''')
a=s.index('                    vals, vdet, beta, dmax, partial_sensor = cache[j][k]')
b=s.index('        for j in list(cache):',a)
s=s[:a]+'''                    vals, partial_sensor, vv, prefix, nominal = cache[j][k]
                    use = kk == k; ix = ii[use]; weight = wr[use] * ww[use]
                    if partial_sensor:
                        affected[ix] += weight
                        ll=np.searchsorted(vv,query[ix],side='left');rr=np.searchsorted(vv,query[ix],side='right')
                        increment=(0.5*(prefix[ll]+prefix[rr])-0.5*prefix[-1])/nominal
                        newout[ix] += weight*increment
                    if len(vals) < nmin: continue
                    rank = (np.searchsorted(vals, query[ix], side='left') + np.searchsorted(vals, query[ix], side='right')) / (2 * len(vals))
                    out[ix] += weight * rank; denout[ix] += weight
                    if not partial_sensor: newout[ix] += weight*(rank-0.5)
'''+s[b:]
(T/'rhef_mass.py').write_text('"""V112 fixed nominal comparison mass; no boundary rank renormalization."""\n'+s)
# Keep previous run_rhef.py unchanged for its existing provenance.
s=(T/'run_rhef.py').read_text().replace("('soft','sensor')","('soft','sensor','mass')")
(T/'run_rhef_mass.py').write_text(s)
print(p)
