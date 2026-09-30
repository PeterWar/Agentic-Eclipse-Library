"""Necessary g1 dependencies only. Read-only; no physical sky-model or delivery approval.
Strictly scoped to the pinned V112 G_MAX_T_e30_W_H0 producer. Existing manual
limb differences may survive only at dL<1, only if equal to the frozen user
source, and only while the measured Gaussian footprint stays below GATE=40.
Photoshop's declared 15-bit quantization is explicit, never a fitted tolerance.
"""
from pathlib import Path
import json,hashlib,ast
import numpy as np
import cv2
from porta_torre_pisa import PSB,sha
from llinatge_v112 import APPROVED_MANIFESTS

IDS=(41,42,54,45,46)
TAGS={41:'P01_NRGF',42:'P01_NRGF_extrap',54:'P03_MGN',45:'P02c_RHEF_local60_native',46:'P02d_RHEF_local30_native'}
VARIANT='G_MAX_T_e30_W_H0'
ROW_BLOCK=256
# Solar coordinates used by the pinned g1 -> v97_comu producer. Both reference
# annuli start at >=5 solar radii; certify below that they lie inside GATE>0.
SOLAR_GEOMETRY=(5361.768111973117,3775.747534140857,440.60304883027544)

def q_declared(a):
 return np.round(np.round(np.asarray(a,np.float64)*32768/65535)*65535/32768).astype(np.uint16)

def d_limb(shape,centre,y0=0):
 cx,cy,r=centre;yy,xx=np.ogrid[y0:y0+shape[0],:shape[1]]
 return (np.hypot(xx-cx,yy-cy)-r).astype(np.float32)

def metadata_failures(active,producer):
 failures=[]
 for key in ('left','top','right','bottom','visible','opacity','blend','clipping','mask'):
  if active[key]!=producer[key]:failures.append('different_'+key)
 if not active['visible'] or not producer['visible']:failures.append('unsupported_hidden_layer')
 if active['blend']!='MULTIPLY' or producer['blend']!='MULTIPLY':failures.append('unsupported_blend')
 if active['clipping']!=0 or producer['clipping']!=0:failures.append('unsupported_clipping')
 for layer in (active,producer):
  if layer['mask'] is not None and layer['mask']['disabled']:failures.append('unsupported_disabled_mask')
 return sorted(set(failures))

def comparison_counts(active,expected,source,centre):
 """Pure array predicate, expected is pre-Photoshop uint16; source is frozen user channel.
 No full-image intermediate; differences within dL<1 require source identity.
 """
 out=dict(changed=0,outside_exception=0,changed_from_source_in_exception=0,max_abs_DN=0,exception_dL_min=None,exception_dL_max=None)
 arrays=(active,expected,source)
 if any(x is None or x.ndim!=2 or x.dtype.kind!='u' or x.dtype.itemsize!=2 for x in arrays):return dict(error='uint16_2D_required')
 if any(x.shape!=active.shape for x in arrays):return dict(error='shape_mismatch')
 for y in range(0,active.shape[0],ROW_BLOCK):
  sl=slice(y,y+ROW_BLOCK);e=q_declared(expected[sl]);a=active[sl];s=source[sl];delta=a.astype(np.int32)-e.astype(np.int32);different=delta!=0;dl=d_limb(a.shape,centre,y);allowed=dl<1
  out['changed']+=int(different.sum());out['outside_exception']+=int((different&~allowed).sum());out['changed_from_source_in_exception']+=int(((a!=s)&allowed).sum());out['max_abs_DN']=max(out['max_abs_DN'],int(np.abs(delta).max(initial=0)))
  v=dl[different&allowed]
  if v.size:
   mn,mx=float(v.min()),float(v.max());out['exception_dL_min']=mn if out['exception_dL_min'] is None else min(mn,out['exception_dL_min']);out['exception_dL_max']=mx if out['exception_dL_max'] is None else max(mx,out['exception_dL_max'])
 out['pass']=out['outside_exception']==0 and out['changed_from_source_in_exception']==0
 return out

