"""Gemini 초록 배경 4컷 이미지 → 투명 프레임 4장 + 시험 GIF.
usage: python gem.py <이미지> <이름>"""
import os, sys, math
import numpy as np, cv2
from PIL import Image
import states as S

G = os.path.join(S.ROOT, 'gemini')
os.makedirs(G, exist_ok=True)
BASE = 0.489 * 2000        # 2000px 폭 이미지에서 캐릭터 높이 409px → 200px 로 줄인 기준

def key_out(im):
    a = np.array(im.convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gr = (g > 200) & (r < 90) & (b < 90)
    rows = np.where(gr.mean(1) > 0.5)[0]
    H = rows.max() + 1
    a = a[:H]; r, g, b = a[..., 0], a[..., 1], a[..., 2]
    key = g - np.maximum(r, b)
    alpha = np.clip(255 - (key - 30) * 255 / 90, 0, 255)
    alpha[key <= 30] = 255; alpha[key >= 120] = 0
    out = np.dstack([a, alpha]).astype(np.uint8)
    sp = np.maximum(out[..., 1].astype(int) - np.maximum(out[..., 0], out[..., 2]).astype(int), 0)
    out[..., 1] = np.where(out[..., 3] > 0, out[..., 1] - sp * 0.9, out[..., 1]).astype(np.uint8)
    return out

def split4(out):
    """연결 성분으로 4마리를 찾고, 작은 조각(움직임 선 등)은 가까운 쪽에 붙인다."""
    m = (out[..., 3] > 40).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    comps = [(i, st[i]) for i in range(1, n) if st[i, 4] > 60]
    big = sorted([c for c in comps if c[1][4] > 4000], key=lambda c: c[1][0] + c[1][2] / 2)
    if len(big) != 4:
        print('  경고: 큰 성분', len(big), '개 → 균등 분할로 대체')
        W = out.shape[1] // 4
        return [out[:, i * W:(i + 1) * W] for i in range(4)], None
    groups = [[c[0]] for c in big]
    for i, s in comps:
        if i in [c[0] for c in big]: continue
        cx = s[0] + s[2] / 2
        d = [abs(cx - (b[1][0] + b[1][2] / 2)) for b in big]
        groups[int(np.argmin(d))].append(i)
    frames = []
    for gp in groups:
        sel = np.isin(lab, gp)
        f = out.copy(); f[~sel, 3] = 0
        frames.append(f)
    return frames, None

def extract(path, name, mult=1.0):
    im = Image.open(path)
    out = key_out(im)
    frames, _ = split4(out)
    res = []
    scale = BASE / im.width * mult
    for i, f in enumerate(frames):
        img = Image.fromarray(f, 'RGBA')
        bb = img.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
        img = img.crop(bb)
        img.save(os.path.join(G, f'{name}_{i + 1}.png'))
        res.append(img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS))
    return res

def comx(img):
    a = np.array(img.getchannel('A')).astype(float)
    xs = np.arange(a.shape[1])
    return (a.sum(0) * xs).sum() / max(a.sum(), 1)

def canvas(img, cx=S.CW * 0.52):
    c = Image.new('RGBA', (S.CW, S.CH), (0, 0, 0, 0))
    x = round(cx - comx(img)); y = S.CH - S.PB - img.height
    c.paste(img, (x, y), img)
    return np.array(c), x, y

def run(path, name, seq, fx=None, mult=1.0):
    fr = extract(path, name, mult)
    out = []
    for k, (i, d) in enumerate(seq):
        arr, x, y = canvas(fr[i])
        if fx:
            arr = S.overlay(arr, lambda dr, SS, k=k, x=x, y=y, w=fr[i].width: fx(dr, SS, k, x, y, w))
        out.append((arr, d))
    n = S.save_gif(name, out)
    print(name, n, 'frames', [f.size for f in fr])
    return fr

def zzz(dr, SS, k, x, y, w):
    for j in range(2):
        ph = ((k / 6) + j * 0.5) % 1
        zx = x + w * 0.72 + ph * 26 + j * 10
        zy = y - 4 - ph * 36
        s = 8 + 7 * ph + j * 2
        al = int(255 * min(1, ph * 4, (1 - ph) * 2.5))
        col = (110, 130, 175, al)
        pts = [(zx, zy), (zx + s, zy), (zx, zy + s), (zx + s, zy + s)]
        dr.line([(px * SS, py * SS) for px, py in pts], fill=col, width=int(3 * SS), joint='curve')

if __name__ == '__main__':
    IM = os.path.join(os.path.dirname(S.ROOT), 'AppData', 'Local', 'Temp')
