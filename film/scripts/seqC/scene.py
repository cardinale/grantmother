# Sequence C (global frames 814-1258). Run: Blender -b -P scene.py -- <mode> args
#   test f1 f2 f3   -> renders those frames to seqC/test_<f>.png
#   range a b       -> renders frames a..b into ../frames/f_#####
import bpy, bmesh, math, os, sys
from mathutils import Vector

WORK = "/Users/ac/Code/aws-hackathon/video/kinetic/seqC"
LOGO = "/Users/ac/Code/aws-hackathon/video/assets/logos/final"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["test", "860"]
W, H = 1920, 1080
FS, FE = 814, 1258

FONT_BLACK = "/Library/Fonts/SF-Pro-Display-Black.otf"
FONT_BOLD = "/Library/Fonts/SF-Pro-Display-Bold.otf"
FONT_SEMI = "/Library/Fonts/SF-Pro-Text-Semibold.otf"
FONT_MED = "/Library/Fonts/SF-Pro-Text-Medium.otf"

def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def hexlin(h):
    h = h.lstrip("#"); return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)
def font(p):
    return bpy.data.fonts.load(p, check_existing=True)
F_BLACK, F_BOLD, F_SEMI, F_MED = font(FONT_BLACK), font(FONT_BOLD), font(FONT_SEMI), font(FONT_MED)

def principled(name, color, rough=0.35, emit=None, es=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    if emit is not None:
        b.inputs["Emission Color"].default_value = emit
        b.inputs["Emission Strength"].default_value = es
    return m
def emission(name, color, s=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = color; e.inputs[1].default_value = s
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0])
    return m
