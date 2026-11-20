import os,sys,pickle,time;sys.path.insert(0,'.')
import numpy as np
import match
from dw import *
d,ch=load(os.environ['DATAWIN'])
sp=parse_sprites(d,ch)
pages={}
def page(i):
    if i not in pages: pages[i]=np.load(f'pages/p{i}.npy')
    return pages[i]
S=match.S
def key(a): # uint32 key from rgba
    a=a.astype(np.uint32);return (a[...,0]<<24)|(a[...,1]<<16)|(a[...,2]<<8)|a[...,3]
def purity(g,s):
    # g,s: flat uint32 keys, same length. returns (p_g->s, p_s->g)
    n=len(g)
    def pur(a,b):
        pair=a.astype(np.uint64)<<32|b.astype(np.uint64)
        u,c=np.unique(pair,return_counts=True)
        ak=(u>>32).astype(np.uint32)
        # for each a, max count
        order=np.lexsort((-c,ak));ak2=ak[order];c2=c[order]
        first=np.r_[True,ak2[1:]!=ak2[:-1]]
        return c2[first].sum()/n
    return pur(g,s),pur(s,g)
uniq={}  # (tex,sx,sy,sw,sh)-> result
t0=time.time()
frames=[]
for si,s in enumerate(sp):
    for fi,f in enumerate(s['frames']):
        frames.append((si,fi,f))
print(len(frames),'frames')
for n,(si,fi,f) in enumerate(frames):
    k=(f['tex'],)+f['src']
    if k in uniq: continue
    sx,sy,sw,sh=f['src']
    if sw==0 or sh==0 or f['tex'] in (0,1) or f['tex']>8: uniq[k]=dict(status='skip');continue
    g=page(f['tex'])[sy:sy+sh,sx:sx+sw]
    T=g[...,3]>0
    npx=int(T.sum())
    if npx<25: uniq[k]=dict(status='tiny',npx=npx);continue
    c=match.find(T)
    if not c: uniq[k]=dict(status='none',npx=npx);continue
    if len(c)>300: uniq[k]=dict(status='toomany',npx=npx,nc=len(c));continue
    gk=key(g)[T]
    sc=[]
    for (y,x) in c:
        sk=key(S[y:y+sh,x:x+sw])[T]
        p1,p2=purity(gk,sk)
        # exact alpha agreement too
        aeq=float((S[y:y+sh,x:x+sw,3][T]==g[...,3][T]).mean())
        sc.append((min(p1,p2),p1,p2,aeq,y,x))
    sc.sort(reverse=True)
    uniq[k]=dict(status='ok',npx=npx,cands=sc)
    if n%100==0: print(n,round(time.time()-t0),flush=True)
pickle.dump((frames,uniq),open(f'match_{os.environ["TAG"]}.pkl','wb'))
import collections
print(collections.Counter(v['status'] for v in uniq.values()),round(time.time()-t0))
