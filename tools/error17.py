"""error: 17.png 4컷(놀람→걱정→손 올리기→유지). 입 변화 구간은 크로스페이드, 앞발 구간은 보간(결과 확인 후 사용)."""
import numpy as np
from PIL import Image
import states as S, gem, smooth as M

IMG = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/images/17.png"

def xfade(A, B, t):
    return np.array(Image.blend(Image.fromarray(A), Image.fromarray(B), t))

def build(use_flow=True):
    fr = gem.extract(IMG, 'error17', 1.27)
    print([f.size for f in fr])
    F = [gem.canvas(f)[0] for f in fr]
    fab, fba = M.flows(F[1], F[2])
    def mid(i, j, t):
        if use_flow and (i, j) in ((1, 2), (2, 1)):
            a, b = (F[1], F[2]); tt = t if (i, j) == (1, 2) else 1 - t
            return M.tween(a, b, fab, fba, tt)
        return xfade(F[i], F[j], t)
    e = M.ease
    out = [(F[0], 600)]
    out += [(mid(0, 1, e(k / 4)), 40) for k in (1, 2, 3)]
    out += [(F[1], 600)]
    out += [(mid(1, 2, e(k / 7)), 40) for k in range(1, 7)]
    out += [(F[2], 500)]
    out += [(mid(2, 3, e(k / 3)), 40) for k in (1, 2)]
    out += [(F[3], 700)]
    out += [(mid(3, 2, e(k / 3)), 40) for k in (1, 2)]
    out += [(F[2], 120)]
    out += [(mid(2, 1, e(k / 7)), 40) for k in range(1, 7)]
    out += [(F[1], 120)]
    out += [(mid(1, 0, e(k / 4)), 40) for k in (1, 2, 3)]
    return out

if __name__ == '__main__':
    out = build()
    print(S.save_gif('error', out), 'frames')
    M.save_apng('error', out)
    # 앞발 구간 중간 프레임 확대 확인
    from PIL import Image as I
    idx = [5, 7, 9, 11]   # 대략 1→2 / 1→2 구간 중간
    sheet = I.new('RGB', (4 * 260, 300), (240, 240, 240))
    for j, i in enumerate(idx):
        im = I.fromarray(out[i][0]); bg = I.new('RGB', im.size, (240, 240, 240)); bg.paste(im, (0, 0), im)
        sheet.paste(bg.crop((70, 20, 330, 270)).resize((260, 250)), (j * 260, 0))
    sheet.save('C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/scratchpad/e17mid.png')
