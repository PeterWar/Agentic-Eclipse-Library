from common import *
import shutil
claim()
for s in ['native','arrays','receipts','vistes','staging']:(OUT/s).mkdir()
refs={'V54':'79386f21103b49c16638846e51d70fe1c5e9a29d873b31fcdf1f23dc1886852f','V53':'6ef9a0cccf063ef796c1390495aa806e216f207b75924dead38c601e9ed9745a'}
products=[]
for ver,expected in refs.items():
    p=CI/('Earthshine_'+ver+'.psb');assert sha(p)==expected
    products.append(dict(path=str(p),sha256=expected,bytes=p.stat().st_size))
authorities=[]
for i,p in enumerate([ROOT/'AGENTS.md',ROOT/'CLAUDE.md',ROOT/'.coordination/CLAUDE_STATUS.md',ROOT/'.coordination/HANDOFF_2026-09-13_CODEX_EARTHSHINE_V54.md',Path('/Users/USUARI/Desktop/Eclipse 2026/IA/ACTIVE.json')]):
    dest=OUT/'receipts'/f'authority_{i}_{p.name}';shutil.copyfile(p,dest);authorities.append(dict(path=str(p),sha256=sha(p),snapshot=str(dest)))
pilot=[m for m in frames() if m['exp']>=.5]
fit=['572A2982','572A2984','572A2979','572A2981','572A2978','572A2972','572A3002']
reserved=[m['stem'] for m in pilot if m['tren']=='vixen' and m['stem'] not in fit]
save('A0_freeze.json',dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),products=products,authorities=authorities,pilot_frames=pilot))
save('PLAN.json',dict(objective='Màxim detall earthshine recuperable, autorització desatesa de Pere. V54 preservada.',priority=['R/B natius junt amb verd','Patró fix residual al sensor','Escales i orientacions 2D','Estrelles PSF secundària'],
    source='Independent calibrated R,G1,G2,B; same frozen geometry, no CFA demosaicing, one bilinear sampling. Channel-specific existing whitebalance, offsets and smooth fields; no green field copied to red/blue.',
    pilot=dict(exposure_min_seconds=.5,fit_vixen=fit,reserved_vixen=reserved,sony='All Sony captures withheld from producer. Initial screen may use training sensor colors, final comparison on entire independently captured Sony.'),
    judge=dict(bands_px=[[8,16],[16,24],[24,40],[40,64],[64,96]],radii=[[60,250],[250,350],[350,410],[410,435],[435,449]],sectors=12,fit='even 30 degree sectors',heldout='odd sectors; reuse of earlier judged G/Sony geometry acknowledged',null_degrees=list(range(30,360,30)),
               injection_seed=551309,transfer=[.90,1.10],model_selection='No optimization against heldout Sony. Report all candidate and failed results. No absolute detector edits to make accepted baseline pass.'),
    candidate_rule='Only corroborated improvement, quantified noise/texture fidelity; no Sony/LROC crossed pixels in Vixen producer. New PSB only after qualification, preserving saved reveal/limb/masks/FOV. No claim of maximum mathematical information or DHS equivalence without evidence.',
    fpn='Measure pose diversity/rank first. Scene and sensor coordinate models trained separately, heldout capture prediction and injected lunar texture. No arbitrary subtraction of texture fixed to the Moon.',
    independence_limits=['Original geometry and calibration use earlier global fits','G1/G2 and RGB share sensor calibration and FPN; not independent sensors','Sony already in broad photo; scientific judge is separately reconstructed source only','Long exposures average turbulence; no unmeasured PSF inversion']))
print('Frozen V54, V53 and pilot',len(pilot),'fit',fit,'reserved',reserved,flush=True)
