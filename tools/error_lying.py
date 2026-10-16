"""error: 19번 이미지의 3·4컷(엎드린 두 컷)만 부드럽게 반복. 서 있는 컷 없음."""
import numpy as np
from PIL import Image
import states as S, gem, smooth as M, error_slump as ES

def build():
    fr = gem.extract(ES.IMG, 'error19', 1.0)
    R = S.CW - S.PR
    A = ES.canvas_at(fr[2], R - fr[2].width)       # 3컷: 꼬리 내림
    B = ES.canvas_at(fr[3], R - fr[3].width)       # 4컷: 꼬리 올림
    e = M.ease
    def xf(a, b, t): return np.array(Image.blend(Image.fromarray(a), Image.fromarray(b), t))
    out = []
    out += [(A, 40)] * 22
    out += [(xf(A, B, e(k / 6)), 40) for k in range(1, 6)]
    out += [(B, 40)] * 12
    out += [(xf(B, A, e(k / 6)), 40) for k in range(1, 6)]
    return out

if __name__ == '__main__':
    print(S.save_gif('error_lying', build()), 'frames')
