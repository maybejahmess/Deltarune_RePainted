import os,sys,pickle,collections,csv;sys.path.insert(0,'.')
import numpy as np
from PIL import Image
from dw import *
d,ch=load(os.environ['DATAWIN'])
sp=parse_sprites(d,ch)
for i in range(9):
    p=f'pages/new{i}.npy'
    if os.path.exists(p): os.remove(p)
pages={i:np.load(f'pages/p{i}.npy').copy() for i in range(2,9)}
TAGS=('susie','kris','ralsei','lancer','jevil','battlemenu','berdly')
KEYS={'susie':('susie',),'kris':('kris',),'ralsei':('ralsei',),'lancer':('lancer',),'jevil':('joker','jevil'),'berdly':('berdly',)}
THR=0.99
sheet={t:np.array(Image.open(f'sheet_{t}.png').convert('RGBA')) for t in TAGS}
data={}
byk=collections.defaultdict(list)
for t in TAGS:
    frames,uniq=pickle.load(open(f'match2_{t}.pkl','rb'));data[t]=uniq
    if not byk:
        for si,fi,f in frames: byk[(f['tex'],)+f['src']].append((sp[si]['name'],fi))
claimed={};rows=collections.defaultdict(list);acc=collections.defaultdict(dict);done=set()
def owned(tag,k):
    ks=KEYS.get(tag)
    return bool(ks) and any(any(x in n for x in ks) for n,_ in byk[k])
for phase in (1,2):
  for tag in TAGS:
    S=sheet[tag]
    for k,v in sorted(data[tag].items()):
        if v['status']!='ok' or (tag,k) in done: continue
        if phase==1 and not owned(tag,k): continue
        names=' '.join(f'{n}[{i}]' for n,i in byk[k]);c=v['cands'];b=c[0];sw,sh=k[3],k[4]
        done.add((tag,k))
        if b[0]<THR: rows[tag].append(['skipped-low-confidence',names,*k,'','',round(b[0],3)]);continue
        tied=[x for x in c if x[0]>=b[0]-1e-9]
        blocks=[S[x[4]:x[4]+sh,x[5]:x[5]+sw] for x in tied]
        if not all((bb==blocks[0]).all() for bb in blocks):
            rows[tag].append(['skipped-ambiguous',names,*k,'','',f'{len(tied)} equal candidates']);continue
        blk=blocks[0]
        if k in claimed and (claimed[k][1]!=blk).any():
            rows[tag].append([f'skipped-conflicts-with-{claimed[k][0]}-sheet',names,*k,b[5],b[4],round(b[0],4)]);continue
        tex,sx,sy,_,_=k
        reg=pages[tex][sy:sy+sh,sx:sx+sw];m=reg[...,3]>0
        gcols=len({tuple(p) for p in reg[m].tolist()})
        if k not in claimed and gcols<=2 and (reg[m]!=blk[m]).any():
            rows[tag].append(['skipped-low-information(<=2 colours, would change)',names,*k,b[5],b[4],round(b[0],4)]);continue
        if k not in claimed: reg[m]=blk[m]
        claimed.setdefault(k,(tag,blk));acc[tag][k]=b
        rows[tag].append(['applied',names,*k,b[5],b[4],round(b[0],4)])
for tag in TAGS:
    with open(f'match_report_{tag}.csv','w',newline='') as f:
        w=csv.writer(f);w.writerow(['status','game_frames_using_region','texture_page','region_x','region_y','w','h','sheet_x','sheet_y','structure_score']);w.writerows(rows[tag])
    ks=KEYS.get(tag);cov=collections.defaultdict(lambda:[0,0])
    if ks:
        others=[x for t,v in KEYS.items() if t!=tag for x in v]
        for s_ in sp:
            nm=s_['name']
            if not any(x in nm for x in ks) or s_['type']!=0 or any(o in nm for o in others): continue
            for fr in s_['frames']:
                kk=(fr['tex'],)+fr['src'];cov[nm][1]+=1
                if kk in acc[tag]: cov[nm][0]+=1
    full=[k for k,v in cov.items() if v[0]==v[1]];part=[(k,v) for k,v in cov.items() if 0<v[0]<v[1]];none=[k for k,v in cov.items() if v[0]==0]
    print(tag,'applied',len(acc[tag]),dict(collections.Counter(r[0].split('(')[0] for r in rows[tag])))
    if ks: print('   named sprites',len(cov),'full',len(full),'partial',part,'\n   unmatched',none)
for i,P in pages.items():
    n=int((P!=np.load(f'pages/p{i}.npy')).any(-1).sum())
    if n: np.save(f'pages/new{i}.npy',P)
    print('page',i,'changed px',n)
