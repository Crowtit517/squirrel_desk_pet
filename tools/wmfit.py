import cv2, numpy as np, itertools
im=cv2.imread('../images/4.png').astype(np.float32)
Y,X=np.mgrid[0:im.shape[0],0:im.shape[1]].astype(np.float32)
def mask(cx,cy,r,p,soft=0.10):
    s=(np.abs(X-cx)/r)**p+(np.abs(Y-cy)/r)**p
    return np.clip((1-s)/soft+0.5,0,1),s
def fix(m,a=0.30):
    m3=m[...,None]*a
    return np.clip((im-m3*255)/(1-m3),0,255)
def cost(cx,cy,r,p):
    m,s=mask(cx,cy,r,p)
    c=fix(m)
    g=cv2.cvtColor(c.astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
    gx=cv2.Sobel(g,cv2.CV_32F,1,0);gy=cv2.Sobel(g,cv2.CV_32F,0,1)
    mag=np.abs(gx)+np.abs(gy)
    band=(s>0.88)&(s<1.12)
    return mag[band].mean()
best=None
for cx in np.arange(901,908,1.0):
  for cy in np.arange(211,218,1.0):
    for r in np.arange(22,30,1.0):
      for p in (0.6,0.7,0.8,0.9,1.0):
        c=cost(cx,cy,r,p)
        if best is None or c<best[0]:best=(c,cx,cy,r,p)
print(best)
c,cx,cy,r,p=best
m,s=mask(cx,cy,r,p)
out=fix(m).astype(np.uint8)
cv2.imwrite('clean_full2.png',out)
crop=lambda x:cv2.resize(x[150:275,768:1024],None,fx=4,fy=4,interpolation=cv2.INTER_NEAREST)
cv2.imwrite('wmfit.png',crop(out))
# 가장자리 옅은 선만 좁게 미디안 처리
band=((s>0.90)&(s<1.14)).astype(np.float32)
band=cv2.GaussianBlur(band,(3,3),0)[...,None]
soft=cv2.medianBlur(out,5)
out2=(out*(1-band)+soft*band).astype(np.uint8)
cv2.imwrite('clean_full2.png',out2)
cv2.imwrite('wmfit2.png',crop(out2))
