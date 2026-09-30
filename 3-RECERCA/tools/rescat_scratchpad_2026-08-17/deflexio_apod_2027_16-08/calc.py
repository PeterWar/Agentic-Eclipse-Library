import math, datetime as dt

D2R=math.pi/180; R2D=180/math.pi

def jd(y,m,d,h=0,mi=0,s=0):
    if m<=2: y-=1; m+=12
    A=y//100; B=2-A+A//4
    day=d+(h+mi/60+s/3600)/24
    return int(365.25*(y+4716))+int(30.6001*(m+1))+day+B-1524.5

def gmst_deg(JD):
    T=(JD-2451545.0)/36525.0
    g=280.46061837+360.98564736629*(JD-2451545.0)+0.000387933*T*T-T*T*T/38710000.0
    return g%360

def sun_radec(JD):
    # low precision (Meeus ch.25), apparent
    T=(JD-2451545.0)/36525.0
    L0=(280.46646+36000.76983*T+0.0003032*T*T)%360
    M=(357.52911+35999.05029*T-0.0001537*T*T)%360
    C=(1.914602-0.004817*T-0.000014*T*T)*math.sin(M*D2R)+(0.019993-0.000101*T)*math.sin(2*M*D2R)+0.000289*math.sin(3*M*D2R)
    true_long=L0+C
    om=125.04-1934.136*T
    lam=true_long-0.00569-0.00478*math.sin(om*D2R)
    eps=23.439291-0.0130042*T
    eps_c=eps+0.00256*math.cos(om*D2R)
    ra=math.atan2(math.cos(eps_c*D2R)*math.sin(lam*D2R), math.cos(lam*D2R))*R2D%360
    dec=math.asin(math.sin(eps_c*D2R)*math.sin(lam*D2R))*R2D
    return ra,dec

def altaz(lat,lon,JD,ra,dec):
    lst=(gmst_deg(JD)+lon)%360
    H=(lst-ra+540)%360-180
    la=lat*D2R; de=dec*D2R; Hr=H*D2R
    sinh=math.sin(la)*math.sin(de)+math.cos(la)*math.cos(de)*math.cos(Hr)
    h=math.asin(sinh)*R2D
    cosA=(math.sin(de)-sinh*math.sin(la))/(math.cos(h*D2R)*math.cos(la))
    cosA=max(-1,min(1,cosA))
    A=math.acos(cosA)*R2D
    if math.sin(Hr)>0: A=360-A
    return h,A,H

LAT,LON=25.6872,32.6396   # Luxor
# --- 1. Sun at mid-totality 2027-08-02 10:05:20 UT
J=jd(2027,8,2,10,5,20)
ra,dec=sun_radec(J)
h,A,H=altaz(LAT,LON,J,ra,dec)
print("Sun 2027-08-02 10:05:20 UT  RA=%.4f deg (%.4fh) Dec=%+.4f  alt=%.3f az=%.3f HA=%+.4f deg (%+.2f min)"%(ra,ra/15,dec,h,A,H,H*4))

# meridian transit time of the Sun that day at Luxor
lo,hi=jd(2027,8,2,9,0,0),jd(2027,8,2,11,0,0)
for _ in range(60):
    mid=(lo+hi)/2
    r,d=sun_radec(mid); hh,aa,HH=altaz(LAT,LON,mid,r,d)
    if HH<0: lo=mid
    else: hi=mid
t=(lo+hi)/2
frac=(t+0.5)%1.0
print("Sun meridian transit at Luxor: %02d:%02d:%02d UT"%(int(frac*24),int(frac*1440)%60,int(frac*86400)%60))

FRA,FDEC=ra,dec   # calibration/eclipse field = Sun's position
HA_TARGET=H
print("\nTarget HA for identical alt/az: %+.5f deg\n"%HA_TARGET)

# --- 2. when is that field at that HA, at night, from Luxor?
def find_time_for_HA(y,m,d,ha_target):
    # search the UT day for the instant LST-RA = ha_target
    best=None
    for sec in range(0,86400,20):
        J=jd(y,m,d)+sec/86400
        lst=(gmst_deg(J)+LON)%360
        HH=(lst-FRA+540)%360-180
        if best is None or abs(HH-ha_target)<best[0]:
            best=(abs(HH-ha_target),J,sec)
    J=best[1]
    # sun altitude then
    r,dd=sun_radec(J); sh,sa,_=altaz(LAT,LON,J,r,dd)
    fh,fa,fH=altaz(LAT,LON,J,FRA,FDEC)
    return J,best[2],sh,fh,fa

