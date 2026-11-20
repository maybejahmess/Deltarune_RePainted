import sys;sys.path.insert(0,'.')
import numpy as np
from PIL import Image
import os
SHEET=os.environ['SHEET']
S=np.array(Image.open(SHEET).convert('RGBA'))
M=S[...,3]>0
H,W=M.shape
def windows(M):
    P=np.pad(M,((0,0),(0,8)))
    w=np.zeros(M.shape,np.uint8)
    for k in range(8): w|=(P[:,k:k+M.shape[1]].astype(np.uint8)<<k)
    return w
W8=windows(M)
hist=np.bincount(W8.ravel(),minlength=256)
def find(T,maxc=2000000):
    h,w=T.shape
    if T.sum()==0: return []
    k=min(8,w);km=(1<<k)-1
    Tp=np.pad(T,((0,0),(0,8)))
    T8=np.zeros(T.shape,np.uint8)
    for j in range(k): T8[:]|=(Tp[:,j:j+w].astype(np.uint8)<<j)
    ys,xs=np.nonzero(T8[:, :w-k+1])
    if len(ys)==0: return []
    vals=T8[ys,xs]
    rare=hist[vals] if k==8 else np.ones(len(vals))
    order=np.argsort(rare,kind='stable')
    # choose anchors: rarest, then others spread out
    sel=[order[0]]
    for i in order[1:]:
        if len(sel)>=5: break
        if all(abs(ys[i]-ys[j])+abs(xs[i]-xs[j])>=4 for j in sel): sel.append(i)
    ay,ax,v=int(ys[sel[0]]),int(xs[sel[0]]),int(vals[sel[0]])
    base=(W8==v) if k==8 else ((W8&km)==v)
    yy,xx=np.nonzero(base)
    yy=yy-ay;xx=xx-ax
    ok=(yy>=0)&(xx>=0)&(yy+h<=H)&(xx+w<=W)
    yy=yy[ok];xx=xx[ok]
    for i in sel[1:]:
        if len(yy)==0: return []
        by,bx,bv=int(ys[i]),int(xs[i]),int(vals[i])
        got=W8[yy+by,xx+bx]
        if k!=8: got=got&km
        m=got==bv
        yy=yy[m];xx=xx[m]
    res=[]
    for y,x in zip(yy.tolist(),xx.tolist()):
        if (M[y:y+h,x:x+w]==T).all(): res.append((y,x))
    return res
