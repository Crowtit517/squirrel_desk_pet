"""모든 상태 GIF를 idle 기준으로 위치·크기·색을 맞춰 theme_squirrel/assets 에 저장한다.
- 서 있는 컷: 꼬리 영역 마스크를 기준 컷과 템플릿 매칭해 (크기, 이동량)을 구한다.
- 엎드린 컷(sleeping): 크기 1.0, 바닥·가운데만 맞춘다.
- 색: 꼬리 영역 중앙 색을 idle 과 같게 보정한다."""
import os, sys, numpy as np, cv2
from PIL import Image
import states as S

TEST = os.path.join(S.ROOT, 'test_states')
OUTD = os.path.join(S.ROOT, 'theme_squirrel', 'assets')
W, H = 352, 270

# (출력 이름, 원본 GIF, 추정에 쓸 프레임 번호(-1=마지막), 방식)
JOBS = [
    ('idle', 'idle.gif', 0, 'match'),
    ('thinking', 'thinking_g.gif', 0, 'match'),
    ('working', 'typing.gif', 0, 'match'),
    ('notification', 'notification_g.gif', 0, 'match'),
    ('attention', 'happy.gif', 0, 'match'),
    ('error', 'error_lying.gif', 0, 'fixed:0.92:14:19'),
    ('react-drag', '@run.gif', 0, 'match'),
    ('sleeping', 'sleeping.gif', 0, 'lying'),
    ('waking', 'waking.gif', -1, 'match'),
    ('building', 'building.gif', 0, 'match'),
    ('conducting', 'conducting.gif', 0, 'match'),
    ('carrying', 'carrying.gif', 0, 'match'),
]

def decode(path):
    g = Image.open(path); out = []
    for i in range(g.n_frames):
        g.seek(i); out.append((np.array(g.convert('RGBA')), g.info.get('duration', 100)))
    return out

def mask(a): return (a[..., 3] > 128)

def bbox(m):
    ys, xs = np.where(m); return xs.min(), xs.max(), ys.min(), ys.max()

def tail_region(m, frac=0.35):
    x0, x1, y0, y1 = bbox(m)
    return x0, y0, int((x1 - x0) * frac), y1 - y0 + 1, (x0, x1, y0, y1)

def tail_color(a, m):
    x0, x1, y0, y1 = bbox(m)
    reg = a[:, x0:x0 + int((x1 - x0) * 0.35)]; mm = reg[..., 3] > 250
    return np.median(reg[mm][:, :3], axis=0)

