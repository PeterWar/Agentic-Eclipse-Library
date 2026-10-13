"""Regression controls from a nine-exposure field case; no private image fixtures."""
import json
import tempfile
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from ael import filters
from ael.filterbank import make_filter, display_detail, radial_rank, NAMES
from ael.develop import tone_map, filters_from_config
from ael.geometry import EclipseGeometry
from . import _radial_legacy as legacy


def _period2(a, r, m, lo=90., hi=260.):
    sel=m & np.isfinite(a) & (r>=lo) & (r<hi)
    bins=np.floor((r[sel]-lo)*4).astype(int)
    count=np.bincount(bins,minlength=int((hi-lo)*4))
    profile=np.bincount(bins,weights=a[sel],minlength=len(count))/np.maximum(count,1)
    radii=lo+(np.arange(len(count))+.5)/4
    hp=profile-gaussian_filter1d(profile,16)
    return float(2*abs(np.mean(hp*np.exp(-2j*np.pi*radii/2))))


def _old_layer(name,a,m,g):
    if name.startswith('nrgf'):
        q=legacy.nrgf(np.log(a) if name=='nrgf_log' else a,m,g,bin_px=2,min_count=12,smooth_bins=3)
        return display_detail(q,m)[0]
    sector=60 if name.endswith('60') else 30 if name.endswith('30') else None
    q=legacy.radial_rank(a,m,g,sector)
    if name=='rhef_upsilon':
        q=np.where(q<.5,.5*np.maximum(2*q,0)**.35,1-.5*np.maximum(2-2*q,0)**.35)
    return q


def test_radial_rings_negative_control_and_seeded_angular_detail():
    g=EclipseGeometry((640,768),(310.3,370.7),60,(310.3,370.7),60)
    r=g.radius_map(); theta=np.radians(g.pa_map()); m=r>65
    a=((np.maximum(r,1)/60)**-3*(1+.3*np.cos(3*theta)+.1*np.sin(7*theta))).astype(np.float32)
    rng=np.random.default_rng(20261005)
    signal=.005*np.sin(37*theta+rng.uniform(-np.pi,np.pi))*np.exp(-((r-160)/65)**4)
    injection=(a*np.exp(signal)).astype(np.float32)
    for name in NAMES[:6]:
        old=_old_layer(name,a,m,g); new=make_filter(name,a,m,g)[0]
        before=_period2(old,r,m); after=_period2(new,r,m)
        assert before>.001, (name,'negative failed to detect rings',before)
        assert after<.1*before, (name,before,after)
        dn=make_filter(name,injection,m,g)[0]-new
        do=_old_layer(name,injection,m,g)-old
        sel=m & (r>90) & (r<260) & np.isfinite(dn) & np.isfinite(do)
        old_transfer=np.sum(do[sel]*signal[sel])/np.sum(signal[sel]**2)
        new_transfer=np.sum(dn[sel]*signal[sel])/np.sum(signal[sel]**2)
        assert .9 <= new_transfer/old_transfer <= 1.3,(name,old_transfer,new_transfer)
        assert np.isnan(new[~m]).all()


def test_radial_sparse_gaps_and_invalid_values_do_not_create_data():
    g=EclipseGeometry((170,210),(99.3,87.1),20)
    r=g.radius_map(); m=(r>24)&~((r>55)&(r<65));m[10:35,145:]=False
    a=(np.maximum(r,1)**-2*(1+.2*np.cos(np.radians(g.pa_map())*5))).astype(np.float32)
    poison=a.copy();poison[~m]=1e30
    for name in NAMES[:6]:
        q=make_filter(name,a,m,g)[0]; other=make_filter(name,poison,m,g)[0]
        assert np.array_equal(q,other,equal_nan=True),name
        assert np.isnan(q[~m]).all(),name
    empty=np.zeros(m.shape,bool)
    assert np.isnan(radial_rank(a,empty,g)).all()
    assert np.isnan(filters.nrgf(a,empty,g)).all()
    # A handful of isolated pixels cannot become valid via neighbouring annuli.
    sparse=np.zeros_like(m);sparse[2,3]=True
    assert np.isnan(radial_rank(a,sparse,g)).all()
    assert np.isnan(filters.nrgf(a,sparse,g)).all()


def test_quantile_constant_and_tied_intensities():
    class OneAnnulus(EclipseGeometry):
        def radius_map(self, *args, **kwargs):
            return np.ones(self.shape,np.float32)*20.5
    g=OneAnnulus((20,20),(10,10),2);m=np.ones(g.shape,bool)
    assert np.all(radial_rank(np.ones(g.shape),m,g)==.5)
    a=np.ones(g.shape);a[10:]=2
    rank=radial_rank(a,m,g)
    assert np.max(np.abs(rank[:10]-.25))<.005
    assert np.max(np.abs(rank[10:]-.75))<.005


