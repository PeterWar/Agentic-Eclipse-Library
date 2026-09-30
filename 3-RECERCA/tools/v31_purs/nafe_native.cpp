// Faithful accelerated Im.y1 from ebuchlin/medocimage/nafe.py.
// 500 local histogram bins, exact supplied membership kernel, cumulative histogram,
// Gaussian filter in intensity with nearest boundary, interpolation at central value.
// Missing physical samples excluded from both local range and histogram weights.
#include <cmath>
#include <algorithm>
#include <vector>
#include <thread>
#include <atomic>
#include <cstdio>
static double point(const float* a,const unsigned char* m,int h,int w,int y,int x,int n,const double* kernel,double sigma){
 int half=n/2,y0=std::max(0,y-half),y1=std::min(h,y+half+1),x0=std::max(0,x-half),x1=std::min(w,x+half+1);
 double lo=INFINITY,hi=-INFINITY;
 for(int yy=y0;yy<y1;yy++)for(int xx=x0;xx<x1;xx++)if(m[(long)yy*w+xx]){double v=a[(long)yy*w+xx];lo=std::min(lo,v);hi=std::max(hi,v);}
 if(lo==hi){lo-=.5;hi+=.5;}
 double hist[500]={0},delta=(hi-lo)/500.;
 for(int yy=y0;yy<y1;yy++)for(int xx=x0;xx<x1;xx++)if(m[(long)yy*w+xx]){
  double v=a[(long)yy*w+xx];int j=std::min(499,std::max(0,(int)((v-lo)/delta)));
  hist[j]+=kernel[(yy-y+half)*n+xx-x+half];
 }
 for(int j=1;j<500;j++)hist[j]+=hist[j-1];
 double tot=hist[499];for(double &v:hist)v/=tot;
 double sb=sigma/delta;
 if(sb<1e-12){double jj=(a[(long)y*w+x]-lo)/delta-.5;jj=std::min(499.,std::max(0.,jj));int j=(int)jj;return hist[j]*(1-(jj-j))+hist[std::min(j+1,499)]*(jj-j);}
 int radius=(int)std::min(1e8,std::floor(4*sb+.5));
 // Need only weights at displacements <=499. The remainder falls on nearest end values.
 double weight[500];int nr=std::min(radius,499);double z=1.,ratio=std::exp(-.5/(sb*sb)),step=std::exp(-1/(sb*sb));double norm=1;
 weight[0]=1;
 for(int j=1;j<=nr;j++){z*=ratio;ratio*=step;weight[j]=z;norm+=2*z;}
 if(radius>499){
  if(sb<20){for(int j=500;j<=radius;j++){z*=ratio;ratio*=step;norm+=2*z;}}
  else {
   // Midpoint Euler-Maclaurin sum of exp(-x²/(2s²)), including first and third derivative terms.
   // At s>=20 error is below double precision relevant to the final16-bit LUT.
   double b=radius+.5,ex=std::exp(-b*b/(2*sb*sb));
   double fp=-b/(sb*sb)*ex, f3=(3*b/std::pow(sb,4)-b*b*b/std::pow(sb,6))*ex;
   norm=sb*std::sqrt(2*M_PI)*std::erf(b/(std::sqrt(2.)*sb))-fp/12.+7*f3/2880.;
  }
 }
 double jj=(a[(long)y*w+x]-lo)/delta-.5;jj=std::min(499.,std::max(0.,jj));int j0=(int)jj,j1=std::min(j0+1,499);
 auto filtered=[&](int j){
  double sum=hist[j],wl=1,wr=1;
  for(int d=1;d<=nr;d++){
   if(j-d>=0){sum+=weight[d]*hist[j-d];wl+=2*weight[d];}
   if(j+d<500){sum+=weight[d]*hist[j+d];wr+=2*weight[d];}
  }
  sum+=(norm-wl)*.5*hist[0]+(norm-wr)*.5*hist[499];
  return sum/norm;
 };
 double p=filtered(j0),q=filtered(j1);return p*(1-(jj-j0))+q*(jj-j0);
}
extern "C" void nafe_points(const float* a,const unsigned char* m,int h,int w,int n,const double* kernel,double sigma,const int* ys,const int* xs,int count,double* out){
 for(int i=0;i<count;i++)out[i]=point(a,m,h,w,ys[i],xs[i],n,kernel,sigma);
}
extern "C" void nafe_full(const float* a,const unsigned char* m,int h,int w,int n,const double* kernel,double sigma,int nt,float* out){
 std::atomic<int> row{0},done{0};std::vector<std::thread> workers;
 for(int t=0;t<nt;t++)workers.emplace_back([&](){
  for(;;){int y=row.fetch_add(1);if(y>=h)break;
   for(int x=0;x<w;x++)out[(long)y*w+x]=m[(long)y*w+x]?point(a,m,h,w,y,x,n,kernel,sigma):0;
   int d=done.fetch_add(1)+1;if(d%250==0){std::printf("NAFE rows %d/%d\n",d,h);std::fflush(stdout);}
  }
 });
 for(auto &t:workers)t.join();
}
