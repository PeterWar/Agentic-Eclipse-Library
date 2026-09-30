#include <vector>
#include <thread>
#include <algorithm>
extern "C" void sparse_b3(const float* a,float* temp,float* out,int h,int w,int step,int nt){
 const float k[5]={.0625f,.25f,.375f,.25f,.0625f};
 std::vector<int> ix(5*w),iy(5*h);
 auto reflect=[](int q,int n){q=((q%(2*n))+2*n)%(2*n);return q<n?q:2*n-1-q;};
 for(int j=0;j<5;j++){
  for(int x=0;x<w;x++)ix[j*w+x]=reflect(x+(j-2)*step,w);
  for(int y=0;y<h;y++)iy[j*h+y]=reflect(y+(j-2)*step,h);
 }
 std::vector<std::thread> ts;
 for(int t=0;t<nt;t++)ts.emplace_back([&,t](){for(int y=t;y<h;y+=nt){
  const float* src=a+(long)y*w;float* dst=temp+(long)y*w;
  for(int x=0;x<w;x++){float v=0;for(int j=0;j<5;j++)v+=k[j]*src[ix[j*w+x]];dst[x]=v;}
 }});
 for(auto &t:ts)t.join();ts.clear();
 for(int t=0;t<nt;t++)ts.emplace_back([&,t](){for(int y=t;y<h;y+=nt){
  const float *r0=temp+(long)iy[y]*w,*r1=temp+(long)iy[h+y]*w,*r2=temp+(long)iy[2*h+y]*w,*r3=temp+(long)iy[3*h+y]*w,*r4=temp+(long)iy[4*h+y]*w;
  float* dst=out+(long)y*w;for(int x=0;x<w;x++)dst[x]=k[0]*r0[x]+k[1]*r1[x]+k[2]*r2[x]+k[3]*r3[x]+k[4]*r4[x];
 }});
 for(auto &t:ts)t.join();
}
