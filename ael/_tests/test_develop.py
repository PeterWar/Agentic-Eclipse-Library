"""Regression tests for the 2024/2026 lessons, with broken-input controls."""
import json
import tempfile
from pathlib import Path
import numpy as np
from ael import filters
from ael.stack import full_resolution_affine, union_canvas, resample_frame, hot_pixel_mask, stack_from_config
from ael.filterbank import achf_isotropic, make_filter, NAMES
from ael.develop import filters_from_config, layer_alpha
from ael.geometry import EclipseGeometry


def raises(error,fn):
    try: fn()
    except error: return
    raise AssertionError(f'expected {error.__name__}')


def test_stack_cfa_pixel_centres_and_affine_negative_control():
    m=full_resolution_affine([[1,0,2],[0,1,-3]])
    assert np.array_equal(m,[[1,0,4],[0,1,-6]])
    shape,origin=union_canvas([(40,50)],[np.array([[1,0,0],[0,1,0]])])
    assert shape==(40,50) and origin==(0,0)
    y,x=np.mgrid[:40,:50].astype(np.float32)
    # Each colour samples the same affine ramp. Correct CFA offsets recover it exactly.
    value=100+2*x+3*y; ratio=np.full_like(value,.1)
    got,support,_,_=resample_frame(value,ratio,np.array([['R','G'],['G','B']]),x,y)
    region=(support>.999); region[:2]=False; region[-2:]=False; region[:,:2]=False; region[:,-2:]=False
    assert np.max(np.abs(got[region]-value[region,None]))<1e-4
    bad,*_=resample_frame(value,ratio,np.array([['R','G'],['G','B']]),x-.5,y-.5)
    assert np.median(np.abs(bad[region]-got[region]))>2


def test_stack_shared_taper_does_not_define_support():
    y,x=np.mgrid[:30,:40].astype(np.float32)
    v=np.ones((30,40,3),np.float32)*100
    r=np.zeros_like(v)+.2; r[...,1]=.95
    rgb,support,coverage,taper=resample_frame(v,r,None,x,y)
    assert np.all(support==1) and np.all(coverage==1)
    assert np.all((taper>0)&(taper<.2))
    assert taper.ndim==2 and rgb.shape[-1]==3
    r[...,1]=1.1
    _,support,coverage,taper=resample_frame(v,r,None,x,y)
    assert np.all(support==0) and np.all(coverage==1) and np.all(taper==0)


def test_hot_pixels_local_noise_rejects_persistent_not_shot_noise():
    rng=np.random.default_rng(7); y,x=np.mgrid[:100,:120]
    scene=100+10000*np.exp(-((x-60)**2+(y-50)**2)/180)
    planes=[]
    for _ in range(7):
        p=(scene+rng.normal(size=scene.shape)*np.sqrt(scene)).astype(np.float32)
        p[20,22]+=2000; p[75,91]+=2000
        planes.append(p)
    hot=hot_pixel_mask(planes,threshold=6,persistence=.8)
    assert hot[20,22] and hot[75,91]
    hot[20,22]=hot[75,91]=False
    assert hot.sum()<5,hot.sum()
    raises(ValueError,lambda:hot_pixel_mask(planes[:2]))


def _recipe(root,two_bands=False):
    y,x=np.mgrid[:70,:90].astype(np.float32)
    sky=30+.1*x+.05*y
    rgb=np.stack([sky*.7,sky,sky*.8],axis=-1)
    frames=[]
    for i,t in enumerate((.2,.6)):
        raw=rgb*t+512
        raw[10:15,10:15]=2000  # deliberately saturated in every exposure
        p=root/f'f{i}.npy'; np.save(p,raw)
        frames.append(dict(path=p.name,kind='rgb',iso=100,exposure_s=t,black=512,white=2000,
             reference_to_input=[[1,0,0],[0,1,0]],moon_xy=[44,34],moon_radius_px=10,cirrus_fraction=0))
    cfg=dict(geometry=dict(shape=[70,90],sun_xy=[44,34],sun_radius_px=10,moon_xy=[44,34],moon_radius_px=10),
             frames=frames,stack=dict(moon_guard_px=0,limb_fade_px=4,band_sigma_px=3 if two_bands else 0))
    p=root/'config.json'; p.write_text(json.dumps(cfg))
    return p,cfg,rgb


