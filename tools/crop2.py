# usage: python3 -I crop2.py <raw_dir> <out_dir> [--debug dir]
import sys,glob,os,numpy as np,cv2
from PIL import Image
src,dst=sys.argv[1],sys.argv[2]
dbg=sys.argv[4] if len(sys.argv)>4 else None
def textmask(g):
    # thin high-contrast strokes (print/handwriting), dark or light
    k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9))
    th=np.maximum(cv2.morphologyEx(g,cv2.MORPH_BLACKHAT,k),cv2.morphologyEx(g,cv2.MORPH_TOPHAT,k))
    m=(th>45).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_RECT,(9,5)))
    n,lab,st,_=cv2.connectedComponentsWithStats(m)
    out=np.zeros_like(m)
    for i in range(1,n):
        x,y,w,h,a=st[i]
        if w>=14 and h>=5 and a>=40 and a/(w*h)>0.18: out[lab==i]=1
    return cv2.dilate(out,cv2.getStructuringElement(cv2.MORPH_RECT,(7,7)))
def crop(path):
    im=Image.open(path).convert('RGB'); W,H=im.size
    sc=400/max(W,H); arr=np.asarray(im.resize((max(1,round(W*sc)),max(1,round(H*sc)))))
    f=arr.astype(float)/255; mx=f.max(2); mn=f.min(2); sat=(mx-mn)/(mx+1e-6)
    ink=((sat>0.12)|(mx<0.82)).astype(float)
    tm=textmask(cv2.cvtColor(arr,cv2.COLOR_RGB2GRAY)).astype(float)
    h,w=ink.shape
    good=ink-4*tm
    ys,xs=np.where(ink>0)
    if len(xs)<200: bw,bh=w,h
    else: bw,bh=xs.max()-xs.min()+1, ys.max()-ys.min()+1
    I=np.pad(good.cumsum(0).cumsum(1),((1,0),(1,0)))
    cx,cy=w/2,h/2; step=2
    for frac in (0.75,0.65,0.55,0.48,0.40):
        s=max(16,int(frac*min(bw,bh)))
        best=(-1e9,0,0)
        for y in range(0,h-s+1,step):
            for x in range(0,w-s+1,step):
                v=I[y+s,x+s]-I[y,x+s]-I[y+s,x]+I[y,x]
                v-=0.0005*((x+s/2-cx)**2+(y+s/2-cy)**2)**.5
                if v>best[0]: best=(v,x,y)
        if best[0]/(s*s)>0.97: break
    _,x,y=best
    box=(int(x/sc),int(y/sc),int((x+s)/sc),int((y+s)/sc))
    out=np.asarray(im.crop(box).resize((320,320),Image.LANCZOS)).copy()
    # edit out any text still inside the crop
    tsub=tm[y:y+s,x:x+s]
    if tsub.sum()>0:
        msk=cv2.resize((tsub*255).astype(np.uint8),(320,320),interpolation=cv2.INTER_NEAREST)
        msk=cv2.dilate(msk,np.ones((5,5),np.uint8))
        out=cv2.inpaint(out,msk,7,cv2.INPAINT_TELEA)
    return Image.fromarray(out),tm
os.makedirs(dst,exist_ok=True)
for f in sorted(glob.glob(os.path.join(src,'*.img'))):
    pid=os.path.basename(f)[:-4]
    try:
        c,tm=crop(f); c.save(os.path.join(dst,pid+'.webp'),quality=72,method=6)
        if dbg: os.makedirs(dbg,exist_ok=True); Image.fromarray((tm*255).astype(np.uint8)).save(os.path.join(dbg,pid+'.png'))
    except Exception as e: print('FAIL',pid,e)
