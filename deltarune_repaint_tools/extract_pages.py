"""Step 1: decode every texture page of a data.win into pages/pN.npy (+ PNG previews)."""
import os,sys
sys.path.insert(0,'.')
import numpy as np
from PIL import Image
from dw import load,textures,decode_tex
d,ch=load(os.environ['DATAWIN'])
os.makedirs('pages',exist_ok=True)
for i,e in enumerate(textures(d,ch)):
    a=decode_tex(d,e)
    np.save(f'pages/p{i}.npy',a);Image.fromarray(a).save(f'pages/p{i}.png')
    print('page',i,a.shape,flush=True)
