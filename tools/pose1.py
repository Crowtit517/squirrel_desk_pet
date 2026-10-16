"""Gemini 포즈 1장(4컷, gemini/pose1_*.png)으로 notification / thinking 시험 GIF 생성"""
import os, math, numpy as np
from PIL import Image
import states as S

G = os.path.join(S.ROOT, 'gemini')
H = 200                                   # 스프라이트 높이 (기존 프레임과 비슷하게)
fr = []
for i in range(1, 5):
    im = Image.open(os.path.join(G, f'pose1_{i}.png')).convert('RGBA')
    k = H / im.height
    fr.append(im.resize((round(im.width * k), H), Image.LANCZOS))
LEFT = 64
def canvas(i):
    c = Image.new('RGBA', (S.CW, S.CH), (0, 0, 0, 0))
    c.paste(fr[i], (LEFT, S.CH - S.PB - H), fr[i])
    return np.array(c)
top = S.CH - S.PB - H

def notification():
    seq = [(2, 0.0, 120), (2, 0.6, 90), (0, 1.25, 90), (1, 1.1, 110), (0, 1.0, 110), (1, 1.0, 110), (0, 1.0, 110), (1, 1.0, 110), (2, 1.0, 160)]
    out = []
    for i, c, d in seq:
        bx, by = LEFT + fr[i].width * 0.80, top - 2
        def fx(dr, SS, c=c):
            if c <= 0: return
            r = 15 * c
            dr.ellipse([(bx - r) * SS, (by - r) * SS, (bx + r) * SS, (by + r) * SS], fill=(229, 72, 58, 255), outline=S.DARK, width=int(2.4 * SS))
            dr.rounded_rectangle([(bx - 2.8 * c) * SS, (by - r * .62) * SS, (bx + 2.8 * c) * SS, (by + r * .12) * SS], 2 * SS, fill=(255, 255, 255, 255))
            dr.ellipse([(bx - 3.2 * c) * SS, (by + r * .34) * SS, (bx + 3.2 * c) * SS, (by + r * .34 + 6.4 * c) * SS], fill=(255, 255, 255, 255))
        out.append((S.overlay(canvas(i), fx), d))
    return out

def thinking():
    seq = [(2, 0, 200), (2, 0, 120), (3, 1, 160), (3, 2, 160), (3, 3, 700), (3, 3, 300), (3, 2, 120), (2, 0, 300)]
    out = []
    for i, n, d in seq:
        bx, by = LEFT + fr[i].width * 0.70, top - 8
        def fx(dr, SS, n=n):
            if not n: return
            dr.ellipse([(bx - 40) * SS, (by - 16) * SS, (bx + 22) * SS, (by + 16) * SS], fill=(255, 248, 232, 255), outline=S.DARK, width=int(2.2 * SS))
            dr.ellipse([(bx - 52) * SS, (by + 14) * SS, (bx - 44) * SS, (by + 22) * SS], fill=(255, 248, 232, 255), outline=S.DARK, width=int(1.8 * SS))
            for k in range(n):
                cx = bx - 26 + k * 15
                dr.ellipse([(cx - 4.5) * SS, (by - 4.5) * SS, (cx + 4.5) * SS, (by + 4.5) * SS], fill=S.DARK)
        out.append((S.overlay(canvas(i), fx), d))
    return out

if __name__ == '__main__':
    print('notification_g', S.save_gif('notification_g', notification()))
    print('thinking_g', S.save_gif('thinking_g', thinking()))
