import sys,struct,bz2,os;sys.path.insert(0,'.')
import numpy as np
from dw import *
SRC=os.environ['DATAWIN']
d,ch=load(SRC);ents=textures(d,ch)
out=bytearray(d);tb,ts=ch['TXTR'];chunk_end=tb+ts
blobs={}
for i,e in enumerate(ents):
    orig=bytes(d[e['ptr']:e['ptr']+e['len']])
    p=f'pages/new{i}.npy'
    if os.path.exists(p) and not (np.load(p)==np.load(f'pages/p{i}.npy')).all():
        arr=np.load(p);h,w=arr.shape[:2];best=None
        for kw in (dict(),dict(d24=False),dict(d16=False),dict(d8=False,d16=False,d24=False)):
            x=qoi_encode(arr,**kw);bl=b'2zoq'+struct.pack('<HHI',w,h,len(x))+bz2.compress(x,9)
            assert (qoi_decode(x,w,h)==arr).all()
            if best is None or len(bl)<len(best): best=bl
        blobs[i]=best;print(i,'new',len(best),'orig',len(orig))
    else: blobs[i]=orig
first=min(i for i in blobs if blobs[i] is not None and not (blobs[i]==bytes(d[ents[i]['ptr']:ents[i]['ptr']+ents[i]['len']])))
print('first changed page',first)
pos=ents[first]['ptr']
al=lambda v:(v+63)//64*64
for i in range(first,len(ents)):
    ptr=al(pos);b=blobs[i]
    out[ptr:ptr+len(b)]=b
    struct.pack_into('<I',out,ents[i]['entry']+8,len(b));struct.pack_into('<I',out,ents[i]['entry']+24,ptr)
    pos=ptr+len(b)
assert pos<=chunk_end,(pos,chunk_end)
# zero the gaps/tail
last_end={}
# clear everything from first.ptr to chunk_end not covered by blobs
cover=np.zeros(chunk_end-ents[first]['ptr'],bool)
for i in range(first,len(ents)):
    ptr=struct.unpack_from('<I',out,ents[i]['entry']+24)[0];ln=struct.unpack_from('<I',out,ents[i]['entry']+8)[0]
    cover[ptr-ents[first]['ptr']:ptr-ents[first]['ptr']+ln]=True
base=ents[first]['ptr']
for j in np.nonzero(~cover)[0].tolist(): out[base+j]=0
print('end of data',pos,'chunk end',chunk_end,'slack',chunk_end-pos)
open(os.environ.get('OUT','rebuilt_data.win'),'wb').write(out);print(len(out),len(d))