def test_stack_linear_hdr_support_two_bands_and_receipts():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        for mode in (False,True):
            p,cfg,truth=_recipe(root,mode)
            dest=root/f'stack_{mode}'; result=stack_from_config(p,dest,progress=lambda *_:None)
            image=np.load(dest/'linear.npy'); valid=np.load(dest/'valid.npy')
            assert np.isnan(image[10:15,10:15]).all()
            assert not valid[34,44]
            assert np.max(np.abs(image[valid]-truth[valid]))<.002
            assert result['shape']==(70,90)
            receipt=json.loads((dest/'receipt.json').read_text())
            assert receipt['inputs']['frame_0']['sha256']
            assert receipt['gates']['nothing_outside_data']
            raises(FileExistsError,lambda:stack_from_config(p,dest,progress=lambda *_:None))
        cfg['stack']['clouds']=True; p.write_text(json.dumps(cfg))
        raises(ValueError,lambda:stack_from_config(p,root/'bad_cloud'))
        cfg['stack']['clouds']=False; cfg['frames'][1]['iso']=200; p.write_text(json.dumps(cfg))
        raises(ValueError,lambda:stack_from_config(p,root/'bad_iso'))
        assert not (root/'bad_iso').exists()


def test_isotropic_radial_null_offcentre_moon_and_negative_control():
    geo=EclipseGeometry((360,430),(198.2,185.3),65,(211.2,177.3),67)
    r=geo.radius_map(); m=~geo.moon_mask(4)
    m[140:180,300:]=False
    a=np.maximum(r,1)**-3
    fixed,info=achf_isotropic(a,m,geo,sigmas=(2,4,8,16),outer_sigma=0)
    log=np.log(a)
    broken=log-filters.normalized_gaussian(log,m,16,min_support=.01)
    limb=m & (geo.radius_map('moon')<geo.moon_radius_px+20)
    assert np.sqrt(np.mean(fixed[limb]**2))<.015
    assert np.std(broken[limb])>5*np.std(fixed[limb])
    assert np.isnan(fixed[~m]).all()
    # An actual angular signal survives; simply zeroing the filter cannot pass.
    injected=a*(1+.03*np.sin(np.radians(geo.pa_map())*30))
    response,_=achf_isotropic(injected,m,geo,sigmas=(2,4,8,16),outer_sigma=0)
    band=m & (r>1.4*65) & (r<2.5*65)
    signal=np.sin(np.radians(geo.pa_map())*30)
    assert np.corrcoef(response[band],signal[band])[0,1]>.95


def test_filterbank_all16_preserve_observed_domain_and_multiply_ramp():
    geo=EclipseGeometry((110,140),(65.2,55.3),18,(67,55),19)
    r=geo.radius_map(); theta=np.radians(geo.pa_map())
    a=(100*np.maximum(r/18,1)**-3*(1+.1*np.sin(12*theta))).astype(np.float32)
    m=~geo.moon_mask(2); m[20:35,105:120]=False
    alpha=np.where(m,np.clip((geo.radius_map('moon')-21)/5,0,1),0)
    assert len(NAMES)==16
    for name in NAMES:
        layer,mode,info=make_filter(name,a,m,geo)
        assert np.isfinite(layer[m]).any(),name
        assert np.isnan(layer[~m]).all(),name
        observed=m&np.isfinite(layer)
        al=layer_alpha(alpha,observed,mode)
        assert np.array_equal(al[observed],alpha.astype(np.float32)[observed])
        assert (al[~observed]==0).all()
    bad=alpha.copy(); bad[0,0]=np.nan
    raises(ValueError,lambda:layer_alpha(bad,m,'multiply'))


