# Sequence A (film 0.00-16.30 s, global frames 0-390). Grantmother kinetic type.
# Run: Blender -b -P seqA.py -- <mode> [frames]   mode: test | final
import bpy, math, random, os, sys
from mathutils import Vector

WORK = "/Users/ac/Code/aws-hackathon/video/kinetic/seqA"
OUTDIR = "/Users/ac/Code/aws-hackathon/video/kinetic/frames"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if argv else "test"
TEST_FRAMES = [int(x) for x in argv[1].split(",")] if len(argv) > 1 else [40, 200, 380]
F0, F1 = 0, 390

FONT_BLACK = "/Library/Fonts/SF-Pro-Display-Black.otf"
FONT_BOLD = "/Library/Fonts/SF-Pro-Display-Bold.otf"
FONT_MED = "/Library/Fonts/SF-Pro-Text-Medium.otf"
FONT_SEMI = "/Library/Fonts/SF-Pro-Text-Semibold.otf"

def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def hexlin(h):
    h = h.lstrip("#")
    return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)
GRAPHITE = hexlin("1c1c1e")

scene = bpy.context.scene
for o in list(scene.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = scene.collection
def link(ob):
    coll.objects.link(ob); return ob
def font(p):
    return bpy.data.fonts.load(p, check_existing=True)
FB, FBO, FM, FS = font(FONT_BLACK), font(FONT_BOLD), font(FONT_MED), font(FONT_SEMI)

def principled(name, color, rough=0.35, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    try: b.inputs["Specular IOR Level"].default_value = spec
    except KeyError: pass
    return m
def emission(name, color, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = color
    e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0])
    return m

M_WHITE = principled("type_white", hexlin("f2f2f4"), rough=0.3)
M_SIDE = principled("type_side", hexlin("8e8e93"), rough=0.4)
M_FLOOR = principled("floor", hexlin("242426"), rough=0.32, spec=0.6)
E_WHITE = emission("hud_white", (1, 1, 1, 1), 1.0)
E_GREY = emission("hud_grey", hexlin("9a9a9e"), 1.0)
E_RULE = emission("hud_rule", hexlin("5a5a5f"), 1.0)
E_DUST = emission("dust", hexlin("8e8e93"), 0.5)

def text(body, fnt, size, extrude=0.0, bevel=0.0, mats=(M_WHITE,), align="CENTER", spacing=1.0, name=None):
    cu = bpy.data.curves.new(name or body, "FONT")
    cu.body = body; cu.font = fnt; cu.size = size
    cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 2
    cu.align_x = align; cu.space_character = spacing
    for m in mats: cu.materials.append(m)
    ob = bpy.data.objects.new(name or body, cu)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    return link(ob)

def bounds(ob):
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))
def width(ob):
    mn, mx = bounds(ob); return mx.x - mn.x

def hero(body, target_w, fnt=FB, ext=0.32, bev=0.03, name=None):
    ob = text(body, fnt, 1.0, ext, bev, name=name)
    ob.location = (0, 0, 0)
    s = target_w / max(width(ob), 1e-4)
    ob.data.size = s
    ob.data.extrude = ext * s / 2.4
    ob.data.bevel_depth = bev * s / 2.4
    return ob

def flat(body, size, fnt=FS, mat=E_WHITE, spacing=1.0, align="CENTER", name=None):
    return text(body, fnt, size, 0.0, 0.0, mats=(mat,), align=align, spacing=spacing, name=name)

def rule(w, h, mat=E_RULE, name="rule"):
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.active_object; ob.name = name
    ob.scale = (w, h, 1); ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.data.materials.append(mat)
    return ob

# ----------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_back(p, s=1.9):
    p = clamp(p) - 1; return 1 + (s + 1) * p ** 3 + s * p ** 2
def ease_out(p): p = clamp(p); return 1 - (1 - p) ** 3
def ease_in(p): p = clamp(p); return p ** 3
def ease_io(p): p = clamp(p); return p * p * (3 - 2 * p)
def lerp(a, b, t): return a + (b - a) * t
def vlerp(a, b, t): return Vector(a).lerp(Vector(b), t)

HIDE = Vector((0, 500, -500))
anims = []  # (ob, fn(f) -> (loc, rot, scale) or None for hidden)
def anim(ob, fn): anims.append((ob, fn))