def image_mat(name, path):
    img = bpy.data.images.load(path, check_existing=True)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = "Cubic"
    e = nt.nodes.new("ShaderNodeEmission"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(t.outputs["Color"], e.inputs["Color"]); nt.links.new(t.outputs["Alpha"], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(e.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs[0])
    try: m.surface_render_method = "BLENDED"
    except Exception: pass
    return m, img
def halo_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0)
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    one = nt.nodes.new("ShaderNodeMath"); one.operation = "MULTIPLY_ADD"; one.inputs[1].default_value = -2.0; one.inputs[2].default_value = 1.0; one.use_clamp = True
    sc = nt.nodes.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = 1.0; sc.use_clamp = True
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.5
    amt = nt.nodes.new("ShaderNodeMath"); amt.operation = "MULTIPLY"; amt.inputs[1].default_value = 0.0; amt.name = "AMT"
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (1, 1, 1, 1); e.inputs[1].default_value = 1.2
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mix = nt.nodes.new("ShaderNodeMixShader")
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    L = nt.links.new
    L(tc.outputs["Generated"], sub.inputs[0]); L(sub.outputs[0], ln.inputs[0]); L(ln.outputs["Value"], one.inputs[0])
    L(one.outputs[0], sc.inputs[0]); L(sc.outputs[0], pw.inputs[0]); L(pw.outputs[0], amt.inputs[0])
    L(amt.outputs[0], mix.inputs[0]); L(tr.outputs[0], mix.inputs[1]); L(e.outputs[0], mix.inputs[2]); L(mix.outputs[0], o.inputs[0])
    try: m.surface_render_method = "BLENDED"
    except Exception: pass
    return m, amt

scene = bpy.context.scene
for o in list(scene.objects): bpy.data.objects.remove(o, do_unlink=True)
coll = scene.collection
def link(ob): coll.objects.link(ob); return ob

M_WHITE = principled("white", hexlin("f2f2f4"), rough=0.3)
M_LINE = principled("line", hexlin("f2f2f4"), rough=0.5, emit=hexlin("f2f2f4"), es=0.35)
M_LABEL = emission("label", hexlin("a8a8ad"), 1.0)
M_RULE = emission("rule", hexlin("3a3a3e"), 1.0)
M_PANEL = principled("panel", hexlin("242426"), rough=0.6)
M_FLOOR = principled("floor", hexlin("242426"), rough=0.55)
M_STAMP = emission("stamp", hexlin("f2f2f4"), 1.0)
M_CARD = principled("card", (0.85, 0.85, 0.86, 1), rough=0.45, emit=(1, 1, 1, 1), es=0.12)
M_CARDG = principled("cardg", (0.9, 0.9, 0.9, 1), rough=0.4, emit=(1, 1, 1, 1), es=0.12)
M_STRIP = principled("strip", hexlin("aeaeb2"), rough=0.6)
M_STRIP2 = principled("strip2", hexlin("d1d1d6"), rough=0.6)
H_WHITE = emission("h_white", (1, 1, 1, 1)); H_GREY = emission("h_grey", hexlin("a8a8ad")); H_RULE = emission("h_rule", hexlin("8e8e93"))

# ---------------------------------------------------------------- keyframe helpers
def fcurves(ob, data=None):
    ad = (data or ob).animation_data
    if not ad or not ad.action: return []
    try: return list(ad.action.fcurves)
    except AttributeError:
        out = []
        for layer in ad.action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags: out.extend(cb.fcurves)
        return out
INTERP = {}  # (id, path, frame) -> interp
def key(ob, path, frame, value, interp="BEZIER"):
    setattr(ob, path, value)
    ob.keyframe_insert(path, frame=frame)
    INTERP[(ob.name, path, frame)] = interp
def finalize_interp():
    for ob in bpy.data.objects:
        for fc in fcurves(ob):
            for kp in fc.keyframe_points:
                ip = INTERP.get((ob.name, fc.data_path, int(round(kp.co.x))))
                if ip: kp.interpolation = ip
                kp.handle_left_type = kp.handle_left_type
def appear(ob, frame):  # invisible (scale 0) before `frame`
    s = tuple(ob.scale)
    key(ob, "scale", frame - 1, (0, 0, 0), "CONSTANT"); key(ob, "scale", frame, s)
def vanish(ob, frame):
    s = tuple(ob.scale)
    key(ob, "scale", frame - 1, s, "CONSTANT"); key(ob, "scale", frame, (0, 0, 0), "CONSTANT")
def slam(ob, t0, final, off, rot_off=(0, 0, 0), dur=5, over=0.07):
    fin = Vector(final); off = Vector(off)
    r0 = Vector(ob.rotation_euler)
    appear(ob, t0 - dur)
    key(ob, "location", t0 - dur, tuple(fin + off), "LINEAR")
    key(ob, "rotation_euler", t0 - dur, tuple(r0 + Vector(rot_off)), "LINEAR")
    key(ob, "location", t0, tuple(fin - off * over))
    key(ob, "rotation_euler", t0, tuple(r0 - Vector(rot_off) * over))
    key(ob, "location", t0 + 3, tuple(fin))
    key(ob, "rotation_euler", t0 + 3, tuple(r0))

def text(body, fnt, size, extrude, bevel, mat, align="LEFT", name="t"):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.font = fnt; cu.size = size
    cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 2; cu.align_x = align
    cu.materials.append(mat)
    return link(bpy.data.objects.new(name, cu))
def bounds(ob):
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))
def stand_text(body, fnt, width=None, size=1.0, extrude=0.3, bevel=0.03, mat=M_WHITE, name="t", align="CENTER"):
    ob = text(body, fnt, size, extrude, bevel, mat, align, name)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    if width:
        mn, mx = bounds(ob); s = width / (mx.x - mn.x)
        ob.data.size = size * s; ob.data.extrude = extrude * s; ob.data.bevel_depth = bevel * s
    return ob
def box(name, w, h, d, mat):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me)); ob.scale = (w, d, h); me.materials.append(mat)
    return ob

