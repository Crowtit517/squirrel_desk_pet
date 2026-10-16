"""두 포즈 사이를 광학 흐름(optical flow)으로 보간해 부드러운 중간 프레임을 만들고, 투명도가 부드러운 APNG로 저장."""
import os, numpy as np, cv2
from PIL import Image
import states as S, gem

def premul(a):
    f = a.astype(np.float32); f[..., :3] *= f[..., 3:4] / 255; return f

def unpremul(f):
    a = f[..., 3:4]; o = f.copy()
    o[..., :3] = np.where(a > 0.5, f[..., :3] * 255 / np.maximum(a, 1e-3), 0)
    return np.clip(o, 0, 255).astype(np.uint8)

def flows(A, B):
    def g(x):
        a = x[..., 3:4] / 255.0
        rgb = x[..., :3] * a + 128 * (1 - a)
        return cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    d = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    d.setFinestScale(0)
    d.setVariationalRefinementIterations(8)
    fab, fba = d.calc(g(A), g(B), None), d.calc(g(B), g(A), None)
    k = (15, 15)
    return cv2.GaussianBlur(fab, k, 5), cv2.GaussianBlur(fba, k, 5)

def tween(A, B, fab, fba, t):
    h, w = A.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    PA, PB = premul(A), premul(B)
    wa = cv2.remap(PA, xx + t * fba[..., 0], yy + t * fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    wb = cv2.remap(PB, xx + (1 - t) * fab[..., 0], yy + (1 - t) * fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return unpremul((1 - t) * wa + t * wb)

def ease(t):
    return t * t * (3 - 2 * t)

def save_apng(name, frames):
    imgs = [Image.fromarray(f) for f, _ in frames]
    imgs[0].save(os.path.join(S.OUT, name + '.apng'), save_all=True, append_images=imgs[1:],
                 duration=[d for _, d in frames], loop=0, disposal=1)

if __name__ == '__main__':
    IMG = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/images/13.png"
    fr = gem.extract(IMG, 'error_new', 1.27)
    A = gem.canvas(fr[0])[0]; B = gem.canvas(fr[1])[0]
    fab, fba = flows(A, B)
    N = 10
    out = [(A, 700)]
    out += [(tween(A, B, fab, fba, ease(i / (N + 1))), 40) for i in range(1, N + 1)]
    out += [(B, 900)]
    out += [(tween(A, B, fab, fba, ease(1 - i / (N + 1))), 40) for i in range(1, N + 1)]
    save_apng('error_smooth', out)
    # 중간 프레임 확인 시트
    pick = [0, 2, 4, 6, 8, 10, 11]
    sheet = Image.new('RGB', (len(pick) * S.CW // 2, S.CH // 2), (58, 58, 68))
    for j, i in enumerate(pick):
        im = Image.fromarray(out[i][0]).resize((S.CW // 2, S.CH // 2), Image.LANCZOS)
        sheet.paste(im, (j * S.CW // 2, 0), im)
    sheet.save('C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/scratchpad/smooth_keys.png')
    print(len(out), 'frames')
