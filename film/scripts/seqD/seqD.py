# Sequence D (climax): 2,000 -> 600. Global frames 1259-1877.
# Run: Blender -b -P seqD.py -- [mode] [args]
#   mode test <f1,f2,...> <pct>   -> renders stills into seqD/test_<f>.png
#   mode final <start> <end>     -> renders frames into kinetic/frames/f_#####
import bpy, bmesh, math, random, os, sys
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view

WORK = "/Users/ac/Code/aws-hackathon/video/kinetic/seqD"
FRAMES = "/Users/ac/Code/aws-hackathon/video/kinetic/frames/f_#####"
LOGO = "/Users/ac/Code/aws-hackathon/video/assets/logos/final/flatkey-on-dark.png"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if argv else "test"
W, H = 1920, 1080
FS, FE = 1259, 1877

def F(t):
    return round(t * 24)

FONT_BLACK = "/Library/Fonts/SF-Pro-Display-Black.otf"
FONT_BOLD = "/Library/Fonts/SF-Pro-Display-Bold.otf"
FONT_SEMI = "/Library/Fonts/SF-Pro-Text-Semibold.otf"
FONT_MED = "/Library/Fonts/SF-Pro-Text-Medium.otf"

def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hexlin(h):
    h = h.lstrip("#")
    return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)

GRAPHITE = hexlin("1c1c1e")
FLOORC = hexlin("242426")
RED = hexlin("e5322b")
WHITE = hexlin("f2f2f4")

def font(p):
    return bpy.data.fonts.load(p, check_existing=True)

