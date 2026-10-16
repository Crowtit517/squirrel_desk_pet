"""error 부드러운 버전: 1↔2컷 크로스페이드 + 천천히 위아래 숨쉬기 + 머리 위 작은 먹구름과 비"""
import math, numpy as np
from PIL import Image
import states as S, gem

IMG = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/images/13.png"

def cloud(dr, SS, cx, cy, k, c=1.0):
    A = int(255 * c)
    fill = (206, 216, 230, A)
    line = (S.DARK[0], S.DARK[1], S.DARK[2], A)
    puffs = [(-21, 3, 11), (-7, -6, 14), (10, -4, 14), (23, 4, 11), (0, 6, 15)]
    for grow, col in ((2.2, line), (0, fill)):
        for dx, dy, r in puffs:
            rr = r + (grow if grow else -0.6)
            x, y = cx + dx, cy + dy
            dr.ellipse([(x - rr) * SS, (y - rr) * SS, (x + rr) * SS, (y + rr) * SS], fill=col)
    # 비: 구름 아래에서 천천히 떨어지며 사라진다
    for j, off in enumerate((-14, 0, 14)):
        ph = ((k / 14) + j / 3) % 1
        x = cx + off + 1
        y0 = cy + 21 + ph * 30
        al = int(255 * c * min(1, (1 - ph) * 2.2))
        dr.line([(x * SS, y0 * SS), ((x - 0.8) * SS, (y0 + 6) * SS)], fill=(105, 165, 225, al), width=int(2.6 * SS))

def build():
    fr = gem.extract(IMG, 'error_new', 1.27)
    a = Image.fromarray(gem.canvas(fr[0])[0]); b = Image.fromarray(gem.canvas(fr[1])[0])
    _, x0, y0 = gem.canvas(fr[0])
    ts = [0] * 8 + [.5] + [1] * 9 + [.5] + [0]*0
    out = []
    for k, t in enumerate(ts):
        t = t * t * (3 - 2 * t)                       # 부드러운 가감속
        im = np.array(Image.blend(a, b, t))
        dy = round(1.2 * math.sin(2 * math.pi * k / len(ts)))
        im = S.affine(im, dy=dy, center=(0, 0))
        w = fr[0].width
        cx, cy = x0 + w * 0.70, y0 - 18 + dy + 1.5 * math.sin(2 * math.pi * k / 14)
        im = S.overlay(im, lambda dr, SS, cx=cx, cy=cy, k=k: cloud(dr, SS, cx, cy, k))
        out.append((im, 100))
    return out

if __name__ == '__main__':
    print(S.save_gif('error_soft', build()))
