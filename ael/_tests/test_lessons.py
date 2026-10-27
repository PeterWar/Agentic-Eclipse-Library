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


# ---- 1.3.4: lessons from Edu's reports (issues #4 and #9) and from the rings they led to -------------------------

def test_default_layers_are_sign_tested_and_have_a_starting_opacity():
    """Every default layer must be in the sign-and-strength test and have a declared starting opacity (an undeclared
    one fell back to 1.00 without any warning). The 1.3.3 defaults fail the first condition: WOW bilateral was the
    default and is not in the sign test."""
    from ael.filterbank import DEFAULTS
    from ael.develop import DEFAULT_OPACITY
    assert set(DEFAULTS) <= set(_DETAIL_GAIN), DEFAULTS
    assert set(DEFAULTS) <= set(DEFAULT_OPACITY), (DEFAULTS, DEFAULT_OPACITY)
    assert DEFAULT_OPACITY['wow_bilateral'] == .37                         # a 1.3.3 recipe keeps its look
    assert not {'nrgf', 'wow_bilateral', 'achf_iso_04'} <= set(_DETAIL_GAIN)


def test_tangential_mean_removal_drops_a_ring_and_keeps_a_ray():
    """The step that keeps the WOW of 1.3.4 from turning a radial-curve residual into a ring: along each circle around
    the Sun it removes the local mean (here with a 10° window; the default is 45°). A ring is constant along its circle and goes; a ray varies along it and
    stays. Negative control: removing an isotropic local mean of 32 px (as the coarse scales of 1.3.3 did) leaves
    half of a 40 px ring."""
    from ael.filterbank import _tangential_frame, _tangential_mean_removed
    g = EclipseGeometry((401, 401), (200., 200.), 40, None, None)
    r = g.radius_map(); yy, xx = np.mgrid[0:401, 0:401]; th = np.degrees(np.arctan2(yy - 200., xx - 200.))
    m = r < 195
    ring = ((r > 120) & (r < 160)).astype(np.float32)
    dth = (th - 40 + 180) % 360 - 180; ray = (np.exp(-.5 * (dth / 2.) ** 2) * ((r > 50) & (r < 190))).astype(np.float32)
    s = (ring + ray + .1 * np.random.default_rng(2).standard_normal(r.shape)).astype(np.float32)
    out = _tangential_mean_removed(s, m, _tangential_frame(m, g), 10.)
    iso = s - np.nan_to_num(filters.normalized_gaussian(np.where(m, s, np.nan), m, 32., .01))
    on_ring = m & (ring > 0) & (np.abs(dth) > 30)
    on_ray = m & (np.abs(dth) < 1) & (r > 125) & (r < 155); beside = m & (np.abs(dth) > 8) & (np.abs(dth) < 20) & (r > 125) & (r < 155)
    assert abs(np.median(out[on_ring])) < .05
    assert np.median(out[on_ray]) - np.median(out[beside]) > .7
    assert np.median(iso[on_ring]) > .3                                    # the control keeps the ring


def _knee_scene(sky=.011, noise=.01, seed=11, R=30):
    """A small Sun on a wide frame and a sky that flattens the profile (a 'knee', as on real data): the fixed-knot
    radial curve cannot follow it and leaves ring-shaped residuals."""
    g = EclipseGeometry((640, 768), (310.3, 370.7), R, (310.3, 370.7), R + 1)
    r = g.radius_map(); th = np.radians(g.pa_map()); m = g.radius_map('moon') > R + 3
    a = ((np.maximum(r, 1) / R) ** -3 * (1 + .3 * np.cos(3 * th) + .1 * np.sin(7 * th)) + sky).astype(np.float32)
    return g, m, a * (1 + noise * np.random.default_rng(seed).standard_normal(a.shape)).astype(np.float32)