def test_filters_command_psb_roundtrip_relative_paths_and_immutable_output():
    import importlib.util,unittest
    if importlib.util.find_spec('psd_tools') is None: raise unittest.SkipTest('psd-tools not installed')
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); geo=EclipseGeometry((100,130),(62,49),15,(64,49),16)
        r=geo.radius_map(); m=~geo.moon_mask(3)
        image=(100*np.maximum(r/15,1)**-3*(1+.1*np.cos(np.radians(geo.pa_map())*16))).astype(np.float32)
        image[~m]=np.nan
        np.save(root/'input.npy',image); np.save(root/'valid.npy',m); geo.to_json(root/'geometry.json')
        cfg=dict(input='input.npy',valid='valid.npy',geometry='geometry.json',display=dict(scale=100,asinh=20),photoshop=True)
        p=root/'filters.json'; p.write_text(json.dumps(cfg))
        result=filters_from_config(p,root/'out',progress=lambda *_:None)
        rec=json.loads(Path(result['receipt']).read_text())
        assert rec['gates']['photoshop_roundtrip']['ok']
        assert rec['gates']['photoshop_roundtrip']['layers']==6
        assert rec['gates']['photoshop_native'].startswith('not checked')
        raises(FileExistsError,lambda:filters_from_config(p,root/'out',progress=lambda *_:None))


def test_two_band_cirrus_weighting_preserves_fine_detail():
    # Two equally exposed observations: one carries a broad cloud residual.
    # Declared cirrus variance must reduce its coarse contamination while leaving
    # common fine structure at its measured amplitude.
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); y,x=np.mgrid[:100,:140].astype(np.float32)
        fine=2*np.sin(x*2*np.pi/8)
        truth=80+fine
        cloud=20*np.exp(-((x-90)**2+(y-50)**2)/500)
        frames=[]
        for i in range(2):
            a=truth+(cloud if i else 0)
            np.save(root/f'{i}.npy',np.repeat((a+512)[...,None],3,axis=-1))
            frames.append(dict(path=f'{i}.npy',kind='rgb',iso=100,exposure_s=1,black=512,white=16000,
                reference_to_input=[[1,0,0],[0,1,0]],moon_xy=[-50,-50],moon_radius_px=5,
                cirrus_fraction=.3 if i else .001))
        cfg=dict(frames=frames,geometry=dict(shape=[100,140],sun_xy=[-50,-50],sun_radius_px=5),
                 stack=dict(band_sigma_px=3,gain_e_per_dn=10,read_noise_dn=0))
        p=root/'recipe.json'; p.write_text(json.dumps(cfg))
        stack_from_config(p,root/'two',progress=lambda *_:None)
        cfg['stack']['band_sigma_px']=0;p.write_text(json.dumps(cfg))
        stack_from_config(p,root/'one',progress=lambda *_:None)
        two=np.load(root/'two/linear.npy')[...,1];one=np.load(root/'one/linear.npy')[...,1]
        roi=np.s_[25:75,60:120]
        assert np.sqrt(np.mean((two[roi]-truth[roi])**2))<.1*np.sqrt(np.mean((one[roi]-truth[roi])**2))
        # A common sinusoid remains at full amplitude in a cloud-free strip.
        strip=np.s_[10:20,10:60]
        amplitude=np.sum((two[strip]-80)*fine[strip])/np.sum(fine[strip]**2)
        assert .9<amplitude<1.1,amplitude


def test_hot_pixel_does_not_suppress_neighbouring_valid_colour_taper():
    y,x=np.mgrid[:20,:24].astype(np.float32)
    a=np.full((20,24,3),100,np.float32);ratio=np.full_like(a,.1)
    hot=[np.zeros((20,24),bool) for _ in range(3)]
    hot[0][8,8]=True;ratio[8,8,0]=100
    _,support,_,taper=resample_frame(a,ratio,None,x+.5,y,hot=hot)
    assert support[8,7]==.5
    assert taper[8,7]==1


def test_stack_rejects_unknown_scientific_parameters_before_writing():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); p,cfg,_=_recipe(root)
        cfg['stack']['limp_fade_px']=3;p.write_text(json.dumps(cfg))
        raises(ValueError,lambda:stack_from_config(p,root/'out'))
        assert not (root/'out').exists()