# ---------------------------------------------------------------- camera rig
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 40; cam_d.sensor_width = 36; cam_d.clip_end = 300
cam = link(bpy.data.objects.new("cam", cam_d)); scene.camera = cam
tgt = link(bpy.data.objects.new("tgt", None))
con = cam.constraints.new("TRACK_TO"); con.target = tgt; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 4.0
TW = 18 / 40; TH = TW * H / W
HK = 0.85
hudroot = link(bpy.data.objects.new("hudroot", None)); hudroot.parent = cam
def cam_key(f, loc, look, interp="BEZIER"):
    loc = Vector(loc); look = Vector(look)
    key(cam, "location", f, tuple(loc), interp); key(tgt, "location", f, tuple(look), interp)
    D = (look - loc).length
    cam_d.dof.focus_distance = D; cam_d.dof.keyframe_insert("focus_distance", frame=f)
    hudroot.location = (0, 0, -9.0); hudroot.scale = (9.0,) * 3

def hp(px, py):  # pixel -> hud-normalized (depth 1)
    return Vector(((px / W - 0.5) * 2 * TW, (0.5 - py / H) * 2 * TH, 0))
def hpx(n): return n / H * 2 * TH
def htext(body, px, py, cap_px, fnt, mat, align="LEFT", track=1.0):
    cu = bpy.data.curves.new("ht", "FONT"); cu.body = body; cu.font = fnt
    cu.size = hpx(cap_px) / 0.72; cu.align_x = align; cu.space_character = track; cu.materials.append(mat)
    ob = bpy.data.objects.new("ht", cu); link(ob); ob.parent = hudroot; ob.location = hp(px, py)
    return ob
def hrect(x0, y0, x1, y1, mat, name="hr"):
    me = bpy.data.meshes.new(name)
    me.from_pydata([hp(x0, y0), hp(x1, y0), hp(x1, y1), hp(x0, y1)], [], [(0, 1, 2, 3)]); me.materials.append(mat)
    ob = link(bpy.data.objects.new(name, me)); ob.parent = hudroot; return ob
def hlogo(path, px, pyc, h_px, name):
    mat, img = image_mat(name, path); iw, ih = img.size; w = h_px * iw / ih
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector((0, -hpx(h_px) / 2, 0)), Vector((hpx(w), -hpx(h_px) / 2, 0)),
                    Vector((hpx(w), hpx(h_px) / 2, 0)), Vector((0, hpx(h_px) / 2, 0))], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[i].uv = c
    me.materials.append(mat)
    ob = link(bpy.data.objects.new(name, me)); ob.parent = hudroot; ob.location = hp(px, pyc); ob.location.z = 0.001
    return ob, w
def hslide(ob, f, dx_px=-60, dur=6):  # HUD element slides in from left
    p = Vector(ob.location); appear(ob, f)
    key(ob, "location", f, tuple(p + Vector((hpx(dx_px), 0, 0))), "LINEAR")
    key(ob, "location", f + dur, tuple(p))
def hout(ob, f):
    vanish(ob, f)

# ---------------------------------------------------------------- floor + lights + world
me = bpy.data.meshes.new("floor"); s = 400
me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)]); me.materials.append(M_FLOOR)
link(bpy.data.objects.new("floor", me))
def area(name, loc, target, energy, size):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size
    ob = link(bpy.data.objects.new(name, ld)); ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return ob
for cx, cy in ((0, 7), (60, 12)):
    c = Vector((cx, cy, 1.5))
    area("key", (cx - 14, cy - 16, 16), c, 1800, 7)
    area("front", (cx - 3, cy - 24, 9), c, 1100, 9)
    area("rim", (cx + 6, cy + 14, 10), c, 6000, 4)
    area("rim2", (cx - 12, cy + 10, 4), c, 2500, 3)
world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = hexlin("1c1c1e")

