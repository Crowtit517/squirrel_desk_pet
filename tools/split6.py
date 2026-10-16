"""겹쳐 닿은 N컷 이미지를 칸 경계 근처에서 알파 질량이 가장 적은 세로선으로 잘라 분리한다."""
import numpy as np, cv2
from PIL import Image
import gem

def split_seams(out, n, search=22):
    m = (out[..., 3] > 40)
    prof = m.sum(0).astype(float)
    prof = np.convolve(prof, np.ones(5) / 5, mode='same')
    W = out.shape[1]
    cuts = [0]
    for i in range(1, n):
        c = int(i * W / n)
        lo, hi = max(c - search, 1), min(c + search, W - 1)
        cuts.append(lo + int(np.argmin(prof[lo:hi])))
    cuts.append(W)
    res = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        f = out[:, a:b].copy()
        mm = (f[..., 3] > 40).astype(np.uint8)
        k, lab, st, _ = cv2.connectedComponentsWithStats(mm, connectivity=8)
        big = 1 + int(np.argmax(st[1:, 4]))
        keep = np.zeros_like(mm, bool)
        for j in range(1, k):
            x, y, w, h, area = st[j]
            edge = (x == 0) or (x + w == f.shape[1])
            if j == big or (area > 60 and not edge and area < 4000):
                keep |= (lab == j)
        f[~keep, 3] = 0
        res.append(f)
    return res, cuts

def extract_n(path, name, n, mult=1.0):
    im = Image.open(path)
    out = gem.key_out(im)
    frames, cuts = split_seams(out, n)
    scale = gem.BASE / im.width * mult
    res = []
    for i, f in enumerate(frames):
        img = Image.fromarray(f, 'RGBA')
        bb = img.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
        img = img.crop(bb)
        img.save(f"{gem.G}/{name}_{i + 1}.png")
        res.append(img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS))
    print(name, 'cuts', cuts, [f.size for f in res])
    return res

if __name__ == '__main__':
    import sys
    IMG = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/images/14.png"
    fr = extract_n(IMG, 'error6', 6, 1.27)
    sheet = Image.new('RGB', (sum(f.width for f in fr) + 70, max(f.height for f in fr) + 20), (58, 58, 68))
    x = 10
    for f in fr:
        sheet.paste(f, (x, 10), f); x += f.width + 10
    sheet.save('C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/scratchpad/err6.png')
