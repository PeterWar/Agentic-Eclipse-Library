"""Repeat ellipse search with diverse centers; retain initial search receipts."""
from study import *
import shutil

for name in sys.argv[1:]:
    path=Path(RUN.rebut(name+'.json'));rep=json.loads(path.read_text())
    old=path.parent/'search_initial_SUPERSEDED';old.mkdir(exist_ok=True)
    if not (old/path.name).exists():shutil.copy2(path,old/path.name)
    s=Samples(center=rep['reference_center'],radial=rep['radial_selection_px'],step=4,
        nsectors=rep['sector_count'],margin_deg=rep['sector_margin_degrees'])
    data=np.load(D/(name+'_samples.npz'));z=data['z']
    assert np.array_equal(s.x,data['x']) and np.array_equal(s.y,data['y'])
    for parity in [0,1]:
        log(name+f' diversified ellipse parity{parity}')
        fit=Fit(s,z,parity)
        circle=next(v for v in rep['fits'] if v['model']=='circle_free' and v['training_parity']==parity)
        row=fit.optimize(ellipse=True,seed=circle['parameters'],quick=True)
        result=compact(row);result.update(model='ellipse_free',training_parity=parity)
        result.update(diagnostics(s,z,fit,row))
        rep['fits']=[v for v in rep['fits'] if not(v['model']=='ellipse_free' and v['training_parity']==parity)]+[result]
        np.savez(D/(name+f'_{parity}_ellipse_free_profile.npz'),knots=row['knots'],profile=row['profile'])
        rep['ellipse_search']='729 joint grid points; best seed at24 distinct centers plus best circle; L-BFGS-B'
        save(name,rep)
        log(name+' '+str((parity,result['center_xy'],result['axis_ratio'],result['heldout'])))
    fig,axes=plt.subplots(2,2,figsize=(13,7))
    for parity in [0,1]:
        for model,label in [('solar_fixed','Solar fix'),('circle_free','Cercle lliure'),('ellipse_free','El·lipse lliure')]:
            row=next(v for v in rep['fits'] if v['model']==model and v['training_parity']==parity)
            p=np.load(D/(name+f'_{parity}_{model}_profile.npz'));good=(p['knots']>=s.radial[0])&(p['knots']<=s.radial[1])
            axes[parity,0].plot(p['knots'][good],p['profile'][good],label=label,lw=.9)
            axes[parity,1].scatter(row['center_xy'][0]-s.center[0],row['center_xy'][1]-s.center[1],label=label)
        axes[parity,0].set_title(f'{name} · entrenament {parity}');axes[parity,0].set_xlabel('Coordenada radial [px]');axes[parity,0].set_ylabel('Perfil estimat');axes[parity,0].legend()
        axes[parity,1].axhline(0,color='gray',lw=.5);axes[parity,1].axvline(0,color='gray',lw=.5)
        axes[parity,1].set_xlim(-135,135);axes[parity,1].set_ylim(135,-135);axes[parity,1].set_aspect('equal')
        axes[parity,1].set_xlabel('Centre − referència: x [px]');axes[parity,1].set_ylabel('y [px]');axes[parity,1].legend()
    fig.tight_layout();fig.savefig(RUN.vista(name+'_profiles.png'),dpi=130);plt.close(fig)
    log(name+' diversified search COMPLETE')