def test_display_shoulder_preserves_bright_order_and_asinh_colour_ratios():
    x=np.geomspace(.1,1e6,120)
    rgb=np.stack([x,.7*x,.25*x],axis=-1)[None]
    m=np.ones(rgb.shape[:2],bool);original=rgb.copy()
    fixed=tone_map(rgb,m,scale=10,strength=20)
    broken=np.clip(np.arcsinh(rgb/10*20)/np.arcsinh(20),0,1)
    assert np.all(broken[0,x>100]==1)  # The old display destroyed distinctions.
    assert np.all(np.diff(fixed[0,:,0])>0)
    assert fixed.max()<1 and np.array_equal(rgb,original)
    u=np.arcsinh(rgb/10*20)/np.arcsinh(20)
    assert np.max(np.abs(fixed[...,1]/fixed[...,0]-u[...,1]/u[...,0]))<1e-6
    assert np.max(np.abs(fixed[...,2]/fixed[...,0]-u[...,2]/u[...,0]))<1e-6
    m[0,5]=False;rgb[0,5]=np.nan
    assert np.all(tone_map(rgb,m,scale=10)[0,5]==0)


def test_display_rejects_invalid_parameters_before_output():
    a=np.ones((2,2,3));m=np.ones((2,2),bool)
    for kwargs in [dict(scale=0),dict(scale=np.nan),dict(scale=1,strength=-2),
                   dict(scale=1,highlight_ceiling=1),dict(scale=1,highlight_ceiling=1-1e-9),
                   dict(scale=1,highlight_ceiling=0)]:
        try: tone_map(a,m,**kwargs)
        except ValueError: pass
        else: raise AssertionError(kwargs)


def test_filters_psb_bright_reference_and_receipt_match_pixels():
    import importlib.util, unittest
    if importlib.util.find_spec('psd_tools') is None:
        raise unittest.SkipTest('psd-tools not installed')
    from psd_tools import PSDImage
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);g=EclipseGeometry((120,150),(71.3,63.4),18)
        r=g.radius_map();m=r>22
        a=(10000*np.maximum(r/18,1)**-3*(1+.3*np.cos(np.radians(g.pa_map())*7))).astype(np.float32)
        rgb=np.stack([a,.7*a,.4*a],axis=-1);np.save(root/'input.npy',rgb);np.save(root/'valid.npy',m);g.to_json(root/'g.json')
        cfg=dict(input='input.npy',valid='valid.npy',geometry='g.json',display=dict(scale=10,asinh=20),
                 filters=['nrgf'],visible=[],photoshop=True)
        p=root/'f.json';p.write_text(json.dumps(cfg));result=filters_from_config(p,root/'out',progress=lambda *_:None)
        rec=json.loads(Path(result['receipt']).read_text());info=rec['parameters']['display'];doc=PSDImage.open(result['files']['psb'])
        ref=doc[1].numpy('color');base=doc[2].numpy('color')
        assert rec['gates']['positive_display_base_not_clipped']
        assert info['positive_base_clip_pixels']==0 and rec['gates']['photoshop_roundtrip']['ok']
        assert np.max(ref)<1 and np.max(base)<1
        assert abs(np.max(ref)-.98)<2/65535
        assert np.max(np.abs(ref[m]*info['linear_reference_scale']-rgb[m]))<info['linear_reference_scale']/65535
        assert np.array_equal(np.load(root/'input.npy'),rgb)


def test_sensor_flat_precedes_cfa_warp_and_preserves_saturation_weights():
    from ael.stack import _prepare, resample_frame
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);y,x=np.mgrid[:60,:80].astype(np.float32)
        truth=120+3*x+2*y
        response=1-.4*np.exp(-((x-35)**2+(y-28)**2)/12)
        np.save(root/'raw.npy',512+.4*truth*response);np.save(root/'flat.npy',response)
        f=dict(path='raw.npy',kind='bayer',pattern=[['R','G'],['G','B']],
               exposure_s=.4,black=512,white=10000,flat='flat.npy')
        v,ratio,pat=_prepare(f,root)
        rgb,support,coverage,taper=resample_frame(v,ratio,pat,x+1.3,y-.7)
        uncal=dict(f);uncal.pop('flat');uv,ur,up=_prepare(uncal,root)
        bad,us,uc,ut=resample_frame(uv,ur,up,x+1.3,y-.7)
        assert np.array_equal(ratio,ur)
        assert np.array_equal(support,us) and np.array_equal(coverage,uc) and np.array_equal(taper,ut)
        inside=(x>5)&(x<70)&(y>5)&(y<50)
        expected=120+3*(x+1.3)+2*(y-.7)
        assert np.max(np.abs(rgb[inside]-expected[inside,None]))<.001
        # Wrong-stage control: the native dust map divided after the warp is misregistered.
        bad=bad/response[...,None]
        assert np.max(np.abs(bad[inside]-expected[inside,None]))>10


