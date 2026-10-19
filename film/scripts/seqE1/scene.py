# Sequence E1: corridor of type, film 78.20-95.20 s, global frames 1878-2285.
# Run: Blender -b -P scene.py -- test <pct> f1,f2,...   |   Blender -b -P scene.py -- final
import bpy, math, os, sys
from mathutils import Vector

WORK = "/Users/ac/Code/aws-hackathon/video/kinetic/seqE1"
LOGO = "/Users/ac/Code/aws-hackathon/video/assets/logos/final"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if argv else "test"
FS, FE = 1878, 2285
W, H = 1920, 1080
FONT_BLACK = "/Library/Fonts/SF-Pro-Display-Black.otf"
FONT_BOLD = "/Library/Fonts/SF-Pro-Display-Bold.otf"
FONT_SEMI = "/Library/Fonts/SF-Pro-Text-Semibold.otf"

def F(t):
    return t * 24.0

def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hexlin(h):
    h = h.lstrip("#")
    return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)

GRAPHITE = hexlin("1c1c1e")
bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"

scene = bpy.context.scene
for o in list(scene.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = scene.collection

def link(ob):
    coll.objects.link(ob)
    return ob

def principled(name, color, rough=0.35, emit=None, es=0.0, spec=0.5):
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
        b.inputs["Emission Strength"].default_value = es
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

M_WHITE = principled("type_white", hexlin("f2f2f4"), rough=0.3)
M_GREY = principled("type_grey", hexlin("8e8e93"), rough=0.35)
M_FLOOR = principled("floor", hexlin("242426"), rough=0.22, spec=0.6)
M_PILLAR = principled("pillar", hexlin("2a2a2d"), rough=0.5)
M_TILE = principled("tile", hexlin("3a3a3e"), rough=0.4)
E_WHITE = emission_mat("e_white", (1, 1, 1, 1), 1.0)
E_LINE = emission_mat("e_line", (1, 1, 1, 1), 6.0)
E_GREY = emission_mat("e_grey", hexlin("9a9aa0"))
E_RULE = emission_mat("e_rule", hexlin("6e6e74"))
E_FLOORRULE = emission_mat("e_floorrule", hexlin("3a3a3e"))

def font(p):
    return bpy.data.fonts.load(p, check_existing=True)
FB, FBO, FS_ = font(FONT_BLACK), font(FONT_BOLD), font(FONT_SEMI)

def empty(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    link(e)
    e.parent = parent
    e.location = loc
    e.rotation_euler = rot
    return e

def text(body, fnt, width=None, height=None, size=1.0, extrude=0.18, bevel=0.02, mat=M_WHITE,
         align="CENTER", spacing=1.0, name="t"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body; cu.font = fnt; cu.size = size
    cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 2
    cu.align_x = align; cu.align_y = "BOTTOM_BASELINE"; cu.space_character = spacing
    ob = bpy.data.objects.new(name, cu)
    cu.materials.append(mat)
    link(ob)
    bpy.context.view_layer.update()
    if width:
        cu.size = size * width / max(ob.dimensions.x, 1e-4)
    elif height:
        cu.size = size * height / max(ob.dimensions.y, 1e-4)
    return ob

def stand(ob, parent, loc):
    """Text stands upright, facing local -Y of the parent."""
    ob.parent = parent
    ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = loc
    return ob

def box(name, size, loc, mat, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (size[0], size[1], size[2])
    ob.data.materials.append(mat)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob

def logo_plane(slug, width, parent, loc):
    m, img = image_mat("logo_" + slug, os.path.join(LOGO, slug + "-on-dark.png"))
    w, h = img.size
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    ob = bpy.context.active_object
    ob.name = "logo_" + slug
    ob.data.materials.append(m)
    ob.scale = (width, width * h / w, 1)
    ob.parent = parent
    ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = loc
    return ob

def check(name, s, parent, loc, mat=M_WHITE, th=0.16):
    e = empty(name, parent, loc)
    a, b = 0.42 * s, 0.95 * s
    for nm, ang, ln in (("a", math.radians(135), a), ("b", math.radians(48), b)):
        d = Vector((math.cos(ang), 0, math.sin(ang)))
        c = d * (ln / 2) + Vector((-0.0, 0, 0))
        box(name + nm, (ln + th * s * 0.5, th * s, th * s), c, mat, e, (0, -ang, 0))
    return e

def keys(ob, frame, loc=None, scale=None, rot=None):
    if loc is not None:
        ob.location = loc; ob.keyframe_insert("location", frame=frame)
    if scale is not None:
        ob.scale = scale if hasattr(scale, "__len__") else (scale,) * 3
        ob.keyframe_insert("scale", frame=frame)
    if rot is not None:
        ob.rotation_euler = rot; ob.keyframe_insert("rotation_euler", frame=frame)

def slam(ob, t, back=9.0, up=1.5, s1=None, dur=6):
    """Slam in from depth (local +Y = away from camera), overshoot, settle on t."""
    f = F(t)
    loc = Vector(ob.location)
    sc = Vector(ob.scale) if s1 is None else Vector(s1)
    keys(ob, f - dur - 1, loc=loc + Vector((0, back, up)), scale=sc * 0.0001)
    keys(ob, f - dur, loc=loc + Vector((0, back, up)), scale=sc * 0.35)
    keys(ob, f + 0.5, loc=loc + Vector((0, -0.35, -0.05)), scale=sc * 1.07)
    keys(ob, f + 3, loc=loc, scale=sc)

def drop(ob, t, h=4.0, dur=5):
    """Stamp drop from above, overshoot squash."""
    f = F(t)
    loc = Vector(ob.location)
    sc = Vector(ob.scale)
    keys(ob, f - dur - 1, loc=loc + Vector((0, -1.5, h)), scale=sc * 0.0001)
    keys(ob, f - dur, loc=loc + Vector((0, -1.5, h)), scale=sc * 1.6)
    keys(ob, f + 0.5, loc=loc + Vector((0, 0.1, -0.05)), scale=sc * 0.94)
    keys(ob, f + 3, loc=loc, scale=sc)

def pop(ob, t, dur=4):
    f = F(t)
    sc = Vector(ob.scale)
    keys(ob, f - dur - 1, scale=sc * 0.0001)
    keys(ob, f - dur, scale=sc * 0.2)
    keys(ob, f + 0.5, scale=sc * 1.12)
    keys(ob, f + 3, scale=sc)

def hud(body, width=None, height=0.22, parent=None, loc=(0, 0, 0), align="LEFT", mat=E_GREY):
    t = text(body, FS_, width=width, height=None if width else height, extrude=0.0, bevel=0.0,
             mat=mat, align=align, spacing=1.18, name="hud")
    return stand(t, parent, loc)

# ----------------------------------------------------------------- corridor
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 50, 0))
floor = bpy.context.active_object
floor.scale = (120, 260, 1)
floor.data.materials.append(M_FLOOR)
for y in range(-60, 150, 6):
    for sx in (-1, 1):
        box("pillar", (0.5, 0.5, 9), (sx * 14, y, 4.5), M_PILLAR)
    box("xrule", (26, 0.04, 0.004), (0, y + 3, 0.002), E_FLOORRULE)
for sx in (-1, 1):
    box("lrule", (0.05, 220, 0.004), (sx * 9.5, 45, 0.002), E_RULE)

# ----------------------------------------------------------------- stations
YS = [0, 34, 68, 102]
SX = [-6.0, 6.0, -6.0, 0.0]
ROT = [math.radians(-10), math.radians(10), math.radians(-10), 0.0]
st = [empty(f"station{i}", None, (SX[i], YS[i], 0), (0, 0, ROT[i])) for i in range(4)]

def lights(i):
    c = Vector((SX[i], YS[i], 2.0))
    for nm, off, en, sz in (("key", (-7, -10, 9), 3200, 5), ("fill", (8, -12, 3), 1300, 6),
                            ("rim", (3, 8, 7), 4200, 3), ("top", (0, -2, 11), 900, 4)):
        ld = bpy.data.lights.new(nm + str(i), "AREA")
        ld.energy = en; ld.size = sz
        ob = bpy.data.objects.new(nm + str(i), ld)
        ob.location = c + Vector(off)
        ob.rotation_euler = (c - ob.location).to_track_quat("-Z", "Y").to_euler()
        link(ob)
for i in range(4):
    lights(i)

# ---- Station 1: PromptQL / SHARED WIKI / approved
s = st[0]
t_lessons = stand(text("LESSONS", FBO, width=3.0, extrude=0.12, bevel=0.012, align="LEFT", name="lessons"), s, (-4.6, 0, 3.15))
slam(t_lessons, 78.4, back=7)
lg1 = logo_plane("promptql", 3.3, s, (-2.95, 0.05, 4.75))
pop(lg1, 79.96)
t_shared = stand(text("SHARED", FB, width=5.0, extrude=0.55, bevel=0.04, align="LEFT", name="shared"), s, (-4.6, 0, 0.02))
bpy.context.view_layer.update()
x_wiki = -4.6 + t_shared.dimensions.x + 0.45
t_wiki = stand(text("WIKI", FB, height=t_shared.dimensions.y, extrude=0.55, bevel=0.04, align="LEFT", name="wiki"), s, (x_wiki, 0, 0.02))
bpy.context.view_layer.update()
t_wiki.data.size = t_shared.data.size
slam(t_shared, 79.64)
slam(t_wiki, 80.94)
right_edge = x_wiki + t_wiki.dimensions.x
rule1 = box("rule1", (right_edge + 4.6, 0.01, 0.018), ((right_edge - 4.6) / 2, 0, 2.95), E_RULE, s)
pop(rule1, 78.6)
h1 = hud("FOUNDER APPROVES EVERY LEARNING", width=4.4, parent=s, loc=(right_edge, 0, 3.15), align="RIGHT", mat=E_WHITE)
pop(h1, 82.44, dur=3)
stamp = empty("stamp", s, (right_edge - 2.2, -1.2, 4.35), (0, math.radians(7), 0))
sw, shh = 4.3, 1.15
for nm, sz, lc in (("t", (sw, 0.12, 0.1), (0, 0, shh / 2)), ("b", (sw, 0.12, 0.1), (0, 0, -shh / 2)),
                   ("l", (0.1, 0.12, shh + 0.1), (-sw / 2, 0, 0)), ("r", (0.1, 0.12, shh + 0.1), (sw / 2, 0, 0))):
    box("stampframe" + nm, sz, lc, M_WHITE, stamp)
t_ap = stand(text("APPROVED", FB, width=2.9, extrude=0.14, bevel=0.012, align="LEFT", name="approved"), stamp, (-1.05, 0, -0.33))
check("stampcheck", 0.62, stamp, (-1.55, 0, -0.32))
drop(stamp, 82.72)

# ---- Station 2: n8n / DEADLINES / calendar ticks
s = st[1]
lg2 = logo_plane("n8n", 2.6, s, (-3.4, 0.05, 4.95))
pop(lg2, 84.02)
t_dl = stand(text("DEADLINES", FB, width=9.4, extrude=0.55, bevel=0.04, align="CENTER", name="deadlines"), s, (0, 0, 0.02))
slam(t_dl, 84.76)
h2 = hud("KEEPS THE DEADLINES", width=3.0, parent=s, loc=(4.7, 0, 4.55), align="RIGHT")
pop(h2, 84.34, dur=3)
rule2 = box("rule2", (9.4, 0.01, 0.018), (0, 0, 4.35), E_RULE, s)
pop(rule2, 84.02)
for k in range(6):
    x = -3.9 + k * 1.56
    tile = empty(f"tile{k}", s, (x, -0.2, 2.6))
    box(f"tilebody{k}", (1.2, 0.22, 1.25), (0, 0, 0.62), M_TILE, tile)
    box(f"tiletop{k}", (1.2, 0.26, 0.22), (0, 0, 1.28), M_WHITE, tile)
    for r in (-0.3, 0.3):
        box(f"tilering{k}", (0.07, 0.3, 0.2), (r, -0.02, 1.42), M_GREY, tile)
    pop(tile, 84.1 + k * 0.08)
    ck = check(f"tick{k}", 0.62, tile, (-0.12, -0.2, 0.3))
    pop(ck, 84.85 + k * 0.12, dur=3)

# ---- Station 3: flexprice / EVERY MATCH, METERED / counter
s = st[2]
lg3 = logo_plane("flexprice", 3.4, s, (-3.0, 0.05, 4.85))
pop(lg3, 85.96)
t_met = stand(text("METERED", FB, width=6.8, extrude=0.55, bevel=0.04, align="LEFT", name="metered"), s, (-4.9, 0, 0.02))
slam(t_met, 86.22)
t_em = stand(text("EVERY MATCH,", FBO, width=4.6, extrude=0.2, bevel=0.015, align="LEFT", name="everymatch"), s, (-4.9, 0, 2.45))
slam(t_em, 86.74, back=6)
rule3 = box("rule3", (10.4, 0.01, 0.018), (0.3, 0, 4.25), E_RULE, s)
pop(rule3, 85.96)
ctr = empty("counter", s, (3.75, -0.5, 0.02))
cw, chh = 2.3, 3.1
for nm, sz, lc in (("t", (cw, 0.25, 0.1), (0, 0, chh)), ("b", (cw, 0.25, 0.1), (0, 0, 0.05)),
                   ("l", (0.1, 0.25, chh), (-cw / 2, 0, chh / 2)), ("r", (0.1, 0.25, chh), (cw / 2, 0, chh / 2))):
    box("ctrframe" + nm, sz, lc, M_WHITE, ctr)
pop(ctr, 86.3)
hc = hud("MATCHES", width=1.35, parent=s, loc=(3.75 - 0.6, -0.5, 3.4), align="LEFT")
pop(hc, 86.3)
DT = [86.74, 87.32, 87.85, 999]
for d in range(3):
    dg = stand(text(str(d + 1), FB, height=2.2, extrude=0.45, bevel=0.03, align="CENTER", name=f"digit{d}"), ctr, (0, -0.1, 0.45))
    sc = Vector(dg.scale)
    f0, f1 = F(DT[d]), F(DT[d + 1])
    keys(dg, f0 - 3, scale=sc * 0.0001)
    keys(dg, f0 - 2, scale=sc * 0.0001, loc=Vector((0, -0.1, 1.6)))
    keys(dg, f0 + 0.5, scale=sc * 1.12, loc=Vector((0, -0.25, 0.4)))
    keys(dg, f0 + 3, scale=sc, loc=Vector((0, -0.1, 0.45)))
    if d < 2:
        keys(dg, f1 - 2, scale=sc, loc=Vector((0, -0.1, 0.45)))
        keys(dg, f1 - 1, scale=sc * 0.0001, loc=Vector((0, -0.1, -0.6)))

# ---- Station 4: askthew / line / AGENTS DO | HUMANS DECIDE
s = st[3]
lg4 = logo_plane("askthew", 1.25, s, (0, 0.05, 4.55))
pop(lg4, 88.78)
line = empty("line", s, (0, -0.3, 0))
box("linebar", (0.07, 0.07, 1.0), (0, 0, 0.5), E_LINE, line)
line.scale = (1, 1, 3.75)
keys(line, F(90.42) - 5, scale=(1, 1, 0.0001), loc=Vector((0, -0.3, 3.75)))
keys(line, F(90.42) - 1, scale=(1, 1, 3.75), loc=Vector((0, -0.3, 0)))
keys(line, F(90.42) + 1, scale=(1.6, 1, 3.75))
keys(line, F(90.42) + 4, scale=(1, 1, 3.75))
WW = 4.3
t_ag = stand(text("AGENTS", FB, width=WW, extrude=0.45, bevel=0.035, align="RIGHT", mat=M_GREY, name="agents"), s, (-0.55, 0, 1.75))
t_do = stand(text("DO", FB, height=t_ag.dimensions.y, extrude=0.45, bevel=0.035, align="RIGHT", mat=M_GREY, name="do"), s, (-0.55, 0, 0.02))
t_do.data.size = t_ag.data.size
t_hu = stand(text("HUMANS", FB, width=WW, extrude=0.45, bevel=0.035, align="LEFT", name="humans"), s, (0.55, 0, 1.75))
t_de = stand(text("DECIDE", FB, width=WW, extrude=0.45, bevel=0.035, align="LEFT", name="decide"), s, (0.55, 0, 0.02))
t_hu.data.size = t_de.data.size = min(t_hu.data.size, t_de.data.size)
slam(t_ag, 91.28, back=6)
slam(t_do, 91.62, back=6)
slam(t_hu, 92.78, back=6)
slam(t_de, 93.22, back=6)
ha = hud("WHAT AGENTS DO", width=1.9, parent=s, loc=(-0.55, 0, 3.55), align="RIGHT")
hh = hud("WHAT HUMANS DECIDE", width=2.4, parent=s, loc=(0.55, 0, 3.55), align="LEFT", mat=E_WHITE)
pop(ha, 91.0, dur=3)
pop(hh, 92.58, dur=3)

# ----------------------------------------------------------------- camera
bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"
cam_d = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_d)
link(cam)
scene.camera = cam
cam_d.lens = 35
cam_d.sensor_width = 36
cam_d.clip_end = 400
tgt = empty("target")
con = cam.constraints.new("TRACK_TO")
con.target = tgt; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
cam_d.dof.use_dof = True
cam_d.dof.focus_object = tgt
cam_d.dof.aperture_fstop = 2.2

def hold_pos(i, push):
    sx = 0 if i == 3 else (1 if SX[i] > 0 else -1)
    return Vector((sx * (1.4 + 0.4 * push), YS[i] - 13.0 + 3.0 * push, 1.45 + 0.15 * push))

def look(i, dz=2.3):
    return Vector((SX[i] * 0.9, YS[i], dz))

CAMKEYS = [  # (t, pos, target)
    (78.20, Vector((0.6, -40, 3.2)), look(0)),
    (79.40, hold_pos(0, 0.0), look(0)),
    (83.50, hold_pos(0, 1.0), look(0, 2.6)),
    (83.92, hold_pos(1, 0.0), look(1)),
    (85.55, hold_pos(1, 0.8), look(1, 2.6)),
    (85.86, hold_pos(2, 0.0), look(2)),
    (88.25, hold_pos(2, 1.0), look(2, 2.5)),
    (88.62, hold_pos(3, -0.3) + Vector((0, 0, 0.1)), look(3, 2.5)),
    (95.20, hold_pos(3, 0.9), look(3, 2.25)),
]
for t, p, g in CAMKEYS:
    keys(cam, F(t), loc=p)
    keys(tgt, F(t), loc=g)

# ----------------------------------------------------------------- world + render
world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = GRAPHITE
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

scene.render.engine = "BLENDER_EEVEE"
ee = scene.eevee
def tryset(obj, attr, val):
    try:
        setattr(obj, attr, val)
    except Exception as ex:
        print("skip", attr, ex)
RT = os.environ.get("E1_RT", "1") == "1"
tryset(ee, "taa_render_samples", int(os.environ.get("E1_SAMPLES", "16")))
tryset(ee, "use_raytracing", RT)
tryset(ee, "ray_tracing_method", "SCREEN")
try:
    ee.ray_tracing_options.resolution_scale = "2"
except Exception as ex:
    print("skip rt res", ex)
tryset(ee, "use_shadows", True)
tryset(scene.render, "use_motion_blur", True)
tryset(scene.render, "motion_blur_shutter", 0.5)
tryset(ee, "motion_blur_steps", 1)
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
scene.frame_start, scene.frame_end = FS, FE

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "seqE1.blend"))

if MODE == "test":
    scene.render.resolution_percentage = int(argv[1]) if len(argv) > 1 else 50
    frames = [int(x) for x in argv[2].split(",")] if len(argv) > 2 else [1930, 1990, 2050]
    import time
    for fr in frames:
        t0 = time.time()
        scene.frame_set(fr)
        scene.render.filepath = os.path.join(WORK, f"test_{fr}.png")
        bpy.ops.render.render(write_still=True)
        print("TIME", fr, round(time.time() - t0, 2))
elif MODE == "final":
    scene.render.resolution_percentage = 100
    scene.render.filepath = "/Users/ac/Code/aws-hackathon/video/kinetic/frames/f_#####"
    scene.render.use_overwrite = True
    if len(argv) > 2:
        scene.frame_start, scene.frame_end = int(argv[1]), int(argv[2])
    bpy.ops.render.render(animation=True)
