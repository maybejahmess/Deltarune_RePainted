import struct,bz2,numpy as np
def u32(d,p): return struct.unpack('<I',d[p:p+4])[0]
HASH=lambda r,g,b,a:(r^g^b^a)&63
def _sx(v,bits): return v-(1<<bits) if v>=(1<<(bits-1)) else v
def qoi_decode(b,w,h):
    assert b[:4]==b'fioq'
    W,H=struct.unpack('<HH',b[4:8])
    n=W*H
    out=bytearray(n*4)
    idx=[(0,0,0,0)]*64
    r=g=bl=0;a=255;p=12;run=0;L=len(b)
    for i in range(n):
        if run>0: run-=1
        elif p<L:
            t=b[p];p+=1
            if t<0x40: r,g,bl,a=idx[t]
            elif t<0x60: run=t&0x1f
            elif t<0x80:
                run=(((t&0x1f)<<8)|b[p])+32;p+=1
            elif t<0xc0:
                r=(r+_sx((t>>4)&3,2))&255;g=(g+_sx((t>>2)&3,2))&255;bl=(bl+_sx(t&3,2))&255
            elif t<0xe0:
                t2=b[p];p+=1
                r=(r+_sx(t&0x1f,5))&255;g=(g+_sx(t2>>4,4))&255;bl=(bl+_sx(t2&15,4))&255
            elif t<0xf0:
                m=(t<<16)|(b[p]<<8)|b[p+1];p+=2
                r=(r+_sx((m>>15)&0x1f,5))&255;g=(g+_sx((m>>10)&0x1f,5))&255
                bl=(bl+_sx((m>>5)&0x1f,5))&255;a=(a+_sx(m&0x1f,5))&255
            else:
                if t&8: r=b[p];p+=1
                if t&4: g=b[p];p+=1
                if t&2: bl=b[p];p+=1
                if t&1: a=b[p];p+=1
            idx[HASH(r,g,bl,a)]=(r,g,bl,a)
        o=i*4
        out[o]=r;out[o+1]=g;out[o+2]=bl;out[o+3]=a
    assert p==L,(p,L)
    return np.frombuffer(bytes(out),np.uint8).reshape(H,W,4)
def qoi_encode(arr,d8=True,d16=True,d24=True):
    H,W,_=arr.shape
    px=[tuple(x) for x in arr.reshape(-1,4).tolist()]
    out=bytearray(b'fioq'+struct.pack('<HHI',W,H,0))
    idx=[(0,0,0,0)]*64; pr=(0,0,0,255); run=0
    def flush(run):
        if run<33: out.append(0x40|(run-1))
        else:
            run-=33; out.append(0x60|(run>>8)); out.append(run&255)
    for q in px:
        if q==pr:
            run+=1
            if run==8224: flush(run);run=0
            continue
        if run: flush(run);run=0
        h=HASH(*q)
        if idx[h]==q: out.append(h)
        else:
            idx[h]=q
            dr=q[0]-pr[0];dg=q[1]-pr[1];db=q[2]-pr[2];da=q[3]-pr[3]
            # wrap deltas into signed 8-bit like the decoder's modular arithmetic
            dr=_sx(dr&255,8);dg=_sx(dg&255,8);db=_sx(db&255,8);da=_sx(da&255,8)
            if d8 and da==0 and -2<=dr<=1 and -2<=dg<=1 and -2<=db<=1:
                out.append(0x80|((dr&3)<<4)|((dg&3)<<2)|(db&3))
            elif d16 and da==0 and -16<=dr<=15 and -8<=dg<=7 and -8<=db<=7:
                out.append(0xc0|(dr&0x1f));out.append(((dg&15)<<4)|(db&15))
            elif d24 and all(-16<=v<=15 for v in (dr,dg,db,da)):
                m=((dr&31)<<15)|((dg&31)<<10)|((db&31)<<5)|(da&31)
                out+=bytes([0xe0|(m>>16),(m>>8)&255,m&255])
            else:
                f=0xf0;vals=bytearray()
                for k,bit in ((0,8),(1,4),(2,2),(3,1)):
                    if q[k]!=pr[k]: f|=bit;vals.append(q[k])
                out.append(f);out+=vals
        pr=q
    if run: flush(run)
    out[8:12]=struct.pack('<I',len(out)-12)
    return bytes(out)
def load(path):
    d=open(path,'rb').read()
    ch={};p=8
    while p<len(d):
        n=d[p:p+4].decode();s=u32(d,p+4);ch[n]=(p+8,s);p+=8+s
    return d,ch
def textures(d,ch):
    base,_=ch['TXTR'];cnt=u32(d,base)
    offs=[u32(d,base+4+4*i) for i in range(cnt)]
    ents=[]
    for i,o in enumerate(offs):
        sc,mip,ln,w,h,gi,ptr,_=struct.unpack('<8I',d[o:o+32]) if False else struct.unpack('<8I',d[o:o+32])
        ents.append(dict(entry=o,len=ln,w=w,h=h,ptr=ptr))
    return ents
def decode_tex(d,e):
    raw=d[e['ptr']:e['ptr']+e['len']]
    assert raw[:4]==b'2zoq'
    w,h=struct.unpack('<HH',raw[4:8])
    return qoi_decode(bz2.decompress(raw[12:]),w,h)

def parse_sprites(d,ch):
    base,sz=ch['SPRT'];cnt=u32(d,base)
    offs=[u32(d,base+4+4*i) for i in range(cnt)]
    def s(p):
        n=u32(d,p-4);return d[p:p+n].decode('utf8','replace')
    out=[]
    for o in offs:
        v=struct.unpack('<14I',d[o:o+56]);name=s(v[0])
        w,h=v[1],v[2]
        q=o+56
        assert u32(d,q)==0xffffffff
        sver=u32(d,q+4);stype=u32(d,q+8)
        if stype!=0:
            out.append(dict(name=name,w=w,h=h,frames=[],type=stype));continue
        q+=12+8  # playback speed + type
        if sver>=2: q+=4
        if sver>=3: q+=4
        nf=u32(d,q);q+=4
        fr=[]
        for i in range(nf):
            tp=u32(d,q+4*i)
            sx,sy,sw,sh,tx,ty,tw,th,bw,bh,tid=struct.unpack('<HHHHHHHHHHH',d[tp:tp+22])
            fr.append(dict(tpag=tp,src=(sx,sy,sw,sh),tgt=(tx,ty,tw,th),bound=(bw,bh),tex=tid))
        out.append(dict(name=name,w=w,h=h,frames=fr,type=0,off=o))
    return out
