"""error: 그 저장소(Clawd) 스타일 — 엎드린 포즈 + X눈 + 빨간 ERROR 글자 + 납작한 그림자"""
import os, numpy as np
from PIL import Image, ImageFont
import states as S, gem

IMG = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/images/8.png"
FONT = next(p for p in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/malgunbd.ttf") if os.path.exists(p))

def place_right(img, right=S.CW - S.PR):
    c = Image.new('RGBA', (S.CW, S.CH), (0, 0, 0, 0))
    x = right - img.width; y = S.CH - S.PB - img.height
    c.paste(img, (x, y), img)
    return np.array(c), x, y

def label_and_shadow(dr, SS, x, y, w, h):
    # 납작한 그림자
    sy = y + h + 1
    dr.ellipse([(x + 4) * SS, (sy - 3) * SS, (x + w - 4) * SS, (sy + 4) * SS], fill=(0, 0, 0, 55))
    # 빨간 ERROR
    f = ImageFont.truetype(FONT, int(20 * SS))
    cx, cy = x + w * 0.58, y - 22
    bb = dr.textbbox((0, 0), "ERROR", font=f, stroke_width=int(3 * SS))
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    dr.text((cx * SS - tw / 2 - bb[0], cy * SS - th / 2 - bb[1]), "ERROR", font=f,
            fill=(229, 72, 58, 255), stroke_width=int(3 * SS), stroke_fill=S.DARK)

def build():
    fr = gem.extract(IMG, 'error_first', 1.0)
    out = []
    for i, d in ((2, 700), (3, 350)):
        arr, x, y = place_right(fr[i])
        w, h = fr[i].width, fr[i].height
        arr = S.overlay(arr, lambda dr, SS, x=x, y=y, w=w, h=h: label_and_shadow(dr, SS, x, y, w, h))
        out.append((arr, d))
    return out

if __name__ == '__main__':
    print(S.save_gif('error_clawd', build()))
