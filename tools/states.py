"""기존 4프레임(frames/f0~f3.png)만으로 '가능' 판정 7개 상태 시험 GIF를 만든다.
파츠(꼬리·머리·귀)는 부드러운 마스크 회전 워프, 눈은 덧칠, 이펙트·소품은 코드로 그려 얹는다."""
import os, math
import numpy as np, cv2
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'test_states')
os.makedirs(OUT, exist_ok=True)

CW, CH = 352, 270
PR, PB = 52, 8          # 오른쪽·아래 여백 (위·왼쪽은 남는 공간)
DARK = (74, 42, 26, 255)
SS = 3                  # 이펙트 슈퍼샘플

def load(i):
    return Image.open(os.path.join(ROOT, 'frames', f'f{i}.png')).convert('RGBA')

def place(im):
    c = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    ox, oy = CW - PR - im.width, CH - PB - im.height
    c.paste(im, (ox, oy), im)
    return np.array(c), ox, oy

def premul(a):
    f = a.astype(np.float32)
    f[..., :3] *= f[..., 3:4] / 255
    return f

def unpremul(f):
    a = f[..., 3:4]
    out = f.copy()
    out[..., :3] = np.where(a > 0, f[..., :3] * 255 / np.maximum(a, 1e-3), 0)
    return np.clip(out, 0, 255).astype(np.uint8)

