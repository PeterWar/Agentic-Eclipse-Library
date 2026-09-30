import json, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
m=json.load(open(S4+'/fc_m1_limbe.json')); o=json.load(open(S4+'/fc_origens.json')); b=json.load(open(S4+'/fc_banda_per_az.json')); t=json.load(open(S4+'/fc_textura_azimutal.json'))
RB=np.arange(436,476)+0.5; RO=np.array(o['r_bins'])+0.5
fig,axs=plt.subplots(2,3,figsize=(18,9)); 
for ax,k in zip(axs.ravel(),['70-75','85-90','95-100','100-105','115-120','0-5']):
    s74=(m['sectors']['V74'] if k in m['sectors']['V74'] else m['referencia']['V74'])[k]; s71=(m['sectors']['V71'] if k in m['sectors']['V71'] else m['referencia']['V71'])[k]; oo=o['sectors'][k]
    ax.plot(RB,s71['L'],'k-',lw=2,label='compost V71'); ax.plot(RB,s74['L'],'r-',lw=2,label='compost V74')
    ax.plot(RO,oo['capa30_L'],'g--',label='capa 30 (contingut propi)'); ax.plot(RO,np.array(oo['capa30_mask'])*100,'g:',label='màscara 30 (×100)')
    ax.plot(RO,oo['base3_L'],'b--',label='base 3 V74'); ax.plot(RO,oo['foto96_L'],'m-.',label='foto 96 (L*)')
    ax.plot(RO,np.array(oo['powaaah57_alfa'])*100,'c:',label='alfa POWAAAH3 V71 (×100)')
    ax.axvline(456,color='gray',lw=0.5); ax.set_xlim(440,470); ax.set_ylim(0,100); ax.set_title(f'az {k}: L* per radi (1 px)'); ax.set_xlabel('r (px des del centre lunar)'); ax.grid(alpha=0.3)
axs[0,0].legend(fontsize=7)
plt.tight_layout(); plt.savefig(S4+'/v_fc_perfils_L_per_sector.png',dpi=110)
# resum numèric
top=[r for r in b if 63<=r['az']<=123]; ref=[r for r in b if (0<=r['az']<30) or (300<=r['az']<330)]
resum={
 'sub_marca_trac_llarg':{'r_marca':[448.5,454.7],'az_marca':[65,123],'mediana_r_per_az':'450.7–452.6 (coincideix amb la vora de la màscara 30 a 450.4–452.3 ±1 px)',
   'vora_mask30_az63-123':[min(r['vora_mask30'] for r in top),max(r['vora_mask30'] for r in top)],'vora_mask30_referencia_az0-30_300-330':[min(r['vora_mask30'] for r in ref),max(r['vora_mask30'] for r in ref)],
   'amplada_banda_plana_px_az63-123':[min(r['amplada_banda'] for r in top),max(r['amplada_banda'] for r in top)],'amplada_banda_plana_px_referencia':[min(r['amplada_banda'] for r in ref),max(r['amplada_banda'] for r in ref)],
   'ressalt_vora_mask30_dL_az63-123':[min(r['ressalt_vora_mask30_dL'] for r in top),max(r['ressalt_vora_mask30_dL'] for r in top)],
   'textura_azimutal_std_L':{'earthshine_r449-451_V74':[t['V74']['r449'],t['V74']['r450'],t['V74']['r451']],'banda_r452-453_V74':[t['V74']['r452'],t['V74']['r453']],'capa30_contingut_r452-453':[t['capa30_contingut']['r452'],t['capa30_contingut']['r453']]},
   'marca_vs_entorn_V74_Lab':m['sub_marques']['trac_llarg_r449-453']['V74'],'marca_vs_entorn_V71_Lab':m['sub_marques']['trac_llarg_r449-453']['V71']},
 'sub_marca_trac_curt':{'r_marca':[458.3,465.7],'az_marca':[80.4,100.5],'marca_vs_entorn_V74':m['sub_marques']['trac_curt_r458-465']['V74'],'marca_vs_entorn_V71':m['sub_marques']['trac_curt_r458-465']['V71'],
   'dif_V74_V71_r458-462_az60-125':json.load(open(S4+'/fc_dif_v74_v71.json'))['458-462'],'pixels_dif_gt2_r458-470':'314 px, tots a az 98,5–105,8 (retoc de Pere a la màscara 76)'},
 'limbe':{'r50_V74_az63-123':[min(r['r50_V74'] for r in top),max(r['r50_V74'] for r in top)],'r50_V71_az63-123':[min(r['r50_V71'] for r in top),max(r['r50_V71'] for r in top)],
   'r50_V74_ref':[min(r['r50_V74'] for r in ref),max(r['r50_V74'] for r in ref)],'r50_V71_ref':[min(r['r50_V71'] for r in ref),max(r['r50_V71'] for r in ref)],
   'amplada10-90_V74_top':[round(m['sectors']['V74'][k]['transit']['amplada'],2) for k in m['sectors']['V74']],'amplada10-90_V71_top':[round(m['sectors']['V71'][k]['transit']['amplada'],2) for k in m['sectors']['V71']],
   'amplada10-90_V74_ref':[round(m['referencia']['V74'][k]['transit']['amplada'],2) for k in m['referencia']['V74']],'amplada10-90_V71_ref':[round(m['referencia']['V71'][k]['transit']['amplada'],2) for k in m['referencia']['V71']],
   'limbe50_foto96_204_per_sector':{k:o['sectors'][k]['foto96_limbe50'] for k in o['sectors']},'limbe50_foto206_per_sector':{k:o['sectors'][k]['foto206_limbe50'] for k in o['sectors']},
   'foto96_amplada10-90_aprox_px':2.5},
 'alfa76_dins_silueta_V74_max_az60-125':max(m['sectors']['V74'][k]['alfa76_max_r440_456'] for k in m['sectors']['V74']),
 'alfa76_dins_silueta_V71_max_az60-125':max(m['sectors']['V71'][k]['alfa76_max_r440_456'] for k in m['sectors']['V71']),
 'nota_az165-207':'la màscara de la capa 30 surt FORA de la silueta (vora a 457–462,6 px, r50 del limbe 452–456): el contingut gris de la capa 30 (L* 15–20) tapa la corona 1–6 px enfora del limbe; no és la m1 però és a tocar de m4/m5'}
json.dump(resum,open(S4+'/fc_resum.json','w'),indent=1,ensure_ascii=False); print(json.dumps(resum,indent=1,ensure_ascii=False)[:3000])
