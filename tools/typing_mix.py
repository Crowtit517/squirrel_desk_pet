"""21·22·23번 이미지의 12컷을 추출·정렬하고, 서로 이어지는 순서를 계산해 typing GIF를 만든다."""
import numpy as np, cv2
from PIL import Image
import states as S, gem

IM = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/images/%d.png"
MULT = 1.22
W, H = 420, 270

def extract_all():
    frames, names = [], []
    for n in (21, 22, 23):
        fr = gem.extract(IM % n, f'typing{n}', MULT)
        for i, f in enumerate(fr):
            frames.append(f); names.append(f'{n}-{i + 1}')
    print([f.size for f in frames])
    return frames, names

def mask(img):
    return (np.array(img.getchannel('A')) > 128).astype(np.uint8)

def align(frames):
    """왼쪽(꼬리·등) 영역의 마스크 겹침이 최대가 되는 이동량을 찾아 모든 컷을 기준 컷에 맞춘다."""
    ref = frames[0]
    def canvas(img, dx, dy):
        c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        c.paste(img, (dx, dy), img); return c
    base = canvas(ref, 20, H - 6 - ref.height)
    bm = np.array(base.getchannel('A')) > 128
    xs = np.where(bm.any(0))[0]; x0, x1 = xs.min(), xs.min() + int((xs.max() - xs.min()) * 0.5)
    out, shifts = [], []
    for k, f0 in enumerate(frames):
        best = None
        scales = (1.0,) if k < 8 else [1.0 + 0.01 * j for j in range(4, 20)]
        for sc in scales:
            f = f0 if sc == 1.0 else f0.resize((round(f0.width * sc), round(f0.height * sc)), Image.LANCZOS)
            for dx in range(8, 36, 1):
                for dy in range(H - 6 - f.height - 14, H - 6 - f.height + 15, 1):
                    c = canvas(f, dx, dy)
                    m = np.array(c.getchannel('A')) > 128
                    aa, bb = m[:, x0:x1], bm[:, x0:x1]
                    score = (aa & bb).sum() / max((aa | bb).sum(), 1)
                    if best is None or score > best[0]:
                        best = (score, dx, dy, sc, f)
        out.append(canvas(best[4], best[1], best[2])); shifts.append(best[:4])
    return out, shifts

if __name__ == '__main__':
    S.CW = W
    frames, names = extract_all()
    al, sh = align(frames)
    for n, s in zip(names, sh):
        print(n, 'iou %.2f' % s[0], 'dx', s[1], 'dy', s[2], 'scale %.2f' % s[3])
    sheet = Image.new('RGB', (4 * W // 2, 3 * H // 2), (58, 58, 68))
    for k, c in enumerate(al):
        im = c.resize((W // 2, H // 2), Image.LANCZOS)
        sheet.paste(im, ((k % 4) * W // 2, (k // 4) * H // 2), im)
    sheet.save('C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/scratchpad/typing_aligned.png')
    np.save('C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/scratchpad/typing_al.npy', np.stack([np.array(c) for c in al]))