def rot_warp(arr, poly, pivot, ang, blur=2.5):
    """poly 안쪽을 pivot 기준으로 ang도(시계 +) 돌린다. 가장자리는 부드럽게 줄어든다."""
    if abs(ang) < 1e-3:
        return arr
    h, w = arr.shape[:2]
    m = np.zeros((h, w), np.float32)
    cv2.fillPoly(m, [np.array(poly, np.int32)], 1.0)
    m = cv2.GaussianBlur(m, (0, 0), blur)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    th = np.deg2rad(ang) * m
    c, s = np.cos(-th), np.sin(-th)
    px, py = pivot
    dx, dy = xx - px, yy - py
    sx = (px + c * dx - s * dy).astype(np.float32)
    sy = (py + s * dx + c * dy).astype(np.float32)
    out = cv2.remap(premul(arr), sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return unpremul(out)

def affine(arr, rot=0.0, sx=1.0, sy=1.0, dx=0.0, dy=0.0, center=(0, 0)):
    cx, cy = center
    a = math.radians(rot)
    R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    S = np.diag([sx, sy, 1.0])
    T1 = np.array([[1, 0, -cx], [0, 1, -cy], [0, 0, 1]])
    T2 = np.array([[1, 0, cx + dx], [0, 1, cy + dy], [0, 0, 1]])
    M = (T2 @ R @ S @ T1)[:2]
    out = cv2.warpAffine(premul(arr), M.astype(np.float32), (CW, CH), flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return unpremul(out)

def ring_color(arr, c, r):
    h, w = arr.shape[:2]
    cx, cy = c
    ys, xs = np.mgrid[0:h, 0:w]
    d = np.hypot(xs - cx, ys - cy)
    sel = (d > r + 2) & (d < r + 6) & (arr[..., 3] > 200)
    px = arr[sel][:, :3]
    px = px[px.sum(1) > 200]            # 윤곽선 같은 어두운 점 제외
    return np.median(px, axis=0).astype(np.uint8) if len(px) else np.array([200, 150, 100], np.uint8)

def edit_eye(arr, c, r, mode='open', shift=(0, 0)):
    """눈동자를 덧칠로 바꾼다. mode: open / shift / closed / happy"""
    if mode == 'open' and shift == (0, 0):
        return arr
    arr = arr.copy()
    h, w = arr.shape[:2]
    cx, cy = c
    col = ring_color(arr, c, r)
    ys, xs = np.mgrid[0:h, 0:w]
    disc = np.hypot(xs - cx, ys - cy) <= r + 2
    patch = arr.copy()
    arr[disc, :3] = col
    arr[disc, 3] = 255
    if mode in ('open', 'shift'):
        sx, sy = shift
        disc2 = np.hypot(xs - cx, ys - cy) <= r + 1
        yy, xx = np.where(disc2)
        ny, nx = yy + sy, xx + sx
        ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        arr[ny[ok], nx[ok]] = patch[yy[ok], xx[ok]]
        return arr
    ov = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    box = [(cx - r) * SS, (cy - r * 0.6) * SS, (cx + r) * SS, (cy + r * 1.1) * SS]
    if mode == 'closed':
        d.arc(box, 20, 160, fill=DARK, width=int(3.2 * SS))
    else:  # happy: ^ 모양
        box = [(cx - r) * SS, (cy - r * 0.2) * SS, (cx + r) * SS, (cy + r * 1.5) * SS]
        d.arc(box, 200, 340, fill=DARK, width=int(3.2 * SS))
    ov = ov.resize((w, h), Image.LANCZOS)
    return np.array(Image.alpha_composite(Image.fromarray(arr), ov))

def overlay(arr, fn):
    """fn(draw, S)로 슈퍼샘플 레이어에 그린 뒤 얹는다."""
    h, w = arr.shape[:2]
    ov = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    fn(ImageDraw.Draw(ov), SS)
    ov = ov.resize((w, h), Image.LANCZOS)
    return np.array(Image.alpha_composite(Image.fromarray(arr), ov))

def acorn(d, S, cx, cy, sc=1.0, tilt=0):
    bw, bh = 22 * sc, 20 * sc
    cap = (110, 66, 30, 255)
    body = (198, 140, 66, 255)
    d.ellipse([(cx - bw) * S, (cy - bh * 0.7) * S, (cx + bw) * S, (cy + bh * 1.3) * S], fill=body, outline=DARK, width=int(2.2 * S))
    d.pieslice([(cx - bw - 1) * S, (cy - bh * 1.35) * S, (cx + bw + 1) * S, (cy + bh * 0.55) * S], 180, 360, fill=cap, outline=DARK, width=int(2.2 * S))
    d.rectangle([(cx - bw * 0.1) * S, (cy - bh * 1.6) * S, (cx + bw * 0.1) * S, (cy - bh * 1.2) * S], fill=cap, outline=DARK, width=int(1.6 * S))
    d.ellipse([(cx - bw * 0.55) * S, (cy + bh * 0.1) * S, (cx - bw * 0.2) * S, (cy + bh * 0.55) * S], fill=(228, 176, 100, 255))

def star(d, S, cx, cy, r, col=(247, 201, 72, 255)):
    pts = []
    for i in range(8):
        a = i * math.pi / 4 - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.38
        pts.append(((cx + rr * math.cos(a)) * S, (cy + rr * math.sin(a)) * S))
    d.polygon(pts, fill=col, outline=DARK)

# ───────────── 프레임별 좌표 (격자 확인값, 소스 좌표) ─────────────
F1 = dict(
    tail=[(-90, -70), (112, -70), (112, 62), (98, 95), (86, 125), (82, 150), (-90, 150)], tail_pivot=(82, 136),
    head=[(118, 15), (214, 15), (214, 112), (160, 118), (120, 100)], head_pivot=(140, 106),
    earL=[(124, 14), (156, 14), (156, 52), (124, 52)], earL_pivot=(140, 54),
    earR=[(158, 12), (194, 12), (194, 42), (158, 42)], earR_pivot=(176, 44),
    eye=(172, 71), eye_r=8, feet=(130, 188))
F3 = dict(
    tail=[(-90, -70), (120, -70), (120, 94), (100, 99), (82, 108), (70, 120), (62, 130), (58, 152), (-90, 152)], tail_pivot=(66, 138),
    head=[(126, 66), (222, 66), (222, 172), (150, 178), (128, 150)], head_pivot=(142, 150),
    eye=(178, 122), eye_r=9, feet=(140, 200))

def shift_pts(pts, ox, oy):
    return [(x + ox, y + oy) for x, y in pts]

def prep(i, spec):
    im = load(i)
    base, ox, oy = place(im)
    s = {}
    for k, v in spec.items():
        if k in ('eye_r',):
            s[k] = v
        elif isinstance(v, list):
            s[k] = shift_pts(v, ox, oy)
        else:
            s[k] = (v[0] + ox, v[1] + oy)
    return base, s

def tail_head(base, s, tail=0.0, head=0.0, earL=0.0, earR=0.0):
    a = base
    a = rot_warp(a, s['tail'], s['tail_pivot'], tail, 2.5)
    a = rot_warp(a, s['head'], s['head_pivot'], head, 4)
    if 'earL' in s:
        a = rot_warp(a, s['earL'], s['earL_pivot'], earL, 1.5)
        a = rot_warp(a, s['earR'], s['earR_pivot'], earR, 1.5)
    return a

# ───────────── 상태 정의 ─────────────
def idle():
    base, s = prep(1, F1)
    N, out = 16, []
    for k in range(N):
        t = k / N
        a = base
        if k in (11, 12):
            a = edit_eye(a, s['eye'], s['eye_r'], 'closed')
        a = tail_head(a, s, tail=4.5 * math.sin(2 * math.pi * t))
        a = affine(a, sy=1 + 0.012 * math.sin(2 * math.pi * t), center=s['feet'])
        out.append((a, 120))
    return out

def thinking():
    base, s = prep(1, F1)
    N, out = 16, []
    cnt = [0, 0, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 2, 1, 0, 0]
    tilt = [0, -1, -2, -3, -4, -5, -5, -5, -5, -5, -5, -4, -3, -2, 0, 0]
    for k in range(N):
        a = tail_head(base, s, tail=3 * math.sin(2 * math.pi * k / N), head=tilt[k])
        n = cnt[k]
        bx, by = s['head'][1][0] - 14, 30
        def fx(d, S, n=n, bx=bx, by=by):
            if n:
                d.ellipse([(bx - 40) * S, (by - 16) * S, (bx + 22) * S, (by + 16) * S], fill=(255, 248, 232, 255), outline=DARK, width=int(2.2 * S))
                d.ellipse([(bx - 52) * S, (by + 14) * S, (bx - 44) * S, (by + 22) * S], fill=(255, 248, 232, 255), outline=DARK, width=int(1.8 * S))
                for i in range(n):
                    cx = bx - 26 + i * 15
                    d.ellipse([(cx - 4.5) * S, (by - 4.5) * S, (cx + 4.5) * S, (by + 4.5) * S], fill=DARK)
        a = overlay(a, fx)
        out.append((a, 150))
    return out

def notification():
    """몸은 그대로, 머리 위에 느낌표만 톡 튀어나온다."""
    base, s = prep(1, F1)
    ox = s['feet'][0] - 130
    oy = s['feet'][1] - 188
    bx, by = 178 + ox, -4 + oy
    sc = [0.0, 0.6, 1.25, 1.1, 1.0, 1.0, 1.0, 1.0, 1.08, 1.0, 1.0, 1.0]
    jy = [0, 0, -3, -2, 0, 0, 0, 0, -2, 0, 0, 0]
    out = []
    for k, (c, j) in enumerate(zip(sc, jy)):
        def fx(d, S, c=c, j=j):
            if c <= 0:
                return
            r = 15 * c
            cy = by + j
            d.ellipse([(bx - r) * S, (cy - r) * S, (bx + r) * S, (cy + r) * S], fill=(229, 72, 58, 255), outline=DARK, width=int(2.4 * S))
            d.rounded_rectangle([(bx - 2.8 * c) * S, (cy - r * 0.62) * S, (bx + 2.8 * c) * S, (cy + r * 0.12) * S], 2 * S, fill=(255, 255, 255, 255))
            d.ellipse([(bx - 3.2 * c) * S, (cy + r * 0.34) * S, (bx + 3.2 * c) * S, (cy + r * 0.34 + 6.4 * c) * S], fill=(255, 255, 255, 255))
        out.append((overlay(base, fx), 100 if k < 8 else 180))
    return out

def happy():
    base, s = prep(1, F1)
    P = [(.95, 0), (.90, 0), (1.06, -14), (1.08, -30), (1.04, -40), (1.0, -42), (1.0, -34),
         (1.03, -20), (1.0, -7), (.90, 0), (.95, 0), (1.02, -3), (1.0, 0), (1.0, 0)]
    D = [100, 100, 70, 70, 70, 80, 80, 80, 80, 90, 100, 100, 120, 120]
    out = []
    for k, (sy, dy) in enumerate(P):
        a = base
        if 3 <= k <= 9:
            a = edit_eye(a, s['eye'], s['eye_r'], 'happy')
        a = tail_head(a, s, tail=10 * (-dy / 42) - 2 * (sy - 1) * 20, head=-3 if dy < -10 else 0)
        a = affine(a, sy=sy, sx=1 + (1 - sy) * 0.5, dy=dy, center=s['feet'])
        def fx(d, S, k=k, dy=dy):
            if 3 <= k <= 9:
                hx = s['head'][1][0]
                star(d, S, hx - 120 + 6, 56 + dy * 0.6, 9)
                star(d, S, hx - 22, 24 + dy * 0.6 + 6, 7)
                star(d, S, hx + 18, 70 + dy * 0.6, 8)
                star(d, S, hx - 70, 36 + dy * 0.6, 5)
        a = overlay(a, fx)
        out.append((a, D[k]))
    return out

def carrying():
    base, s = prep(1, F1)
    ox = s['feet'][0] - 130
    oy = s['feet'][1] - 188
    ax, ay = 196 + ox, 142 + oy
    def hold(d, S):
        w, h = 19, 17
        body = (190, 128, 62, 255)
        cap = (96, 58, 28, 255)
        d.ellipse([(ax - w) * S, (ay - h * 0.55) * S, (ax + w) * S, (ay + h * 1.25) * S], fill=body, outline=DARK, width=int(3 * S))
        d.pieslice([(ax - w - 1) * S, (ay - h * 1.25) * S, (ax + w + 1) * S, (ay + h * 0.45) * S], 180, 360, fill=cap, outline=DARK, width=int(3 * S))
        d.rectangle([(ax - 2) * S, (ay - h * 1.55) * S, (ax + 2) * S, (ay - h * 1.1) * S], fill=cap, outline=DARK, width=int(2 * S))
        d.ellipse([(ax - w * 0.6) * S, (ay + h * 0.1) * S, (ax - w * 0.25) * S, (ay + h * 0.55) * S], fill=(224, 170, 96, 255))
    with_acorn = overlay(base, hold)
    # 원래 앞발을 도토리 위에 다시 얹어 '잡고 있는' 느낌을 만든다
    paw = np.zeros(base.shape[:2], bool)
    poly = np.array([(166 + ox, 116 + oy), (190 + ox, 116 + oy), (192 + ox, 150 + oy), (166 + ox, 150 + oy)], np.int32)
    m = np.zeros(base.shape[:2], np.uint8); cv2.fillPoly(m, [poly], 255)
    sel = (m > 0) & (base[..., 3] > 0)
    with_acorn = with_acorn.copy(); with_acorn[sel] = base[sel]
    N, out = 8, []
    for k in range(N):
        t = k / N
        a = tail_head(with_acorn, s, tail=4 * math.sin(2 * math.pi * t))
        a = affine(a, rot=2.2 * math.sin(2 * math.pi * t), dy=-2.5 * abs(math.sin(2 * math.pi * t)), center=s['feet'])
        out.append((a, 110))
    return out

def sweeping():
    base, s = prep(3, F3)
    N, out = 16, []
    for k in range(N):
        t = k / N
        ang = -4 + 4 * math.sin(2 * math.pi * t * 2)
        a = tail_head(base, {k_: v for k_, v in s.items() if not k_.startswith('ear')}, tail=ang, head=0)
        gy = s['feet'][1] - 2
        gx = s['tail_pivot'][0]
        near_left = max(0.0, -math.sin(2 * math.pi * t))
        def fx(d, S, near_left=near_left, t=t):
            if near_left > 0.2:
                for j in range(4):
                    r = (3 + 3 * near_left) * (1 - j * 0.12)
                    px_ = gx - 40 - j * 13 - 6 * near_left
                    py_ = gy - 4 - j * 5 * near_left - 3 * math.sin(t * 20 + j)
                    d.ellipse([(px_ - r) * S, (py_ - r) * S, (px_ + r) * S, (py_ + r) * S], fill=(224, 208, 178, 235), outline=(150, 118, 84, 255), width=int(1.4 * S))
        a = overlay(a, fx)
        out.append((a, 90))
    return out

STATES = [('idle', idle), ('thinking', thinking), ('notification', notification), ('happy', happy),
          ('carrying', carrying), ('sweeping', sweeping)]

def save_gif(name, frames):
    imgs = [Image.fromarray(f) for f, _ in frames]
    durs = [d for _, d in frames]
    # 공유 팔레트(깜빡임 방지)
    mont = Image.new('RGB', (CW * min(len(imgs), 6), CH))
    for i, im in enumerate([imgs[j] for j in sorted(set(int(round(q * (len(imgs) - 1) / 5)) for q in range(6)))]):
        bg = Image.new('RGB', im.size, (200, 150, 100)); bg.paste(im, (0, 0), im); mont.paste(bg, (i * CW, 0))
    pal = mont.quantize(255, dither=Image.NONE)
    ps = []
    for im in imgs:
        al = np.array(im)[..., 3]
        rgb = Image.new('RGB', im.size, (200, 150, 100)); rgb.paste(im, (0, 0), im)
        q = rgb.quantize(palette=pal, dither=Image.NONE)
        arr = np.array(q); arr[al < 128] = 255
        p = Image.fromarray(arr, 'P'); p.putpalette(pal.getpalette()[:765] + [0, 0, 0]); p.info['transparency'] = 255
        ps.append(p)
    ps[0].save(os.path.join(OUT, name + '.gif'), save_all=True, append_images=ps[1:], duration=durs,
               loop=0, transparency=255, disposal=2, optimize=False)
    # 키프레임 시트
    n = len(imgs); pick = sorted(set(int(round(i * (n - 1) / 5)) for i in range(6)))
    sheet = Image.new('RGB', (len(pick) * (CW // 2), CH // 2), (58, 58, 68))
    for j, i in enumerate(pick):
        sm = imgs[i].resize((CW // 2, CH // 2), Image.LANCZOS); sheet.paste(sm, (j * (CW // 2), 0), sm)
    sheet.save(os.path.join(OUT, name + '_keys.png'))
    return n

if __name__ == '__main__':
    import sys
    only = sys.argv[1:] or [n for n, _ in STATES]
    for name, fn in STATES:
        if name in only:
            print(name, save_gif(name, fn()), 'frames')
