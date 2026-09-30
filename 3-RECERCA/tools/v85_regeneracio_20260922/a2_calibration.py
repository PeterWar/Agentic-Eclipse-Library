"""Regenerate missing F0 calibrators using frozen recipe and hash-verified RAW.
Outputs are confined to this task; original input files remain read-only.
"""
from pathlib import Path
import sys,os,json,hashlib,datetime,time,tempfile,subprocess,importlib.metadata,copy
R=Path(__file__).resolve().parents[3];O=R/'4-RESULTATS/v85_regeneracio_20260922';H=R/'2-ARXIU/reconstruccio_compactacio_20260915/raw_replay'
CID='CODEX_V85_REGENERACIO_20260922'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,j):
 with Path(p).open('x') as f:json.dump(j,f,indent=2,ensure_ascii=False)
def claim():assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CID
claim();freeze=json.loads((H/'FROZEN.json').read_text());idx={}
for p in (R/'0-RAW').rglob('*'):
 if p.is_file() and p.suffix.upper() in ['.ARW','.CR3']:idx.setdefault(p.name,[]).append(p)
I=O/'raw_inputs';I.mkdir(exist_ok=True);manifest=[]
for train,j in freeze['trains'].items():
 for n,row in enumerate(j['inputs']):
  candidates=[p for p in idx.get(Path(row['path']).name,[]) if p.stat().st_size==row['identity']['bytes']]
  assert len(candidates)==1,(train,row['path'],candidates)
  p=candidates[0];st=p.stat();h=sha(p);assert h==row['sha256'],p
  link=I/train/row['role']/p.name;link.parent.mkdir(parents=True,exist_ok=True)
  if not link.exists():link.symlink_to(os.path.relpath(p,link.parent))
  assert link.resolve()==p.resolve()
  manifest.append({'train':train,'role':row['role'],'path':str(p.relative_to(R)),'sha256':h,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns})
  if n%100==0:print('HASH',train,n,'/',len(j['inputs']),flush=True)
manifest_file=O/'RAW_INPUTS_VERIFIED.json'
if not manifest_file.exists():save(manifest_file,{'inputs':manifest,'count':len(manifest),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
else:assert json.loads(manifest_file.read_text())['inputs']==manifest
sys.path.insert(0,str(H/'frozen_code'));import comu,f0
for name,expected in freeze['copied_code_sha256'].items():
 p=H/'frozen_code'/name
 if p.exists():assert sha(p)==expected,(p,expected)
comu.EFEM=str(R/'3-RECERCA/de421.bsp')
for train,j in freeze['trains'].items():comu.TRENS[train]=dict(copy.deepcopy(j['config']),dir=str(I/train))
# Block Python writes outside this task, including through RAW symlinks.
def check(p):
 if isinstance(p,int):return
 p=Path(os.fsdecode(p)).resolve()
 if p!=O and O not in p.parents:raise PermissionError('Write outside task: '+str(p))
def audit(event,args):
 if event=='open':
  path,mode,flags=args
  if (isinstance(mode,str) and any(z in mode for z in 'wax+')) or (flags or 0)&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):check(path)
 elif event in ('os.mkdir','os.remove','os.rmdir','os.chmod','os.chown','os.utime'):check(args[0])
 elif event in ('os.rename','os.link','os.symlink'):check(args[0]);check(args[1])
 elif event in ('socket.connect','socket.connect_ex','socket.bind','socket.getaddrinfo'):raise PermissionError('Network not used')
sys.addaudithook(audit)
S=O/'scratch';S.mkdir(exist_ok=True);tempfile.tempdir=str(S)
start=time.monotonic()
for train in ['VIXEN','SONYTOT']:
 claim();N=O/('calibration_'+train)
 if (N/'COMPLETE.json').exists():
  done=json.loads((N/'COMPLETE.json').read_text());assert done['PASS']
  for report in done['phases']:
   assert report['PASS']
   for row in report['files']:assert sha(O/row['path'])==row['sha256']
  continue
 N.mkdir(exist_ok=True)
 for name in comu.FASES:(N/name).mkdir(exist_ok=True)
 class SafeRun(comu.Run):
  def fase(self,n,*parts):
   p=Path(self.dir)/comu.FASES[n]/Path(*parts);check(p);(p.parent if parts else p).mkdir(parents=True,exist_ok=True);return str(p)
  def desa_rebut(self,name,data):save(self.rebut(name),data);self.rebuts[name]=data
 run=SafeRun(tren=train,segell='20260922_V85',dir=str(N),mode='CIENCIA')
 env={p:importlib.metadata.version(p) for p in ['numpy','rawpy','astropy','opencv-python','scipy']}
 if not (N/'MANIFEST.json').exists():save(N/'MANIFEST.json',{'recipe':'Frozen F0 functions; only input/output paths remapped','code':freeze['copied_code_sha256'],'environment':env,'RAW_manifest_sha256':sha(manifest_file),'train':train})
 reports=[]
 for phase,fn in [('F0.1',f0.pedestal_i_blanc),('F0.2',f0.masters_dark),('F0.3',f0.flat_radial)]:
  receipt=N/(phase+'_VERIFIED.json')
  if receipt.exists():
   report=json.loads(receipt.read_text());assert report['PASS'],receipt
   for row in report['files']:assert sha(O/row['path'])==row['sha256']
   reports.append(report);continue
  print('START',train,phase,flush=True);t=time.monotonic();fn(run)
  old=H/('v2_round1_'+train);verify=json.loads((old/(phase+'_VERIFIED.json')).read_text());files=[]
  for row in verify['fits']:
   suffix=Path(row['path']).parts;rel=Path(*suffix[suffix.index('0-calibracio'):]);p=N/rel;got=sha(p)
   files.append({'path':str(p.relative_to(O)),'sha256':got,'expected':row['file_sha256'],'exact':got==row['file_sha256']})
  js=[]
  for row in verify['json']:
   a=json.loads((N/'4-rebuts'/row['name']).read_text());b=json.loads((old/'4-rebuts'/row['name']).read_text())
   js.append({'name':row['name'],'exact':a==b})
  report={'phase':phase,'train':train,'files':files,'json':js,'PASS':all(x['exact'] for x in files+js),'seconds':time.monotonic()-t}
  save(receipt,report);reports.append(report);print('RESULT',train,phase,report['PASS'],round(report['seconds'],1),flush=True)
  if not report['PASS']:raise RuntimeError('Calibration changed; investigate '+str(receipt))
 assert all(report['PASS'] for report in reports)
 save(N/'COMPLETE.json',{'PASS':True,'phases':reports,'elapsed_total':time.monotonic()-start})
print('CALIBRATIONS_COMPLETE',round(time.monotonic()-start,1),flush=True)
