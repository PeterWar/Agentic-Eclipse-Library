from common60 import *
claim();inputs=[(SRC,'84c2231052b12d5eb88b97717010905072ed78de70f4a11312b08b93300391c9'),(SRC.parent/'V58.psb','67bb653012fed649c6ec36ee3d593fcfeec2019960056ee99ad5f01becb15a9a'),(SRC.parent.parent/'Capes interiors/Earthshine_V56.psb','edee45ad76f08f8450beed3e85ed0d226eb0b1e11347478d2e998d74281ce12e')];rows=[]
for p,h in inputs:
 v=sha(p);rows.append({'path':str(p),'sha256':v,'expected':h,'exact':v==h});print(p.name,v==h,flush=True)
assert all(q['exact'] for q in rows);save('E2_sources_unchanged.json',rows)
