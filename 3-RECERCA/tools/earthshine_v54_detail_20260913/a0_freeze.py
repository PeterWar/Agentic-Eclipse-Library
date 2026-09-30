"""Freeze source identities and photographic baseline, before any candidate."""
from common import *
from psd_tools import PSDImage
import shutil
claim()
assert sha(V53)==V53_SHA
for sub in ['vistes','arrays','receipts','staging']: (OUT/sub).mkdir(exist_ok=False)
authorities=[ROOT/'AGENTS.md',ROOT/'CLAUDE.md',ROOT/'.coordination/HANDOFF_2026-09-13_CLAUDE_A_CODEX_EARTHSHINE_DETALL.md',
 Path('/Users/USUARI/Desktop/Eclipse 2026/IA/ACTIVE.json'),ROOT/'.coordination/CLAUDE_STATUS.md']
saved=[]
for i,p in enumerate(authorities):
    target=OUT/'receipts'/f'authority_{i}_{p.name}'
    shutil.copyfile(p,target);saved.append(dict(path=str(p),sha256=sha(p),snapshot=str(target)))
m=json.loads((ROOT/'research/tools/earthshine_native_psf_20260911/delivery_manifest.json').read_text())
rows=m['files']; rows=rows.values() if isinstance(rows,dict) else rows
known={r.get('path',r.get('file')):r.get('sha256') for r in rows}
paths=[SRC/'compositor_cache/G.npy',SRC/'compositor_cache/W.npy',SRC/'B0_new_all.npz',
 ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz',
 ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json',
 ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy',
 ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json']
inputs=[]
for p in paths:
    digest=sha(p);expected=known.get(str(p));
    if expected: assert digest==expected,(p,digest,expected)
    inputs.append(dict(path=str(p),sha256=digest,bytes=p.stat().st_size,prior_manifest_match=bool(expected)))
raw=json.loads((SRC/'A2_all_native.json').read_text())['frames']
for row in raw:
    p=Path(row['raw_path']); assert sha(p)==row['raw_sha256'],p
    inputs.append(dict(path=str(p),sha256=row['raw_sha256'],bytes=p.stat().st_size,prior_manifest_match=True))
print('Verified sources',len(inputs),flush=True)
s=PSDImage.open(V53);assert s.size==(10551,7506) and s.depth==16 and len(s)==26
layers=[fingerprint(l) for l in s]; lun=list(s)[25]
assert lun.name=='V49 · graella verda nativa · Camera Raw de Pere' and lun.size==(N,N)
rgb=np.stack([channel(lun,c) for c in range(3)],-1)
np.save(OUT/'arrays/V53_moon_rgb.npy',rgb)
np.save(OUT/'arrays/V53_lunar_alpha.npy',channel(lun,-1))
np.save(OUT/'arrays/V53_lunar_mask.npy',channel(lun,-2)[Y0:Y0+N,X0:X0+N])
assert np.array_equal(rgb,np.load(ROOT/'research/tools/earthshine_v50_temporal_20260912/cau/lun_rgb_vel_u16.npy'))
save('A0_freeze.json',dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),authorities=saved,inputs=inputs,
  V53=dict(path=str(V53),sha256=V53_SHA,bytes=V53.stat().st_size,layers=layers),raw67_verified=True,
  geometry=dict(N=N,CX=CX,CY=CY,X0=X0,Y0=Y0),baseline_cache_exact=True))
save('PLAN.json',dict(objective='Executar les quatre vies del handoff i lliurar una versio nova amb millores validades',
 routes=[dict(id=1,name='Deconvolucio de lala mesurada en lineal',proof='Ajust de PSF qualificat fora dajust, sensibilitat als models de fons, injeccio escena-convolucio-inversa; no derivar PSF del camp Camera Raw'),
 dict(id=2,name='Guany per banda amb soroll mesurat',proof='Particions alternes i temporals; patró fix contrastat amb Sony; guany Wiener/garrote sense terme creuat productor'),
 dict(id=3,name='Seleccio temporal per azimut',proof='Pesos continus declarats, llista88 i rellotge comu, suport valid i comparacio externa reservada'),
 dict(id=4,name='Textura corroborada40-64',proof='Fotogrames separats, nul girat, amplitud i retencio; cap pixel de LROC o DHS al producte')],
 acceptance=['Comparacio mateixa vara V53/candidat en lineal i pantalla','Injeccio cega0.90-1.10 amb model de transferencia declarat','Cap nou halo/costura: perfils sectorials, arcs, vora i vistes',
 'Originals i capes no objectiu exactes','Dos lectors PSB, Photoshop OBRE26capes, readback<=6DN16 i recomposicio<=3DN16','Informe de les quatre vies, incloent negatives, manifest i handoff'],
 prohibited=['Moure FOV o remostrejar el document','Compensacio anular afegida','Textures externes com a fonts','Executar camps antics amb claims obsolets'],
 statistical_limits=['Geometria i calibracio ja ajustades globalment','Sony ja present a base ampla: retencio fotografica, independencia nomes a fonts Vixen separades','Nul girat exploratori; cel parcialment compartit']))
print('A0 done',flush=True)
