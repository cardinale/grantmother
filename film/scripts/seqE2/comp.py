# composite HUD RGBA frames over 3D frames. usage: comp.py <dir_3d_pattern> <hud_dir> <out_pattern> frames...
import sys, os
from PIL import Image
from multiprocessing import Pool
src, hud, out = sys.argv[1], sys.argv[2], sys.argv[3]
fr = [int(x) for x in sys.argv[4:]]
def one(f):
    hp = os.path.join(hud, "h_%05d.png" % f)
    sp = src % f
    if not (os.path.exists(hp) and os.path.exists(sp)):
        return f, False
    a = Image.open(sp).convert("RGBA")
    h = Image.open(hp).convert("RGBA")
    if h.size != a.size:
        h = h.resize(a.size, Image.LANCZOS)
    Image.alpha_composite(a, h).convert("RGB").save(out % f)
    return f, True
if __name__ == "__main__":
    with Pool(6) as p:
        r = p.map(one, fr)
    print("composited", sum(1 for _, ok in r if ok), "of", len(r))