def test_stack_reference_canvas_is_explicit_and_keeps_native_geometry():
    from ael.stack import stack_from_config
    from .test_develop import _recipe, raises
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);p,cfg,_=_recipe(root)
        cfg['frames'][1]['reference_to_input']=[[1,0,3],[0,1,-2]]
        cfg['stack']['canvas']='reference';p.write_text(json.dumps(cfg))
        result=stack_from_config(p,root/'native',progress=lambda *_:None)
        assert result['shape']==(70,90)
        outgeo=json.loads((root/'native/geometry.json').read_text())
        assert outgeo['sun_xy']==cfg['geometry']['sun_xy']
        cfg['stack']['canvas']='union';p.write_text(json.dumps(cfg))
        result=stack_from_config(p,root/'union',progress=lambda *_:None)
        assert result['shape']==(72,93)
        cfg['stack']['canvas']='crop';p.write_text(json.dumps(cfg))
        raises(ValueError,lambda:stack_from_config(p,root/'bad'))
        assert not (root/'bad').exists()




def _ring_band(a, r, m, lo, hi, pa=None, sector=None, pmin=2., pmax=16.):
    """RMS of the azimuthal-mean profile in the 2–16 px period band, after removing a smooth trend.

    A filtered, weighted RMS: it detects concentric structure, it is not a bound on every ring. Returns None
    when a radial bin of the region has no data (gaps are not interpolated away).
    """
    sel=m & np.isfinite(a) & (r>=lo) & (r<hi)
    if sector is not None:
        sel&=np.abs((pa-sector+180)%360-180)<22.5
    bins=np.floor((r[sel]-lo)*4).astype(int)
    count=np.bincount(bins,minlength=int((hi-lo)*4))[:int((hi-lo)*4)]
    if (count==0).any():
        return None
    profile=np.bincount(bins,weights=a[sel],minlength=len(count))[:len(count)]/count
    x=(np.arange(len(count))-len(count)/2)/len(count)
    profile=profile-np.polyval(np.polyfit(x,profile,5),x)
    freq=np.fft.rfftfreq(len(profile),.25); spec=np.fft.rfft(profile*np.hanning(len(profile)))
    band=np.fft.irfft(np.where((freq>=1/pmax)&(freq<=1/pmin),spec,0),n=len(profile))
    cut=len(band)//8
    return float(np.sqrt(np.mean(band[cut:-cut]**2)))


def _ring_free_scene(moon_xy=(310.3,370.7)):
    g=EclipseGeometry((640,768),(310.3,370.7),60,moon_xy,61)
    r=g.radius_map(); pa=g.pa_map(); theta=np.radians(pa)
    m=g.radius_map('moon')>63
    m[:,700:]=False                                   # a straight coverage edge
    a=((np.maximum(r,1)/60)**-3*(1+.3*np.cos(3*theta)+.1*np.sin(7*theta))).astype(np.float32)
    return g,r,pa,theta,m,a


_ZONES=((70,110),(110,220),(220,268))      # limb, middle, outer: inside the largest Sun-centred circle (269 px)
                                            # clear of the frame and of the coverage edge


