from pathlib import Path
import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'output/earthshine_compatibility_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_COMPATIBILITY_20260911'
r=json.loads((out/'E1_separate_captures.json').read_text());a=r['results']['linear']['40_64'];b=r['results']['log']['40_64'];vn=[f'572A{n}' for n in range(2979,2985)];sn=['DSC06987','DSC06993','DSC06996','DSC06999'];p=r['paths'];vals=np.array([[a[v+'_'+s]['r'] for s in sn] for v in vn]);ok=np.array([[a['triples'][v+'_'+s] and b['triples'][v+'_'+s] for s in sn] for v in vn])
fig,ax=plt.subplots(figsize=(9,6),layout='constrained');im=ax.imshow(vals,vmin=-.4,vmax=.4,cmap='RdBu_r')
for i in range(6):
 for j in range(4):ax.text(j,i,f'{vals[i,j]:.3f}'+(' ✓' if ok[i,j] else ''),ha='center',va='center',color='white' if abs(vals[i,j])>.25 else 'black')
ax.set_xticks(range(4),[f"Sony {p[s]['exp']:g}s\nC2+{p[s]['t_mid_C2']:.0f}s" for s in sn]);ax.set_yticks(range(6),[f"Vixen {p[v]['exp']:g}s · C2+{p[v]['t_mid_C2']:.0f}s" for v in vn]);ax.set_title('Zona verda superior: textura a 40–64 px\n✓ Controls Vixen/Sony/LROC superats en lineal i log\nProva exploratòria; cap PSB nou',fontsize=12);fig.colorbar(im,ax=ax,label='Correlació Vixen–Sony')
fig.savefig(out/'vistes/E1_separate_captures.png',dpi=150);plt.close(fig)