# ================================================================ BEAT 1: CONVERSATION (t 35.14 -> f843)
conv = stand_text("CONVERSATION", F_BLACK, width=10.0, size=1.0, extrude=0.35, bevel=0.035, name="conv")
slam(conv, 843, (0, 0, 0), (0, 26, 3.5), rot_off=(math.radians(-35), 0, 0), dur=5)
vanish(conv, 887)
cap1 = htext("IT STARTS WITH A", 960, 210, 22, F_SEMI, H_GREY, align="CENTER", track=1.25)
hslide(cap1, 828, dx_px=0); hout(cap1, 881)
r1 = hrect(900, 232, 1020, 234, H_RULE); appear(r1, 829); hout(r1, 881)

cam_key(814, (-5.2, -15.5, 0.5), (-1.2, 0, 0.75))
cam_key(872, (1.6, -11.6, 0.62), (0.4, 0, 0.62))
cam_key(880, (0.9, -2.4, 0.45), (0.4, 8, 0.9), "LINEAR")
cam_key(886, (-1.0, 0.6, 1.4), (-0.8, 13.5, 3.0))
cam_key(896, (-3.0, 1.0, 2.9), (-1.0, 13.5, 3.3))
cam_key(970, (-2.0, 1.6, 3.0), (-0.9, 13.5, 3.3))

# ================================================================ BEAT 2: Masky + live fact lines
mlogo, mw = hlogo(os.path.join(LOGO, "masky-on-dark.png"), 110, 150, 150, "masky")
hslide(mlogo, 881, dx_px=-80, dur=7)
ml1 = htext("INTERVIEWER", 110 + mw + 34, 138, 15, F_SEMI, H_GREY, track=1.3); hslide(ml1, 883)
ml2 = htext("Masky avatar", 110 + mw + 34, 178, 26, F_SEMI, H_WHITE); hslide(ml2, 884)
mr = hrect(110 + mw + 18, 110, 110 + mw + 20, 190, H_RULE); appear(mr, 882)
for _o in (mlogo, mr): vanish(_o, 1053)
ml1.data.body = "INTERVIEWER  ·  MASKY AVATAR"; ml2.data.body = "Masky avatar"
ml1.data.body = "INTERVIEWER · Masky avatar"
bpy.data.objects.remove(ml2, do_unlink=True)
ml1.data.size = hpx(20) / 0.72; ml1.location = hp(110 + mw + 34, 160); vanish(ml1, 1053)

PY = 14.0; X0 = -4.6; LIFT = 0.3
rows = [  # label, text, size, z, type start frame, chars per frame
    ("FOUNDER", "Anthony Cardinale", 0.78, 3.0, 901, 1.3),
    ("ORGANIZATION", "Comfortist LLC", 0.78, 1.95, 920, 1.3),
    ("MISSION", "Giving small nonprofits the power", 0.5, 0.95, 941, 2.1),
    (None, "of a grant-writing team", 0.5, 0.3, 957, 2.0),
]
TYPE = []
lines = []
float_off = [(-0.4, -1.4, 0.05, -3), (0.6, 0.9, -0.05, 2.5), (-0.2, -0.6, 0.0, -1.5), (0.3, 0.2, 0.0, 1.5)]
for i, (lab, body, sz, z, f0, cpf) in enumerate(rows):
    ob = text(body, F_BOLD, sz, 0.035, 0.006, M_LINE, "LEFT", "fact%d" % i)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    final = Vector((X0, PY, z + LIFT))
    dx, dy, dz, rz = float_off[i]
    floatp = final + Vector((dx, dy, dz))
    ob.location = floatp
    rf = (math.pi / 2, 0, math.radians(rz))
    key(ob, "location", f0, tuple(floatp)); key(ob, "rotation_euler", f0, rf)
    key(ob, "location", 968, tuple(floatp + Vector((0.15, -0.1, 0.03)))); key(ob, "rotation_euler", 968, rf)
    key(ob, "location", 976, tuple(final - Vector((0, 0.05, 0)))); key(ob, "rotation_euler", 976, (math.pi / 2, 0, 0))
    key(ob, "location", 979, tuple(final)); key(ob, "rotation_euler", 979, (math.pi / 2, 0, 0))
    lines.append(ob)
    TYPE.append((ob.data, body, f0, cpf))
    if lab:
        lb = text(lab, F_SEMI, 0.2, 0.0, 0.0, M_LABEL, "LEFT", "lab%d" % i)
        lb.data.space_character = 1.3
        lb.rotation_euler = rf; lb.location = floatp + Vector((0, 0, sz * 0.95 + 0.05))
        appear(lb, f0)
        key(lb, "location", f0, tuple(lb.location)); key(lb, "rotation_euler", f0, rf)
        key(lb, "location", 968, tuple(floatp + Vector((0.15, -0.1, 0.03 + sz * 0.95 + 0.05)))); key(lb, "rotation_euler", 968, rf)
        key(lb, "location", 979, tuple(final + Vector((0, 0, sz * 0.95 + 0.05)))); key(lb, "rotation_euler", 979, (math.pi / 2, 0, 0))
