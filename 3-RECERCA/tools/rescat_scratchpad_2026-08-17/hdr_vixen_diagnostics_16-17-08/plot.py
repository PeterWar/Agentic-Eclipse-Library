import numpy as np, json, math
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
per = json.load(open('perfils.json')); lin = json.load(open('lineal.json'))
exec(open('corba.py').read().split("t_now, coef_now")[0])
def prof(name, key): return np.array([d['rmid'] for d in per[name] if key in d]), np.array([d[key] for d in per[name] if key in d])
fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))
r, y = prof('sketch','Y'); ax[0].plot(r, y, 'k-', label='sketch (Y, sRGB)')
r, y = prof('foto','Y'); ax[0].plot(r, y, 'r-', label='FOTO actual (Y)')
t1,_ = corba((0.82,0.60,0.15), u0); ax[0].plot(rm, t1, 'r:', label='corba 0.82/0.60/0.15 (model)')
t2,_ = corba((0.78,0.50,0.175), u0); ax[0].plot(rm, t2, 'b--', label='corba 0.78/0.50/0.175 (proposta)')
ax[0].set_xlabel('R☉'); ax[0].set_ylabel('nivell sRGB'); ax[0].set_xlim(1,8.5); ax[0].set_ylim(0.1,0.9); ax[0].legend(fontsize=8); ax[0].set_title('gradient radial'); ax[0].grid(alpha=.3)
for nom, col in (('sketch','k'),('foto','r')):
    r, v = prof(nom,'RG'); ax[1].plot(r, v, col+'-', label=f'{nom} R/G')
    r, v = prof(nom,'BG'); ax[1].plot(r, v, col+'--', label=f'{nom} B/G')
ax[1].axhline(1, color='gray', lw=.5); ax[1].set_xlim(1,8.5); ax[1].set_xlabel('R☉'); ax[1].legend(fontsize=8); ax[1].set_title('cromaticitat (valors sRGB codificats)'); ax[1].grid(alpha=.3)
# disc
d = json.load(open('disc.json'))
for k, col, lab in (('sketch','k','sketch'),('foto','r','FOTO')):
    p = np.array(d[k]['perfil_G_Y']); ax[2].plot(p[:,0], p[:,2], col+'-o', label=f'{lab} disc (Y)')
ax[2].axhline(0.1844, color='k', ls=':', label='cel sketch 6 R☉'); ax[2].axhline(0.1613, color='r', ls=':', label='cel FOTO 6 R☉')
ax[2].set_xlabel('r / R_lluna'); ax[2].set_title('earthshine: perfil dins del disc'); ax[2].legend(fontsize=8); ax[2].grid(alpha=.3)
plt.tight_layout(); plt.savefig('sketch_vs_foto_perfils.png', dpi=110)
print('ok')
