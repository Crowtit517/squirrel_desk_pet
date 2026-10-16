"""정렬된 12컷에서 타자와 어울리는 컷만 골라, 서로 이어지는 순서(최단 순환)로 부드럽게 연결해 GIF 저장."""
import itertools, numpy as np
from PIL import Image
import states as S
import typing_mix as TM

NP = 'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/scratchpad/typing_al.npy'
NAMES = ['21-1', '21-2', '21-3', '21-4', '22-1', '22-2', '22-3', '22-4', '23-1', '23-2', '23-3', '23-4']
DROP = {'23-1', '23-3'}                       # 팔을 크게 흔드는 컷은 타자가 아니라서 제외
OUTW = 352

def premul(a):
    f = a.astype(np.float32); f[..., :3] *= f[..., 3:4] / 255; return f

def dist(a, b):
    return float(np.abs(premul(a) - premul(b)).mean())

def tour(D):
    n = len(D)
    best = list(range(n)); bl = sum(D[best[i]][best[(i + 1) % n]] for i in range(n))
    rng = np.random.default_rng(0)
    for _ in range(4000):
        p = list(rng.permutation(n))
        improved = True
        while improved:
            improved = False
            for i in range(n - 1):
                for j in range(i + 2, n):
                    a, b, c, d = p[i], p[i + 1], p[j], p[(j + 1) % n]
                    if D[a][c] + D[b][d] < D[a][b] + D[c][d] - 1e-9:
                        p[i + 1:j + 1] = reversed(p[i + 1:j + 1]); improved = True
        l = sum(D[p[i]][p[(i + 1) % n]] for i in range(n))
        if l < bl: best, bl = p[:], l
    return best, bl

def xfade(a, b, t):
    return np.array(Image.blend(Image.fromarray(a), Image.fromarray(b), t))

def tone_match(A):
    """꼬리·등(왼쪽) 영역의 중앙 색을 기준 컷에 맞춰 컷마다 색 차이를 없앤다."""
    def med(f):
        reg = f[:, :170]; m = reg[..., 3] > 250
        return np.median(reg[m][:, :3], axis=0)
    ref = med(A[0]); out = []
    for f in A:
        g = ref / np.maximum(med(f), 1)
        h = f.copy().astype(np.float32)
        h[..., :3] = np.clip(h[..., :3] * g, 0, 255)
        out.append(h.astype(np.uint8))
        print('gain', np.round(g, 3))
    return np.stack(out)

def build():
    A = tone_match(np.load(NP))
    keep = [i for i, n in enumerate(NAMES) if n not in DROP]
    F = [A[i][:, :OUTW] for i in keep]
    D = [[dist(a, b) for b in F] for a in F]
    order, total = tour(D)
    # 21-1 에서 시작하도록 회전
    s = order.index(0); order = order[s:] + order[:s]
    print('순서:', [NAMES[keep[i]] for i in order], '총거리 %.2f' % total)
    out = []
    for k in range(len(order)):
        i, j = order[k], order[(k + 1) % len(order)]
        out.append((F[i], 100))
        d = D[i][j]
        if d < 4.5:
            out.append((xfade(F[i], F[j], 0.5), 40))
    return out

if __name__ == '__main__':
    out = build()
    S.CW = OUTW
    print(S.save_gif('typing', out), 'frames')
