# Sequence B: film 16.30-33.90 s -> global frames 391-813.
# Run: Blender -b -P scene.py -- test 400,520,700   |   -- final
import bpy, math, sys, os, time
from mathutils import Vector, Quaternion, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if argv else "test"
WORK = "/Users/ac/Code/aws-hackathon/video/kinetic/seqB"
FRAMES = "/Users/ac/Code/aws-hackathon/video/kinetic/frames/f_#####"
F0, F1 = 391, 813
W, H = 1920, 1080

FB = "/Library/Fonts/SF-Pro-Display-Black.otf"
FBO = "/Library/Fonts/SF-Pro-Display-Bold.otf"
FTS = "/Library/Fonts/SF-Pro-Text-Semibold.otf"

def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def hexlin(h):
    h = h.lstrip("#")
    return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)
def fr(t):  # film seconds -> frame
    return t * 24.0

scene = bpy.context.scene
for o in list(scene.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = scene.collection
def link(ob):
    coll.objects.link(ob); return ob
def font(p):
    return bpy.data.fonts.load(p, check_existing=True)

def principled(name, color, rough=0.35, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    try: b.inputs["Specular IOR Level"].default_value = spec
    except KeyError: pass
    return m
def emission_mat(name, color, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = color
    e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    return m, e

M_WHITE = principled("type_white", hexlin("f2f2f4"), rough=0.3)
M_GREY = principled("type_grey", (0.30, 0.30, 0.31, 1), rough=0.4)
M_GREY2 = principled("type_grey2", (0.16, 0.16, 0.17, 1), rough=0.45)
M_FLOOR = principled("floor", hexlin("242426"), rough=0.62, spec=0.18)
M_HUD, E_HUD = emission_mat("hud", (0.92, 0.92, 0.93, 1), 0.0)
M_RULE, E_RULE = emission_mat("rule", (0.55, 0.55, 0.57, 1), 0.0)

def make_text(body, fnt, size, name, mat, align="CENTER", ext=None, bev=None, spacing=1.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body; cu.font = font(fnt); cu.size = size
    cu.extrude = size * 0.075 if ext is None else ext
    cu.bevel_depth = size * 0.007 if bev is None else bev
    cu.bevel_resolution = 2
    cu.align_x = align; cu.space_character = spacing
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    return link(ob)
def bounds(ob):
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))
def width_of(ob):
    mn, mx = bounds(ob); return mx.x - mn.x
def fit(ob, w):  # resize text so its width == w
    s = w / width_of(ob)
    cu = ob.data
    cu.size *= s; cu.extrude *= s; cu.bevel_depth *= s

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(u): u = clamp(u); return u * u * (3 - 2 * u)
def ease_io(u): u = clamp(u); return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
def ease_in(u): u = clamp(u); return u * u
def ease_out(u): u = clamp(u); return 1 - (1 - u) ** 3
def bump(t, t0, n=5, amp=1.0):  # damped overshoot after impact
    s = t - t0
    if s < 0 or s > n * 3: return 0.0
    return amp * math.sin(math.pi * s / n) * math.exp(-s / n)
def slam_in(t, land, dur):  # returns (visible, progress 0..1 accelerating into land)
    if t < land - dur: return False, 0.0
    return True, ease_in((t - (land - dur)) / dur)

HIDE = (1e-4, 1e-4, 1e-4)

# ---------------------------------------------------------------- times (frames)
T_BIG, T_FND = fr(16.5), fr(16.92)
T_PRO, T_GRA, T_WRI = fr(18.62), fr(19.3), fr(19.72)
CUT_B = 500
T_TINY, T_NONP = fr(20.9), fr(21.26)
CUT_C = 550
T_WHO, T_STILL, T_AWAKE = fr(23.1), fr(24.56), fr(24.78)
LAMP_OFF = 100000
T_RUSH, T_GM, T_HUD = fr(27.4), fr(28.44), fr(29.7)

anims = []  # (fn(t) -> None applies values, list of (datablock, path))

# ================================================================ SET A  (origin)
WA = 19.0
fnd = make_text("FOUNDATIONS", FB, 3.0, "fnd", M_WHITE); fit(fnd, WA)
big = make_text("BIG", FB, 8.0, "big", M_WHITE); fit(big, WA)
hF = bounds(fnd)[1].z
ZB = hF + 0.55
big.location = (0, 0, ZB)
capB = bounds(big)[1].z - ZB
print("A: hF", hF, "capB", capB)

def a_big(t):
    vis, p = slam_in(t, T_BIG, 6)
    if not vis: big.scale = HIDE; return
    big.location = (0, 0, ZB + 18 * (1 - p))
    sq = bump(t, T_BIG, 4, 0.10)
    big.scale = (1 + sq * 0.5, 1, 1 - sq)
anims.append((a_big, [(big, "location"), (big, "scale")]))

def a_fnd(t):
    vis, p = slam_in(t, T_FND, 6)
    if not vis: fnd.scale = HIDE; return
    fnd.location = (0, 50 * (1 - p) - bump(t, T_FND, 5, 0.9), 0)
    fnd.scale = (1, 1, 1)
anims.append((a_fnd, [(fnd, "location"), (fnd, "scale")]))

XW = WA / 2 + 1.5
SW = 1.15
rows = [("PROFESSIONAL", 2 * SW * 1.32, T_PRO), ("GRANT", SW * 1.32, T_GRA), ("WRITERS", 0.0, T_WRI)]
march = []
for k in range(0, 5):
    for (word, z, tl) in rows:
        mat = M_WHITE if k == 0 else (M_GREY if k < 3 else M_GREY2)
        ob = make_text(word, FBO, SW, f"m_{word}_{k}", mat, align="LEFT")
        march.append((ob, k, z, tl + 2.0 * k))
def mk_march(ob, k, z, tl):
    def f(t):
        vis, p = slam_in(t, tl, 6)
        if not vis: ob.scale = HIDE; return
        ob.scale = (1, 1, 1)
        x0 = XW + 3.6 * k
        y0 = 9.0 * k
        # step-march toward camera after formation is complete
        ph = max(0.0, (t - T_PRO) / 6.0)
        step = (math.floor(ph) + smooth(ph - math.floor(ph))) * 0.32 if k > 0 else 0.0
        hop = 0.10 * abs(math.sin(math.pi * ph)) if k > 0 else 0.0
        ob.location = (x0 + 16 * (1 - p), y0 + 10 * (1 - p) - step - bump(t, tl, 5, 0.35), z + hop)
    return f
for (ob, k, z, tl) in march:
    anims.append((mk_march(ob, k, z, tl), [(ob, "location"), (ob, "scale")]))

# ================================================================ SET B  (x = 300)
XB = 300.0
tiny = make_text("tiny", FB, 0.85, "tiny", M_WHITE, align="LEFT")
nonp = make_text("nonprofits", FB, 0.85, "nonp", M_WHITE, align="LEFT")
wt, wn = width_of(tiny), width_of(nonp)
gap = 0.85 * 0.26
xs = XB - (wt + gap + wn) / 2
def mk_pop(ob, x, land, y=0.0, z=0.0, h=1.4):
    def f(t):
        vis, p = slam_in(t, land, 4)
        if not vis: ob.scale = HIDE; return
        s = t - land
        hop = h * 0.22 * abs(math.sin(math.pi * s / 5)) * math.exp(-s / 5) if s > 0 else 0
        ob.location = (x, y, z + h * (1 - p) + hop)
        sq = bump(t, land, 3, 0.18)
        ob.scale = (1 + sq * 0.6, 1, 1 - sq)
    return f
anims.append((mk_pop(tiny, xs, T_TINY, z=0.85 * 0.24), [(tiny, "location"), (tiny, "scale")]))
anims.append((mk_pop(nonp, xs + wt + gap, T_NONP, z=0.85 * 0.24), [(nonp, "location"), (nonp, "scale")]))

# ================================================================ SET C  (x = 600)
XC = 600.0
SC = 0.40
words_c = [("WHOEVER’S", T_WHO), ("STILL", T_STILL), ("AWAKE", T_AWAKE)]
objs_c = []
for w, tl in words_c:
    objs_c.append((make_text(w, FBO, SC, "c_" + w[:4], M_WHITE, align="LEFT"), tl))
gc = SC * 0.30
tot = sum(width_of(o) for o, _ in objs_c) + gc * 2
x = XC - tot / 2
for o, tl in objs_c:
    xo = x
    anims.append((mk_pop(o, xo, tl, h=0.5), [(o, "location"), (o, "scale")]))
    x += width_of(o) + gc

# ================================================================ SET D  (x = 600, y = 60)
YD = 60.0
WD = 30.0
gm = make_text("GRANTMOTHER", FB, 4.0, "gm", M_WHITE); fit(gm, WD)
capD = bounds(gm)[1].z
def a_gm(t):
    vis, p = slam_in(t, T_GM, 6)
    if not vis: gm.scale = HIDE; return
    gm.location = (XC, YD, 16 * (1 - p))
    sq = bump(t, T_GM, 4, 0.12)
    gm.scale = (1 + sq * 0.4, 1, 1 - sq)
anims.append((a_gm, [(gm, "location"), (gm, "scale")]))

hud = make_text("A GRANT OFFICE THAT SMALL NONPROFITS SHARE", FTS, 1.0, "hud", M_HUD,
                ext=0.0, bev=0.0, spacing=1.12)
fit(hud, WD * 0.62)
ZH = capD + 1.5
hud_y = YD - 0.6
def a_hud(t):
    u = ease_out((t - T_HUD) / 7)
    hud.scale = (1, 1, 1) if t >= T_HUD - 1 else HIDE
    hud.location = (XC, hud_y, ZH - 0.35 * (1 - u))
anims.append((a_hud, [(hud, "location"), (hud, "scale")]))
def a_hud_e(t):
    E_HUD.inputs["Strength"].default_value = 1.0 * smooth((t - T_HUD) / 6)
    E_RULE.inputs["Strength"].default_value = 1.0 * smooth((t - T_HUD + 2) / 6)
anims.append((a_hud_e, [(E_HUD.inputs["Strength"], "default_value"), (E_RULE.inputs["Strength"], "default_value")]))
# thin rules either side of HUD line
hw = WD * 0.62 / 2
hud_cap = 0.72 * hud.data.size
rules = []
for side in (-1, 1):
    bpy.ops.mesh.primitive_plane_add(size=1)
    r = bpy.context.active_object
    r.data.materials.append(M_RULE)
    r.rotation_euler = (math.pi / 2, 0, 0)
    rules.append((r, side))
def mk_rule(r, side):
    def f(t):
        u = ease_out((t - T_HUD - 2) / 10)
        L = (WD / 2 - hw - 0.6) * max(u, 1e-4)
        r.scale = (L, 0.035, 1) if t >= T_HUD else HIDE
        r.location = (XC + side * (hw + 0.6 + L / 2), hud_y, ZH + hud_cap * 0.42)
    return f
for r, side in rules:
    anims.append((mk_rule(r, side), [(r, "location"), (r, "scale")]))

# ================================================================ floor
bpy.ops.mesh.primitive_plane_add(size=6000, location=(300, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(M_FLOOR)

# ================================================================ lights
def mklight(name, kind, loc, target, size=2.0):
    ld = bpy.data.lights.new(name, kind)
    if kind == "AREA": ld.size = size
    else: ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return link(ob)
cA = Vector((0, 0, 4))
LA = [mklight("A_key", "AREA", (-18, -20, 20), cA, 8), mklight("A_front", "AREA", (6, -30, 6), cA, 10),
      mklight("A_rim", "AREA", (6, 14, 14), cA, 6), mklight("A_rim2", "AREA", (20, 10, 5), (14, 0, 2), 4)]
EA = [5200, 5200, 9000, 2500]
cB = Vector((XB, 0, 0.3))
LB = [mklight("B_top", "AREA", (XB - 3, -6, 9), cB, 6), mklight("B_rim", "AREA", (XB + 2, 6, 4), cB, 3)]
EB = [1500, 500]
lamp = mklight("C_lamp", "SPOT", (XC - 0.4, -1.6, 3.4), (XC, 0.3, 0.0), 0.12)
lamp.data.spot_size = math.radians(58); lamp.data.spot_blend = 0.45
EC = 520
cD = Vector((XC, YD, capD * 0.5))
LD = [mklight("D_key", "AREA", (XC - 22, YD - 26, 22), cD, 10), mklight("D_front", "AREA", (XC + 4, YD - 40, 6), cD, 14),
      mklight("D_rim", "AREA", (XC + 8, YD + 16, 16), cD, 8), mklight("D_rim2", "AREA", (XC - 18, YD + 12, 6), cD, 6)]
ED = [7500, 7000, 12000, 4000]

def a_lights(t):
    for l, e in zip(LA, EA): l.data.energy = e if t < CUT_B else 0.0
    for l, e in zip(LB, EB): l.data.energy = e if CUT_B <= t < CUT_C else 0.0
    # lamp: click-on flicker at cut, flicker-off at LAMP_OFF
    if t < CUT_C or t >= LAMP_OFF + 6: k = 0.0
    elif t < CUT_C + 4: k = [0.0, 1.0, 0.15, 1.0][int(t - CUT_C)]
    elif t >= LAMP_OFF: k = [0.4, 1.0, 0.1, 0.6, 0.0, 0.0][int(t - LAMP_OFF)]
    else: k = 1.0
    lamp.data.energy = EC * k
    kd = (0.25 * smooth((t - T_RUSH - 6) / 12) + 0.75 * smooth((t - (T_GM - 3)) / 3)) * (1 + 0.35 * math.exp(-max(0, t - T_GM) / 4) * (t >= T_GM))
    for l, e in zip(LD, ED): l.data.energy = e * kd
anims.append((a_lights, [(l.data, "energy") for l in LA + LB + [lamp] + LD]))

# ================================================================ camera
cd = bpy.data.cameras.new("cam")
cam = link(bpy.data.objects.new("cam", cd))
scene.camera = cam
cam.rotation_mode = "QUATERNION"
cd.sensor_width = 36
cd.dof.use_dof = True
def lerpv(a, b, u): return Vector(a).lerp(Vector(b), u)
def shake(t, t0, amp, n=10):
    s = t - t0
    if s < 0 or s > n: return Vector()
    d = amp * math.exp(-s / (n / 3))
    return Vector((math.sin(s * 2.9) * d, 0, math.cos(s * 3.7) * d * 0.8))

D_DIST = WD * 1.25
def cam_state(t):
    """returns pos, target, lens, fstop, roll_deg"""
    if t < CUT_B:  # A: low monumental push
        u = smooth((t - F0) / (CUT_B - F0))
        pos = lerpv((0.5, -31.0, 0.55), (6.5, -25.0, 1.0), u)
        tgt = lerpv((2.5, 0, 4.6), (5.0, 0, 3.4), u)
        pos += shake(t, T_BIG, 0.35) + shake(t, T_FND, 0.22)
        return pos, tgt, 27, 2.2, -2.5 + 2.0 * u, (0, 0, 2.5)
    if t < CUT_C:  # B: vast empty, slow pull back
        u = smooth((t - CUT_B) / (CUT_C - CUT_B))
        pos = lerpv((XB - 1.2, -13.5, 1.6), (XB - 2.4, -20.0, 2.6), u)
        tgt = lerpv((XB + 0.4, 0, 1.6), (XB + 0.8, 0, 2.2), u)
        return pos, tgt, 35, 2.8, 0.0, (XB, 0, 0.3)
    if t < T_RUSH:  # C: lonely line, slow push
        u = smooth((t - CUT_C) / (T_RUSH - CUT_C))
        pos = lerpv((XC - 1.0, -11.0, 0.85), (XC - 0.3, -9.0, 0.7), u)
        tgt = lerpv((XC, 0, 0.55), (XC, 0, 0.4), u)
        return pos, tgt, 35, 1.8, 0.0, (XC, 0, 0.2)
    # rush + D
    p_end = Vector((XC - 1.2, YD - D_DIST, 1.2))
    t_end = Vector((XC, YD, capD * 0.75))
    if t < T_GM - 1:
        u = ease_io((t - T_RUSH) / (T_GM - 1 - T_RUSH))
        pos = lerpv((XC - 0.3, -9.0, 0.7), p_end, u)
        pos.z += 0.25 * math.sin(math.pi * u) * 0  # keep above the line
        if pos.y < 1.5 and pos.y > -1.5: pos.z = max(pos.z, 0.55)
        tgt = lerpv((XC, 0, 0.4), t_end, smooth(u * 1.6))
        fd = (Vector(tgt) - pos).length
        return pos, tgt, 35 - 7 * math.sin(math.pi * u), 4.0, 3.0 * math.sin(math.pi * u), tgt
    u = smooth((t - T_GM) / (F1 - T_GM))
    pos = p_end + Vector((1.8, 3.0, 0.5)) * u + shake(t, T_GM, 0.45, 12)
    tgt = t_end + Vector((0.4, 0, 0.3)) * u
    return pos, tgt, 35, 4.0, -1.5 * u, (XC, YD, capD * 0.6)

prevq = [None]
def a_cam(t):
    pos, tgt, lens, fs, roll, foc = cam_state(t)
    cam.location = pos
    q = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y")
    q = q @ Quaternion((0, 0, 1), math.radians(roll))
    if prevq[0] is not None and q.dot(prevq[0]) < 0: q.negate()
    prevq[0] = q.copy()
    cam.rotation_quaternion = q
    cd.lens = lens
    cd.dof.aperture_fstop = fs
    cd.dof.focus_distance = (Vector(foc) - Vector(pos)).length
anims.append((a_cam, [(cam, "location"), (cam, "rotation_quaternion"), (cd, "lens"),
                      (cd.dof, "aperture_fstop"), (cd.dof, "focus_distance")]))

# ================================================================ bake
times = sorted(set([f + h for f in range(F0 - 4, F1 + 4) for h in (0.0, 0.5)]))
for t in times:
    for fn, paths in anims:
        fn(t)
        for db, p in paths:
            db.keyframe_insert(p, frame=t)
def set_linear(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return
    try:
        fcs = ad.action.fcurves
    except AttributeError:
        fcs = [fc for layer in ad.action.layers for strip in layer.strips
               for cb in strip.channelbags for fc in cb.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
for idb in list(bpy.data.objects) + list(bpy.data.lights) + list(bpy.data.cameras) + list(bpy.data.materials):
    set_linear(idb)
    if hasattr(idb, "node_tree") and idb.node_tree: set_linear(idb.node_tree)

# ================================================================ world + render
world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = hexlin("1c1c1e")
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
r = scene.render
r.engine = "BLENDER_EEVEE"
ee = scene.eevee
def tryset(o, a, v):
    try: setattr(o, a, v)
    except Exception as e: print("skip", a, e)
tryset(ee, "taa_render_samples", int(argv[2]) if len(argv) > 2 else 12)
tryset(ee, "use_raytracing", False)
tryset(r, "use_motion_blur", True)
tryset(r, "motion_blur_shutter", 0.5)
tryset(r, "motion_blur_position", "START")
tryset(ee, "motion_blur_steps", 1)
tryset(ee, "use_shadows", True)
tryset(ee, "shadow_ray_count", 1)
tryset(ee, "shadow_step_count", 4)
tryset(ee, "shadow_resolution_scale", 0.5)
scene.view_settings.view_transform = "Standard"
r.resolution_x, r.resolution_y = W, H
r.resolution_percentage = 100
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGB"
r.image_settings.color_depth = "8"
scene.frame_start, scene.frame_end = F0, F1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "seqB.blend"))

if MODE == "final":
    r.filepath = FRAMES
    r.use_file_extension = True
    r.use_overwrite = True
    bpy.ops.render.render(animation=True)
else:
    fl = [int(x) for x in (argv[1] if len(argv) > 1 else "400,520,700").split(",")]
    for f in fl:
        scene.frame_set(f)
        r.filepath = os.path.join(WORK, f"test_{f:05d}.png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"TIME frame {f}: {time.time() - t0:.2f}s")
