"""error 최종 후보: 17번 4컷(놀람→걱정→손 올리기) + 손 올리는 구간에 맞춰 나타나는 작은 비구름.
전 프레임 40ms(25fps)로 통일해 비가 끊기지 않게 한다."""
import math
import numpy as np
from PIL import Image
import states as S, gem, smooth as M, error17 as E17, error_soft as ES

def build():
    fr = gem.extract(E17.IMG, 'error17', 1.27)
    F = [gem.canvas(f)[0] for f in fr]
    _, x0, y0 = gem.canvas(fr[0])
    w = fr[0].width
    fab, fba = M.flows(F[1], F[2])
    e = M.ease
    def xf(i, j, t):
        return E17.xfade(F[i], F[j], t)
    def fl(t):
        return M.tween(F[1], F[2], fab, fba, t)
    seq = []          # (이미지, 구름 알파 0~1)
    def hold(i, n, c): seq.extend([(F[i], c)] * n)
    def tr(fn, n, c0, c1):
        for k in range(1, n + 1):
            t = k / (n + 1); seq.append((fn(e(t)), c0 + (c1 - c0) * e(t)))
    hold(0, 15, 0)
    tr(lambda t: xf(0, 1, t), 4, 0, 0)
    hold(1, 13, 0)
    tr(fl, 5, 0, 0.7)
    hold(2, 8, 1)
    tr(lambda t: xf(2, 3, t), 2, 1, 1)
    hold(3, 22, 1)
    tr(lambda t: xf(3, 2, t), 2, 1, 1)
    hold(2, 3, 1)
    tr(lambda t: fl(1 - t), 5, 1, 0.3)
    tr(lambda t: xf(1, 0, t), 4, 0.3, 0)
    N = len(seq)
    out = []
    for k, (im, c) in enumerate(seq):
        cx = x0 + w * 0.70
        cy = y0 - 20 + 1.6 * math.sin(2 * math.pi * k / 28)
        if c > 0.02:
            def fx(dr, SS, cx=cx, cy=cy, k=k, c=c):
                ES.cloud(dr, SS, cx, cy, k, c)
            im = S.overlay(im, fx)
        out.append((im, 40))
    return out

if __name__ == '__main__':
    out = build()
    print(S.save_gif('error_release', out), 'frames')
    M.save_apng('error_release', out)
    pick = [0, 18, 26, 36, 48, 62, 72]
    sheet = Image.new('RGB', (len(pick) * S.CW // 2, S.CH // 2), (58, 58, 68))
    for j, i in enumerate(pick):
        i = min(i, len(out) - 1)
        im = Image.fromarray(out[i][0]).resize((S.CW // 2, S.CH // 2), Image.LANCZOS)
        sheet.paste(im, (j * S.CW // 2, 0), im)
    sheet.save(S.os.path.join(S.OUT, 'error_release_keys.png'))
