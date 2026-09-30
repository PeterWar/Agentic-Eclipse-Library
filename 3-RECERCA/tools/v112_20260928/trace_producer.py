"""Read-only input trace around a deterministic stage, without changing its operators."""
from pathlib import Path
import sys,os,json,runpy,hashlib,time
R=Path(__file__).resolve().parents[3]
receipt=Path(sys.argv[1]).resolve();script=Path(sys.argv[2]).resolve();args=sys.argv[3:]
assert not receipt.exists();assert str(receipt).startswith(str(R/'4-RESULTATS/v112_20260928'))
seen=set();written=set();enabled=True

def audit(event,arg):
 if not enabled or event!='open':return
 f,mode,flags=arg
 if not isinstance(f,(str,bytes,os.PathLike)):return
 try:p=Path(f).resolve()
 except (OSError,ValueError):return
 if not p.is_relative_to(R):return
 if isinstance(mode,str) and any(c in mode for c in 'wax+') or isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT):written.add(p)
 else:seen.add(p)

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
sys.addaudithook(audit)
t=time.time();argv=[str(script),*args];sys.argv=argv.copy();sys.path.insert(0,str(script.parent))
runpy.run_path(str(script),run_name='__main__')
enabled=False
seen.add(script);seen.add(Path(__file__).resolve())
for m in tuple(sys.modules.values()):
 f=getattr(m,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_relative_to(R) and p.exists():seen.add(p)
inputs={str(p):sha(p) for p in sorted(seen-written) if p.is_file()}
outputs={str(p):sha(p) for p in sorted(written) if p.is_file()}
import numpy,scipy,cv2
record=dict(status='COMPLETED',argv=argv,cwd=str(Path.cwd()),env={k:v for k,v in os.environ.items() if k.startswith(('V97_','V98_','V108_','OPENBLAS_','PYTHONDONTWRITEBYTECODE'))},python=sys.version,packages=dict(numpy=numpy.__version__,scipy=scipy.__version__,opencv=cv2.__version__),inputs=inputs,outputs=outputs,elapsed_seconds=time.time()-t,scope='Replay from explicitly traced frozen derived inputs. Does not assert RAW-to-PSB reconstruction.')
receipt.write_text(json.dumps(record,indent=2)+'\n');print('TRACE_COMPLETED',receipt,flush=True)
