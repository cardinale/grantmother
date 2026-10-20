# Grantmother kinetic film, sequence E2 (finale + end card), global frames 2286-2879.
# Run: Blender -b -P scene.py -- <mode> [pct] [frames]
#   mode test  -> render listed frames (comma list) at pct into seqE2/test_#####.png
#   mode final -> render full range into kinetic/frames/f_#####.png
import bpy, bmesh, math, random, os, sys
from mathutils import Vector

WORK = "/Users/ac/Code/aws-hackathon/video/kinetic/seqE2"
FRAMES = "/Users/ac/Code/aws-hackathon/video/kinetic/frames/f_#####"
LOGO = "/Users/ac/Code/aws-hackathon/video/assets/logos/final"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if argv else "test"
PCT = int(argv[1]) if len(argv) > 1 else 50
TEST_FRAMES = [int(x) for x in argv[2].split(",")] if len(argv) > 2 and argv[2][0].isdigit() else [2300]
SAMPLES = int(argv[3]) if len(argv) > 3 else 16
W, H = 1920, 1080
F0, F1 = 2286, 2879

FONT_BLACK = "/Library/Fonts/SF-Pro-Display-Black.otf"
FONT_BOLD = "/Library/Fonts/SF-Pro-Display-Bold.otf"
FONT_TXT_SEMI = "/Library/Fonts/SF-Pro-Text-Semibold.otf"
FONT_TXT_MED = "/Library/Fonts/SF-Pro-Text-Medium.otf"

def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def hexlin(h):
    h = h.lstrip("#")
    return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)
GRAPHITE = hexlin("1c1c1e")
FLOORC = hexlin("242426")
TYPEW = hexlin("f2f2f4")

def font(p):
    return bpy.data.fonts.load(p, check_existing=True)
F_BLACK, F_BOLD, F_SEMI, F_MED = font(FONT_BLACK), font(FONT_BOLD), font(FONT_TXT_SEMI), font(FONT_TXT_MED)

def tryset(obj, attr, val):
    try:
        setattr(obj, attr, val)
    except Exception as ex:
        print("skip", attr, ex)

