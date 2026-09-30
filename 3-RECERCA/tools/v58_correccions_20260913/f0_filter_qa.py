from filters58 import *
claim();C=O/'filters';S=O/'sources';rep={};ref=np.load(S/'fusion_starless.npy',mmap_mode='r')[...,1];sony=np.load(S/'sony_starless.npy',mmap_mode='r')[...,1];radii=np.linspace(1.15,1.8,70).astype('float32');Rpol=polar(np.log(np.maximum(ref,1e-6)),CX,CY,RS,radii);Spol=polar(np.log(np.maximum(sony,1e-6)),CX,CY,RS,radii);tags=['P01_NRGF','P01_NRGF_extrap','P02_RHEF','P02b_RHEF_ups0.35','03','03v30','07','01','04','05','06','P03_MGN','P04_WOW','P05_WOW_bilateral']
for tag in tags:
 a=np.load(C/f'{tag}_u16.npy',mmap_mode='r');P=polar(a.astype('float32')/65535,CX,CY,RS,radii);rep[tag]=dict(alignment=correlate(P,Rpol),independent_sony=correlate(P,Spol));print(tag,rep[tag],flush=True)
rep['controls']={str(deg):correlate(np.roll(Rpol,round(deg*4),axis=1),Rpol) for deg in [0,1,-1,180]};save('F0_filter_qa.json',rep)