def slam_depth(home, f_land, dur=5, depth=45.0, f_out=None, out_fn=None, rot0=(0, 0, 0), base_rot=(math.pi / 2, 0, 0)):
    """Fly in from depth (+Y) landing on f_land with overshoot toward camera."""
    home = Vector(home)
    def fn(f):
        if f < f_land - dur: return None
        if f_out is not None and f >= f_out:
            r = out_fn(f - f_out, home) if out_fn else None
            return r
        p = (f - (f_land - dur)) / dur
        if p < 1:
            q = ease_in(p) if True else p
            loc = home + Vector((0, depth * (1 - q), 0))
            rr = [b + r * (1 - q) for b, r in zip(base_rot, rot0)]
            return loc, rr, 1.0
        # overshoot / settle (pushed toward camera then back)
        k = f - f_land
        bounce = -0.9 * math.exp(-k / 2.2) * math.cos(k * 1.3)
        return home + Vector((0, bounce, 0)), list(base_rot), 1.0 + 0.04 * math.exp(-k / 2.0) * math.cos(k * 1.3)
    return fn

def slam_drop(home, f_land, dur=5, height=14.0, f_out=None, out_fn=None, base_rot=(math.pi / 2, 0, 0)):
    home = Vector(home)
    def fn(f):
        if f < f_land - dur: return None
        if f_out is not None and f >= f_out:
            return out_fn(f - f_out, home) if out_fn else None
        p = (f - (f_land - dur)) / dur
        if p < 1:
            return home + Vector((0, 0, height * (1 - ease_in(p)))), list(base_rot), 1.0
        k = f - f_land
        b = -0.35 * math.exp(-k / 2.0) * math.cos(k * 1.4)
        sq = 1.0 + 0.05 * math.exp(-k / 2.0) * math.cos(k * 1.4)
        return home + Vector((0, 0, b)), list(base_rot), (sq, 1.0, 2.0 - sq)
    return fn

def snap_in(home, f_in, f_out=None, base_rot=(math.pi / 2, 0, 0), dur=3, out_dur=3):
    home = Vector(home)
    def fn(f):
        if f < f_in: return None
        if f_out is not None and f >= f_out + out_dur: return None
        p = ease_out((f - f_in + 1) / dur)
        sx = lerp(0.0001, 1.0, p)
        sy = lerp(0.2, 1.0, p)
        if f_out is not None and f >= f_out:
            q = ease_in((f - f_out + 1) / out_dur)
            sx = lerp(1.0, 0.0001, q); sy = lerp(1.0, 0.3, q)
        return home, list(base_rot), (sx, sy, 1.0)
    return fn

def push_out(direction, spin=(0, 0, 0), dur=6):
    d = Vector(direction)
    def fn(k, home):
        if k > dur: return None
        q = ease_in((k + 1) / dur)
        return home + d * q, [math.pi / 2 + spin[0] * q, spin[1] * q, spin[2] * q], 1.0
    return fn

def F(t): return int(round(t * 24))

# ================================================================= STAGE A: title (y=0)
WORD = "Grantmother"
TITLE_W = 19.0
probe = hero(WORD, TITLE_W, name="probe")
SZ = probe.data.size; EXT = probe.data.extrude; BEV = probe.data.bevel_depth
full_mn, full_mx = bounds(probe)
bpy.data.objects.remove(probe, do_unlink=True)

def left_text(body):
    ob = text(body, FB, SZ, EXT, BEV, align="LEFT", name="tmp")
    return ob
letters = []
x0 = -TITLE_W / 2
for k, ch in enumerate(WORD):
    pre = left_text(WORD[:k + 1]); _, pmx = bounds(pre)
    one = left_text(ch); _, omx = bounds(one)
    bpy.data.objects.remove(pre, do_unlink=True)
    pos_x = pmx.x - omx.x
    one.name = f"L_{k}_{ch}"
    letters.append((one, pos_x))
# recentre
lx = [p for _, p in letters]
mins = []
for ob, px in letters:
    ob.location = (px, 0, 0)
