from common58 import *
claim();rep=json.loads((O/'D4_sources.json').read_text());src=np.load(R/'research/tools/v38_20260908/cau/vixen_total_v38.npy',mmap_mode='r');out=np.load(O/'sources/vixen_starless.npy',mmap_mode='r+');reject=[]
for row in rep['outputs']['vixen']['measurements']:
 star=rep['selected'][row['index']]['star'];check=star.get('vixen');ok=bool(check and check['snr']>7 and check['contrast']>2)
 if not ok and 'TYC' in star:
  x,y=row['xy'];out[y-32:y+33,x-32:x+33]=src[y-32:y+33,x-32:x+33];reject.append(row['index'])
out.flush();save('D4b_vixen_non_detections.json',dict(restored_to_original=reject,reason='no measured stellar signal in this train; do not subtract positive noise at Sony-only star position',vixen_sha256=sha(O/'sources/vixen_starless.npy')));print(reject)
