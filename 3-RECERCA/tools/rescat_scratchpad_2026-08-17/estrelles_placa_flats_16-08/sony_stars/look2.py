import numpy as np
IA=np.load("IMGA.npy"); IC=np.load("IMGC.npy")
def show(IM,x,y,lab,H=12):
    st=IM[y-H:y+H+1,x-H:x+H+1]
    print(f"--- {lab} centred ({x},{y}), ADU/s, 1 px per char-cell ---")
    for i in range(st.shape[0]):
        print("  "+"".join(f"{st[i,j]:6.0f}" for j in range(st.shape[1])))
# the chain
show(IC,3770,1850,"group C stack, chain region")
print()
show(IC,5550,404,"group C stack, brightest source")