mn_all = min(bounds(o)[0].x for o, _ in letters); mx_all = max(bounds(o)[1].x for o, _ in letters)
shift = -(mn_all + mx_all) / 2
TITLE_Z = 0.6
rng = random.Random(11)
for k, (ob, px) in enumerate(letters):
    home = (px + shift, 0, TITLE_Z)
    f_land = F(0.8) + 2 * k + 5
    rot0 = (rng.uniform(-0.6, 0.6), rng.uniform(-0.5, 0.5), rng.uniform(-0.4, 0.4))
    anim(ob, slam_depth(home, f_land, dur=5, depth=38.0 + 3 * k, rot0=rot0))

cap_mn, cap_mx = bounds(letters[1][0])  # 'r' for x-height reference
# tagline: flat HUD line under the title
TAG = "A grant office that refuses to lie."
tag = flat(TAG, 0.62, fnt=FM, mat=E_WHITE, spacing=1.05, name="tagline")
tag_z = TITLE_Z - 1.25
f_tag = F(3.5)
anim(tag, snap_in((0, -0.4, tag_z), f_tag, dur=3))
tw = width(tag) if False else 12.6
ruleL = rule(1.0, 0.012, name="ruleL"); ruleR = rule(1.0, 0.012, name="ruleR")
def rule_fn(side):
    def fn(f):
        if f < f_tag: return None
        p = ease_out((f - f_tag) / 6)
        L = 3.2 * p
        cx = side * (6.9 + L / 2)
        return Vector((cx, -0.4, tag_z + 0.22)), [math.pi / 2, 0, 0], (max(L, 1e-4), 1, 1)
    return fn
anim(ruleL, rule_fn(-1)); anim(ruleR, rule_fn(1))
# small HUD annotation top-left of the title
ann = flat("GRANT OFFICE  /  EST. HONESTY", 0.30, fnt=FS, mat=E_GREY, spacing=1.25, align="LEFT", name="ann")
anim(ann, snap_in((-9.6, -0.4, TITLE_Z + 3.45), F(1.6), dur=3))
ann_rule = rule(1.0, 0.01, name="annrule")
def annr(f):
    if f < F(1.6): return None
    p = ease_out((f - F(1.6)) / 8); L = 19.2 * p
    return Vector((-9.6 + L / 2, -0.4, TITLE_Z + 3.3)), [math.pi / 2, 0, 0], (max(L, 1e-4), 1, 1)
anim(ann_rule, annr)

# ================================================================= STAGE B (y=70)
SY = 70.0
f_meet, f_founder = F(6.4), F(7.02)
f_three1, f_three2 = F(7.98), F(9.02)
f_one, f_very, f_big, f_ask = F(10.56), F(10.82), F(11.44), F(12.06)
f_40k, f_for, f_fourth = F(13.38), F(14.5), F(15.48)

# "A FOUNDER" HUD label
lbl_small = flat("MEET", 0.42, fnt=FS, mat=E_GREY, spacing=1.4, name="meet")
lbl = flat("A FOUNDER", 1.5, fnt=FS, mat=E_WHITE, spacing=1.18, name="afounder")
anim(lbl_small, snap_in((0, SY, 3.6), f_meet, f_out=f_three1 - 3))
anim(lbl, snap_in((0, SY, 1.6), f_founder - 2, f_out=f_three1 - 3))
fr_t = rule(1.0, 0.014, mat=E_GREY, name="fr_t"); fr_b = rule(1.0, 0.014, mat=E_GREY, name="fr_b")
def frame_rule(z, f_in):
    def fn(f):
        if f < f_in or f >= f_three1 - 1: return None
        p = ease_out((f - f_in) / 7); L = 10.5 * p
        return Vector((0, SY, z)), [math.pi / 2, 0, 0], (max(L, 1e-4), 1, 1)
    return fn
anim(fr_t, frame_rule(3.25, f_meet)); anim(fr_b, frame_rule(1.15, f_founder - 2))

# 3 SCHOOLS / 3 COUNSELORS
schools = hero("3 SCHOOLS", 15.5, name="3schools")
couns = hero("3 COUNSELORS", 15.5, name="3couns")
sch_h = bounds(schools)[1].z - bounds(schools)[0].z
cou_h = bounds(couns)[1].z - bounds(couns)[0].z
GAP = 0.55
cou_z = -0.6
sch_z = cou_z + cou_h + GAP
anim(schools, slam_depth((0, SY, sch_z), f_three1 + 1, dur=4, depth=40, rot0=(0.0, 0, 0.25),
                         f_out=f_one - 3, out_fn=push_out((-26, 14, 9), spin=(0.4, 0, 0.7))))