def gaussian_support():
 impulse=np.zeros((129,129),np.float32);impulse[64,64]=1
 kernel=cv2.GaussianBlur(impulse,(0,0),6)
 yy,xx=np.nonzero(kernel);rx=int(np.max(np.abs(xx-64)));ry=int(np.max(np.abs(yy-64)))
 reach=1+float(np.hypot(rx,ry))
 return dict(cv2_version=cv2.__version__,sigma=6.0,dtype='float32',radius_x=rx,radius_y=ry,nonzero_taps=int(len(xx)),measured_mass=float(kernel.sum(dtype=np.float64)),limb_exception_exclusive=1.0,gate_zero_below=40.0,max_exception_influence_bound=reach,pass_dependency=rx==24 and ry==24 and reach<40)

def base_reaches_knee(shape,centre,y0,canvas_height,rx,ry):
 """Exact square-kernel dilation of dL>40 on the finite canvas.
 The farthest point from the limb centre in each kernel is a corner. This
 dependency domain is derived from the operator, not from observed defects.
 """
 cx,cy,r=centre;yy,xx=np.ogrid[y0:y0+shape[0],:shape[1]]
 dx=np.maximum(np.abs(np.clip(xx-rx,0,shape[1]-1)-cx),np.abs(np.clip(xx+rx,0,shape[1]-1)-cx))
 dy=np.maximum(np.abs(np.clip(yy-ry,0,canvas_height-1)-cy),np.abs(np.clip(yy+ry,0,canvas_height-1)-cy))
 return (np.hypot(dx,dy)-r).astype(np.float32)>40

