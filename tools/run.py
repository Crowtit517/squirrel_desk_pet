import numpy as np
from PIL import Image
F=[Image.open(f'frames/f{i}.png') for i in range(4)]
LIFT=10
CW=max(f.width for f in F);CH=max(f.height for f in F)+LIFT
def place(fr,lift=0):
    c=Image.new('RGBA',(CW,CH),(0,0,0,0))
    c.paste(fr,(CW-fr.width,CH-fr.height-lift),fr)   # 얼굴(오른쪽) 기준 정렬, 발 바닥 기준
    return c
def to_p(img):
    a=np.array(img);al=a[:,:,3]
    q=Image.fromarray(a[:,:,:3]).quantize(255,dither=Image.NONE)
    pal=(q.getpalette()+[0]*768)[:768]
    arr=np.array(q);arr[al<128]=255
    p=Image.fromarray(arr,'P');p.putpalette(pal);p.info['transparency']=255
    return p
def save(name,seq):
    imgs=[place(F[i],l) for i,l,d in seq];durs=[d for i,l,d in seq]
    ps=[to_p(im) for im in imgs]
    ps[0].save(name+'.gif',save_all=True,append_images=ps[1:],duration=durs,loop=0,transparency=255,disposal=2,optimize=False)
    imgs[0].save(name+'.apng',save_all=True,append_images=imgs[1:],duration=durs,loop=0,disposal=1)
    return imgs
C=save('squirrel_run_c',[(0,0,120),(3,0,120),(2,4,100)])
E=save('squirrel_run_e',[(0,0,120),(3,0,120),(2,0,100)])
W=CW*3+40;s=Image.new('RGB',(W,CH+20),(60,60,70));x=10
for im in (C[0],C[1],C[2]):
    s.paste(im,(x,10),im);x+=CW+10
s.save('runcheck_c.png')