def _ring_levels(layer, g, m, r0=2., r1=9., w=.1, n=8):
    rs = g.rsun_map(); pa = (g.pa_map() + 360) % 360; out = []
    for a0 in np.arange(r0, r1, w):
        vals = [np.median(layer[k]) - .5 for s in range(n)
                for k in [m & np.isfinite(layer) & (rs >= a0) & (rs < a0 + w) & (pa >= s * 360 / n) & (pa < (s + 1) * 360 / n)]
                if k.sum() > 30]
        if len(vals) >= 6: out.append(float(np.median(vals)))
    return np.array(out)


def test_wow_does_not_turn_the_radial_curve_residual_into_rings():
    """Issue #4 follow-up: on the author's 2026 data plain WOW made a dark ring at 4.75 R☉ out of a -0.5 % residual of
    the radial curve. Here the same mechanism on a synthetic knee: the WOW of 1.3.4 must keep the ring levels (median
    of 8 sectors in rings of 0.1 R☉, 2–9 R☉) well below those of the same WOW without the tangential step."""
    from ael.filterbank import radial_log_residual, wow_measured
    g, m, a = _knee_scene()
    layer = make_filter('wow', a, m, g)[0]
    res, _ = radial_log_residual(a, m, g); q, _ = wow_measured(res, m, g, tangential_from=99)
    rs = g.rsun_map(); control = display_detail(q, m, scale_region=(rs >= 1.1) & (rs < 2.))[0]
    rms = lambda x: float(np.sqrt(np.mean(_ring_levels(x, g, m) ** 2)))
    assert rms(layer) < .8 * rms(control), (rms(layer), rms(control))


def _tangent_radial_index(layer, g, m, r0, r1, lag):
    from scipy.ndimage import map_coordinates
    cx, cy = g.sun_xy; yy, xx = np.mgrid[0:layer.shape[0], 0:layer.shape[1]]
    k = m & (g.radius_map() >= r0) & (g.radius_map() < r1) & np.isfinite(layer)
    ys, xs = yy[k].astype(float), xx[k].astype(float)
    ur = np.stack([xs - cx, ys - cy]); ur /= np.hypot(*ur); ut = np.stack([-ur[1], ur[0]])
    a0 = layer[k]
    ar = map_coordinates(layer, [ys + lag * ur[1], xs + lag * ur[0]], order=1, cval=np.nan)
    at = map_coordinates(layer, [ys + lag * ut[1], xs + lag * ut[0]], order=1, cval=np.nan)
    def rho(x, y):
        o = np.isfinite(x) & np.isfinite(y); x = x[o] - x[o].mean(); y = y[o] - y[o].mean()
        return float((x * y).sum() / np.sqrt((x * x).sum() * (y * y).sum()))
    return rho(a0, ar) / rho(a0, at)


def test_wow_leaves_the_noise_texture_isotropic():
    """The tangential step must not leave radial streaks (or arcs) in the noise of the outer field: the correlation at
    4 and 6 px along the radius and along the circle stay equal (index within 2.5 %). The controls are independent of
    the layer: the same layer plus radial streaks, or plus arcs, made from another noise field (smoothed along the
    radius over 3 px, or along the circle over 2°) with a third of the layer's spread, must both be caught. A
    tangential step of 1° instead of 45° streaks the layer itself and fails."""
    from scipy import ndimage as ndi
    from ael.filterbank import _tangential_frame, _tangential_mean_removed
    g = EclipseGeometry((640, 768), (310.3, 370.7), 60, (310.3, 370.7), 61)
    r = g.radius_map(); th = np.radians(g.pa_map()); m = g.radius_map('moon') > 63
    a = ((np.maximum(r, 1) / 60) ** -3 * (1 + .3 * np.cos(3 * th) + .1 * np.sin(7 * th))).astype(np.float32)
    a = a * (1 + .05 * np.random.default_rng(3).standard_normal(a.shape)).astype(np.float32)
    layer = make_filter('wow', a, m, g)[0]; fr = _tangential_frame(m, g)
    n = np.where(m, np.random.default_rng(11).standard_normal(m.shape), 0).astype(np.float32)
    p = ndi.gaussian_filter1d(ndi.map_coordinates(n, [fr['Y'], fr['X']], order=1, mode='constant'), 3., axis=0)
    radial = ndi.map_coordinates(np.concatenate([p, p[:, :1]], 1), [fr['r'], fr['ti']], order=1, mode='nearest')
    unit = lambda x: x / np.std(x[m])
    k = np.std(layer[m & (g.radius_map() >= 200)]) / 3
    streaks = np.where(m, layer + k * unit(radial), np.nan)
    arcs = np.where(m, layer + k * unit(n - _tangential_mean_removed(n, m, fr, 2.)), np.nan)
    for lag in (4, 6):
        assert .975 <= _tangent_radial_index(layer, g, m, 200, 268, lag) <= 1.025, lag
        for control in (streaks, arcs):
            assert not .975 <= _tangent_radial_index(control, g, m, 200, 268, lag) <= 1.025, lag


