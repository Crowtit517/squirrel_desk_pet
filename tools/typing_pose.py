"""typing(working): 20번 이미지 4컷 + 코드로 그린 노트북·받침대. 앞발이 키보드 위에서 번갈아 움직인다."""
import numpy as np
from PIL import Image
import states as S, gem

IMG = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/images/20.png"
OUT = S.DARK

def laptop(dr, SS, x, y, key_hit=None):
    """x,y = 키보드 윗면 왼쪽 끝. 옆모습 노트북 + 나무 받침대."""
    bw = 92
    # 받침대(나무)
    dr.rounded_rectangle([(x - 6) * SS, (y + 7) * SS, (x + bw + 6) * SS, (y + 17) * SS], 3 * SS, fill=(196, 150, 96, 255), outline=OUT, width=int(2.4 * SS))
    dr.rectangle([(x + bw - 8) * SS, (y + 17) * SS, (x + bw + 2) * SS, (S.CH - S.PB) * SS], fill=(176, 130, 80, 255), outline=OUT, width=int(2.4 * SS))
    dr.rectangle([(x + 24) * SS, (y + 17) * SS, (x + 34) * SS, (S.CH - S.PB) * SS], fill=(176, 130, 80, 255), outline=OUT, width=int(2.4 * SS))
    # 본체
    dr.rounded_rectangle([x * SS, (y - 1) * SS, (x + bw) * SS, (y + 8) * SS], 3 * SS, fill=(205, 212, 224, 255), outline=OUT, width=int(2.4 * SS))
    for i in range(7):                                  # 키
        kx = x + 8 + i * 11
        hit = (key_hit == i)
        dr.rounded_rectangle([kx * SS, (y + (1.6 if hit else 0.2)) * SS, (kx + 7) * SS, (y + 3.4) * SS], 1 * SS,
                             fill=(120, 190, 240, 255) if hit else (150, 160, 178, 255))
    # 모니터(키보드 오른쪽에 세워 둠, 코드 줄이 보이게)
    mx, my = x + bw - 22, y - 58
    dr.rectangle([(mx + 12) * SS, (y - 12) * SS, (mx + 20) * SS, (y + 1) * SS], fill=(150, 160, 178, 255), outline=OUT, width=int(2 * SS))
    dr.rounded_rectangle([mx * SS, my * SS, (mx + 44) * SS, (my + 46) * SS], 4 * SS, fill=(70, 78, 98, 255), outline=OUT, width=int(2.4 * SS))
    dr.rounded_rectangle([(mx + 4) * SS, (my + 4) * SS, (mx + 40) * SS, (my + 42) * SS], 2 * SS, fill=(34, 40, 58, 255))
    for j, (w, c) in enumerate(((22, (140, 230, 170)), (30, (230, 235, 245)), (16, (120, 190, 240)), (26, (230, 235, 245)), (20, (140, 230, 170)))):
        dr.line([((mx + 8) * SS, (my + 9 + j * 6.5) * SS), ((mx + 8 + w) * SS, (my + 9 + j * 6.5) * SS)], fill=c + (255,), width=int(2.2 * SS))

W = 420
LEFT = 10

def paw_y(img):
    """오른쪽 끝(앞발 끝) 근처에서 가장 아래쪽 쪽 y의 중앙값"""
    a = np.array(img.getchannel('A')) > 128
    cols = np.where(a.any(0))[0]
    xr = cols.max()
    ys = np.where(a[:, xr - 12:xr + 1].any(1))[0]
    return float(np.median(ys))

def build():
    fr = gem.extract(IMG, 'typing', 1.22)
    print([f.size for f in fr])
    # 몸은 꼬리 쪽 가장자리에 맞춰 모든 컷에서 같은 자리에 고정
    pos = [(LEFT, S.CH - S.PB - f.height) for f in fr]
    paws = [pos[i][1] + paw_y(fr[i]) for i in range(4)]
    tip = min(LEFT + f.width for f in fr)             # 가장 짧게 뻗은 앞발 끝에 맞춤
    kx = tip - 12                                       # 책상은 모든 프레임에서 같은 자리
    ky = float(np.mean(paws)) + 3                      # 앞발이 키보드 높이에 오도록
    print('paw y', [round(p) for p in paws], 'keyboard y', round(ky), 'desk x', kx)
    seq = [(0, 0), (1, 3), (2, 5), (3, 2), (2, 4), (1, 1)]
    out = []
    for i, hit in seq:
        arr = np.zeros((S.CH, W, 4), np.uint8)
        arr = S.overlay(arr, lambda dr, SS, hit=hit: laptop(dr, SS, kx, ky, hit))
        base = Image.fromarray(arr)
        base.alpha_composite(fr[i], pos[i])
        out.append((np.array(base), 130))
    return out

if __name__ == '__main__':
    print(S.save_gif('typing_test', build()))
