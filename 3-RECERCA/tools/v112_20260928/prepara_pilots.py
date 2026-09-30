from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[3]; T=Path(__file__).parent; O=R/'4-RESULTATS/v112_20260928'
def save(p,v):
 assert not p.exists(),p
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
save(O/'CONTRACTE_PREVI.json', dict(schema='V112-method-and-quality-1',source=json.loads((O/'FONT.json').read_text()),
 corrected_layers_allowed=[41,42,45,46], channels_allowed=[0,1,2],
 annotation_hidden=412,exact_inventory=True,new_layers_forbidden=True,imports_forbidden=True,
 protected='Every other channel and all metadata, geometry, order, opacity and masks. Only annotation412 visibility changes.',
 manual=[234,308], manual_234_support=2130,
 native_manual=dict(max_abs_DN=64,rms_DN=16,meaning='Predeclared rendering tolerance only; manual source pixels and operation exact. Never fit a composite residual to meet it.'),
 causality='RHEF cells lose votes abruptly at nmin=200 and renormalize. Recompute operator45/46, then dependent NRGF41/42 with V111 opacity46=31, then full Photoshop adjustments.',
 candidates=['legacy reproduction','legacy detrend control','soft-vote shrinkage no detrend','soft-vote shrinkage with detrend'],
 soft_vote=dict(nmin=200,nfull=400,formula='rank_effective = 0.5 + smoothstep(n,200,400)*(rank-0.5); four nominal interpolation weights, no renormalization after dropping a cell',neutral='0.5 is empirical rank of observed query alone; never fills radiance',outer_vs_inner='Need preservation evidence; do not compensate any changed composite'),
 controls=dict(constant='No spatial structure from support; exact rank0.5',gradient='Report level and edge discontinuity, no new spike exceeding legacy',wedge='At fixed independently located coverage crossings, at least50% reduction in max low-frequency step at40px separation; full report including nulls',
 north='Fixed marks2/3/5 and angular/radial nulls at30/60/120px; report all even failing. No painted correction mask.',
 transfer='Paired injected Fourier modes on derived linear input at96,160,256px. Additional transfer0.90..1.10 in unchanged/full-support scientific domain. No RAW-to-PSB determinism claim.',
 external='Brno only judge. Freeze registration before candidate QA; coherent amplitude retention >=0.90 relative V111 in predeclared valid full support, no correlation decline >0.02. Outside independent coverage explicitly unvalidated.'),
 file_gates=['all active corrected channels equal declared operator outputs','all unchanged decoded channels and normalized metadata equal V111','control and candidate full native renders including paired239/241 off','full ImageData equals full native RGB render','exact ICC and canvas','p6 PASSA','Photoshop OBRE'],
 rejected='V109, any unknown new layer, renamed/renumbered compensation, edited manual mask, mutated native adjustment, source hash drift. Structure alone cannot approve science.'))
old=R/'3-RECERCA/tools/v98_20260925/rhef_local_sim.py'
s=old.read_text().replace('def rhef_local_sim(', 'def rhef_local_sim(')
s=s.replace('if len(vals) < nmin: continue', 'if len(vals) < nmin: continue')
# Keep nominal missing-cell rank exactly half, avoiding the disappearing-vote renormalization.
s=s.replace('out = np.zeros(len(idx), np.float32); denout = np.zeros(len(idx), np.float32)', 'out = np.full(len(idx), 0.5, np.float32); denout = np.zeros(len(idx), np.float32)')
s=s.replace('out[ix] += weight * rank; denout[ix] += weight', 'confidence = float(np.clip((len(vals) - nmin) / nmin, 0, 1)); confidence = confidence * confidence * (3 - 2 * confidence)\n                    out[ix] += weight * confidence * (rank - 0.5); denout[ix] += weight * confidence')
s=s.replace('np.where(denout > 0, out / np.maximum(denout, 1e-9), np.nan)', 'out')
(T/'rhef_soft.py').write_text('"""V112 pilot: smooth confidence of an empirical rank, never synthesized radiance. Frozen original remains unchanged."""\n'+s)
(T/'run_rhef.py').write_text('''from pathlib import Path
import sys,runpy,importlib.util,json
R=Path(__file__).resolve().parents[3];T=Path(__file__).parent
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V112_ESTRELLES_I_ARTEFACTES_20260928'
mode=sys.argv.pop(1)
if mode=='soft':
 spec=importlib.util.spec_from_file_location('rhef_local_sim',T/'rhef_soft.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);sys.modules['rhef_local_sim']=module
elif mode!='legacy':raise ValueError(mode)
sys.argv[0]=str(R/'3-RECERCA/tools/v98_20260925/f3_filtres_v98.py')
runpy.run_path(sys.argv[0],run_name='__main__')
''')
print('contract',hashlib.sha256((O/'CONTRACTE_PREVI.json').read_bytes()).hexdigest())