def knee_stack_check(target,active):
 out=dict(status='FAIL',meaning='Necessary dependencies of the pinned g1 operator; not proof of sky, scientific quality, full Photoshop semantics, or delivery',failures=[],rows=[],channels=[],physical_sky_model_proven=False,helper_sha256=sha(Path(__file__)))
 def ck(ok,name,**details):
  if not ok:out['failures'].append(dict(check=name,**details))
  return bool(ok)
 verified={}
 def frozen(path,manifest):
  path=Path(path);key=str(path)
  if key not in verified:
   verified[key]=bool(path.is_file() and key in manifest['files'] and sha(path)==manifest['files'][key])
  if not ck(verified[key],'frozen_semantic_input',path=key):raise ValueError('unverified input '+key)
  return path
 try:
  spec=target.get('lineage')
  if not ck(isinstance(spec,dict) and bool(spec.get('path')),'frozen_semantic_manifest'):return out
  path=Path(spec['path'])
  if not ck(path.is_file(),'frozen_semantic_manifest',reason='missing file'):return out
  digest=sha(path)
  if not ck(digest==spec.get('sha256') and digest in APPROVED_MANIFESTS,'frozen_semantic_manifest',sha256=digest):return out
  m=json.loads(path.read_text());out['manifest_sha256']=digest
  if not ck(m.get('schema')=='V112-causal-replay-1','semantic_schema'):return out
  parameter=frozen(m['parameter_source'],m);producer=PSB(str(parameter))
  sourcepath=frozen(m['source']['path'],m)
  if not ck(m['files'][str(sourcepath)]==m['source']['sha256'],'frozen_user_source'):return out
  source=PSB(str(sourcepath));shape=(active.height,active.width)
  ck((active.width,active.height,active.depth,active.mode)==(producer.width,producer.height,16,3)==(source.width,source.height,source.depth,source.mode),'canvas_RGB16')
  records=[v for v in m['traces'] if v['role']=='g1_first']
  if not ck(len(records)==1,'one_g1_first_trace'):return out
  receipt=records[0];trace=json.loads(frozen(receipt['path'],m).read_text())
  if not ck(trace['status']=='COMPLETED' and trace['argv']==receipt['argv'] and trace['env']==receipt['env'],'observed_g1_trace_binding'):return out
  argv=trace['argv'];env=trace['env'];frozen(argv[0],m)
  if not ck(len(argv)==6 and argv[1]==VARIANT and argv[2]=='--psb' and argv[3]==str(parameter) and argv[4]=='--filtres-std','fixed_g1_operator_arguments'):return out
  reportpath=Path(env['V97_SORT'])/('G1_'+VARIANT+'.json');report=json.loads(frozen(reportpath,m).read_text());par=report['variants'][VARIANT]['parametres']
  ck(par['sigma_suau_px']==6.0 and par['limbe_px']==[40,80] and par['pixel_a_pixel'] is False and par['compta_superposar'] is False and par['porta_radial_4_7_5_0_Rsol'] is False,'fixed_domain_and_kernel')
  kernel=gaussian_support();out['gaussian_support']=kernel;ck(kernel['pass_dependency'],'limb_exception_does_not_reach_gate')
  # The code implementing these assumptions is pinned by the observed manifest.
  franja=frozen(env['V98_FRANJA'],m)
  with np.load(franja) as Q:
   centre=tuple(map(float,Q['centre']));qbox=tuple(map(int,Q['box']));qG=Q['G'].copy();qdom=Q['domini'].copy()
  out['limb_definition']=dict(centre=centre,exception='dL<1, matching frozen user source exactly',GATE='0 below40; smoothstep40..80')
  common=frozen(parameter.parent.parent/'3-RECERCA/tools/v97_refundacio_20260924/v97_comu.py',m)
  tree=ast.parse(common.read_text())
  geometry=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Tuple) and [e.id for e in n.targets[0].elts]==['CX','CY','RS'])
  if not ck(tuple(geometry)==SOLAR_GEOMETRY,'pinned_solar_geometry'):return out
  sx,sy,sr=SOLAR_GEOMETRY
  annulus_min_distance=5*sr-float(np.hypot(sx-centre[0],sy-centre[1]))-centre[2]
  out['base_dependency_scope']=dict(meaning='VAL intersect square-kernel dilation of GATE>0; SEC/HQ are subsets of that seed',solar_geometry=SOLAR_GEOMETRY,reference_annulus_min_dL_bound=annulus_min_distance)
  if not ck(annulus_min_distance>40,'sky_samples_inside_dependency_seed'):return out
  basepath=frozen(env['V108_BASE'],m);base=np.load(basepath,mmap_mode='r')
  if not ck(base.dtype.kind=='u' and base.dtype.itemsize==2 and base.shape==shape+(3,),'V108_BASE_RGB16'):return out
  science=Path(env['V97_FONTS']);G=np.load(frozen(science/'base_G.npy',m),mmap_mode='r');support=np.load(frozen(science/'support.npy',m),mmap_mode='r')
  if not ck(G.shape==shape and support.shape==shape,'science_domain_shape'):return out
  def domain_rows(y,end):
   gg=np.asarray(G[y:end]).copy();mm=np.asarray(support[y:end],bool)&np.isfinite(gg)&(gg>0)
   qy0,qy1,qx0,qx1=qbox;lo,hi=max(y,qy0),min(end,qy1)
   if hi>lo:
    mm[lo-y:hi-y,qx0:qx1]=qdom[lo-qy0:hi-qy0]&(qG[lo-qy0:hi-qy0]>0)
   raw=np.asarray(base[y:end],np.float32);B=(raw[...,0]+2*raw[...,1]+raw[...,2])/(4*65535);dl=d_limb(mm.shape,centre,y)
   influence=base_reaches_knee(mm.shape,centre,y,shape[0],kernel['radius_x'],kernel['radius_y'])
   return mm&(dl>=0)&(B>1e-4)&influence
  def channel(psb,lid,cid):
   layer=psb.layer(lid)
   if cid not in layer['chans']:return None
   if cid==-2:
    md=layer['mask'];fill=md['background']*257 if md else 0
   else:fill=0
   return psb.channel_box(lid,cid,(0,0,shape[1],shape[0]),fill=fill)
  def compare(lid,cid,expected,name):
   got=channel(active,lid,cid);original=channel(source,lid,cid)
   row=dict(layer=lid,channel=cid,role=name,**comparison_counts(got,expected,original,centre))
   out['channels'].append(row);ck(row.get('pass',False),'effective_input_channel',details=row)
   del got,original
  for lid in IDS:
   a,p=active.layer(lid),producer.layer(lid);fail=metadata_failures(a,p);out['rows'].append(dict(layer=lid,producer_opacity=p['opacity'],active_opacity=a['opacity'],metadata_failures=fail));ck(not fail,'operation_dependencies',layer=lid,details=fail)
   ck((a['left'],a['top'],a['right'],a['bottom'])==(0,0,shape[1],shape[0]),'full_canvas_operator_geometry',layer=lid)
   ma=channel(active,lid,-2);mp=channel(producer,lid,-2)
   ck((ma is None and mp is None) or (ma is not None and mp is not None and np.array_equal(ma,mp)),'exact_mask_canvas',layer=lid);del ma,mp
   if lid in (41,42):
    # This is the literal ALFA formula consumed by the pinned g1 code, not an arbitrary output file.
    al=np.empty(shape,np.uint16)
    for y in range(0,shape[0],ROW_BLOCK):al[y:y+ROW_BLOCK]=np.round(np.clip(d_limb(al[y:y+ROW_BLOCK].shape,centre,y),0,1)*65535).astype(np.uint16)
    compare(lid,-1,al,'literal_g1_ALPHA');del al
   else:
    aliases=m['g1_inputs']['g1_first']
    for suffix,cids in [('_alfa_u16.npy',[-1]),('_u16.npy',[0,1,2])]:
     alias=str(Path(argv[5])/(TAGS[lid]+suffix));resolved=aliases.get(alias)
     if not ck(bool(resolved) and str(Path(alias).resolve())==resolved,'bound_FSTD_alias',layer=lid,path=alias):return out
     fp=frozen(resolved,m)
     if not ck(trace['inputs'].get(str(fp))==m['files'][str(fp)],'actual_g1_read_input',path=str(fp)):return out
     expected=np.load(fp,mmap_mode='r')
     for cid in cids:compare(lid,cid,expected,'actual_g1_FSTD'+suffix)
     del expected
  # g1 B is the raw encoded RGB base. Validate both its values and absence of
  # alpha/mask attenuation on its physical model domain (outside the exception).
  la,lp=active.layer(3),producer.layer(3)
  ck(all(la[k]==lp[k] for k in ('left','top','right','bottom','mask','visible','opacity','blend','clipping')),'base_operation_matches_parameter_source')
  ck(la['visible'] and la['opacity']==255 and la['blend']=='NORMAL' and la['clipping']==0 and (la['mask'] is None or not la['mask']['disabled']),'base3_operator_assumptions')
  ck((la['left'],la['top'],la['right'],la['bottom'])==(0,0,shape[1],shape[0]),'base3_full_canvas')
  for cid in [0,1,2]:compare(3,cid,base[...,cid],'V108_BASE_RGB')
  for cid in [-1,-2]:
   aa=channel(active,3,cid);pp=channel(producer,3,cid)
   ck((aa is None and pp is None) or (aa is not None and pp is not None and np.array_equal(aa,pp)),'base_alpha_mask_matches_parameter_source',channel=cid)
   bad=0
   if aa is not None:
    for y in range(0,shape[0],ROW_BLOCK):
     end=min(y+ROW_BLOCK,shape[0]);bad+=int((domain_rows(y,end)&(aa[y:end]!=65535)).sum())
   ck(bad==0,'base_not_attenuated_on_model_domain',channel=cid,pixels=bad);out.setdefault('base_model_domain',[]).append(dict(channel=cid,nonopaque_pixels=bad));del aa,pp
  out['verified_input_hashes']={p:m['files'][p] for p,ok in verified.items() if ok}
  out['base_B_audited']=True
  if not out['failures']:out['status']='NECESSARY_DEPENDENCIES_PASS'
 except Exception as e:
  out['failures'].append(dict(check='semantic_verification_error',type=type(e).__name__,message=str(e)))
 out['limits']=['Necessary dependencies only: no independent sky estimate, no physical restoration proof, no SNR/injection/Brno approval.', 'Quantization q is declared Photoshop representation, not an optimized tolerance.', 'Full source roster/native recomposition/manual operation/lineage gates remain separately required.', 'A changed future producer or kernel requires a reviewed contract, not automatic acceptance by this helper.']
 return out