# measure lines at full body for panel layout
xmax = max(bounds(o)[1].x for o in lines)
for o in lines:  # restore location for measurement independence
    pass
def on_frame(sc, *a):
    f = sc.frame_current
    for cu, body, f0, cpf in TYPE:
        n = 0 if f < f0 else min(len(body), int((f - f0 + 1) * cpf))
        cu.body = body[:n] if n > 0 else " "
bpy.app.handlers.frame_change_pre.clear()
bpy.app.handlers.frame_change_pre.append(on_frame)

# FACT SHEET panel (locks at 974)
PX0, PX1 = X0 - 0.7, xmax + 0.9
PZ0, PZ1 = 0.45 + LIFT - 0.45, 3.0 + LIFT + 1.55
pcx, pcz = (PX0 + PX1) / 2, (PZ0 + PZ1) / 2
panel = box("panel", PX1 - PX0, PZ1 - PZ0, 0.04, M_PANEL); panel.location = (pcx, PY + 0.12, pcz)
appear(panel, 974); key(panel, "scale", 974, (0.02, 0.04, PZ1 - PZ0), "LINEAR")
key(panel, "scale", 980, (PX1 - PX0, 0.04, PZ1 - PZ0))
RT = 0.03
rules = [("top", pcx, PZ1, PX1 - PX0, RT), ("bot", pcx, PZ0, PX1 - PX0, RT),
         ("hdr", pcx, PZ1 - 0.62, PX1 - PX0 - 0.6, RT * 0.7)]
for nm, x, z, w, h in rules:
    r = box("rule_" + nm, w, h, 0.02, M_RULE); r.location = (x, PY + 0.02, z)
    appear(r, 974); key(r, "scale", 974, (0.01, 0.02, h), "LINEAR"); key(r, "scale", 981, (w, 0.02, h))
for nm, x in (("l", PX0), ("r", PX1)):
    r = box("rule_" + nm, RT, PZ1 - PZ0, 0.02, M_RULE); r.location = (x, PY + 0.02, pcz)
    appear(r, 976); key(r, "scale", 976, (RT, 0.02, 0.01), "LINEAR"); key(r, "scale", 982, (RT, 0.02, PZ1 - PZ0))
