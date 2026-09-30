"""Reproduce C4 from its exact native-response arrays (saved before judging).
Original command also derived arrays from C1 PSDs as implemented in C2.
Writes a distinct reproduction receipt and asserts identical numeric results.
"""
from b2_judge import *
claim();z=np.load(OUT/'arrays/C4_injection_native_responses.npz')
A=band(map_coordinates(z['baseline'],co,order=3),40,64);B=band(map_coordinates(z['candidate'],co,order=3),40,64);rows=[]
for lo,hi in [(100,300),(300,370),(370,435),(435,449)]:
    for sec in range(12):
        m=np.broadcast_to((rr[:,None]>=lo)&(rr[:,None]<hi),(len(rr),nt))&((np.arange(nt)[None,:]//120)==sec);x=A[m];y=B[m];gain=float(x@y/(x@x))
        rows.append(dict(radius=[lo,hi],sector=sec,transfer=gain,r=corr(A,B,m),pass_gate=.9<=gain<=1.1))
original=json.loads((OUT/'C4_native_injection_band.json').read_text())['rows'];assert rows==original
save('C4_reproduction.json',dict(exact=True,rows=48,original=str(OUT/'C4_native_injection_band.json'),input_sha256=sha(OUT/'arrays/C4_injection_native_responses.npz')))
