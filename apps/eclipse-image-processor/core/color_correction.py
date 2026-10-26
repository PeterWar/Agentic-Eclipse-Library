"""PSB-only native Color Correction group from the supplied Photoshop colour guide.

The application display RGB is explicitly treated as sRGB, not camera-linear RGB.
Native adjustments are recomposed by Photoshop; no colour-corrected application
preview or approximate Photoshop renderer is used.
Adobe format: https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/
"""
import hashlib
import io
import numpy as np
from PIL import ImageCms
from .cancellation import check_cancelled

PALETTE = ((0,'3A2638'),(35,'B96343'),(65,'EDAA64'),(85,'F7D7A4'),(100,'FFF4DE'))
ADJUSTMENT_NAMES = ('Corona Gradient Map','Corona Color Balance','Sky Hue Saturation')


def srgb_profile():
    return ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()


def correction_masks(rgb, valid, geometry):
    """RGB16 display-based initial masks, never a reconstruction of missing data.

    The outer field supplies a robust sky level/spread. Corona membership starts
    above that spread, so sky noise is not deliberately coloured as coronal rays.
    Both masks exclude the measured lunar disk separately. These are editable
    starting masks, not calibrated segmentation thresholds.
    """
    a=np.asarray(rgb)
    valid=np.asarray(valid,bool)
    if a.dtype != np.uint16 or a.ndim != 3 or a.shape[-1] != 3 or valid.shape != a.shape[:2]:
        raise ValueError('Color Correction requires matching RGB16 and validity')
    cx,cy,radius=(float(geometry[key]) for key in ('sx','sy','sr'))
    if not np.isfinite([cx,cy,radius]).all() or radius <= 0:
        raise ValueError('Color Correction requires finite lunar geometry and positive radius')
    y,x=np.ogrid[:a.shape[0],:a.shape[1]]
    distance=np.hypot(x-cx,y-cy)
    use=valid & (distance>radius)
    if not use.any():
        raise ValueError('Color Correction has no observed pixels outside the lunar disk')
    luminance=a.astype(np.float32) @ np.array([.30,.59,.11],np.float32)
    outer=use & (distance>=np.percentile(distance[use],75))
    low=float(np.median(luminance[outer]))
    noise=float(1.4826*np.median(np.abs(luminance[outer]-low)))
    high=float(np.percentile(luminance[use],99.5))
    span=max(float(high-low),1.)
    level=(luminance-low)/span
    start=max(.02,2.5*noise/span)
    end=max(.20,6*noise/span,start+.01)
    def smooth(t):
        t=np.clip(t,0,1)
        return t*t*(3-2*t)
    outside=smooth((distance-radius)/max(1.,.03*radius))*valid
    corona=smooth((level-start)/(end-start))*outside
    sky=(1-smooth((level-max(.01,noise/span))/max(.10,2*noise/span)))*outside
    masks=tuple(np.rint(mask*65535).astype(np.uint16) for mask in (corona,sky))
    return masks,dict(method='editable display-luminance masks with separate lunar/validity exclusion',
                      display_sky_median=low,display_sky_mad=noise,display_p995=high,
                      corona_range=[start,end],lunar_feather_px=max(1.,.03*radius),
                      review_required=True)


def _mask(layer, values):
    from psd_tools.constants import ChannelID, Compression
    from psd_tools.psd.layer_and_mask import MaskData, MaskFlags, ChannelData, ChannelInfo
    h,w=values.shape
    layer._record.mask_data=MaskData(top=0,left=0,bottom=h,right=w,background_color=0,flags=MaskFlags())
    channel=ChannelData(Compression.ZIP_WITH_PREDICTION)
    channel.set_data(np.ascontiguousarray(values).astype('>u2').tobytes(),w,h,16,2)
    layer._record.channel_info.append(ChannelInfo(ChannelID.USER_LAYER_MASK,len(channel.data)+2))
    layer._channels.append(channel)