fs = text("FACT SHEET", F_BOLD, 0.34, 0.04, 0.006, M_WHITE, "LEFT", "factsheet")
fs.data.space_character = 1.12
fs.rotation_euler = (math.pi / 2, 0, 0)
slam(fs, 974, (X0, PY - 0.02, PZ1 - 0.47), (0, -2.0, 0.6), dur=4)
# SOURCE OF TRUTH stamp on "bound" (42.32 -> f1016)
st = link(bpy.data.objects.new("stamp", None))
stt = text("SOURCE OF TRUTH", F_SEMI, 0.26, 0.0, 0.0, M_STAMP, "CENTER", "stamp_t"); stt.data.space_character = 1.3
stt.parent = st; stt.location = (0, 0, -0.09)
bpy.context.view_layer.update()
smn, smx = stt.bound_box[0], stt.bound_box[6]
sw = (smx[0] - smn[0]) + 0.5; sh = 0.62
for nm, (x, y, w, h) in {"t": (0, sh / 2, sw, 0.035), "b": (0, -sh / 2, sw, 0.035),
                         "l": (-sw / 2, 0, 0.035, sh), "r": (sw / 2, 0, 0.035, sh)}.items():
    me = bpy.data.meshes.new("sr"); me.from_pydata([(x - w / 2, y - h / 2, 0), (x + w / 2, y - h / 2, 0), (x + w / 2, y + h / 2, 0), (x - w / 2, y + h / 2, 0)], [], [(0, 1, 2, 3)])
    me.materials.append(M_STAMP); ob = link(bpy.data.objects.new("sr", me)); ob.parent = st
st.rotation_euler = (math.pi / 2, math.radians(5), 0)
SPOS = Vector((PX1 - sw / 2 - 0.35, PY - 0.3, PZ1 - 0.3))
appear(st, 1012)
key(st, "location", 1012, tuple(SPOS + Vector((0, -3.0, 0))), "LINEAR"); key(st, "scale", 1012, (2.4, 2.4, 2.4), "LINEAR")
key(st, "location", 1016, tuple(SPOS)); key(st, "scale", 1016, (0.94, 0.94, 0.94))
key(st, "location", 1018, tuple(SPOS)); key(st, "scale", 1018, (1, 1, 1))

cam_key(1000, (1.2, -1.2, 2.25), (pcx - 0.3, PY, pcz + 0.1))
cam_key(1050, (1.9, -2.2, 2.35), (pcx - 0.1, PY, pcz + 0.1), "LINEAR")

# ================================================================ BEAT 3: Glasser scout (44.1 -> f1058)
BX = 60.0; CY = 14.0
cam_key(1058, (BX - 4.6, 1.0, 1.55), (BX - 0.6, CY, 2.2), "BEZIER")
cam_key(1160, (BX - 2.0, 0.4, 1.9), (BX - 0.1, CY, 2.2))
glogo, gw = hlogo(os.path.join(LOGO, "glasser-on-dark.png"), 110, 132, 54, "glasser")
hslide(glogo, 1058, dx_px=-140, dur=7)
gr = hrect(110, 186, 110 + 46, 188, H_RULE); appear(gr, 1061)
gl = htext("FUNDER SCOUT", 110, 222, 18, F_SEMI, H_WHITE, track=1.35); hslide(gl, 1061)