def test_achf_does_not_burn_the_limb_when_the_sky_is_in_the_frame():
    """Issue #9 (Edu): with the sky in the frame most pixels are faint outer field, one whole-image spread is small
    and the ACHF detail next to the limb saturates in blocks of pure black and white. The per-ring display of 1.3.4
    keeps both tails under 1 % and the median at 0.5 from the limb to 2.5 R☉; the 1.3.3 display ('global') is the
    negative control."""
    g, m, a = _knee_scene(sky=.001, noise=.002, seed=5)
    rs = g.rsun_map()
    assert np.array_equal(make_filter('achf_iso_04', a, m, g)[0], make_filter('achf_iso_04', a, m, g, achf_display='rings')[0],
                          equal_nan=True)                                       # 'rings' is the default
    for disp, ok in (('rings', True), ('global', False)):
        q = make_filter('achf_iso_04', a, m, g, achf_display=disp)[0]
        for lo, hi in ((1.08, 1.5), (1.5, 2.5)):
            k = m & np.isfinite(q) & (rs >= lo) & (rs < hi)
            tails = max(np.mean(q[k] <= .01), np.mean(q[k] >= .99))
            if ok: assert tails < .01 and abs(np.median(q[k]) - .5) < .02, (lo, tails)
            else: assert tails > .1, (lo, tails)


def test_fine_detail_gate_passes_wow_and_fails_bilateral_and_inverted_detail():
    """The real-data gate Edu proposed in issue #4 (ael.gates.fine_detail_fidelity), on a synthetic eclipse with fine
    angular structure and two independent noise realisations: the WOW of 1.3.4 passes; WOW bilateral and a WOW with
    its detail inverted fail. Rings where the reference fails its own rotation null are not judged."""
    from ael.gates import fine_detail_fidelity
    g = EclipseGeometry((640, 768), (310.3, 370.7), 60, (310.3, 370.7), 61)
    r = g.radius_map(); th = np.radians(g.pa_map()); m = g.radius_map('moon') > 63
    rng = np.random.default_rng(1234)
    fine = sum(rng.uniform(.004, .012) * np.sin(k * th + rng.uniform(0, 2 * np.pi)) for k in range(20, 140, 2))
    a = ((np.maximum(r, 1) / 60) ** -3 * (1 + .3 * np.cos(3 * th)) * np.exp(fine)).astype(np.float32)
    A, B = (a * (1 + .004 * np.random.default_rng(s).standard_normal(a.shape)).astype(np.float32) for s in (1, 2))
    rings = ((1.3, 1.6), (1.6, 2.0))
    wa, wb = make_filter('wow', A, m, g)[0], make_filter('wow', B, m, g)[0]
    res = fine_detail_fidelity(wa, wb, A, B, m, g, rings=rings)
    assert any(x['accredited'] for x in res['rings']) and res['passed'] is True, res
    assert fine_detail_fidelity(1 - wa, 1 - wb, A, B, m, g, rings=rings)['passed'] is False
    ba, bb = make_filter('wow_bilateral', A, m, g)[0], make_filter('wow_bilateral', B, m, g)[0]
    assert fine_detail_fidelity(ba, bb, A, B, m, g, rings=rings)['passed'] is False