def _adjustment(group, cls, name, data, mask, mode, opacity):
    from psd_tools.constants import BlendMode, ChannelID, Compression, Tag
    from psd_tools.psd.layer_and_mask import LayerRecord, ChannelDataList, ChannelData, ChannelInfo
    from psd_tools.psd.tagged_blocks import TaggedBlock
    record=LayerRecord(name=name,channel_info=[ChannelInfo(ChannelID.TRANSPARENCY_MASK,2)])
    record.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME,name)
    record.tagged_blocks.set_data(Tag.LAYER_ID,group._psd._next_layer_id)
    group._psd._next_layer_id+=1
    record.tagged_blocks[cls._KEY]=TaggedBlock(key=cls._KEY,data=data)
    record.blend_mode=BlendMode(mode)
    record.opacity=round(255*opacity)
    layer=cls(group,record,ChannelDataList([ChannelData(Compression.RAW,data=b'')]))
    _mask(layer,mask)
    group.append(layer)
    return layer


def add_color_correction(doc, rgb, valid, geometry):
    """Append a Normal/50% group with a snapshot base and three native adjustments."""
    from psd_tools.api.layers import Group
    from psd_tools.api.adjustments import GradientMap, ColorBalance, HueSaturation
    from psd_tools.psd.adjustments import (GradientMap as GradientData, ColorStop, TransparencyStop,
                                          ColorBalance as BalanceData, HueSaturation as HueData)
    from psd_tools.constants import BlendMode, Resource, Compression
    from psd_tools.psd.image_resources import ImageResource, VersionInfo
    from .psb_export import add_layer
    check_cancelled()
    (corona,sky),mask_info=correction_masks(rgb,valid,geometry)
    group=Group.new(doc,'Color Correction')
    group.blend_mode=BlendMode.NORMAL
    group.opacity=128
    base=add_layer(doc,'Base Color — snapshot',rgb,np.asarray(valid,np.uint16)*65535)
    group.append(base)
    stops=[]
    for position,colour in PALETTE:
        channels=tuple(int(colour[i:i+2],16)*257 for i in (0,2,4))
        stops.append(ColorStop(round(position/100*4096),50,0,(*channels,0)))
    gradient=GradientData(version=3,is_reversed=0,is_dithered=1,name='Copper Gold Ivory',method=b'Gcls',
                          color_stops=stops,transparency_stops=[TransparencyStop(0,50,100),TransparencyStop(4096,50,100)],
                          interpolation=4096,minimum_color=[0,0,0,0],maximum_color=[32768]*4)
    _adjustment(group,GradientMap,ADJUSTMENT_NAMES[0],gradient,corona,b'colr',.30)
    _adjustment(group,ColorBalance,ADJUSTMENT_NAMES[1],
                BalanceData(shadows=(0,0,0),midtones=(8,-2,-8),highlights=(4,0,-6),luminosity=True),corona,b'colr',.30)
    # Photoshop's six default colour ranges: red, yellow, green, cyan, blue, magenta.
    ranges=((315,345,15,45),(15,45,75,105),(75,105,135,165),
            (135,165,195,225),(195,225,255,285),(255,285,315,345))
    hue=HueData(enable=0,colorization=(0,0,0),master=(0,0,0),
                items=[[r,(0,-10 if i==3 else -20 if i==4 else 0,0)] for i,r in enumerate(ranges)])
    _adjustment(group,HueSaturation,ADJUSTMENT_NAMES[2],hue,sky,b'norm',1.)
    profile=srgb_profile()
    doc._record.image_resources[Resource.ICC_PROFILE]=ImageResource(key=Resource.ICC_PROFILE,data=profile)
    # The stored RGB is the uncorrected reference, not a fake rendering of native adjustments.
    doc._record.image_resources[Resource.VERSION_INFO]=ImageResource(key=Resource.VERSION_INFO,
        data=VersionInfo(has_composite=False,writer='Eclipse Image Processor',reader='Adobe Photoshop',file_version=1))
    doc._update_record()
    check_cancelled()
    return dict(group='Color Correction',group_opacity_255=128,profile='sRGB',
                profile_sha256=hashlib.sha256(profile).hexdigest(),
                input_space='Application display RGB assumed sRGB; original linear pixels unchanged',
                palette=[dict(position=p,srgb='#'+c) for p,c in PALETTE],masks=mask_info,
                corona_mask_sha256=hashlib.sha256(corona.tobytes()).hexdigest(),
                sky_mask_sha256=hashlib.sha256(sky.tobytes()).hexdigest(),
                base_sha256=hashlib.sha256(np.ascontiguousarray(rgb).tobytes()).hexdigest(),
                merged_reference='Uncorrected base; native Photoshop recomposition required',
                base_snapshot=True,preview=False,tiff_jpeg=False)


