"""error(지침 버전): 18/19번 이미지. loop = 엎드린 두 컷 + ERROR 글자(안정적), full = 서 있다가 뻗는 전체 흐름"""
import numpy as np
from PIL import Image
import states as S, gem, error_clawd as C

IM = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-ple/54287b17-52ab-4cb6-a14f-465a13590374/images/%d.png"

def with_label(fr, i, d):
    arr, x, y = C.place_right(fr[i])
    w, h = fr[i].width, fr[i].height
    arr = S.overlay(arr, lambda dr, SS: C.label_and_shadow(dr, SS, x, y, w, h))
    return (arr, d)

def loop(n):
    fr = gem.extract(IM % n, f'error{n}', 1.0)
    print(n, [f.size for f in fr])
    out = [with_label(fr, 2, 700), with_label(fr, 3, 400)]
    S.save_gif(f'error{n}_loop', out)
    return fr

def full(n, fr):
    seq = []
    for i, d in ((0, 700), (1, 700)):
        seq.append((gem.canvas(fr[i])[0], d))
    seq.append(with_label(fr, 2, 800))
    seq.append(with_label(fr, 3, 500))
    seq.append(with_label(fr, 2, 500))
    seq.append(with_label(fr, 3, 500))
    S.save_gif(f'error{n}_full', seq)

if __name__ == '__main__':
    for n in (18, 19):
        fr = loop(n)
        full(n, fr)
