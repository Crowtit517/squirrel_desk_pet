"""error 시험본: 걱정 포즈 + 머리 위 빨간 ERROR 글자(깜빡임)"""
import math, os, numpy as np
from PIL import Image, ImageFont
import states as S, gem

IMG = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/images/13.png"
FONT = next(p for p in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/malgunbd.ttf") if os.path.exists(p))

def label(dr, SS, cx, cy, on):
    if not on:
        return
    f = ImageFont.truetype(FONT, int(17 * SS))
    txt = "ERROR"
    bb = dr.textbbox((0, 0), txt, font=f, stroke_width=int(3 * SS))
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    dr.text((cx * SS - w / 2 - bb[0], cy * SS - h / 2 - bb[1]), txt, font=f,
            fill=(229, 72, 58, 255), stroke_width=int(3 * SS), stroke_fill=S.DARK)

def build():
    fr = gem.extract(IMG, 'error_new', 1.27)
    a = Image.fromarray(gem.canvas(fr[1])[0]); b = Image.fromarray(gem.canvas(fr[0])[0])
    _, x0, y0 = gem.canvas(fr[1])
    ts = [0] * 9 + [.5] + [1] * 9 + [.5]
    out = []
    for k, t in enumerate(ts):
        im = np.array(Image.blend(a, b, t))
        w = fr[1].width
        on = (k % 10) < 7                    # 천천히 깜빡
        bob = 1.5 * math.sin(2 * math.pi * k / len(ts))
        im = S.overlay(im, lambda dr, SS, on=on, bob=bob: label(dr, SS, x0 + w * 0.62, y0 - 14 + bob, on))
        out.append((im, 100))
    return out

if __name__ == '__main__':
    print(S.save_gif('error_text', build()))
