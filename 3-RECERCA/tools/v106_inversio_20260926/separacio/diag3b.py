import numpy as np, pickle
from inversio import Inversio
sig = dict(np.load('SIG.npz')); vt = pickle.load(open('VAR_irls.pkl', 'rb'))
fr = [j for j in range(67) if sig['sig'][j].min() < 0.5]
for dphi in [0.0625, 0.25]:
    I = Inversio(sig_tab=sig, verbose=True, dphi=dphi); I.var_tab = vt
    I.prepara(fr); I.construeix(fr); I.resol()
    L = I.L; res = L['y'] - I.C.ravel()[L['p']] - I.pred_lun
    print(dphi, I.nphi, I.lam.shape, 'rms pred', np.sqrt(np.mean(I.pred_lun**2)), 'rms y', np.sqrt(np.mean(L['y']**2)), 'rms res', np.sqrt(np.mean(res**2)), 'w-mean res²', np.mean(L['w']*res**2))
