import os,sys,pickle,time;sys.path.insert(0,'.')
import numpy as np
import match
from dw import *
from runmatch_lib import key,purity,page
S=match.S;SK=key(S)
frames,uniq=pickle.load(open(f'match_{os.environ["TAG"]}.pkl','rb'))
rng=np.random.default_rng(1)
t0=time.time()
tm=[k for k,v in uniq.items() if v['status']=='toomany']
for n,k in enumerate(tm):
    tex,sx,sy,sw,sh=k
    g=page(tex)[sy:sy+sh,sx:sx+sw];T=g[...,3]>0
    c=match.find(T)
    if not c: uniq[k]=dict(status='none',npx=int(T.sum()));continue
    c=np.array(c);yy=c[:,0];xx=c[:,1]
    gk=key(g)
    py,px=np.nonzero(T)
    sel=rng.choice(len(py),size=min(120,len(py)),replace=False)
    sy_,sx_=py[sel],px[sel];gs=gk[sy_,sx_]
    A=rng.integers(0,len(sel),600);B=rng.integers(0,len(sel),600)
    keep=A!=B;A=A[keep];B=B[keep]
    eqg=gs[A]==gs[B]
    agree=np.zeros(len(c))
    for a,b,e in zip(A,B,eqg):
        agree+=((SK[yy+sy_[a],xx+sx_[a]]==SK[yy+sy_[b],xx+sx_[b]])==e)
    agree/=len(A)
    top=np.argsort(-agree)[:400]
    gkf=gk[T];sc=[]
    for i in top:
        if agree[i]<0.97: break
        y,x=int(yy[i]),int(xx[i])
        sk=SK[y:y+sh,x:x+sw][T]
        p1,p2=purity(gkf,sk)
        aeq=float((S[y:y+sh,x:x+sw,3][T]==g[...,3][T]).mean())
        sc.append((min(p1,p2),p1,p2,aeq,y,x))
    sc.sort(reverse=True)
    uniq[k]=dict(status='ok' if sc else 'none',npx=int(T.sum()),cands=sc,from_toomany=True,nc=len(c))
    if n%20==0: print(n,len(tm),round(time.time()-t0),flush=True)
pickle.dump((frames,uniq),open(f'match2_{os.environ["TAG"]}.pkl','wb'))
import collections
print(collections.Counter(v['status'] for v in uniq.values()))
