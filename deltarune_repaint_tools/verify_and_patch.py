"""Step 6: verify the rebuilt data.win against the original and write an IPS patch.
Usage: DATAWIN=original data.win python3 verify_and_patch.py rebuilt_data.win out.ips"""
import os,sys
sys.path.insert(0,'.')
import numpy as np
from dw import *
SRC=os.environ['DATAWIN'];NEW=sys.argv[1];OUT=sys.argv[2]
o=open(SRC,'rb').read();n=open(NEW,'rb').read()
d1,ch1=load(SRC);d2,ch2=load(NEW)
assert ch1==ch2 and len(o)==len(n),'chunk layout or file size changed'
for i,e in enumerate(textures(d2,ch2)):
    a=decode_tex(d2,e)
    exp=np.load(f'pages/new{i}.npy') if os.path.exists(f'pages/new{i}.npy') else np.load(f'pages/p{i}.npy')
    print('page',i,'ok' if (a==exp).all() else 'MISMATCH')
tb,ts=ch1['TXTR']
diff=np.nonzero(np.frombuffer(o,np.uint8)!=np.frombuffer(n,np.uint8))[0]
print('bytes changed outside TXTR:',int(((diff<tb)|(diff>=tb+ts)).sum()))
print('sprite tables identical:',parse_sprites(d1,ch1)==parse_sprites(d2,ch2))
dl=diff.tolist();runs=[];start=prev=dl[0]
for p in dl[1:]:
    if p-prev>8: runs.append((start,prev+1));start=p
    prev=p
runs.append((start,prev+1));ips=bytearray(b'PATCH')
for s,e in runs:
    while s<e:
        L=min(e-s,0xffff);assert s!=0x454f46;ips+=s.to_bytes(3,'big')+L.to_bytes(2,'big')+n[s:s+L];s+=L
ips+=b'EOF';open(OUT,'wb').write(ips)
t=bytearray(o);p=5
while ips[p:p+3]!=b'EOF':
    s=int.from_bytes(ips[p:p+3],'big');L=int.from_bytes(ips[p+3:p+5],'big');t[s:s+L]=ips[p+5:p+5+L];p+=5+L
print('IPS written:',len(ips),'bytes; reproduces rebuilt file:',bytes(t)==n)