print("date        UT time   local(UT+2)  Sun alt   field alt  field az")
for (y,m,d) in [(2026,11,1),(2026,12,1),(2026,12,15),(2027,1,1),(2027,1,15),(2027,2,1),(2027,2,2),(2027,2,15),(2027,3,1),(2027,3,15),(2027,4,1),(2027,4,15)]:
    J,sec,sunalt,falt,faz=find_time_for_HA(y,m,d,HA_TARGET)
    hh=sec//3600; mm=(sec%3600)//60
    loc=(sec+7200)%86400
    print("%04d-%02d-%02d   %02d:%02d    %02d:%02d        %+6.1f    %6.2f    %6.2f"%(y,m,d,hh,mm,loc//3600,(loc%3600)//60,sunalt,falt,faz))

# --- 3. field at the same alt/az on the nights just before the eclipse (on site)
print("\nOn-site pre-eclipse nights: which RA is at HA=%+.3f deg when the Sun is 18 deg below horizon or lower"%HA_TARGET)
for (y,m,d) in [(2027,7,28),(2027,7,30),(2027,8,1)]:
    # find local midnight-ish: scan night hours, report RA that sits at target HA at 22:00 and 00:00 and 02:00 local (UT+2)
    for loclabel,lochr in [("22:00",22),("00:00",24),("02:00",26)]:
        secs=(lochr*3600-7200)
        J=jd(y,m,d)+secs/86400
        lst=(gmst_deg(J)+LON)%360
        raneed=(lst-HA_TARGET)%360
        r,dd=sun_radec(J); sh,_,_=altaz(LAT,LON,J,r,dd)
        print("  %04d-%02d-%02d %s local: LST=%.3f deg -> field RA=%.3f deg = %02dh%04.1fm, Dec=%+.2f ; Sun alt %+.1f"%(y,m,d,loclabel,lst,raneed,raneed/15,(raneed/15%1)*60,FDEC,sh))

print("\n--- window boundaries (Sun < -18 deg at the moment the field is at the eclipse alt/az) ---")
import datetime
d0=datetime.date(2026,10,20)
prev=None
for i in range(0,200):
    d=d0+datetime.timedelta(days=i)
    J,sec,sunalt,falt,faz=find_time_for_HA(d.year,d.month,d.day,HA_TARGET)
    if prev is not None and (prev>-18)!=(sunalt>-18):
        print("  crossing -18 deg around %s  (Sun alt %.1f, local %02d:%02d)"%(d.isoformat(),sunalt,((sec+7200)%86400)//3600,(((sec+7200)%86400)%3600)//60))
    prev=sunalt

print("\n--- new moons Nov 2026 - Apr 2027 ---")
NM0=2451550.09766; SYN=29.530588853
k0=int((jd(2026,11,1)-NM0)/SYN)
for k in range(k0,k0+7):
    J=NM0+k*SYN
    # convert JD -> calendar
    Z=int(J+0.5); F=(J+0.5)-Z
    A=Z
    if Z>=2299161:
        al=int((Z-1867216.25)/36524.25); A=Z+1+al-al//4
    B=A+1524; C=int((B-122.1)/365.25); D=int(365.25*C); E=int((B-D)/30.6001)
    day=B-D-int(30.6001*E)+F
    mo=E-1 if E<14 else E-13
    yr=C-4716 if mo>2 else C-4715
    print("  new moon %04d-%02d-%05.2f UT"%(yr,mo,day))

print("\n--- contact hour angles at Luxor (C2 10:02:07, mid 10:05:20, C3 10:08:30 UT) ---")
for lab,(hh,mm,ss) in [("C2",(10,2,7)),("mid",(10,5,20)),("C3",(10,8,30))]:
    J=jd(2027,8,2,hh,mm,ss); r,d=sun_radec(J); h,A,H=altaz(LAT,LON,J,r,d)
    print("  %s: alt=%.3f az=%.3f HA=%+.3f deg = %+.2f min ; zenith distance %.2f deg"%(lab,h,A,H,H*4,90-h))