def principled(name, color, rough=0.35, spec=0.5, emit=None, es=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    try:
        b.inputs["Specular IOR Level"].default_value = spec
    except KeyError:
        pass
    if emit is not None:
        b.inputs["Emission Color"].default_value = emit
        b.inputs["Emission Strength"].default_value = es
    return m

def emission_mat(name, color, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = color
    e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    return m

def image_mat(name, path):
    img = bpy.data.images.load(path, check_existing=True)
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = "Cubic"
    e = nt.nodes.new("ShaderNodeEmission")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(t.outputs["Color"], e.inputs["Color"])
    nt.links.new(t.outputs["Alpha"], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(e.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs[0])
    tryset(m, "surface_render_method", "BLENDED")
    return m, img

# ======================================================== 3D scene
scene = bpy.context.scene
scene.name = "E2_3D"
for o in list(scene.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = scene.collection
scene.render.fps = 24
scene.frame_start, scene.frame_end = F0, F1

def link(ob):
    coll.objects.link(ob); return ob

def make_text(body, fnt, size, extrude, bevel, name, mats, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body; cu.font = fnt; cu.size = size
    cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 2
    cu.align_x = align
    ob = bpy.data.objects.new(name, cu)
    for m in mats:
        cu.materials.append(m)
    return link(ob)

def bounds(ob):
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))

def letters(ob):
    """Convert text to mesh, split into glyph objects sorted left->right, origins at glyph centre."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    me.transform(ob.matrix_world)
    mats = list(ob.data.materials)
    bpy.data.objects.remove(ob, do_unlink=True)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bm.verts.ensure_lookup_table()
    # connected components
    comp_of = {}
    cid = 0
    for v in bm.verts:
        if v.index in comp_of:
            continue
        stack = [v]
        while stack:
            x = stack.pop()
            if x.index in comp_of:
                continue
            comp_of[x.index] = cid
            for e in x.link_edges:
                o2 = e.other_vert(x)
                if o2.index not in comp_of:
                    stack.append(o2)
        cid += 1
    # merge components whose x-ranges nest inside another (e.g. counters already joined; dots)
    out = []
    for c in range(cid):
        g = bm.copy()
        g.verts.ensure_lookup_table()
        bmesh.ops.delete(g, geom=[vv for vv in g.verts if comp_of[vv.index] != c], context="VERTS")
        if len(g.verts) < 3:
            g.free(); continue
        cen = sum((v.co for v in g.verts), Vector()) / len(g.verts)
        mn = Vector((min(v.co.x for v in g.verts), min(v.co.y for v in g.verts), min(v.co.z for v in g.verts)))
        mx = Vector((max(v.co.x for v in g.verts), max(v.co.y for v in g.verts), max(v.co.z for v in g.verts)))
        cen = (mn + mx) / 2
        for v in g.verts:
            v.co -= cen
        m2 = bpy.data.meshes.new("g%d" % c); g.to_mesh(m2); g.free()
        for mt in mats:
            m2.materials.append(mt)
        o = bpy.data.objects.new(m2.name, m2); o.location = cen
        link(o)
        out.append(o)
    bm.free()
    out.sort(key=lambda o: o.location.x)
    return out

def key(ob, path, f, val, interp=None, easing=None):
    setattr(ob, path, val)
    ob.keyframe_insert(path, frame=f)
    if interp:
        ad = ob.animation_data
        for fc in ad.action.fcurves if hasattr(ad.action, "fcurves") else []:
            pass
    if interp:
        set_interp(ob, path, f, interp, easing)

def all_fcurves(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):
        try:
            return list(act.fcurves)
        except Exception:
            pass
    res = []
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                res.extend(cb.fcurves)
    return res

def set_interp(ob, path, f, interp, easing=None):
    for fc in all_fcurves(ob):
        if fc.data_path != path:
            continue
        for kp in fc.keyframe_points:
            if abs(kp.co.x - f) < 1e-3:
                kp.interpolation = interp
                if easing:
                    kp.easing = easing

def hide_between(ob, f_on, f_off=None):
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=F0 - 20)
    ob.hide_render = False; ob.keyframe_insert("hide_render", frame=f_on)
    if f_off is not None:
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=f_off)

M_W1 = principled("type_w1", TYPEW, rough=0.3)
M_W2 = principled("type_w2", TYPEW, rough=0.3)
M_W3 = principled("type_w3", (0.6, 0.6, 0.62, 1), rough=0.35)
M_SIG = principled("sig", (1, 1, 1, 1), rough=0.2, emit=(1, 1, 1, 1), es=2.2)
M_FLOOR = principled("floor", FLOORC, rough=0.32, spec=0.6)

# floor
bpy.ops.mesh.primitive_plane_add(size=600, location=(40, 100, 0))
floor = bpy.context.active_object
floor.data.materials.append(M_FLOOR)

# ---------------- beat 1: NOTHING / GOES OUT  (set at x=0)
S1 = 5.0
l1 = make_text("NOTHING", F_BLACK, S1, 0.55, 0.035, "nothing", [M_W1])
l2 = make_text("GOES OUT", F_BLACK, S1, 0.55, 0.035, "goesout", [M_W1])
for ob, z in ((l1, 2.05), (l2, 0.0)):
    ob.rotation_euler = (math.pi / 2, 0, 0); ob.location = (0, 0, z)
mn, mx = bounds(l2)
print("goesout", mn, mx)
g1 = letters(l1)
g2 = letters(l2)
print("glyphs", len(g1), len(g2))

def drop_in(o, land, rng, height=7.0):
    fin = o.location.copy()
    o.location = fin + Vector((rng.uniform(-0.3, 0.3), rng.uniform(-1.5, 0.5), height))
    o.rotation_euler = (rng.uniform(-0.5, 0.5), rng.uniform(-0.4, 0.4), rng.uniform(-0.3, 0.3))
    o.scale = (1, 1, 1)
    for p in ("location", "rotation_euler"):
        o.keyframe_insert(p, frame=land - 6)
        set_interp(o, p, land - 6, "QUAD", "EASE_IN")
    o.location = fin; o.rotation_euler = (0, 0, 0)
    o.keyframe_insert("location", frame=land); o.keyframe_insert("rotation_euler", frame=land)
    for f, s in ((land - 1, (0.95, 0.95, 1.12)), (land, (1.1, 1.1, 0.82)), (land + 2, (0.97, 0.97, 1.05)), (land + 4, (1, 1, 1))):
        o.scale = s; o.keyframe_insert("scale", frame=f)
    hide_between(o, land - 7)

rng = random.Random(7)
for i, o in enumerate(g1):
    drop_in(o, 2291 + int(i * 0.5), rng)
for i, o in enumerate(g2):
    land = (2308 + int(i * 0.6)) if i < 4 else (2325 + int((i - 4) * 0.6))
    drop_in(o, land, rng)

# dim the wall when the signature arrives
bsdf1 = M_W1.node_tree.nodes["Principled BSDF"].inputs["Base Color"]
bsdf1.default_value = TYPEW; bsdf1.keyframe_insert("default_value", frame=2362)
bsdf1.default_value = (0.1, 0.1, 0.105, 1); bsdf1.keyframe_insert("default_value", frame=2372)

# signature: handwritten stroke drawn by bevel_factor_end
sig_cu = bpy.data.curves.new("signature", "CURVE")
sig_cu.dimensions = "3D"
sig_cu.bevel_depth = 0.075
sig_cu.bevel_resolution = 3
sig_cu.use_fill_caps = True
tryset(sig_cu, "bevel_factor_mapping_end", "SPLINE")
sp = sig_cu.splines.new("POLY")
pts = []
N = 420
U_END = 9.5 * math.pi
for k in range(N):
    u = U_END * k / (N - 1)
    env = 0.55 + 0.45 * math.sin(u * 0.33 + 0.4)
    x = 0.17 * u - 0.32 * math.sin(u)
    z = 0.62 * math.cos(u) * env + 0.18 * math.sin(0.41 * u)
    x += 0.32 * z  # slant
    y = 0.18 * math.sin(u * 0.5)
    pts.append((x, y, z))
# flourish: underline swoosh back to the left
lx, ly, lz = pts[-1]
for k in range(1, 90):
    s = k / 89
    x = lx + 0.6 * math.sin(s * math.pi * 0.5) - (lx + 0.9) * s ** 1.4
    z = lz - 1.1 * math.sin(s * math.pi * 0.5) - 0.15 * s
    pts.append((x, 0.12 * s, z))
sp.points.add(len(pts) - 1)
SC = 1.25
cx = (max(p[0] for p in pts) + min(p[0] for p in pts)) / 2
for p, (x, y, z) in zip(sp.points, pts):
    p.co = ((x - cx) * SC, y * SC, z * SC, 1)
sig = bpy.data.objects.new("signature", sig_cu)
sig_cu.materials.append(M_SIG)
link(sig)
sig.location = (0, -3.2, 2.0)
sig_cu.bevel_factor_end = 0.0; sig_cu.keyframe_insert("bevel_factor_end", frame=2366)
sig_cu.bevel_factor_end = 1.0; sig_cu.keyframe_insert("bevel_factor_end", frame=2398)
hide_between(sig, 2366, 2438)

# ---------------- beat 2: Grantmother + tagline (set at x=60)
GX = 60.0
TZ = 1.2
title = make_text("Grantmother", F_BLACK, 6.8, 0.6, 0.04, "title", [M_W2])
title.rotation_euler = (math.pi / 2, 0, 0); title.location = (GX, 0, TZ)
tmn, tmx = bounds(title)
print("title bounds", tmn, tmx, "width", tmx.x - tmn.x)
tg = letters(title)
print("title glyphs", len(tg))
rng = random.Random(11)
for i, o in enumerate(tg):
    fin = o.location.copy()
    land = 2439 + int(i * 0.5)
    o.location = fin + Vector((rng.uniform(-6, 6), rng.uniform(40, 70), rng.uniform(-2, 5)))
    o.rotation_euler = (rng.uniform(-1.5, 1.5), rng.uniform(-1.2, 1.2), rng.uniform(-1.5, 1.5))
    for p in ("location", "rotation_euler"):
        o.keyframe_insert(p, frame=land - 11)
        set_interp(o, p, land - 11, "CUBIC", "EASE_IN")
    o.location = fin + Vector((0, -0.9, 0)); o.rotation_euler = (0, 0, 0)
    o.keyframe_insert("location", frame=land); o.keyframe_insert("rotation_euler", frame=land)
    o.location = fin + Vector((0, 0.25, 0)); o.keyframe_insert("location", frame=land + 2)
    o.location = fin; o.keyframe_insert("location", frame=land + 5)
    hide_between(o, land - 11)

# tagline: words placed left->right, one object per word
TS = 2.0
words = [("A", 2475), ("grant", 2476), ("office", 2483), ("that", 2493), ("refuses", 2503), ("to", 2513), ("lie.", 2526)]
tmp = []
widths = []
for wd, _ in words:
    t = make_text(wd, F_BOLD, TS, 0.22, 0.015, "w_" + wd, [M_W3], align="LEFT")
    t.rotation_euler = (math.pi / 2, 0, 0)
    a, b = bounds(t)
    widths.append(b.x - a.x)
    tmp.append(t)
space = TS * 0.26
total = sum(widths) + space * (len(words) - 1)
x = GX - total / 2
tag_objs = []
for (wd, land), t, wdt in zip(words, tmp, widths):
    a, b = bounds(t)
    t.location = (x - a.x + t.location.x, 0.3, 0.0)
    fin = t.location.copy()
    x += wdt + space
    t.location = fin + Vector((0, -6, 3.2)); t.rotation_euler = (math.pi / 2 - 0.9, 0, 0)
    for p in ("location", "rotation_euler"):
        t.keyframe_insert(p, frame=land - 5)
        set_interp(t, p, land - 5, "QUAD", "EASE_IN")
    t.location = fin + Vector((0, 0.15, 0)); t.rotation_euler = (math.pi / 2, 0, 0)
    t.keyframe_insert("location", frame=land); t.keyframe_insert("rotation_euler", frame=land)
    t.location = fin; t.keyframe_insert("location", frame=land + 3)
    # fast exit at 106 s: fall back and down through the floor
    t.keyframe_insert("location", frame=2543)
    set_interp(t, "location", 2543, "QUAD", "EASE_IN")
    t.location = fin + Vector((0, 3, -3)); t.keyframe_insert("location", frame=2551)
    hide_between(t, land - 6, 2552)
    tag_objs.append(t)

# ---------------- camera
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 35; cam_d.clip_start = 0.05; cam_d.clip_end = 400
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.2
cam = link(bpy.data.objects.new("cam", cam_d)); scene.camera = cam
tgt = link(bpy.data.objects.new("tgt", None))
foc = link(bpy.data.objects.new("focus", None))
cam_d.dof.focus_object = foc
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"

def ckey(f, cpos, tpos, fpos=None, interp=None, easing=None):
    cam.location = cpos; cam.keyframe_insert("location", frame=f)
    tgt.location = tpos; tgt.keyframe_insert("location", frame=f)
    foc.location = fpos if fpos else tpos; foc.keyframe_insert("location", frame=f)
    if interp:
        for o in (cam, tgt, foc):
            set_interp(o, "location", f, interp, easing)

# beat 1 drift
ckey(F0, (-3.0, -15.0, 0.6), (0, 0, 1.9), (0, 0, 1.9), "LINEAR")
ckey(2362, (0.4, -12.6, 0.9), (0, 0, 1.9), (0, 0, 1.9), "LINEAR")
ckey(2372, (0.6, -12.3, 0.95), (0, -1, 1.9), (0, -3.2, 2.0), "LINEAR")
ckey(2412, (1.2, -11.4, 1.1), (0, -1, 1.9), (0, -3.2, 2.0), "QUAD", "EASE_IN")
# whip: fly through the gap between the two lines
ckey(2437.4, (0.2, 3.0, 1.88), (0, 30, 1.88), (0, 3.0, 1.88), "CONSTANT")
# beat 2: Grantmother, slow push
ckey(2437.5, (GX - 4.0, -25.0, 0.9), (GX, 0, 2.2), (GX, 0, 2.2), "LINEAR")
ckey(2470, (GX - 1.8, -22.0, 1.2), (GX, 0, 2.0), (GX, 0, 2.0), "LINEAR")
ckey(2543, (GX - 0.6, -19.0, 1.4), (GX, 0, 1.9), (GX, 0, 1.9), "CUBIC", "EASE_IN_OUT")
# end card: pull back, title up top, nearly still
ckey(2578, (GX + 0.0, -50.0, 4.2), (GX, 0, -6.4), (GX, 0, TZ + 1.2), "LINEAR")
ckey(F1, (GX + 0.8, -48.5, 4.3), (GX, 0, -6.3), (GX, 0, TZ + 1.2), "LINEAR")

# ---------------- lights + world
sun_d = bpy.data.lights.new("sun", "SUN"); sun_d.energy = 2.6; sun_d.angle = math.radians(6)
sun = link(bpy.data.objects.new("sun", sun_d)); sun.rotation_euler = (math.radians(52), 0, math.radians(-32))
def area(name, loc, target, energy, size):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.size = size
    o = link(bpy.data.objects.new(name, d)); o.location = loc
    dvec = Vector(target) - Vector(loc)
    o.rotation_euler = dvec.to_track_quat("-Z", "Y").to_euler()
    return o
area("rim1", (0, 6, 14), (0, 0, 2), 500, 8)
area("rim2", (GX, 6, 14), (GX, 0, 3), 600, 10)
area("fill1", (-8, -12, 8), (0, 0, 2), 500, 10)
area("fill2", (GX - 10, -16, 9), (GX, 0, 3), 600, 12)

world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
wn = world.node_tree.nodes
wn["Background"].inputs["Color"].default_value = GRAPHITE
wn["Background"].inputs["Strength"].default_value = 1.0

ee = scene.eevee
tryset(ee, "taa_render_samples", SAMPLES)
tryset(ee, "use_raytracing", False)
tryset(ee, "use_shadows", True)
tryset(scene.render, "use_motion_blur", True)
tryset(scene.render, "motion_blur_shutter", 0.5)
tryset(ee, "motion_blur_steps", 1)
tryset(ee, "motion_blur_max", 48)
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

# ======================================================== HUD scene (ortho, transparent)
hud = bpy.data.scenes.new("E2_HUD")
hud.render.fps = 24
hud.frame_start, hud.frame_end = F0, F1
hc = hud.collection
U = 0.01
def P(px, py):
    return Vector((px * U, -py * U, 0))
hcam_d = bpy.data.cameras.new("hcam"); hcam_d.type = "ORTHO"; hcam_d.ortho_scale = W * U
hcam = bpy.data.objects.new("hcam", hcam_d); hc.objects.link(hcam)
hcam.location = (W * U / 2, -H * U / 2, 10); hud.camera = hcam
HW = emission_mat("hud_w", (0.95, 0.95, 0.95, 1), 1.0)
HG = emission_mat("hud_g", (lin(0.6), lin(0.6), lin(0.6), 1), 1.0)
HR = emission_mat("hud_rule", hexlin("3a3a3e"), 1.0)
HRL = emission_mat("hud_rule_l", (lin(0.45), lin(0.45), lin(0.47), 1), 1.0)

def htext(body, px, py, size_px, fnt, mat, align="LEFT", track=1.0):
    cu = bpy.data.curves.new("h", "FONT"); cu.body = body; cu.font = fnt
    cu.size = size_px * U; cu.align_x = align; cu.space_character = track
    cu.materials.append(mat)
    o = bpy.data.objects.new("h", cu); hc.objects.link(o)
    o.location = P(px, py)
    return o

def rect(x0, y0, x1, y1, mat):
    me = bpy.data.meshes.new("r")
    me.from_pydata([P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)], [], [(0, 1, 2, 3)])
    me.materials.append(mat)
    o = bpy.data.objects.new("r", me); hc.objects.link(o)
    return o

def hb(ob):
    hud_layer = hud.view_layers[0]
    hud_layer.update()
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return min(p.x for p in pts) / U, max(p.x for p in pts) / U

def logo_plane(slug, cx, cy, w_px, h_px):
    m, img = image_mat("logo_" + slug, os.path.join(LOGO, slug + "-on-dark.png"))
    me = bpy.data.meshes.new("lg_" + slug)
    hw, hh = w_px * U / 2, h_px * U / 2
    me.from_pydata([(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name="UV")
    for li, uv in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]):
        me.uv_layers[0].data[li].uv = uv
    me.materials.append(m)
    o = bpy.data.objects.new("lg_" + slug, me); hc.objects.link(o)
    o.location = P(cx, cy)
    return o

def hud_in(o, f, dx=0.0, dy=40.0, f_off=None, dur=7):
    fin = o.location.copy()
    o.location = fin + Vector((dx * U, -dy * U, 0)); o.scale = (0.7, 0.7, 1)
    o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
    set_interp(o, "location", f, "EXPO", "EASE_OUT"); set_interp(o, "scale", f, "BACK", "EASE_OUT")
    o.location = fin; o.scale = (1, 1, 1)
    o.keyframe_insert("location", frame=f + dur); o.keyframe_insert("scale", frame=f + dur)
    hide_between(o, f, f_off)

def logo_size(slug, area_px, hmax):
    img = bpy.data.images.load(os.path.join(LOGO, slug + "-on-dark.png"), check_existing=True)
    r = img.size[0] / img.size[1]
    h = math.sqrt(area_px / r); w = h * r
    if h > hmax:
        h = hmax; w = h * r
    return w, h

# ---- beat 1 HUD: SIGNED BY THE FOUNDER
r1 = rect(120, 868, 560, 870, HRL); hud_in(r1, 2366, dx=-80, dy=0, f_off=2412)
t1 = htext("SIGNED BY THE FOUNDER", 120, 912, 30, F_SEMI, HW, track=1.25); hud_in(t1, 2368, dx=-60, dy=0, f_off=2412)
t1b = htext("Nothing is sent without it", 120, 952, 22, F_MED, HG); hud_in(t1b, 2372, dx=-60, dy=0, f_off=2412)

# ---- end card HUD
END = 2550
name_t = htext("ANTHONY CARDINALE  ·  COMFORTIST LLC", W / 2, 400, 26, F_SEMI, HW, align="CENTER", track=1.25)
hud_in(name_t, END, dy=20)
a_, b_ = hb(name_t)
rl = rect(a_ - 240, 390, a_ - 40, 391.5, HRL); hud_in(rl, END + 2, dx=-40, dy=0)
rr = rect(b_ + 40, 390, b_ + 240, 391.5, HRL); hud_in(rr, END + 2, dx=40, dy=0)

def logo_row(slugs, label, y_label, y_row, f0, gap=72, area=11000, hmax=78, special=None):
    lab = htext(label, W / 2, y_label, 18, F_SEMI, HG, align="CENTER", track=1.35)
    hud_in(lab, f0 - 3, dy=12)
    sizes = []
    for s in slugs:
        a, hm = area, hmax
        if special and s in special:
            a, hm = special[s]
        sizes.append(logo_size(s, a, hm))
    total = sum(w for w, h in sizes) + gap * (len(slugs) - 1)
    print("row", label, "width", total)
    assert total <= W - 240, "logo row too wide"
    x = (W - total) / 2
    objs = []
    for i, (s, (w, h)) in enumerate(zip(slugs, sizes)):
        o = logo_plane(s, x + w / 2, y_row, w, h)
        hud_in(o, f0 + i * 3, dy=70, dur=9)
        x += w + gap
        objs.append(o)
    return objs

logo_row(["promptql", "masky", "glasser", "flatkey", "n8n", "flexprice", "askthew"],
         "POWERED BY", 492, 568, END + 6,
         special={"masky": (3600, 54), "flatkey": (6400, 76), "askthew": (6400, 76)})
logo_row(["snyk", "prelint", "tenki", "celesto"], "BUILT WITH", 690, 762, END + 32,
         special={"celesto": (6400, 76)})
# bottom line with aws logo
bl = htext("UNIVERSAL CELEBRATION HACKATHON  ·  AWS BUILDER LOFT  ·  OCTOBER 19, 2026", 0, 0, 22, F_SEMI, HW, track=1.2)
a_, b_ = hb(bl)
aw, ah = logo_size("aws", 3400, 40)
total = aw + 22 + (b_ - a_)
x0 = (W - total) / 2
bl.location = P(x0 + aw + 22 - a_, 912)
rect_top = rect(120, 860, W - 120, 861, HR); hud_in(rect_top, END + 50, dx=0, dy=0)
hud_in(bl, END + 54, dy=16)
aws = logo_plane("aws", x0 + aw / 2, 904, aw, ah); hud_in(aws, END + 52, dy=30)
fn = htext("Concept film. Nonprofit and figures are illustrative.", W / 2, 990, 17, F_MED, HG, align="CENTER")
hud_in(fn, END + 62, dy=10)

hud.render.engine = "BLENDER_EEVEE"
tryset(hud.eevee, "taa_render_samples", 8)
tryset(hud.render, "use_motion_blur", True)
tryset(hud.render, "motion_blur_shutter", 0.5)
hud.render.film_transparent = True
hud.view_settings.view_transform = "Standard"
hw_ = bpy.data.worlds.new("hw"); hud.world = hw_

# ======================================================== master (VSE composite)
master = bpy.data.scenes.new("E2_MASTER")
master.render.fps = 24
master.frame_start, master.frame_end = F0, F1
se = master.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
s3 = strips.new_scene(name="s3d", scene=scene, channel=1, frame_start=F0)
s3.frame_offset_start = 0
sh = strips.new_scene(name="shud", scene=hud, channel=2, frame_start=F0)
sh.blend_type = "ALPHA_OVER"
for s in (s3, sh):
    tryset(s, "scene_input", "CAMERA")
print("strip ranges", s3.frame_final_start, s3.frame_final_end, sh.frame_final_start, sh.frame_final_end)
master.view_settings.view_transform = "Standard"
master.view_settings.look = "None"
for sc in (scene, hud, master):
    sc.render.resolution_x = W; sc.render.resolution_y = H
    sc.render.resolution_percentage = PCT
master.render.use_sequencer = True
master.render.image_settings.file_format = "PNG"
master.render.image_settings.color_mode = "RGB"
master.render.image_settings.color_depth = "8"
master.render.use_file_extension = True

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "seqE2_%s.blend" % MODE + os.environ.get("FS", "")))

import time
HUD_DIR = os.path.join(WORK, "hud")
hud.render.image_settings.file_format = "PNG"
hud.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
def hud_frames():
    return list(range(2366, 2413)) + list(range(2550, F1 + 1))
if MODE == "test":
    for f in TEST_FRAMES:
        scene.frame_set(f)
        scene.render.filepath = os.path.join(WORK, "test_%05d.png" % f)
        t0 = time.time()
        bpy.ops.render.render(write_still=True, scene=scene.name)
        print("RENDERED", f, round(time.time() - t0, 2))
        hud.frame_set(f)
        hud.render.filepath = os.path.join(WORK, "testhud_%05d.png" % f)
        bpy.ops.render.render(write_still=True, scene=hud.name)
elif MODE == "hud":
    hud.render.filepath = os.path.join(HUD_DIR, "h_#####")
    for f in hud_frames():
        hud.frame_set(f)
        hud.render.filepath = os.path.join(HUD_DIR, "h_%05d.png" % f)
        bpy.ops.render.render(write_still=True, scene=hud.name)
elif MODE == "final":
    scene.frame_start = int(os.environ.get("FS", F0)); scene.frame_end = int(os.environ.get("FE", F1))
    scene.render.filepath = FRAMES
    scene.render.use_file_extension = True
    scene.render.use_overwrite = True
    bpy.ops.render.render(animation=True, scene=scene.name)
