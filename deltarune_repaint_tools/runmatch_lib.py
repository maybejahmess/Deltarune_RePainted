import os
import sys,pickle,time;sys.path.insert(0,'.')
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
