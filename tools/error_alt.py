"""error 대안 2종: 당황(식은땀+떨림) / 어지러움(별이 머리 주위를 돈다). pose1_4 걱정 표정 컷 사용."""
import math, numpy as np
import states as S
import pose1 as P

fr, LEFT, top = P.fr, P.LEFT, P.top
W4 = fr[3].width

def drop(dr, SS, x, y, s=1.0, a=255):
    pts = [(x, y - 9 * s), (x + 5 * s, y + 1 * s), (x, y + 6 * s), (x - 5 * s, y + 1 * s)]
    dr.polygon([(px * SS, py * SS) for px, py in pts], fill=(120, 190, 235, a), outline=(60, 110, 160, a))
    dr.ellipse([(x - 5.4 * s) * SS, (y - 2 * s) * SS, (x + 5.4 * s) * SS, (y + 6.4 * s) * SS], fill=(120, 190, 235, a), outline=(60, 110, 160, a), width=int(1.6 * SS))

def flustered():
    out = []
    N = 12
    for k in range(N):
        dx = 2 if k % 2 == 0 else -2
        c = np.array(P.canvas(3))
        c = S.affine(c, dx=dx, center=(0, 0))
        hx, hy = LEFT + W4 * 0.80, top + 34
        ph = (k % 6) / 6
        def fx(dr, SS, ph=ph, hx=hx, hy=hy):
            drop(dr, SS, hx + 14, hy + ph * 22, 1.0, int(255 * (1 - ph * 0.7)))
            drop(dr, SS, hx - 26, hy - 6 + ((ph + 0.5) % 1) * 18, 0.8, 220)
            for j, (ox_, oy_) in enumerate([(-30, -40), (-38, -26), (-24, -22)]):
                pass
        c = S.overlay(c, fx)
        out.append((c, 90))
    return out

def dizzy():
    out = []
    N = 16
    for k in range(N):
        t = k / N
        c = np.array(P.canvas(3))
        c = S.affine(c, rot=2.0 * math.sin(2 * math.pi * t), center=(LEFT + W4 * 0.5, S.CH - S.PB))
        cx, cy = LEFT + W4 * 0.78, top + 4
        def fx(dr, SS, t=t, cx=cx, cy=cy):
            for j in range(3):
                a = 2 * math.pi * (t + j / 3)
                x = cx + 36 * math.cos(a); y = cy + 9 * math.sin(a)
                S.star(dr, SS, x, y, 8 if math.sin(a) > 0 else 6)
        c = S.overlay(c, fx)
        out.append((c, 80))
    return out

if __name__ == '__main__':
    print('error_flustered', S.save_gif('error_flustered', flustered()))
    print('error_dizzy', S.save_gif('error_dizzy', dizzy()))
