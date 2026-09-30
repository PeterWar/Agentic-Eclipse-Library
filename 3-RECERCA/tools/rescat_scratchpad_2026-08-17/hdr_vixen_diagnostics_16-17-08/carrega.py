import numpy as np, tifffile, cv2, time
t0=time.time()
S='/Users/USUARI/Downloads/Sketchaprox.tif'
im=tifffile.imread(S)
print('llegit', im.shape, im.dtype, time.time()-t0)
h,w,_=im.shape
small=cv2.resize(im,(w//4,h//4),interpolation=cv2.INTER_AREA)
del im
sk=small.astype(np.float32)/65535.0
np.save('sketch_q4.npy', sk)
print('sketch q4', sk.shape, sk.min(), sk.max(), time.time()-t0)
prev=cv2.resize(sk,(1914,1297),interpolation=cv2.INTER_AREA)
cv2.imwrite('sketch_prev.jpg',(prev[...,::-1]*255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,90])
F='/Users/USUARI/Desktop/Eclipse 2026/Corona_HDR_Vixen/corona_vixen_FOTO.tif'
fo=tifffile.imread(F).astype(np.float32)/65535.0
np.save('foto.npy', fo)
print('foto', fo.shape, fo.min(), fo.max())
prev=cv2.resize(fo,(1698,1128),interpolation=cv2.INTER_AREA)
cv2.imwrite('foto_prev.jpg',(prev[...,::-1]*255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,90])
print('fet', time.time()-t0)