def _offcentre_hole_scene(seed=4, R=40, offset=8., hole=50.):
    """A power-law corona whose index changes with position angle (-3 ± 0.8 cos PA), the data excluded within
    ``hole`` px of a Moon ``offset`` px off the Sun, 1 % noise: the radial curve leaves a residual that slopes in r
    with the sign of cos PA, as a real corona does next to an excluded band."""
    g = EclipseGeometry((512, 512), (256., 256.), R, (256. + offset, 256.), R + 4)
    r = g.radius_map(); th = np.radians(g.pa_map())
    a = ((np.maximum(r, 1) / R) ** (-3 + .8 * np.cos(th))).astype(np.float32)
    a = a * (1 + .01 * np.random.default_rng(seed).standard_normal(a.shape)).astype(np.float32)
    return g, g.radius_map('moon') > hole, a


def _edge_level(layer, g, m, lo, hi, hole=50.):
    """RMS over twelve 30° sectors of the median level (layer - 0.5) at lo–hi px from the edge of the hole."""
    d = g.radius_map('moon') - hole; pa = (g.pa_map() + 360) % 360
    v = [np.median(layer[k]) - .5 for s in range(12)
         for k in [m & np.isfinite(layer) & (d >= lo) & (d < hi) & (pa >= 30 * s) & (pa < 30 * s + 30)] if k.sum() > 30]
    return float(np.sqrt(np.mean(np.square(v))))


def test_wow_draws_no_level_along_an_edge_of_the_data():
    """On the author's 2026 data the WOW of 1.3.4 as first written drew a level of up to ±6.6 % in the first 24 px
    outside the excluded lunar band, of either sign from sector to sector: a kernel cut by the edge sees one side
    only. With symmetric observed pairs and the coarse scales weighted by the observed fraction of their kernel, the
    level next to the edge (0–16 px) stays within 1.6 times the same statistic 40–72 px out. The same WOW without
    either step is the negative control (about five times its own null here)."""
    from ael.filterbank import radial_log_residual, wow_measured
    g, m, a = _offcentre_hole_scene()
    layer = make_filter('wow', a, m, g)[0]
    res, _ = radial_log_residual(a, m, g); rs = g.rsun_map()
    q, _ = wow_measured(res, m, g, pairs=False, edge_completeness=None)
    control = display_detail(q, m, scale_region=(rs >= 1.1) & (rs < 2.))[0]
    edge, null = _edge_level(layer, g, m, 0, 16), _edge_level(layer, g, m, 40, 72)
    c_edge, c_null = _edge_level(control, g, m, 0, 16), _edge_level(control, g, m, 40, 72)
    assert edge < 1.6 * null and edge < .5 * c_edge, (edge, null, c_edge)
    assert c_edge > 3 * c_null, (c_edge, c_null)


def test_starlet_with_symmetric_pairs_reconstructs_exactly_and_invents_nothing():
    """The paired smoothing changes the coefficients next to an edge, never the sum: details + coarse = image on the
    observed pixels, NaN elsewhere; away from every edge the coefficients are those of the plain starlet."""
    rng = np.random.default_rng(0); img = rng.standard_normal((200, 240)).astype(np.float32)
    m = np.ones(img.shape, bool); m[60:120, 80:150] = False; m[:, :7] = False
    d1, c1 = filters.starlet(img, m, 6, .01, pairs=True); d0, _ = filters.starlet(img, m, 6, .01)
    rec = sum(d1) + c1
    assert np.nanmax(np.abs(rec - img)[m]) < 1e-5 and np.isnan(rec[~m]).all()
    far = np.zeros_like(m); far[150:180, 170:220] = True                   # ≥ 20 px from the hole and from the frame;
    assert np.allclose(d1[2][far], d0[2][far], atol=1e-6)                  # scale 3 reaches 14 px
    assert not np.allclose(d1[2][m][:, None], d0[2][m][:, None], atol=1e-6)  # and next to an edge it does differ