anim(couns, slam_depth((0, SY, cou_z), f_three2 + 1, dur=4, depth=40, rot0=(0.0, 0, -0.25),
                       f_out=f_one - 3, out_fn=push_out((26, 14, -7), spin=(-0.4, 0, -0.7))))
# HUD tags beside the counts
t_sch = flat("SCHOOLS  01-03", 0.3, fnt=FS, mat=E_GREY, spacing=1.3, align="LEFT", name="t_sch")
anim(t_sch, snap_in((-7.75, SY - 0.3, sch_z + sch_h + 0.25), f_three1 + 3, f_out=f_one - 3))
t_cou = flat("COUNSELORS  01-03", 0.3, fnt=FS, mat=E_GREY, spacing=1.3, align="LEFT", name="t_cou")
anim(t_cou, snap_in((-7.75, SY - 0.3, cou_z - 0.55), f_three2 + 3, f_out=f_one - 3))

# ONE VERY / BIG ASK.
def line_words(words, size_w, fnt=FB):
    obs = [hero(w, 1.0, fnt=fnt, name="w_" + w) for w in words]
    # common size: fit total width
    for o in obs: o.data.size = 1.0; o.data.extrude = 0.32 / 2.4; o.data.bevel_depth = 0.03 / 2.4
    ws = [width(o) for o in obs]
    gap = 0.3
    tot = sum(ws) + gap * (len(ws) - 1)
    s = size_w / tot
    xs = []; x = -size_w / 2
    for o, w in zip(obs, ws):
        o.data.size = s; o.data.extrude = 0.32 * s / 2.4; o.data.bevel_depth = 0.03 * s / 2.4
        xs.append(x + w * s / 2); x += (w + gap) * s
    return obs, xs, s
(l1, l1x, s1) = line_words(["ONE", "VERY"], 13.0)
(l2, l2x, s2) = line_words(["BIG", "ASK."], 15.5)
h1 = bounds(l1[0])[1].z - bounds(l1[0])[0].z
h2 = bounds(l2[0])[1].z - bounds(l2[0])[0].z
z2 = -0.7; z1 = z2 + h2 + 0.6
outs = [(-30, 40, 10), (30, 40, 12), (-30, 40, -8), (30, 40, -10)]
for o, x, fl, d in zip(l1 + l2, l1x + l2x, [f_one, f_very, f_big, f_ask], outs):
    z = z1 if o in l1 else z2
    anim(o, slam_depth((x, SY, z), fl + 1, dur=4, depth=36, rot0=(0.3, 0, 0),
                       f_out=f_40k - 3, out_fn=push_out(d, spin=(0.6, 0.3, 0.5), dur=5)))

# $40k : drops from above
k40 = hero("$40k", 17.0, ext=0.45, name="40k")
k40_h = bounds(k40)[1].z - bounds(k40)[0].z
k40_z = -0.9
def k40_after(k, home):
    # at "for": lift and recede to make room, then thrown up at "fourth"
    f = f_for + k
    if f < f_fourth - 3:
        p = ease_out((f - f_for) / 6)
        return home + Vector((lerp(0, 3.2, p), lerp(0, 14, p), lerp(0, 4.0, p))), [math.pi / 2, 0, 0], lerp(1.0, 0.62, p)
    q = ease_in((f - (f_fourth - 3) + 1) / 5)
    if q >= 1: return None
    return home + Vector((3.2, 14 + 30 * q, 4.0 + 22 * q)), [math.pi / 2 - 0.6 * q, 0, 0.2 * q], 0.62
anim(k40, slam_drop((0, SY, k40_z), f_40k + 1, dur=4, height=16, f_out=f_for, out_fn=k40_after))
t40 = flat("THE ASK  /  USD", 0.32, fnt=FS, mat=E_GREY, spacing=1.3, align="LEFT", name="t40")
anim(t40, snap_in((-8.5, SY - 0.4, k40_z + k40_h + 0.3), f_40k + 3, f_out=f_for - 1))