card_mesh = bpy.data.meshes.new("cardm"); bm = bmesh.new()
CW, CH = 2.3, 1.45
vs = [bm.verts.new(v) for v in ((-CW / 2, -CH / 2, 0), (CW / 2, -CH / 2, 0), (CW / 2, CH / 2, 0), (-CW / 2, CH / 2, 0))]
bm.faces.new(vs)
bmesh.ops.bevel(bm, geom=bm.verts[:], offset=0.14, segments=6, affect="VERTICES")
bm.to_mesh(card_mesh); bm.free()
import random
rng = random.Random(4)
cards = []
GLOW = [1, 4, 6]
halos = {}
for i in range(8):
    r, c = divmod(i, 4)
    m = M_CARDG if i in GLOW else M_CARD
    me = card_mesh.copy(); me.materials.append(m)
    cd = link(bpy.data.objects.new("card%d" % i, me))
    sol = cd.modifiers.new("s", "SOLIDIFY"); sol.thickness = 0.07
    cd.rotation_euler = (math.pi / 2, 0, 0)
    # abstract strips
    def strip(x0, y, w, h, mat):
        sm = bpy.data.meshes.new("st"); sm.from_pydata([(x0, y - h / 2, 0.012), (x0 + w, y - h / 2, 0.012), (x0 + w, y + h / 2, 0.012), (x0, y + h / 2, 0.012)], [], [(0, 1, 2, 3)])
        sm.materials.append(mat); so = link(bpy.data.objects.new("st", sm)); so.parent = cd
    strip(-CW / 2 + 0.22, CH / 2 - 0.3, 0.5 + rng.random() * 0.5, 0.14, M_STRIP)
    for k in range(3):
        strip(-CW / 2 + 0.22, CH / 2 - 0.62 - k * 0.22, (CW - 0.44) * rng.uniform(0.45, 0.95), 0.06, M_STRIP2)
    home = Vector((BX + (-3.75 + c * 2.5), CY, 3.15 - r * 1.75 + 0.15))
    f0 = 1066 + i * 2 + rng.randint(0, 2)
    slam(cd, f0, tuple(home), (rng.uniform(-6, 6), 30, rng.uniform(2, 6)),
         rot_off=(rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), rng.uniform(-1, 1)), dur=6)
    cards.append((cd, home))
    if i in GLOW:
        hm, amt = halo_mat("halo%d" % i)
        hme = bpy.data.meshes.new("halo"); hw_, hh_ = CW * 2.2, CH * 2.6
        hme.from_pydata([(-hw_ / 2, -hh_ / 2, 0), (hw_ / 2, -hh_ / 2, 0), (hw_ / 2, hh_ / 2, 0), (-hw_ / 2, hh_ / 2, 0)], [], [(0, 1, 2, 3)])
        uv = hme.uv_layers.new(); hme.materials.append(hm)
        ho = link(bpy.data.objects.new("halo%d" % i, hme)); ho.parent = cd; ho.location = (0, 0, -0.25)
        halos[i] = amt
# glow on "actually fund" (46.5 -> f1116, fund f1125)
bc = M_CARD.node_tree.nodes["Principled BSDF"]
bg = M_CARDG.node_tree.nodes["Principled BSDF"]
def mkey(sock, f, v):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f)
mkey(bc.inputs["Base Color"], 1114, (0.85, 0.85, 0.86, 1)); mkey(bc.inputs["Base Color"], 1124, (0.32, 0.32, 0.34, 1))
mkey(bc.inputs["Emission Strength"], 1114, 0.12); mkey(bc.inputs["Emission Strength"], 1124, 0.0)
mkey(bg.inputs["Emission Strength"], 1114, 0.12); mkey(bg.inputs["Emission Strength"], 1124, 0.6)
for i, amt in halos.items():
    mkey(amt.inputs[1], 1114, 0.0); mkey(amt.inputs[1], 1125, 0.35)
    mkey(amt.inputs[1], 1212, 0.35)
    mkey(amt.inputs[1], 1222, 0.6 if i == 4 else 0.12)
for i in GLOW:
    cd, home = cards[i]
    key(cd, "location", 1116, tuple(home))
    lifted = home + Vector((0, -1.3, 0.25))
    key(cd, "location", 1125, tuple(lifted))
    cards[i] = (cd, lifted)