def test_a_recipe_written_for_the_old_defaults_keeps_its_look():
    """A recipe written for 1.3.3 lists WOW bilateral, the default Overlay layer up to 1.3.3. Without 'opacities' or
    'visible' it must still come out visible at 0.37, as it did then; listed next to the new WOW, it is a hidden layer
    to compare with. Control: the opacity of a listed filter without a starting opacity is 1."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp); g = EclipseGeometry((120, 150), (71.3, 63.4), 18)
        r = g.radius_map(); m = r > 22
        a = (10000 * np.maximum(r / 18, 1) ** -3 * (1 + .3 * np.cos(np.radians(g.pa_map()) * 7))).astype(np.float32)
        np.save(root / 'input.npy', np.stack([a, .7 * a, .4 * a], axis=-1)); np.save(root / 'valid.npy', m); g.to_json(root / 'g.json')
        def layers(filters):
            cfg = dict(input='input.npy', valid='valid.npy', geometry='g.json', display=dict(scale=10, asinh=20), filters=filters, photoshop=False)
            p = root / 'f.json'; p.write_text(json.dumps(cfg))
            res = filters_from_config(p, root / ('out_' + '_'.join(filters)), progress=lambda *_: None)
            return {x['name']: x for x in json.loads(Path(res['receipt']).read_text())['parameters']['layers']}
        old = layers(['nrgf', 'wow_bilateral', 'achf_iso_04'])
        assert old['wow_bilateral']['visible'] and old['wow_bilateral']['opacity'] == .37, old['wow_bilateral']
        both = layers(['nrgf', 'wow', 'wow_bilateral', 'mgn'])
        assert both['wow']['visible'] and not both['wow_bilateral']['visible'] and both['wow_bilateral']['opacity'] == .37
        assert both['mgn']['opacity'] == 1 and not both['mgn']['visible']


def test_tangential_step_has_no_switch_where_the_frame_cuts_the_circles_and_keeps_a_gap_local():
    """The tangential step of the new WOW is a normalised convolution along each circle around the Sun. A constant is
    constant along every circle, also where the frame leaves only a short arc of it (the corners): it must go
    everywhere, with no switch line where the observed share of the window crosses some threshold (a 0/1 switch at a
    share of 0.2 drew an arc at each corner, the negative control: 382 pixels). Only a pixel whose circle has no
    observed sample within reach on the polar grid keeps its value (here 2, in the very corner of the frame). And a
    pixel without a value must stay a single pixel: its gap must not spread along its circle."""
    from ael.filterbank import _tangential_frame, _tangential_mean_removed
    g = EclipseGeometry((300, 420), (120.3, 140.7), 30, None, None)
    m = g.radius_map() > 40; fr = _tangential_frame(m, g)
    out = _tangential_mean_removed(np.ones(m.shape, np.float32), m, fr, 10.)
    ys, xs = np.nonzero(m & (np.abs(out) > 1e-3))
    assert len(ys) <= 4 and all(min(y, x, 299 - y, 419 - x) <= 2 for y, x in zip(ys, xs)), list(zip(ys, xs))
    s = np.where(m, np.random.default_rng(4).standard_normal(m.shape), 0).astype(np.float32); s[200, 300] = np.nan
    out = _tangential_mean_removed(s, m, fr, 10.)
    assert np.isnan(out[m]).sum() <= 1, int(np.isnan(out[m]).sum())
    from scipy import ndimage as ndi                                              # the control: a 0/1 switch at 0.2
    pv = ndi.map_coordinates(np.where(m, 1., 0.).astype(np.float32), [fr['Y'], fr['X']], order=1, mode='constant')
    pm = pv > .5; sig = 10 / 360 * fr['n_theta']
    den = ndi.gaussian_filter1d(pm.astype(np.float32), sig, axis=1, mode='wrap')
    assert ((den > 0) & (den <= .2) & pm).any()                                   # the scene has such arcs


def test_wow_falls_back_to_white_noise_when_the_far_field_cannot_be_measured():
    """With the sky subtracted (about 30 % of the pixels beyond 6 R☉ at or below zero, scattered), nothing is left of
    the far field once it is eroded, and its noise cannot be measured: the new WOW must fall back to white-noise
    factors, as 1.3.3 did, and say so in its parameters, instead of returning no layer. The control shows the
    condition: measured on that field, the factors come out NaN."""
    import warnings
    from ael.filterbank import radial_log_residual
    R = 30; g = EclipseGeometry((640, 768), (310.3, 370.7), R, (310.3, 370.7), R + 1)
    r = g.radius_map(); th = np.radians(g.pa_map()); m = g.radius_map('moon') > R + 3
    a = ((np.maximum(r, 1) / R) ** -3 * (1 + .3 * np.cos(3 * th))).astype(np.float32)
    a = a + .002 * np.random.default_rng(9).standard_normal(a.shape).astype(np.float32)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        q, _, info = make_filter('wow', a, m, g)
        pos = m & (a > 0); res, _ = radial_log_residual(a, pos, g)
        nf = filters.noise_factors(res, pos, pos & (g.rsun_map() > 6), n_scales=6)
    assert info['noise_factors'] == 'white noise' and np.isfinite(q[pos]).mean() > .99, info['noise_factors']
    assert not np.isfinite(nf).all()


def test_fine_detail_gate_mechanisms_each_catch_their_case():
    """Each mechanism of ael.gates.fine_detail_fidelity on a case that only it can catch. Layers are the data's own
    band-pass (an ideal layer passes), then: (a) a smooth corona whose only 'detail' next to the Moon is the edge
    bias, the same in both stacks: the rotation null must refuse to accredit the ring (control: without the null it
    would pass); (b) stacks so noisy that a layer reproducing its own stack, noise included, follows it closely: it
    must fail crosswise (control: compared with its own stack it passes); (c) inverted patches on 17 % of the area:
    every rho stays above 0.5, so only the inversion count can fail it; (d) half a 45° sector inverted: the whole rings
    pass, so only the worst sector can fail it."""
    import warnings
    from ael.gates import fine_detail_fidelity
    g = EclipseGeometry((640, 768), (310.3, 370.7), 60, (310.3, 370.7), 61)
    r = g.radius_map(); th = np.radians(g.pa_map()); pa = g.pa_map(); m = g.radius_map('moon') > 63
    rng = np.random.default_rng(1234)
    fine = sum(rng.uniform(.004, .012) * np.sin(k * th + rng.uniform(0, 2 * np.pi)) for k in range(20, 140, 2))
    smooth = ((np.maximum(r, 1) / 60) ** -3 * (1 + .3 * np.cos(3 * th))).astype(np.float32)
    a = (smooth * np.exp(fine)).astype(np.float32)
    noisy = lambda img, sn, seed: (img * (1 + sn * np.random.default_rng(seed).standard_normal(img.shape))).astype(np.float32)

    def layer(L, flip=None):
        x = np.where(m, np.log(np.where(m, L, 1.)), np.nan).astype(np.float32); k = m & np.isfinite(x)
        b = filters.normalized_gaussian(x, k, 1.5, .25) - filters.normalized_gaussian(x, k, 6., .25)
        out = .5 + .1 * b / np.nanstd(b[m])
        return np.where(m, np.where(flip, 1 - out, out) if flip is not None else out, np.nan).astype(np.float32)
    rings = ((1.3, 1.6), (1.6, 2.0))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        A, B = noisy(a, .004, 1), noisy(a, .004, 2)
        assert fine_detail_fidelity(layer(A), layer(B), A, B, m, g, rings=rings)['passed'] is True
        SA, SB = noisy(smooth, .004, 3), noisy(smooth, .004, 4)                                           # (a)
        ra = fine_detail_fidelity(layer(SA), layer(SB), SA, SB, m, g, rings=((1.06, 1.12),), guard_px=0)
        assert ra['rings'][0]['reference_rho'] > .9 and not ra['rings'][0]['accredited'] and ra['passed'] is None, ra['rings']
        assert fine_detail_fidelity(layer(SA), layer(SB), SA, SB, m, g, rings=((1.06, 1.12),), guard_px=0,
                                    rotation_null_max=1.)['passed'] is True
        NA, NB = noisy(a, .09, 5), noisy(a, .09, 6)                                                       # (b)
        rb = fine_detail_fidelity(layer(NA), layer(NB), NA, NB, m, g, rings=rings)
        assert all(x['accredited'] for x in rb['rings']) and rb['passed'] is False, rb['rings']
        assert fine_detail_fidelity(layer(NA), layer(NA), NA, NA, m, g, rings=rings)['passed'] is True
        blob = filters.normalized_gaussian(np.random.default_rng(7).standard_normal(m.shape).astype(np.float32), None, 1.5, 0.)
        flip = blob > np.quantile(blob[m], .83)                                                           # (c)
        rc = fine_detail_fidelity(layer(A, flip), layer(B, flip), A, B, m, g, rings=rings)
        assert rc['passed'] is False and min(min(x['rho_reference'], x['rho_ab'], x['worst_sector_rho']) for x in rc['rings']) > .5, rc['rings']
        wedge = np.abs((pa - 112.5 + 180) % 360 - 180) < 11.25                                            # (d)
        rd = fine_detail_fidelity(layer(A, wedge), layer(B, wedge), A, B, m, g, rings=rings)
        assert rd['passed'] is False and all(x['rho_reference'] > .5 and x['inversions_pct'] < 10 and x['rho_ab'] > .5 for x in rd['rings']), rd['rings']


def test_wow_tangential_step_leaves_no_dark_wings_beside_compact_structure():
    """A local mean along the circle the size of a feature darkens the circle on both sides of it (the coarse
    coefficient of a compact feature is a bright core in a dark ring). With the 10° window of the first draft a bright
    knot at 1.4 R☉ (σ 12 px) left a mean change of −0.37 at 12–20° beside it, against −0.13 without any tangential step
    (independent review, 27-10-2026). With the default window (45°) the wings must stay within 1.3 times those of the
    same WOW without the step (plus 0.02); the 10° window is the negative control."""
    import warnings
    from ael.filterbank import radial_log_residual, wow_measured
    g = EclipseGeometry((900, 1100), (550.3, 450.7), 80., (550.3, 450.7), 81.)
    r = g.radius_map(); th = np.radians(g.pa_map()); pa = g.pa_map(); m = g.radius_map('moon') > 83; cx, cy = g.sun_xy
    base = ((np.maximum(r, 1) / 80.) ** -3 * (1 + .3 * np.cos(2 * th)) + .002)
    noise = 1 + .01 * np.random.default_rng(4).standard_normal(r.shape)
    yy, xx = np.mgrid[0:900, 0:1100]; bx, by = cx + 112 * np.cos(np.radians(30)), cy - 112 * np.sin(np.radians(30))
    knot = np.exp(-.5 * ((xx - bx) ** 2 + (yy - by) ** 2) / 12. ** 2)
    pab = float(pa[int(round(by)), int(round(bx))]); rs = g.rsun_map()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        R1 = radial_log_residual((base * (1 + knot) * noise).astype(np.float32), m, g)[0]
        R0 = radial_log_residual((base * noise).astype(np.float32), m, g)[0]

        def wing(**kw):
            lay = lambda res: display_detail(wow_measured(res, m, g, **kw)[0], m, scale_region=(rs >= 1.1) & (rs < 2.))[0]
            d = lay(R1) - lay(R0); off = np.abs((pa - pab + 180) % 360 - 180)
            return float(np.nanmean(d[m & (np.abs(r - 112) < 4) & (off >= 12) & (off <= 20)]))
        default, none, narrow = wing(), wing(tangential_from=99), wing(tangential_sigma_deg=10.)
    assert default >= 1.3 * none - .02, (default, none)
    assert narrow < 1.3 * none - .02, (narrow, none)


def test_wow_measures_correlated_noise_and_does_not_whiten_it_into_blotches():
    """The measured noise factors are the cure for the blotches of plain WOW in a real stack's outer field. With noise
    correlated over a few pixels (as registration and fusion make it), the coarse texture of the layer in the outer
    field (band-pass 4–16 px, 5–9 R☉) must stay below 0.85 of what the same WOW makes with white-noise factors (the
    negative control: the factors of 1.3.3)."""
    import warnings
    from scipy import ndimage as ndi
    from ael.filterbank import radial_log_residual, wow_measured
    R = 30; g = EclipseGeometry((640, 768), (310.3, 370.7), R, (310.3, 370.7), R + 1)
    r = g.radius_map(); th = np.radians(g.pa_map()); m = g.radius_map('moon') > R + 3; rs = g.rsun_map()
    n = ndi.gaussian_filter(np.random.default_rng(12).standard_normal(m.shape), 1.5); n /= n.std()
    a = (((np.maximum(r, 1) / R) ** -3 * (1 + .3 * np.cos(3 * th)) + .01) * (1 + .02 * n)).astype(np.float32)

    def coarse(L):
        ok = m & np.isfinite(L)
        bp = filters.normalized_gaussian(L, ok, 4., .25) - filters.normalized_gaussian(L, ok, 16., .25)
        return float(np.std(bp[ok & (rs > 5) & (rs < 9) & np.isfinite(bp)]))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        measured, _, info = make_filter('wow', a, m, g)
        res, _ = radial_log_residual(a, m, g); q, winfo = wow_measured(res, m, g, noise_region_rsun=1e9)
        white = display_detail(q, m, scale_region=(rs >= 1.1) & (rs < 2.))[0]
    assert info['noise_factors'] == 'measured' and winfo['noise_factors'] == 'white noise'
    assert coarse(measured) < .85 * coarse(white), (coarse(measured), coarse(white))


def test_wow_refuses_absurd_noise_factors_and_ring_display_falls_back_on_a_narrow_wedge():
    """Two cases that must give a layer, as 1.3.3 did, and say how. (1) A far field clipped to a constant (8-bit data,
    sky at 5 counts): the measured factors come out absurd (scale 0 has almost no spread), so the WOW uses white-noise
    factors and gives the reason. (2) Data only in a wedge of 8°: no annulus holds 50 pixels, so the ACHF layer takes
    the whole-image display and says so. Controls: the factors measured on that field are absurd; with a full disc the
    ring display is used."""
    import warnings
    g = EclipseGeometry((600, 700), (350.3, 300.7), 40., (350.3, 300.7), 41.)
    r = g.radius_map(); th = np.radians(g.pa_map()); m = g.radius_map('moon') > 43
    a = (np.maximum(r, 1) / 40.) ** -3 * (1 + .3 * np.cos(3 * th)) * 1000 * (1 + .01 * np.random.default_rng(1).standard_normal(r.shape))
    q8 = np.maximum(np.round(a), 5.).astype(np.float32)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        _, _, info = make_filter('wow', q8, m, g)
        from ael.filterbank import radial_log_residual
        res, _ = radial_log_residual(q8, m, g)
        nf = filters.noise_factors(res, m, m & (g.rsun_map() > 6), n_scales=6)
    assert info['noise_factors'] == 'white noise' and 'not measurable' in info['white_noise_reason'], info
    assert not (np.isfinite(nf).all() and (nf <= 50 * filters.STARLET_NOISE[:6]).all()), nf
    g = EclipseGeometry((200, 300), (150.2, 100.1), 15., None, None)
    r = g.radius_map(); th = np.radians(g.pa_map())
    a = (((np.maximum(r, 1) / 15.) ** -3 * (1 + .3 * np.cos(3 * th)) + .01) * (1 + .01 * np.random.default_rng(2).standard_normal(r.shape))).astype(np.float32)
    wedge = (r > 15.75) & (np.abs(g.pa_map() - 90) < 4)
    q, _, info = make_filter('achf_iso_04', a, wedge, g)
    assert np.isfinite(q[wedge]).all() and info['display'].startswith('one spread'), info['display']
    assert make_filter('achf_iso_04', a, r > 15.75, g)[2]['display'] == 'level and spread per ring'