def estimate(ref_a, a):
    rm = mask(ref_a); tx0, ty0, tw, th, _ = tail_region(rm)
    T = rm[ty0:ty0 + th, tx0:tx0 + tw].astype(np.float32)
    best = None
    PAD = 60
    for sc in np.arange(0.86, 1.16, 0.01):
        m = cv2.resize(mask(a).astype(np.float32), None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
        P = np.zeros((m.shape[0] + 2 * PAD, m.shape[1] + 2 * PAD), np.float32)
        P[PAD:PAD + m.shape[0], PAD:PAD + m.shape[1]] = m
        if P.shape[0] < T.shape[0] or P.shape[1] < T.shape[1]: continue
        r = cv2.matchTemplate(P, T, cv2.TM_CCOEFF_NORMED)
        inter = cv2.matchTemplate(P, T, cv2.TM_CCORR)           # 겹친 픽셀 수
        r = np.where(inter >= 0.6 * T.sum(), r, -1)             # 겹침이 부족한 위치는 무효
        _, mx, _, loc = cv2.minMaxLoc(r)
        if best is None or mx > best[0]:
            best = (mx, sc, tx0 - (loc[0] - PAD), ty0 - (loc[1] - PAD))
    return best[1], best[2], best[3], best[0]

def eye_d(a):
    rgb = a[..., :3].astype(int); al = a[..., 3] > 200
    dark = (rgb.sum(2) < 200) & al
    n, lab, st, _ = cv2.connectedComponentsWithStats(dark.astype(np.uint8), connectivity=8)
    best = None
    for i in range(1, n):
        x, y, w, h, ar = st[i]
        if 40 < ar < 1500 and 0.7 < w / h < 1.4 and ar / (w * h) > 0.6:
            if best is None or ar > best[0]: best = (ar, (w + h) / 2)
    return best[1] if best else None

def apply(a, sc, dx, dy, gain):
    f = a.astype(np.float32); f[..., :3] *= f[..., 3:4] / 255
    M = np.array([[sc, 0, dx], [0, sc, dy]], np.float32)
    o = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    al = o[..., 3:4]; rgb = np.where(al > 0.5, o[..., :3] * 255 / np.maximum(al, 1e-3), 0)
    lum = rgb.mean(2, keepdims=True)
    w = np.clip((lum - 50) / 90.0, 0, 1)                       # 어두운 윤곽선은 색을 거의 건드리지 않음
    rgb = np.clip(rgb * (1 + (np.asarray(gain) - 1) * w), 0, 255)
    return np.dstack([rgb, np.clip(al, 0, 255)]).astype(np.uint8)

def main():
    os.makedirs(OUTD, exist_ok=True)
    ref = decode(os.path.join(TEST, 'idle.gif'))[0][0]
    rm = mask(ref); rx0, rx1, ry0, ry1 = bbox(rm); rcol = tail_color(ref, rm)
    global REF_EYE
    REF_EYE = eye_d(ref)
    print('기준 눈 지름 %.1fpx' % REF_EYE)
    print('기준 idle: 바닥 y=%d  중심 x=%d  꼬리색=%s' % (ry1, (rx0 + rx1) // 2, rcol.astype(int)))
    S.OUT = OUTD
    report = []
    for name, src, idx, mode in JOBS:
        fr = decode(os.path.join(S.ROOT, src[1:]) if src.startswith('@') else os.path.join(TEST, src))
        est = fr[idx][0]
        em = mask(est)
        if mode.startswith('fixed'):
            _, a_, b_, c_ = mode.split(':'); sc, dx, dy, score = float(a_), int(b_), int(c_), 1.0
        elif mode == 'match':
            sc, dx, dy, score = estimate(ref, est)
            if score < 0.6: print('  주의: %s 매칭 점수 낮음 %.2f' % (name, score))
        else:
            sc = 1.0; x0, x1, y0, y1 = bbox(em)
            dx = (rx0 + rx1) // 2 - (x0 + x1) // 2; dy = ry1 - y1; score = 0
        if mode == 'match' and name != 'idle':
            e = eye_d(est)
            if e:
                f = float(np.clip(REF_EYE / (e * sc), 0.82, 1.12))      # 눈 지름을 idle 과 같게
                sc2 = sc * f
                tmp0 = apply(est, sc2, 0, 0, 1.0); bx0 = bbox(mask(tmp0))[0]
                print('   %s: 눈 %.1fpx → 크기 %.2f→%.2f' % (name, e * sc, sc, sc2))
                sc, dx = sc2, rx0 - bx0                                    # 꼬리 왼쪽 끝은 idle 과 같게
        # 크기 변환 뒤 위치를 바닥 기준선 y 로 한 번 더 정확히 맞춘다(발이 뜨거나 가라앉지 않게)
        tmp = apply(est, sc, dx, dy, 1.0); tm = mask(tmp); _, _, _, ty1 = bbox(tm)
        dy += ry1 - ty1
        gain = rcol / np.maximum(tail_color(est, em), 1)
        out = [(apply(a, sc, dx, dy, gain), d) for a, d in fr]
        n = S.save_gif(name, out)
        k = os.path.join(OUTD, name + '_keys.png')
        if os.path.exists(k): os.remove(k)
        report.append((name, sc, dx, dy, score, gain))
        print('%-13s 크기 %.2f  이동(%+d,%+d)  매칭 %.2f  색보정 %s  프레임 %d' % (name, sc, dx, dy, score, np.round(gain, 2), n))

if __name__ == '__main__':
    main()