# FOR A  +  giant 4 / TH
fora = hero("FOR A", 6.0, fnt=FBO, ext=0.25, name="fora")
four = hero("4", 1.0, name="four")
four.data.size = 9.5; four.data.extrude = 0.45 * 9.5 / 2.4 / 2.2; four.data.bevel_depth = 0.035 * 9.5 / 2.4 / 2.2
fmn, fmx = bounds(four)
four_w = fmx.x - fmn.x; four_h = fmx.z - fmn.z
th = hero("TH", 2.4, name="th")
th_h = bounds(th)[1].z - bounds(th)[0].z
four_x = 2.2; four_z = -1.6
fora_x = four_x - four_w / 2 - 0.6 - 3.0
fora_z = four_z
anim(fora, slam_depth((fora_x, SY, fora_z), f_for + 1, dur=4, depth=30, rot0=(0, 0, 0.2)))
anim(four, slam_drop((four_x, SY, four_z), f_fourth + 1, dur=4, height=18))
anim(th, slam_depth((four_x + four_w / 2 + 0.25 + 1.2, SY, four_z + four_h - th_h), f_fourth + 3, dur=3, depth=24))
t4 = flat("SCHOOL  04", 0.32, fnt=FS, mat=E_GREY, spacing=1.3, align="LEFT", name="t4")
anim(t4, snap_in((four_x + four_w / 2 + 0.3, SY - 0.4, four_z + 0.15), f_fourth + 5))
r4 = rule(1.0, 0.012, mat=E_GREY, name="r4")
def r4fn(f):
    if f < f_fourth + 4: return None
    p = ease_out((f - f_fourth - 4) / 8); L = 4.5 * p
    return Vector((four_x + four_w / 2 + 0.3 + L / 2, SY - 0.4, four_z + 0.75)), [math.pi / 2, 0, 0], (max(L, 1e-4), 1, 1)
anim(r4, r4fn)

# ================================================================= environment
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 40, -2.6))
floor = bpy.context.active_object; floor.data.materials.append(M_FLOOR)

# dust specks for parallax / speed
import bmesh
bm = bmesh.new(); r = random.Random(3)
for i in range(520):
    c = Vector((r.uniform(-35, 35), r.uniform(-60, 130), r.uniform(-2.3, 16)))
    s = r.uniform(0.015, 0.05)
    res = bmesh.ops.create_cube(bm, size=s)
    bmesh.ops.translate(bm, verts=res["verts"], vec=c)
me = bpy.data.meshes.new("dust"); bm.to_mesh(me)
dust = bpy.data.objects.new("dust", me); me.materials.append(E_DUST); link(dust)

def area(name, loc, target, energy, size):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size
    ob = bpy.data.objects.new(name, ld); ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return link(ob)
for cy in (0.0, SY):
    c = Vector((0, cy, 2.0))
    area("key", (-16, cy - 14, 18), c, 2600, 6)
    area("front", (-4, cy - 24, 6), c, 5200, 8)
    area("rim", (6, cy + 10, 12), c, 7000, 3)
    area("rim2", (-12, cy + 9, 4), c, 2600, 2)
    area("top", (0, cy - 2, 16), c, 1400, 3)

world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = GRAPHITE
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

# ================================================================= camera
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 38; cam_d.clip_start = 0.05; cam_d.clip_end = 400
cam = bpy.data.objects.new("cam", cam_d); link(cam); scene.camera = cam
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.0
tgt = bpy.data.objects.new("look", None); link(tgt)
con = cam.constraints.new("TRACK_TO"); con.target = tgt; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"

F_WHIP0, F_WHIP1 = F(5.8), F(6.4)
landings = sorted([F(0.8) + 2 * k + 5 for k in range(len(WORD))][::5] + [f_three1 + 1, f_three2 + 1, f_one + 1,
                   f_big + 1, f_ask + 1, f_40k + 1, f_fourth + 1])
def shake(f):
    v = Vector((0, 0, 0))
    for fl in landings:
        k = f - fl
        if 0 <= k < 12:
            amp = (0.22 if fl in (f_40k + 1, f_fourth + 1) else 0.1) * math.exp(-k / 3.0)
            v += Vector((math.sin(k * 2.7 + fl), 0, math.cos(k * 3.3 + fl))) * amp
    return v

