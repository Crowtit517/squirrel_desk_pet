"""error 최종 후보: 19번 이미지에서 꼬리 파닥(4컷) 제외, 지친 서 있기→주저앉기→엎드림→천천히 복귀. 효과 없음."""
import math
import numpy as np
from PIL import Image
import states as S, gem, smooth as M

IMG = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/images/19.png"

def canvas_at(img, x):
    c = Image.new('RGBA', (S.CW, S.CH), (0, 0, 0, 0))
    c.paste(img, (round(x), S.CH - S.PB - img.height), img)
    return np.array(c)

def build():
    fr = gem.extract(IMG, 'error19', 1.0)
    R = S.CW - S.PR
    x1 = R - fr[1].width            # 서 있는 컷: 코끝을 오른쪽 기준선에
    x0 = x1                         # 1·2컷은 같은 자리
    x2 = R - fr[2].width            # 엎드린 컷도 코끝 기준
    A = canvas_at(fr[0], x0); B = canvas_at(fr[1], x1); L = canvas_at(fr[2], x2)
    cxL = x2 + fr[2].width * 0.5
    e = M.ease
    def xf(a, b, t):
        return np.array(Image.blend(Image.fromarray(a), Image.fromarray(b), t))
    out = []
    def hold(im, n): out.extend([(im, 40)] * n)
    def tr(a, b, n):
        for k in range(1, n + 1):
            out.append((xf(a, b, e(k / (n + 1))), 40))
    hold(A, 15); tr(A, B, 5); hold(B, 15); tr(B, L, 6)
    for k in range(60):                                   # 엎드림: 아주 작은 숨쉬기 1회
        s = 1 + 0.008 * math.sin(2 * math.pi * k / 60)
        out.append((S.affine(L, sy=s, center=(cxL, S.CH - S.PB)), 40))
    tr(L, B, 8); tr(B, A, 5)
    return out

if __name__ == '__main__':
    out = build()
    print(S.save_gif('error_slump', out), 'frames')