# FIT CHECKER (48.5 -> f1164); cuts (49.08 -> f1178)
fc_l = htext("FIT CHECKER", 1810, 132, 30, F_SEMI, H_WHITE, align="RIGHT", track=1.25); hslide(fc_l, 1164, dx_px=60)
fc_r = hrect(1810 - 46, 160, 1810, 162, H_RULE); appear(fc_r, 1166)
sweep = box("sweep", 0.05, 5.4, 0.05, M_STAMP)
appear(sweep, 1174)
key(sweep, "location", 1174, (BX - 7.5, CY - 1.6, 2.4), "LINEAR"); key(sweep, "location", 1186, (BX + 7.5, CY - 1.6, 2.4), "LINEAR")
vanish(sweep, 1187)
for i in range(8):
    if i in GLOW: continue
    cd, home = cards[i]
    fcut = 1175 + int((home.x - (BX - 7.5)) / 15 * 12)
    key(cd, "location", fcut, tuple(home)); key(cd, "rotation_euler", fcut, (math.pi / 2, 0, 0))
    key(cd, "location", fcut + 5, tuple(home + Vector((14, -2, rng.uniform(-0.5, 1.5)))), "LINEAR")
    key(cd, "rotation_euler", fcut + 5, (math.pi / 2 + rng.uniform(-0.6, 0.6), rng.uniform(-0.8, 0.8), -1.2))
    vanish(cd, fcut + 6)
# regroup the 3 survivors
for slot, i in enumerate(GLOW):
    cd, cur = cards[i]
    dest = Vector((BX + (-2.75 + slot * 2.75), CY - 1.3, 2.5))
    key(cd, "location", 1188, tuple(cur)); key(cd, "location", 1200, tuple(dest))
    cards[i] = (cd, dest)
# THE FOUNDER PICKS (50.58 -> f1214)
tfp = stand_text("THE FOUNDER PICKS", F_BLACK, width=7.6, size=1.0, extrude=0.3, bevel=0.03, name="tfp")
slam(tfp, 1214, (BX, CY - 4.2, 0.0), (0, 22, 3.0), rot_off=(math.radians(-30), 0, 0), dur=5)
for i in GLOW:
    cd, cur = cards[i]
    key(cd, "location", 1212, tuple(cur))
    if i == 4:
        key(cd, "location", 1222, tuple(cur + Vector((0, -3.6, 0.55)))); key(cd, "rotation_euler", 1212, (math.pi / 2, 0, 0))
        key(cd, "rotation_euler", 1222, (math.pi / 2 - 0.08, 0, 0.06)); key(cd, "location", 1258, tuple(cur + Vector((0, -3.9, 0.6))))
    else:
        key(cd, "location", 1222, tuple(cur + Vector((0, 1.6, -0.1))))
mkey(bg.inputs["Base Color"], 1212, (0.9, 0.9, 0.9, 1))
cam_key(1200, (BX - 1.2, -0.2, 2.1), (BX, CY - 1, 2.0))
cam_key(1258, (BX + 0.4, -1.6, 2.35), (BX, CY - 2, 1.9))

finalize_interp()

# ---------------------------------------------------------------- render settings
scene.render.engine = "BLENDER_EEVEE"
ee = scene.eevee
def tryset(o, a, v):
    try: setattr(o, a, v)
    except Exception as ex: print("skip", a, ex)
tryset(ee, "taa_render_samples", 12); tryset(ee, "use_raytracing", False); tryset(ee, "use_shadows", True)
tryset(scene.render, "use_motion_blur", True); tryset(scene.render, "motion_blur_shutter", 0.5); tryset(ee, "motion_blur_steps", 1)
scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "None"
scene.render.resolution_x = W; scene.render.resolution_y = H; scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGB"; scene.render.image_settings.color_depth = "8"
scene.frame_start, scene.frame_end = FS, FE

mode = argv[0]
if mode == "save":
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "seqC.blend"))
elif mode == "test":
    import time
    for f in [int(x) for x in argv[1:]]:
        t = time.time(); scene.frame_set(f); on_frame(scene)
        scene.render.filepath = os.path.join(WORK, "test_%d.png" % f)
        bpy.ops.render.render(write_still=True); print("TIME", f, round(time.time() - t, 2))
elif mode == "range":
    a, b = int(argv[1]), int(argv[2])
    scene.frame_start, scene.frame_end = a, b
    scene.render.filepath = "/Users/ac/Code/aws-hackathon/video/kinetic/frames/f_#####"
    scene.render.use_overwrite = True
    bpy.ops.render.render(animation=True)
