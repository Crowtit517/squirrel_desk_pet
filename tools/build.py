import cv2, numpy as np
from PIL import Image
im=cv2.imread('../images/4.png')
# 1) 워터마크 제거: 30% 흰색 덧칠 되돌리기 + 가장자리 인페인트
cx,cy=904,214
def star(r,k):
    pts=[]
    for i in range(8):
        ang=i*np.pi/4-np.pi/2
        pts.append((cx+(r if i%2==0 else r*k)*np.cos(ang),cy+(r if i%2==0 else r*k)*np.sin(ang)))
    m=np.zeros(im.shape[:2],np.uint8);cv2.fillPoly(m,[np.array(pts,np.int32)],255);return m
core,outer=star(23,0.44),star(32,0.62)
f=im.astype(np.float32);inv=np.clip((f-0.30*255)/0.70,0,255)
out=f.copy();out[core>0]=inv[core>0]
ring=((outer>0)&(core==0)).astype(np.uint8)*255
out=cv2.inpaint(out.astype(np.uint8),ring,4,cv2.INPAINT_TELEA)
soft=cv2.medianBlur(out,5)
m=cv2.GaussianBlur((outer>0).astype(np.float32),(9,9),0)[...,None]
out=(out*(1-m*0.8)+soft*(m*0.8)).astype(np.uint8)
out=cv2.imread('clean_full2.png')
# 2) 프레임 자르기 + 배경 제거 (가장자리에서 흰색/회색 영역 채우기)
xs=[(6,250),(262,506),(496,764),(774,1018)];y0,y1=26,268
frames=[]
for (a,b) in xs:
    c=out[y0:y1,a:b].copy()
    h,w=c.shape[:2]
    mx=c.max(2).astype(int);mn=c.min(2).astype(int)
    cand=((mx-mn)<16)&(mn>150)
    lab=cv2.connectedComponents(cand.astype(np.uint8),connectivity=4)[1]
    border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    bg=np.isin(lab,list(border))
    bg=cv2.dilate(bg.astype(np.uint8),np.ones((3,3),np.uint8))>0
    bg&=(mn>120)
    alpha=np.where(bg,0,255).astype(np.uint8)
    n,lab2,st,_=cv2.connectedComponentsWithStats((alpha>0).astype(np.uint8),connectivity=8)
    for i in range(1,n):
        if st[i,4]<40:alpha[lab2==i]=0
    rgba=np.dstack([cv2.cvtColor(c,cv2.COLOR_BGR2RGB),alpha])
    ys,xx=np.where(alpha>0);pad=3
    rgba=rgba[max(ys.min()-pad,0):ys.max()+pad+1,max(xx.min()-pad,0):xx.max()+pad+1]
    frames.append(Image.fromarray(rgba,'RGBA'))
import os;os.makedirs('frames',exist_ok=True)
for i,fr in enumerate(frames):fr.save(f'frames/f{i}.png');print(i,fr.size)
# 미리보기: 어두운 배경 위
W=sum(f.width for f in frames)+10*5;H=max(f.height for f in frames)+20
for name,col in (('dark',(40,40,48)),('light',(235,235,235))):
    sheet=Image.new('RGB',(W,H),col);x=10
    for fr in frames:
        sheet.paste(fr,(x,H-10-fr.height),fr);x+=fr.width+10
    sheet.save(f'sheet_{name}.png')

# 3) 같은 캔버스에 발 기준 하단 중앙 정렬 후 GIF/APNG 저장
CW,CH=max(f.width for f in frames),max(f.height for f in frames)
canv=[]
for fr in frames:
    c=Image.new('RGBA',(CW,CH),(0,0,0,0));c.paste(fr,((CW-fr.width)//2,CH-fr.height),fr);canv.append(c)
def to_p(img):
    a=np.array(img);al=a[:,:,3]
    q=Image.fromarray(a[:,:,:3]).quantize(255,dither=Image.NONE)
    pal=(q.getpalette()+[0]*768)[:768]
    arr=np.array(q);arr[al<128]=255
    p=Image.fromarray(arr,'P');p.putpalette(pal);p.info['transparency']=255
    return p
ps=[to_p(c) for c in canv]
ps[0].save('squirrel.gif',save_all=True,append_images=ps[1:],duration=180,loop=0,transparency=255,disposal=2,optimize=False)
canv[0].save('squirrel.apng',save_all=True,append_images=canv[1:],duration=180,loop=0,disposal=1)
print('canvas',CW,CH)
