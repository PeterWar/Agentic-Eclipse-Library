from a16_build_psb import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 out=O/'marks246_T_R02';box=(4830,3300,5240,4030);x0,y0,x1,y1=box;marks=np.load(O/'ROI_L246.npz')['c-1'][y0-3000:y1-3000,x0-4600:x1-4600]>0;z=np.load(O/'current_lunar_support.npz');a,b,c,d=z['box'];moon=z['support'][y0-b:y1-b,x0-a:x1-a];extent=[x0,x1,y1,y0]
 for tags,name in [(['P04_WOW','P05_WOW_bilateral','P03_MGN'],'E2'),(['01','04','05','06'],'E3')]:
  fig,axes=plt.subplots(len(tags),4,figsize=(13,5*len(tags)),squeeze=False)
  for i,tag in enumerate(tags):
   lid=next(k for k,v in MAP.items() if v==tag);actual=PSB(str(O/'V84_Pere_input.psb')).channel_box(lid,1,box);values=[actual,*[np.load(p/(tag+'_u16.npy'),mmap_mode='r')[y0:y1,x0:x1] for p in [O/'filters_baseline/products/filters',O/'filters_selected',O/('filters_physical_T_E2' if name=='E2' else 'filters_physical_E3')/'products/filters']]]
   lo,hi=np.percentile(values[0][~moon],[1,99]);
   for j,(label,q) in enumerate(zip(['V84 Pere','Regenerated baseline','Delivered V85','Physical T R02'],values)):
    ax=axes[i,j];img=np.ma.array(q,mask=moon);ax.imshow(img,cmap='gray',vmin=lo,vmax=hi,extent=extent,interpolation='nearest');ax.contour(marks,levels=[.5],colors='#FF6C6C',linewidths=.4,extent=extent,origin='upper');ax.set_title(tag+' | '+label);ax.set_xticks([]);ax.set_yticks([])
  fig.suptitle('Same display limits per row. Red: user mark246; masked Moon. Diagnostic raw filters.');fig.tight_layout();fig.savefig(out/(name+'_comparison.png'),dpi=140);plt.close(fig)
 print('PANELS_COMPLETE')
if __name__=='__main__':guard();main()