def test_no_filter_makes_rings_on_a_ring_free_input():
    """All sixteen filters, not only the radial ones (issue #1 blamed rings on ACHF/MGN/WOW).

    In this scene (a ring-free corona with angular structure and no noise, the Moon on the Sun's centre, a
    straight coverage edge) and these regions: two-pixel grooves with the 1.2.1 measure; rings of 2–16 px over
    whole rings in three radial zones inside the largest circle clear of the edges and, in the middle and outer
    zones, in all eight 45° sectors (near the limb a 45° sector holds too few pixels to tell the controls from the
    filters); the support of every filter band by band from the lunar limb and from the straight edge, and in
    every sector. The sectors are fixed by the input, so an output cannot avoid one by leaving it empty. Positive
    controls must be detected. Not checked here, because they are reported limitations (docs/FIELD_LESSONS.md):
    the bands that an off-centre Moon or a straight edge make in ACHF and WOW, and the structure WOW bilateral
    draws in sectors of a noise-free corona.
    """
    g,r,pa,theta,m,a=_ring_free_scene()
    rm=g.radius_map('moon'); yy,xx=np.mgrid[0:m.shape[0],0:m.shape[1]]
    assert min(g.sun_xy[0],g.sun_xy[1],m.shape[0]-g.sun_xy[1],700-g.sun_xy[0])>_ZONES[-1][1]

    def sector(lo,hi,c):
        return m & (r>=lo) & (r<hi) & (np.abs((pa-c+180)%360-180)<22.5)
    sectors=[(lo,hi,c) for lo,hi in _ZONES[1:] for c in range(0,360,45)]
    assert all(_ring_band(np.where(m,1.,np.nan),r,m,lo,hi,pa,c) is not None for lo,hi,c in sectors)
    old2=_old_layer('nrgf',a,m,g)
    assert _period2(old2,r,m)>.005
    old10=display_detail(legacy.nrgf(a,m,g,bin_px=10,min_count=12,smooth_bins=0),m)[0]
    rings=sum(np.sin(2*np.pi*r/p) for p in (8,9,10))/3
    base=make_filter('achf_iso_04',a,m,g)[0]
    for control in (old10,np.where(m,base+.1*rings,np.nan)):
        assert all(_ring_band(control,r,m,lo,hi)>.005 for lo,hi in _ZONES)
    assert all(_ring_band(np.where(m,base+.02*rings,np.nan),r,m,lo,hi)>.005 for lo,hi in _ZONES[:2])
    holed=base.copy(); holed[(rm>=63)&(rm<66)]=np.nan                      # a layer that drops a band at the limb
    assert np.isfinite(holed[m & (rm>=63) & (rm<64)]).mean()<.99
    cut=base.copy(); cut[sector(220,268,0)]=np.nan                          # a layer that drops a whole sector
    assert np.isfinite(cut[sector(220,268,0)]).mean()<.99
    for name in NAMES:
        layer=make_filter(name,a,m,g)[0]
        assert np.isnan(layer[~m]).all(), name
        first=2 if name.startswith('achf_angular') else 0                   # its angular kernel needs neighbours
        for d in range(first,20):
            assert np.isfinite(layer[m & (rm>=63+d) & (rm<64+d)]).mean()>=.99, (name,'limb',d)
            assert np.isfinite(layer[m & (yy>150) & (yy<470) & (xx==699-d)]).mean()>=.99, (name,'edge',d)
        for lo,hi,c in sectors:
            assert np.isfinite(layer[sector(lo,hi,c)]).mean()>=.99, (name,'sector',lo,hi,c)
        assert _period2(layer,r,m)<.15*_period2(old2,r,m), name
        whole=[_ring_band(layer,r,m,lo,hi) for lo,hi in _ZONES]
        assert max(whole)<.005, (name,whole)
        if name!='wow_bilateral':
            values=[_ring_band(layer,r,m,lo,hi,pa,c) for lo,hi,c in sectors]
            assert max(values)<.005, (name,max(values))


# Transfer of a faint injected pattern by each layer in 1.3.0 (display units per unit ln I), measured on this scene.
_DETAIL_GAIN={'nrgf':.64,'nrgf_log':.62,'rhef':1.25,'rhef_upsilon':.92,'rhef_local60':2.83,'rhef_local30':5.47,
              'achf_angular':19.18,'achf_angular4':30.22,'achf_angular8':10.28,'achf_iso_01':6.72,'achf_iso_04':17.86,
              'achf_iso_05':4.05,'achf_iso_06':3.31,'mgn':6.63,'wow':14.73}


def test_filters_keep_injected_fine_detail_with_its_sign_and_strength():
    """A faint angular pattern added to the corona must come out with its own sign and its 1.3.0 strength (±25 %).

    WOW bilateral is left out on purpose: it can return faint fine detail with the opposite sign, a reported
    limitation (docs/FIELD_LESSONS.md); its correction will have to bring it into this test.
    """
    g,r,pa,theta,m,a=_ring_free_scene()
    rng=np.random.default_rng(20261005)
    signal=.005*np.sin(37*theta+rng.uniform(-np.pi,np.pi))*np.exp(-((r-160)/65)**4)
    noise=(1+.003*np.random.default_rng(1).standard_normal(a.shape)).astype(np.float32)
    clean=(a*noise).astype(np.float32); injected=(a*np.exp(signal)*noise).astype(np.float32)
    sel=m & (r>90) & (r<260)
    assert set(_DETAIL_GAIN)==set(NAMES)-{'wow_bilateral'}
    for name,expected in _DETAIL_GAIN.items():
        change=make_filter(name,injected,m,g)[0]-make_filter(name,clean,m,g)[0]
        ok=sel & np.isfinite(change)
        corr=float(np.corrcoef(change[ok],signal[ok])[0,1])
        gain=float(np.sum(change[ok]*signal[ok])/np.sum(signal[ok]**2))
        assert corr>.5 and abs(gain/expected-1)<.25, (name,corr,gain)