def principled(name, color, rough=0.35, emit=None, emit_strength=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    try:
        b.inputs["Specular IOR Level"].default_value = spec
    except KeyError:
        pass
    if emit is not None:
        b.inputs["Emission Color"].default_value = emit
        b.inputs["Emission Strength"].default_value = emit_strength
    return m

def emission_mat(name, color, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
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
    m = bpy.data.materials.new(name)
    m.use_nodes = True
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
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m, img

scene = bpy.context.scene
for o in list(scene.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = scene.collection

def link(ob):
    coll.objects.link(ob)
    return ob

def make_text(body, fnt, size, extrude, bevel, name, mats, align="LEFT"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body; cu.font = fnt; cu.size = size
    cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 2
    cu.align_x = align
    ob = bpy.data.objects.new(name, cu)
    for m in mats:
        cu.materials.append(m)
    return link(ob)

def bounds_world(ob):
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))

def fcurves(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return []
    try:
        return list(ad.action.fcurves)
    except AttributeError:
        out = []
        for layer in ad.action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out.extend(cb.fcurves)
        return out

def set_interp(ob, mode, data_path=None):
    for fc in fcurves(ob):
        if data_path is None or fc.data_path == data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = mode

def key(ob, f, loc=None, rot=None, scale=None):
    if loc is not None:
        ob.location = loc; ob.keyframe_insert("location", frame=f)
    if rot is not None:
        ob.rotation_euler = rot; ob.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        ob.scale = scale; ob.keyframe_insert("scale", frame=f)

def vis(ob, on_frames):
    """on_frames: list of (frame, bool) for visibility; constant."""
    for f, v in on_frames:
        ob.hide_render = not v; ob.hide_viewport = not v
        ob.keyframe_insert("hide_render", frame=f)
        ob.keyframe_insert("hide_viewport", frame=f)
    set_interp(ob, "CONSTANT", "hide_render")
    set_interp(ob, "CONSTANT", "hide_viewport")

# ------------------------------------------------------------ materials
M_WHITE = principled("type_white", (0.80, 0.80, 0.81, 1), rough=0.3)
M_RED = principled("type_red", RED, rough=0.42, spec=0.25, emit=RED, emit_strength=0.25)
M_RED_CORE = principled("red_core", RED, rough=0.55, emit=RED, emit_strength=2.2)
M_FLOOR = principled("floor", FLOORC, rough=0.32, spec=0.5)

SIZE = 7.5
EXT = 0.55
BEV = 0.045
F_BLACK = font(FONT_BLACK)
F_BOLD = font(FONT_BOLD)
F_SEMI = font(FONT_SEMI)
F_MED = font(FONT_MED)
SP = SIZE * 0.26

_c = make_text(",", F_BLACK, SIZE, EXT, BEV, "comma_probe", [M_WHITE])
_c.rotation_euler = (math.pi / 2, 0, 0)
LIFT = -bounds_world(_c)[0].z + 0.03   # keep the comma tail above the floor
bpy.data.objects.remove(_c, do_unlink=True)
print("LIFT", LIFT)

def stand(ob, x):
    ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = (x, 0, LIFT)

t_we = make_text("We", F_BLACK, SIZE, EXT, BEV, "we", [M_WHITE]); stand(t_we, 0)
mn, mx = bounds_world(t_we)
t_serve = make_text("serve", F_BLACK, SIZE, EXT, BEV, "serve", [M_WHITE]); stand(t_serve, mx.x + SP)
mn, mx = bounds_world(t_serve)
X2K = mx.x + SP
t_2k = make_text("2,000", F_BLACK, SIZE, EXT, BEV, "two_k_src", [M_RED]); stand(t_2k, X2K)
mn2, mx2 = bounds_world(t_2k)
XST = mx2.x + SP
t_st = make_text("students", F_BLACK, SIZE, EXT, BEV, "students", [M_WHITE]); stand(t_st, XST)
mnS, mxS = bounds_world(t_st)
CAP = mx2.z
W2K = mx2.x - mn2.x
x2k_c = (mn2.x + mx2.x) / 2
X_END = mxS.x

# ------------------------------------------------------------ fracture 2,000
def to_world_mesh(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    me.transform(ob.matrix_world)
    return me

def bsp(bm, depth, rng):
    pieces = [bm]
    for lvl in range(depth):
        nxt = []
        for p in pieces:
            if len(p.verts) < 4:
                continue
            cen = sum((v.co for v in p.verts), Vector()) / len(p.verts)
            ang = rng.uniform(0, math.pi)
            n = Vector((math.cos(ang), rng.uniform(-0.35, 0.35), math.sin(ang))).normalized()
            co = cen + Vector((rng.uniform(-.25, .25), 0, rng.uniform(-.25, .25)))
            halves = []
            for keep in ("inner", "outer"):
                q = p.copy()
                geom = q.verts[:] + q.edges[:] + q.faces[:]
                r = bmesh.ops.bisect_plane(q, geom=geom, plane_co=co, plane_no=n,
                                           clear_outer=(keep == "inner"), clear_inner=(keep == "outer"), dist=1e-5)
                cut = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
                if cut:
                    f = bmesh.ops.holes_fill(q, edges=cut, sides=0)
                    for face in f["faces"]:
                        face.material_index = 1
                if len(q.verts) >= 4:
                    halves.append(q)
            if len(halves) == 2:
                nxt.extend(halves)
            else:
                nxt.append(p)
        pieces = nxt
    return pieces

me2k = to_world_mesh(t_2k)
bpy.data.objects.remove(t_2k, do_unlink=True)
bm_all = bmesh.new(); bm_all.from_mesh(me2k)
bmesh.ops.remove_doubles(bm_all, verts=bm_all.verts[:], dist=1e-4)
bm_all.verts.ensure_lookup_table()
glyph_bms = []
seen = set()
for v in bm_all.verts:
    if v.index in seen:
        continue
    stack = [v]; comp = set()
    while stack:
        x = stack.pop()
        if x.index in comp:
            continue
        comp.add(x.index)
        for e in x.link_edges:
            o = e.other_vert(x)
            if o.index not in comp:
                stack.append(o)
    seen |= comp
    g = bm_all.copy()
    bmesh.ops.delete(g, geom=[vv for vv in g.verts if vv.index not in comp], context="VERTS")
    glyph_bms.append(g)

rig2k = bpy.data.objects.new("rig2k", None); link(rig2k)
rng = random.Random(7)
shards = []
for gi, g in enumerate(glyph_bms):
    depth = 4 if len(g.verts) > 60 else 2
    gcen = sum((v.co for v in g.verts), Vector()) / len(g.verts)
    for p in bsp(g, depth, rng):
        me = bpy.data.meshes.new(f"shard_{gi}")
        p.to_mesh(me)
        ob = bpy.data.objects.new(me.name, me)
        me.materials.append(M_RED); me.materials.append(M_RED_CORE)
        c = sum((v.co for v in me.vertices), Vector()) / len(me.vertices)
        ob["gc"] = list(gcen)
        me.transform(Matrix.Translation(-c))
        ob.location = c
        ob.parent = rig2k
        link(ob)
        shards.append(ob)
print("shards", len(shards))

# ------------------------------------------------------------ timing
T_WRITER = F(52.6)
T_WE = F(53.72)      # drafts
T_SERVE = F(54.7)    # letter
T_2K = F(57.88)
T_ST = F(59.04)
T_AUD = F(61.42)
T_FLAT = F(64.04)
T_SCAN0 = F(65.2)
T_SCAN1 = F(66.6)
T_UNS = F(66.94)
T_600 = F(68.6)
T_SNIP = F(70.62)    # 1695
T_600ST = F(72.4)
T_TRUE = F(74.2)
T_FUND = F(75.66)
print("SNIP", T_SNIP)

# ------------------------------------------------------------ word slams
def slam_from_depth(ob, t0, dz=0.0):
    """scale-in from depth with overshoot; arrives at t0."""
    base = ob.location.copy()
    vis(ob, [(FS, False), (t0 - 5, True)])
    key(ob, t0 - 5, loc=base + Vector((0, 38, CAP * 0.6 + dz)))
    key(ob, t0, loc=base + Vector((0, -1.4, 0)))
    key(ob, t0 + 2, loc=base + Vector((0, 0.35, 0)))
    key(ob, t0 + 4, loc=base)

slam_from_depth(t_we, T_WE)
slam_from_depth(t_serve, T_SERVE)
# students: slam then (after snip) slide left to close the gap
st_base = t_st.location.copy()
slam_from_depth(t_st, T_ST)

# 2,000: drops from above, hard
vis(rig2k, [])
for ob in shards:
    vis(ob, [(FS, False), (T_2K - 4, True), (T_SNIP + 30, False)])
key(rig2k, T_2K - 4, loc=Vector((0, -2, CAP * 2.4)), scale=(1, 1, 1))
key(rig2k, T_2K, loc=Vector((0, 0, 0)), scale=(1.05, 1, 0.9))
key(rig2k, T_2K + 2, loc=Vector((0, 0, CAP * 0.06)), scale=(0.98, 1, 1.03))
key(rig2k, T_2K + 4, loc=Vector((0, 0, 0)), scale=(1, 1, 1))
set_interp(rig2k, "LINEAR", "location")

# ------------------------------------------------------------ 600
t600 = make_text("600", F_BLACK, SIZE, EXT * 1.1, BEV, "six_hundred", [M_WHITE])
t600.rotation_euler = (math.pi / 2, 0, 0)
t600.location = (0, 0, 0)
mn6, mx6 = bounds_world(t600)
w6 = mx6.x - mn6.x
X600 = mn2.x - mn6.x
print("LAYOUT", X2K, W2K, X_END, CAP, w6)
GAP = W2K - w6
HOVER = CAP * 1.45
vis(t600, [(FS, False), (T_600 - 5, True)])
key(t600, T_600 - 5, loc=Vector((X600, -0.6, HOVER + CAP * 1.8)))
key(t600, T_600, loc=Vector((X600, -0.6, HOVER - CAP * 0.06)))
key(t600, T_600 + 3, loc=Vector((X600, -0.6, HOVER + CAP * 0.02)))
key(t600, T_600 + 6, loc=Vector((X600, -0.6, HOVER)))
key(t600, T_SNIP - 4, loc=Vector((X600, -0.6, HOVER + CAP * 0.08)))   # wind-up
key(t600, T_SNIP - 1, loc=Vector((X600, -0.6, CAP * 0.55)))
key(t600, T_SNIP, loc=Vector((X600, -0.3, LIFT)), scale=(1.06, 0.86, 1))
key(t600, T_SNIP + 2, loc=Vector((X600, -0.2, LIFT + CAP * 0.03)), scale=(0.98, 1.04, 1))
key(t600, T_SNIP + 4, loc=Vector((X600, 0, LIFT)), scale=(1, 1, 1))
key(t600, T_FUND, loc=Vector((X600, 0, LIFT)))
key(t600, FS, scale=(1, 1, 1))

# students slides left into place after the snip
key(t_st, T_SNIP + 6, loc=st_base)
key(t_st, T_SNIP + 16, loc=st_base - Vector((GAP, 0, 0)))
X_END2 = X_END - GAP

# ------------------------------------------------------------ crack + shatter
bpy.context.view_layer.update()
# camera must exist to aim shards at it; build camera first (below) then shards.

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data); link(cam)
scene.camera = cam
LENS = 35.0
cam_data.lens = LENS; cam_data.sensor_width = 36
cam_data.clip_start = 0.3; cam_data.clip_end = 600
look = bpy.data.objects.new("look", None); link(look)
con = cam.constraints.new("TRACK_TO"); con.target = look
con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
cam_data.dof.use_dof = True
cam_data.dof.focus_object = look
cam_data.dof.aperture_fstop = 8.0

HFOV_W = 36.0 / LENS  # visible width per unit distance

def shot(f, xc, zc, width, ang_deg, camz, interp=None):
    d = width / HFOV_W
    a = math.radians(ang_deg)
    key(cam, f, loc=Vector((xc + math.sin(a) * d, -math.cos(a) * d, camz)))
    key(look, f, loc=Vector((xc, 0, zc)))

xWe_c = (0 + (bounds_world(t_serve)[1].x)) / 2
SENT_C = X_END / 2
SENT_C2 = X_END2 / 2
# Writer beat: dolly along the sentence as it is drafted, low oblique
xServe_c = (bounds_world(t_serve)[0].x + bounds_world(t_serve)[1].x) / 2
shot(FS, xWe_c - 4, CAP * 0.5, 26, -30, 0.9)
shot(T_WE + 4, xWe_c - 1, CAP * 0.5, 24, -26, 0.9)
shot(T_SERVE + 20, xServe_c, CAP * 0.5, 24, -18, 1.0)
shot(T_2K - 6, x2k_c - 3, CAP * 0.55, 26, -26, 0.8)
# admire the lie: slow low orbit across 2,000, students arrives
shot(T_2K + 3, x2k_c, CAP * 0.6, 20, -24, 0.7)
shot(T_ST - 6, x2k_c + 2, CAP * 0.6, 22, -6, 0.7)
shot(T_ST + 8, (x2k_c + X_END) / 2, CAP * 0.55, 30, 10, 0.8)
shot(T_AUD - 6, (x2k_c + X_END) / 2 + 2, CAP * 0.55, 30, 24, 0.8)
# whip to the auditor: wide, whole sentence
shot(T_AUD, SENT_C, CAP * 0.9, 56, 10, 3.0)
shot(T_FLAT, SENT_C, CAP * 0.9, 54, 4, 3.2)
shot(T_SCAN1, SENT_C + 1, CAP * 0.9, 52, -4, 3.0)
shot(T_UNS + 10, x2k_c + 1, CAP * 1.0, 38, -10, 2.2)
# push in on the gap with 600 hanging above
shot(T_600 + 6, x2k_c, CAP * 1.25, 32, -12, 1.4)
shot(T_SNIP - 2, x2k_c, CAP * 1.2, 29, -8, 1.2)
shot(T_SNIP + 6, x2k_c + 2, CAP * 0.8, 31, -6, 1.2)
# settle on the truth
shot(T_600ST, SENT_C2, CAP * 0.95, 50, -10, 1.6)
shot(FE, SENT_C2 + 1, CAP * 0.95, 47, -5, 1.5)

# camera shake on the snip (3-4 frames)
for i, (dx, dz) in enumerate([(0.9, -0.7), (-0.7, 0.5), (0.45, -0.3), (-0.2, 0.15)]):
    f = T_SNIP + i
    scene.frame_set(f)
    key(look, f, loc=look.location + Vector((dx, 0, dz)))
    key(cam, f, loc=cam.location + Vector((dx * 0.3, 0, dz * 0.3)))
scene.frame_set(T_SNIP + 5)
key(look, T_SNIP + 5, loc=look.location.copy())
key(cam, T_SNIP + 5, loc=cam.location.copy())

# slight crack on UNSUPPORTED, then shatter toward camera
scene.frame_set(T_SNIP)
CAMP = cam.matrix_world.translation.copy()
scene.frame_set(FS)
IMPACT = Vector((x2k_c, 0, CAP * 0.95))
cam_right = Vector((1, 0, 0))
for ob in shards:
    c = ob.location.copy()
    gc = Vector(ob["gc"])
    crack = (c - gc) * 0.03 + Vector((0, -0.05, 0))
    key(ob, T_UNS - 1, loc=c, rot=Euler((0, 0, 0)))
    key(ob, T_UNS + 2, loc=c + crack, rot=Euler((rng.uniform(-.03, .03), rng.uniform(-.03, .03), rng.uniform(-.03, .03))))
    key(ob, T_SNIP - 1, loc=c + crack * 1.6)
    # aim past the lens: target point near camera plane, offset sideways/up
    radial = Vector((c.x - IMPACT.x, 0, c.z - IMPACT.z))
    off = Vector((radial.x * rng.uniform(1.0, 2.6) + rng.uniform(-7, 7), 0,
                  radial.z * rng.uniform(0.6, 1.4) + rng.uniform(-3, 5)))
    tgt = CAMP + off + Vector((0, rng.uniform(-6, 8), 0))
    v = (tgt - c)
    nfr = rng.uniform(6, 15)            # frames to reach the camera plane
    vel = v / nfr
    rot_v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * rng.uniform(0.15, 0.45)
    p = c + crack * 1.6
    r = Vector((0, 0, 0))
    for k in range(0, 31, 2):
        f = T_SNIP + k
        if k == 0:
            pos = p + vel * 1.4
        else:
            pos = p + vel * (k + 1.4) + Vector((0, 0, -0.012 * k * k))
        rr = rot_v * (k + 1)
        key(ob, f, loc=pos, rot=Euler(tuple(rr)))
    set_interp(ob, "LINEAR", "location")
    set_interp(ob, "LINEAR", "rotation_euler")

# flash light on the impact
fl = bpy.data.lights.new("flash", "POINT"); fl.color = (1, 1, 1)
flo = bpy.data.objects.new("flash", fl); link(flo)
flo.location = Vector((x2k_c, -4, CAP * 0.7))
for f, e in ((FS, 0), (T_SNIP - 1, 0), (T_SNIP, 0), (T_SNIP + 3, 0), (T_SNIP + 7, 0)):
    fl.energy = e; fl.keyframe_insert("energy", frame=f)

# ------------------------------------------------------------ scan line (3D)
scan_mat = emission_mat("scan", (1, 1, 1, 1), 6.0)
bpy.ops.mesh.primitive_plane_add(size=1)
scan = bpy.context.active_object
scan.data.materials.append(scan_mat)
scan.scale = (0.18, 1, CAP * 1.6)
scan.rotation_euler = (math.pi / 2, 0, 0)
vis(scan, [(FS, False), (T_SCAN0, True), (T_SCAN1 + 1, False)])
key(scan, T_SCAN0, loc=Vector((-3, -1.2, CAP * 0.6)))
key(scan, T_SCAN1, loc=Vector((X_END + 3, -1.2, CAP * 0.6)))
set_interp(scan, "LINEAR", "location")
# soft glow trail plane behind scan line
glow_mat = emission_mat("scan_glow", (1, 1, 1, 1), 1.2)
bpy.ops.mesh.primitive_plane_add(size=1)
glow = bpy.context.active_object
glow.data.materials.append(glow_mat)
glow.scale = (1.2, 1, CAP * 1.5)
glow.rotation_euler = (math.pi / 2, 0, 0)
vis(glow, [(FS, False), (T_SCAN0, True), (T_SCAN1 + 1, False)])
key(glow, T_SCAN0, loc=Vector((-3.7, -1.15, CAP * 0.6)))
key(glow, T_SCAN1, loc=Vector((X_END + 2.3, -1.15, CAP * 0.6)))
set_interp(glow, "LINEAR", "location")

# ------------------------------------------------------------ floor, lights, world
bpy.ops.mesh.primitive_plane_add(size=1200, location=(SENT_C, 0, 0))
bpy.context.active_object.data.materials.append(M_FLOOR)

def area(name, loc, target, energy, size):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy; ld.size = size
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return link(ob)

def sun(name, rot, strength, angle=0.2):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = strength; ld.angle = angle
    ob = bpy.data.objects.new(name, ld)
    ob.rotation_euler = Euler(tuple(math.radians(a) for a in rot))
    return link(ob)

sun("key", (62, 0, -38), 2.6)       # front-left, high
sun("fill", (75, 0, 30), 0.9)
sun("rim", (-60, 0, 160), 4.0)      # from behind
sun("top", (10, 0, 0), 0.8)

world = bpy.data.worlds.new("w"); scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wn["Background"].inputs["Color"].default_value = GRAPHITE
wn["Background"].inputs["Strength"].default_value = 1.0

# ------------------------------------------------------------ HUD (camera-parented, flat, emissive)
HD = 8.0
UPX = HFOV_W * HD / W   # world units per pixel at HUD depth
E_WHITE = emission_mat("h_white", WHITE)
E_GREY = emission_mat("h_grey", hexlin("a8a8ad"))
E_DIM = emission_mat("h_dim", hexlin("6e6e74"))
E_RULE = emission_mat("h_rule", hexlin("8e8e93"))
E_RED = emission_mat("h_red", RED, 1.0)
E_SCRIM = emission_mat("h_scrim", (0, 0, 0, 1), 1.0)

def hpos(px, py, z=0.0):
    return Vector(((px - W / 2) * UPX, (H / 2 - py) * UPX, -HD + z))

def hparent(ob):
    ob.parent = cam
    link(ob)
    return ob

def htext(body, px, py, size_px, fnt, mat, align="LEFT", track=1.0):
    cu = bpy.data.curves.new("ht", "FONT")
    cu.body = body; cu.font = fnt; cu.size = size_px * UPX; cu.align_x = align
    cu.space_character = track
    cu.materials.append(mat)
    ob = bpy.data.objects.new("ht", cu)
    ob.location = hpos(px, py)
    return hparent(ob)

def rect(x0, y0, x1, y1, mat, z=0.0):
    me = bpy.data.meshes.new("r")
    me.from_pydata([hpos(x0, y0, z) - hpos(0, 0, 0), hpos(x1, y0, z) - hpos(0, 0, 0),
                    hpos(x1, y1, z) - hpos(0, 0, 0), hpos(x0, y1, z) - hpos(0, 0, 0)], [], [(0, 1, 2, 3)])
    me.materials.append(mat)
    ob = bpy.data.objects.new("r", me)
    ob.location = hpos(0, 0, 0)
    return hparent(ob)

def grow_line(x0, y0, x1, y1, w, mat, f0, f1, hide_at=None):
    """rule growing from (x0,y0) toward (x1,y1)."""
    a = Vector((x0, y0)); b = Vector((x1, y1)); d = b - a
    L = d.length
    me = bpy.data.meshes.new("gl")
    me.from_pydata([Vector((0, -w / 2 * UPX, 0)), Vector((L * UPX, -w / 2 * UPX, 0)),
                    Vector((L * UPX, w / 2 * UPX, 0)), Vector((0, w / 2 * UPX, 0))], [], [(0, 1, 2, 3)])
    me.materials.append(mat)
    ob = bpy.data.objects.new("gl", me)
    ob.location = hpos(x0, y0)
    ob.rotation_euler = (0, 0, math.atan2(-d.y, d.x))
    hparent(ob)
    key(ob, f0, scale=(0.001, 1, 1)); key(ob, f1, scale=(1, 1, 1))
    vv = [(FS, False), (f0, True)]
    if hide_at:
        vv.append((hide_at, False))
    vis(ob, vv)
    return ob

def pop(ob, f0, f_off=None, slide=0.0):
    """pop in (scale overshoot) at f0, hide at f_off."""
    vv = [(FS, False), (f0, True)]
    if f_off:
        vv.append((f_off, False))
    vis(ob, vv)
    loc = ob.location.copy()
    key(ob, f0, loc=loc + Vector((slide * UPX, 0, 0)))
    key(ob, f0 + 4, loc=loc)

def logo(px, py_center, h_px):
    mat, img = image_mat("logo_flatkey", LOGO)
    iw, ih = img.size
    w = h_px * iw / ih
    o = hpos(0, 0)
    y0, y1 = py_center - h_px / 2, py_center + h_px / 2
    me = bpy.data.meshes.new("logo")
    me.from_pydata([hpos(px - w / 2, y1) - o, hpos(px + w / 2, y1) - o, hpos(px + w / 2, y0) - o, hpos(px - w / 2, y0) - o],
                   [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = c
    me.materials.append(mat)
    ob = bpy.data.objects.new("logo", me)
    ob.location = o
    return hparent(ob)

ML = 96
RULE = 1.5
# role tags (top-left)
g1 = []
g1.append(htext("WRITER", ML, 112, 46, F_SEMI, E_WHITE, track=1.15))
g1.append(htext("·  model A", ML + 212, 112, 46, F_MED, E_GREY))
for o in g1:
    pop(o, T_WRITER, T_AUD - 3, slide=-30)
r1 = grow_line(ML, 136, ML + 500, 136, RULE, E_RULE, T_WRITER, T_WRITER + 8, hide_at=T_AUD - 3)
g2 = []
g2.append(htext("AUDITOR", ML, 112, 46, F_SEMI, E_WHITE, track=1.15))
g2.append(htext("·  model B", ML + 250, 112, 46, F_MED, E_GREY))
for o in g2:
    pop(o, T_AUD, T_SNIP, slide=-30)
grow_line(ML, 136, ML + 540, 136, RULE, E_RULE, T_AUD, T_AUD + 8, hide_at=T_SNIP)

# flatkey routing diagram (top centre)
LX, LY, LH = 960, 100, 110
lg = logo(LX, LY, LH)
pop(lg, T_FLAT - 4, T_UNS + 14)
fk = htext("FLATKEY", LX, LY + 86, 24, F_SEMI, E_GREY, align="CENTER", track=1.3)
pop(fk, T_FLAT - 4, T_UNS + 14)
grow_line(LX - 4, LY + 100, 680, 250, 2, E_RULE, T_FLAT, T_FLAT + 7, hide_at=T_UNS + 14)
grow_line(LX + 4, LY + 100, 1240, 250, 2, E_WHITE, T_FLAT, T_FLAT + 7, hide_at=T_UNS + 14)
ta = htext("model A", 680, 296, 38, F_MED, E_GREY, align="CENTER")
tb = htext("model B", 1240, 296, 38, F_SEMI, E_WHITE, align="CENTER")
for o in (ta, tb):
    pop(o, T_FLAT + 6, T_UNS + 14)
na = htext("WRITER", 680, 330, 20, F_SEMI, E_DIM, align="CENTER", track=1.3)
nb = htext("AUDITOR", 1240, 330, 20, F_SEMI, E_GREY, align="CENTER", track=1.3)
for o in (na, nb):
    pop(o, T_FLAT + 8, T_UNS + 14)

# scan readout
sc = htext("CHECKING EVERY CLAIM AGAINST THE INTERVIEW", ML, 1010, 26, F_SEMI, E_GREY, track=1.25)
pop(sc, T_SCAN0, T_SNIP)

# UNSUPPORTED callout anchored to 2,000
scene.frame_set(T_UNS + 4)
bpy.context.view_layer.update()
def scr(co):
    v = world_to_camera_view(scene, cam, Vector(co))
    return (v.x * W, (1 - v.y) * H)
ax, ay = scr((x2k_c, -0.3, CAP * 1.02))
print("2k anchor at UNS", ax, ay)
UX, UY = ax - 260, max(ay - 130, 420)
u1 = htext("UNSUPPORTED", UX, UY, 62, F_SEMI, E_RED, track=1.12)
u2 = htext("INTAKE SAID: 600", UX, UY + 58, 38, F_SEMI, E_WHITE, track=1.12)
ur = grow_line(UX, UY + 16, UX + 520, UY + 16, 2, E_RED, T_UNS, T_UNS + 5, hide_at=T_600 - 6)
pop(u1, T_UNS, T_600 - 6, slide=-40)
pop(u2, T_UNS + 3, T_600 - 6, slide=-40)
# after camera push: re-anchor the callout higher-left, persistent until the snip
scene.frame_set(T_600 + 4)
ax2, ay2 = scr((x2k_c, -0.3, -0.2))
print("2k left anchor at 600", ax2, ay2)
VX, VY = ax2, min(ay2 + 70, 960)
v1 = htext("UNSUPPORTED", VX, VY, 56, F_SEMI, E_RED, align="CENTER", track=1.12)
v2 = htext("INTAKE SAID: 600", VX, VY + 52, 36, F_SEMI, E_WHITE, align="CENTER", track=1.12)
vis(v1, [(FS, False), (T_600 - 6, True), (T_SNIP, False)])
vis(v2, [(FS, False), (T_600 - 6, True), (T_SNIP, False)])

# TRUE + and still worth funding
scene.frame_set(T_TRUE)
bx, by = scr((mn2.x + w6 / 2, -0.3, CAP * 1.05))
print("600 anchor at TRUE", bx, by)
tr = htext("TRUE", bx, max(by - 40, 200), 66, F_SEMI, E_WHITE, align="CENTER", track=1.25)
pop(tr, T_TRUE)
trl = grow_line(bx - 90, max(by - 40, 200) + 22, bx + 90, max(by - 40, 200) + 22, 2, E_WHITE, T_TRUE, T_TRUE + 5)
fund = htext("and still worth funding", W / 2, 920, 128, F_BOLD, E_WHITE, align="CENTER")
pop(fund, T_FUND)
fund_loc = fund.location.copy()
key(fund, T_FUND, loc=fund_loc + Vector((0, -40 * UPX, 0)), scale=(1.0, 1.0, 1))
key(fund, T_FUND + 3, loc=fund_loc + Vector((0, 4 * UPX, 0)))
key(fund, T_FUND + 6, loc=fund_loc)

# ------------------------------------------------------------ render settings
scene.render.engine = "BLENDER_EEVEE"
ee = scene.eevee
def tryset(obj, attr, val):
    try:
        setattr(obj, attr, val)
    except Exception as ex:
        print("skip", attr, ex)
tryset(ee, "taa_render_samples", 16)
tryset(ee, "use_raytracing", False)
tryset(ee, "use_shadows", True)
tryset(scene.render, "use_motion_blur", True)
tryset(scene.render, "motion_blur_shutter", 0.5)
tryset(ee, "motion_blur_steps", 1)
tryset(ee, "motion_blur_depth_scale", 100)
tryset(ee, "motion_blur_max", 64)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.resolution_x = W
scene.render.resolution_y = H
scene.render.fps = 24
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "seqD.blend"))

if MODE == "test":
    frames = [int(x) for x in argv[1].split(",")]
    pct = int(argv[2]) if len(argv) > 2 else 50
    scene.render.resolution_percentage = pct
    import time
    for f in frames:
        scene.frame_set(f)
        scene.render.filepath = os.path.join(WORK, f"test_{f}.png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print("RENDERED", f, round(time.time() - t0, 2))
elif MODE == "final":
    scene.render.resolution_percentage = 100
    scene.frame_start = int(argv[1]) if len(argv) > 1 else FS
    scene.frame_end = int(argv[2]) if len(argv) > 2 else FE
    scene.frame_step = int(argv[3]) if len(argv) > 3 else 1
    scene.render.filepath = FRAMES
    scene.render.use_file_extension = True
    scene.render.use_overwrite = True
    bpy.ops.render.render(animation=True)