def verify_color_correction(doc, rgb, valid, geometry):
    """Verify hierarchy, native parameter blocks, full-resolution mask bytes and profile."""
    from psd_tools.constants import BlendMode, ChannelID, Resource
    from psd_tools.api.adjustments import GradientMap, ColorBalance, HueSaturation
    group=doc[-1]
    if not group.is_group() or group.name!='Color Correction' or group.blend_mode!=BlendMode.NORMAL or group.opacity!=128 or not group.visible:
        raise ValueError('Color Correction group metadata mismatch')
    if len(group)!=4 or [l.name for l in list(group)[1:]]!=list(ADJUSTMENT_NAMES):
        raise ValueError('Color Correction layer hierarchy mismatch')
    if group[0].name!='Base Color — snapshot':
        raise ValueError('Color Correction base snapshot mismatch')
    h,w=rgb.shape[:2]
    if {int(info.id) for info in group[0]._record.channel_info}!={-1,0,1,2}:
        raise ValueError('Color Correction base channels mismatch')
    for info,channel in zip(group[0]._record.channel_info,group[0]._channels):
        cid=int(info.id)
        expected=np.asarray(valid,np.uint16)*65535 if cid==-1 else rgb[...,cid]
        if channel.get_data(w,h,16,2)!=np.ascontiguousarray(expected).astype('>u2').tobytes():
            raise ValueError('Color Correction base pixels mismatch')
    gradient,balance,hue=list(group)[1:]
    if not isinstance(gradient,GradientMap) or not isinstance(balance,ColorBalance) or not isinstance(hue,HueSaturation):
        raise ValueError('Color Correction requires native adjustment layers')
    expected_stops=[(round(p/100*4096),tuple(int(c[i:i+2],16)*257 for i in (0,2,4))) for p,c in PALETTE]
    if ([(s.location,tuple(s.color[:3])) for s in gradient.color_stops]!=expected_stops or
            any(s.midpoint!=50 or s.mode!=0 for s in gradient.color_stops) or
            [(s.location,s.midpoint,s.opacity) for s in gradient.transparency_stops]!=[(0,50,100),(4096,50,100)] or
            gradient.reversed or not gradient.dithered or gradient._data.method!=b'Gcls' or gradient._data.interpolation!=4096):
        raise ValueError('Color Correction gradient mismatch')
    if (balance.shadows,balance.midtones,balance.highlights,balance.luminosity)!=((0,0,0),(8,-2,-8),(4,0,-6),1):
        raise ValueError('Color Correction balance mismatch')
    if hue.enable_colorization or hue.master!=(0,0,0) or [tuple(item[1]) for item in hue.data]!=[(0,0,0)]*3+[(0,-10,0),(0,-20,0),(0,0,0)]:
        raise ValueError('Color Correction hue/saturation mismatch')
    (corona,sky),_=correction_masks(rgb,valid,geometry)
    for layer,mask,mode,opacity in ((gradient,corona,BlendMode.COLOR,76),(balance,corona,BlendMode.COLOR,76),(hue,sky,BlendMode.NORMAL,255)):
        if layer.blend_mode!=mode or layer.opacity!=opacity or not layer.visible or not layer.has_mask():
            raise ValueError('Color Correction adjustment metadata mismatch')
        data=layer._record.mask_data
        if (data.top,data.left,data.bottom,data.right,data.background_color)!=(0,0,h,w,0) or data.flags.mask_disabled or data.flags.invert_mask:
            raise ValueError('Color Correction mask bounds or flags mismatch')
        channels={int(info.id):data for info,data in zip(layer._record.channel_info,layer._channels)}
        if channels[int(ChannelID.USER_LAYER_MASK)].get_data(w,h,16,2)!=mask.astype('>u2').tobytes():
            raise ValueError('Color Correction mask mismatch')
    profile=doc._record.image_resources.get_data(Resource.ICC_PROFILE)
    if not profile or 'sRGB' not in ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(profile))):
        raise ValueError('Color Correction requires an embedded sRGB profile')
    if doc._record.image_resources.get_data(Resource.VERSION_INFO).has_composite:
        raise ValueError('Color Correction must request native recomposition')
    return dict(native_adjustments=True,editable_masks=True,srgb=True,native_recomposition_required=True)