def cam_at(f):
    """returns cam loc, look target, focus distance"""
    if f < F_WHIP0:
        p = f / F_WHIP0
        loc = Vector((lerp(-6.5, -3.0, ease_io(p)), lerp(-36, -27, p), lerp(0.4, 1.0, p)))
        look = Vector((lerp(-1.0, 0.0, p), 0, 1.6))
        return loc, look, None
    if f < F_WHIP1:
        p = (f - F_WHIP0) / (F_WHIP1 - F_WHIP0)
        q = ease_in(p) * 0.85 + 0.15 * p
        loc = Vector((lerp(-3.0, -2.0, q), lerp(-27, 48, q), lerp(1.0, 1.4, q)))
        look = Vector((lerp(0, 0, q), lerp(0, SY, q), lerp(1.6, 2.4, q)))
        return loc, look, None
    # stage B drift
    p = (f - F_WHIP1) / (F1 - F_WHIP1)
    loc = Vector((lerp(-4.0, 3.0, ease_io(p)), lerp(50.0, 55.5, p), lerp(0.2, 1.4, p)))
    look = Vector((lerp(-0.6, 0.6, p), SY, 2.0))
    # small forward push-ins on beats
    for fb, amt in ((f_three1, 0.8), (f_one, 0.6), (f_40k, -1.2), (f_fourth, 1.6)):
        if f >= fb:
            loc.y += amt * ease_out((f - fb) / 10)
    # after the 4 lands, look shifts to center the "4"
    if f >= f_fourth:
        q = ease_io((f - f_fourth) / 10)
        look.x = lerp(look.x, -0.4, q); look.z = lerp(look.z, 2.4, q)
    return loc, look, None

# ================================================================= bake keyframes
for f in range(F0, F1 + 1):
    for ob, fn in anims:
        r = fn(f)
        if r is None:
            loc, rot, sc = HIDE, (math.pi / 2, 0, 0), 0.0001
        else:
            loc, rot, sc = r
        if not isinstance(sc, (tuple, list)): sc = (sc, sc, sc)
        ob.location = loc; ob.rotation_euler = rot; ob.scale = sc
        ob.keyframe_insert("location", frame=f); ob.keyframe_insert("rotation_euler", frame=f)
        ob.keyframe_insert("scale", frame=f)
    loc, look, _ = cam_at(f)
    loc = loc + shake(f)
    cam.location = loc; tgt.location = look
    cam.keyframe_insert("location", frame=f); tgt.keyframe_insert("location", frame=f)
    # focus: distance to stage plane along view
    stage_y = 0.0 if f < F_WHIP0 + 4 else SY
    cam_d.dof.focus_distance = max(abs(stage_y - loc.y), 0.5)
    cam_d.dof.keyframe_insert("focus_distance", frame=f)

# per-frame keys: linear interpolation (motion blur reads between keys)
for ob in [o for o, _ in anims] + [cam, tgt]:
    ad = ob.animation_data
    if ad and ad.action:
        try:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
        except AttributeError:
            pass

# ================================================================= render settings
scene.render.engine = "BLENDER_EEVEE"
ee = scene.eevee
def tryset(obj, attr, val):
    try: setattr(obj, attr, val)
    except Exception as ex: print("skip", attr, ex)
tryset(ee, "taa_render_samples", 16)
tryset(ee, "use_raytracing", False)
tryset(ee, "use_shadows", True)
tryset(scene.render, "use_motion_blur", True)
tryset(scene.render, "motion_blur_shutter", 0.5)
tryset(ee, "motion_blur_steps", 1)
tryset(ee, "motion_blur_max", 48)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.resolution_x = 1920; scene.render.resolution_y = 1080; scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
scene.frame_start = F0; scene.frame_end = F1
scene.render.use_overwrite = True; scene.render.use_placeholder = False

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "seqA.blend"))

if MODE == "test":
    import time
    for f in TEST_FRAMES:
        scene.frame_set(f)
        scene.render.filepath = os.path.join(WORK, f"test_{f:05d}.png")
        t = time.time(); bpy.ops.render.render(write_still=True)
        print(f"RENDER frame {f}: {time.time() - t:.2f}s")
else:
    scene.render.filepath = os.path.join(OUTDIR, "f_#####")
    bpy.ops.render.render(animation=True)
