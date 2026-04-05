"""
Blender 3D Modeler — Generates Blender Python scripts + trimesh/numpy-stl fallback
Creates parametric game models (gems, potions, weapons, terrain) as OBJ/STL.
"""
import os, json, math, struct
import numpy as np
from stl import mesh as stl_mesh

# ─── BLENDER PYTHON SCRIPT GENERATOR ────────────────────────────────

BLENDER_MODEL_HEADER = """# ============================================================
# Blender Python Script: {name}
# Run: blender --background --python {script_name}
# Exports: OBJ, STL, and .blend files
# ============================================================
import bpy
import bmesh
import math
import os

# Clear default scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
output_dir = r"{output_dir}"
os.makedirs(output_dir, exist_ok=True)

"""

BLENDER_GEM = """
# ── Create Gem: {name} ──
def create_gem(facets={facets}, height={height}, radius={radius}):
    bm = bmesh.new()
    top = bm.verts.new((0, 0, height/2))
    bottom = bm.verts.new((0, 0, -height/2))
    mid_verts = []
    for i in range(facets):
        angle = 2 * math.pi * i / facets
        v = bm.verts.new((radius * math.cos(angle), radius * math.sin(angle), 0))
        mid_verts.append(v)
    # Top faces
    for i in range(facets):
        bm.faces.new([top, mid_verts[i], mid_verts[(i+1)%facets]])
    # Bottom faces
    for i in range(facets):
        bm.faces.new([bottom, mid_verts[(i+1)%facets], mid_verts[i]])
    bm.normal_update()
    me = bpy.data.meshes.new("{name}_mesh")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("{name}", me)
    scene.collection.objects.link(obj)
    # Material
    mat = bpy.data.materials.new("{name}_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = ({r}, {g}, {b}, 1)
    bsdf.inputs["Roughness"].default_value = 0.1
    bsdf.inputs["IOR"].default_value = 2.42
    obj.data.materials.append(mat)
    return obj

gem = create_gem()
# Smart UV Project
bpy.context.view_layer.objects.active = gem
gem.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=66)
bpy.ops.object.mode_set(mode='OBJECT')

# Export
bpy.ops.wm.obj_export(filepath=os.path.join(output_dir, "{name}.obj"))
bpy.ops.wm.stl_export(filepath=os.path.join(output_dir, "{name}.stl"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "{name}.blend"))
"""

BLENDER_POTION = """
# ── Create Potion: {name} ──
def create_potion(body_r={body_radius}, neck_r={neck_radius}, height={height}):
    # Body (sphere-ish)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=body_r, location=(0, 0, body_r))
    body = bpy.context.active_object
    body.name = "{name}_body"
    body.scale[2] = height * 0.6 / (2 * body_r)

    # Neck (cylinder)
    neck_h = height * 0.35
    bpy.ops.mesh.primitive_cylinder_add(radius=neck_r, depth=neck_h,
        location=(0, 0, height * 0.6 + neck_h/2))
    neck = bpy.context.active_object
    neck.name = "{name}_neck"

    # Cork
    bpy.ops.mesh.primitive_cylinder_add(radius=neck_r*1.3, depth=0.05,
        location=(0, 0, height * 0.6 + neck_h + 0.025))
    cork = bpy.context.active_object
    cork.name = "{name}_cork"

    # Join all
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = "{name}"

    # Material
    mat = bpy.data.materials.new("{name}_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = ({r}, {g}, {b}, 1)
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Transmission Weight"].default_value = 0.8
    obj.data.materials.append(mat)
    return obj

potion = create_potion()
bpy.ops.wm.obj_export(filepath=os.path.join(output_dir, "{name}.obj"))
bpy.ops.wm.stl_export(filepath=os.path.join(output_dir, "{name}.stl"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "{name}.blend"))
"""

BLENDER_SHIELD = """
# ── Create Shield: {name} ──
def create_shield(radius={radius}, depth={depth}, rim={rim_width}):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(0,0,0))
    obj = bpy.context.active_object
    obj.name = "{name}"
    obj.scale[1] = depth / radius
    # Rim torus
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=rim,
        location=(0,0,0), rotation=(math.pi/2,0,0))
    rim_obj = bpy.context.active_object
    rim_obj.name = "{name}_rim"
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    obj = bpy.context.active_object

    mat = bpy.data.materials.new("{name}_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = ({r}, {g}, {b}, 1)
    bsdf.inputs["Metallic"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.3
    obj.data.materials.append(mat)
    return obj

shield = create_shield()
bpy.ops.wm.obj_export(filepath=os.path.join(output_dir, "{name}.obj"))
bpy.ops.wm.stl_export(filepath=os.path.join(output_dir, "{name}.stl"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "{name}.blend"))
"""

BLENDER_SWORD = """
# ── Create Sword: {name} ──
def create_sword(bl={blade_length}, bw={blade_width}, gw={guard_width}, hl={handle_length}):
    bm = bmesh.new()
    # Blade
    v0 = bm.verts.new((-bw/2, 0, 0))
    v1 = bm.verts.new((bw/2, 0, 0))
    v2 = bm.verts.new((bw/2, 0, bl*0.85))
    v3 = bm.verts.new((0, 0, bl))
    v4 = bm.verts.new((-bw/2, 0, bl*0.85))
    bm.faces.new([v0, v1, v2, v3, v4])
    # Guard
    g0 = bm.verts.new((-gw/2, 0, -0.02))
    g1 = bm.verts.new((gw/2, 0, -0.02))
    g2 = bm.verts.new((gw/2, 0, 0.02))
    g3 = bm.verts.new((-gw/2, 0, 0.02))
    bm.faces.new([g0, g1, g2, g3])
    # Handle
    h0 = bm.verts.new((-bw/3, 0, -0.02))
    h1 = bm.verts.new((bw/3, 0, -0.02))
    h2 = bm.verts.new((bw/3, 0, -hl))
    h3 = bm.verts.new((-bw/3, 0, -hl))
    bm.faces.new([h0, h1, h2, h3])
    bm.normal_update()
    me = bpy.data.meshes.new("{name}_mesh")
    bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new("{name}", me)
    scene.collection.objects.link(obj)
    # Solidify
    mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
    mod.thickness = 0.03
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Solidify")
    mat = bpy.data.materials.new("{name}_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = ({r}, {g}, {b}, 1)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.2
    obj.data.materials.append(mat)
    return obj

sword = create_sword()
bpy.ops.wm.obj_export(filepath=os.path.join(output_dir, "{name}.obj"))
bpy.ops.wm.stl_export(filepath=os.path.join(output_dir, "{name}.stl"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "{name}.blend"))
"""

BLENDER_TEMPLATES = {"gem": BLENDER_GEM, "potion": BLENDER_POTION,
                     "shield": BLENDER_SHIELD, "sword": BLENDER_SWORD}

def generate_blender_scripts(config, output_dir):
    sd = os.path.join(output_dir, "scripts", "blender"); os.makedirs(sd, exist_ok=True)
    gen = []
    for m in config["pipeline_3d"]["models"]:
        t = m["type"]; tmpl = BLENDER_TEMPLATES.get(t)
        if not tmpl: continue
        name = m["name"]; p = m["params"]; c = m["color"]
        r,g,b = c[0]/255, c[1]/255, c[2]/255
        fmt = {"name":name,"r":f"{r:.3f}","g":f"{g:.3f}","b":f"{b:.3f}",
               "output_dir":os.path.join(output_dir,"models_3d").replace("\\","/")}
        fmt.update(p)
        sn = f"model_{name}.py"
        sp = os.path.join(sd, sn)
        with open(sp, "w", encoding="utf-8") as f:
            f.write(BLENDER_MODEL_HEADER.format(name=name, script_name=sn,
                    output_dir=fmt["output_dir"]))
            f.write(tmpl.format(**fmt))
        gen.append({"type":"blender_script","name":sn,"path":sp,
                    "tool":"Blender","model":name})
    return gen

# ─── NUMPY-STL FALLBACK ─────────────────────────────────────────────

def _make_gem_stl(facets, height, radius):
    verts = [(0,0,height/2), (0,0,-height/2)]
    for i in range(facets):
        a = 2*math.pi*i/facets
        verts.append((radius*math.cos(a), radius*math.sin(a), 0))
    faces = []
    for i in range(facets):
        faces.append((0, i+2, (i+1)%facets+2))
        faces.append((1, (i+1)%facets+2, i+2))
    v = np.array(verts); f = np.array(faces)
    m = stl_mesh.Mesh(np.zeros(len(f), dtype=stl_mesh.Mesh.dtype))
    for i,face in enumerate(f):
        for j in range(3): m.vectors[i][j] = v[face[j]]
    return m

def _make_potion_stl(body_r, neck_r, height):
    faces_list = []
    # Body sphere approx
    stacks, slices = 8, 12
    body_h = height * 0.6
    for i in range(stacks):
        t0 = math.pi*i/stacks; t1 = math.pi*(i+1)/stacks
        for j in range(slices):
            p0 = 2*math.pi*j/slices; p1 = 2*math.pi*(j+1)/slices
            v0 = (body_r*math.sin(t0)*math.cos(p0), body_r*math.sin(t0)*math.sin(p0), body_r*math.cos(t0)+body_r)
            v1 = (body_r*math.sin(t0)*math.cos(p1), body_r*math.sin(t0)*math.sin(p1), body_r*math.cos(t0)+body_r)
            v2 = (body_r*math.sin(t1)*math.cos(p1), body_r*math.sin(t1)*math.sin(p1), body_r*math.cos(t1)+body_r)
            v3 = (body_r*math.sin(t1)*math.cos(p0), body_r*math.sin(t1)*math.sin(p0), body_r*math.cos(t1)+body_r)
            faces_list.append((v0,v1,v2)); faces_list.append((v0,v2,v3))
    # Neck cylinder
    segs = 12; nh = height*0.35; nz = body_h
    for i in range(segs):
        a0 = 2*math.pi*i/segs; a1 = 2*math.pi*(i+1)/segs
        b0 = (neck_r*math.cos(a0), neck_r*math.sin(a0), nz)
        b1 = (neck_r*math.cos(a1), neck_r*math.sin(a1), nz)
        t0 = (neck_r*math.cos(a0), neck_r*math.sin(a0), nz+nh)
        t1 = (neck_r*math.cos(a1), neck_r*math.sin(a1), nz+nh)
        faces_list.append((b0,b1,t1)); faces_list.append((b0,t1,t0))
    m = stl_mesh.Mesh(np.zeros(len(faces_list), dtype=stl_mesh.Mesh.dtype))
    for i, (a,b,c) in enumerate(faces_list):
        m.vectors[i] = np.array([a,b,c])
    return m

def _make_shield_stl(radius, depth):
    faces_list = []; segs = 24
    for i in range(segs):
        a0 = 2*math.pi*i/segs; a1 = 2*math.pi*(i+1)/segs
        front = (0, 0, depth/2)
        back = (0, 0, -depth/2)
        f0 = (radius*math.cos(a0), radius*math.sin(a0), 0)
        f1 = (radius*math.cos(a1), radius*math.sin(a1), 0)
        faces_list.append((front,f0,f1))
        faces_list.append((back,f1,f0))
    m = stl_mesh.Mesh(np.zeros(len(faces_list), dtype=stl_mesh.Mesh.dtype))
    for i,(a,b,c) in enumerate(faces_list):
        m.vectors[i] = np.array([a,b,c])
    return m

def _make_sword_stl(blade_length, blade_width):
    hw = blade_width/2
    verts = [(-hw,0,0),(hw,0,0),(hw,0.015,0),(-hw,0.015,0),
             (-hw,0,blade_length*0.85),(hw,0,blade_length*0.85),
             (hw,0.015,blade_length*0.85),(-hw,0.015,blade_length*0.85),
             (0,0.0075,blade_length)]
    faces = [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,8),(5,6,8),(6,7,8),(7,4,8),(0,1,2,3)]
    face_tris = []
    for f in faces:
        if len(f)==4: face_tris.extend([(f[0],f[1],f[2]),(f[0],f[2],f[3])])
        else: face_tris.append(f)
    v = np.array(verts)
    m = stl_mesh.Mesh(np.zeros(len(face_tris), dtype=stl_mesh.Mesh.dtype))
    for i,f in enumerate(face_tris):
        for j in range(3): m.vectors[i][j] = v[f[j]]
    return m

FALLBACK_BUILDERS = {
    "gem": lambda p: _make_gem_stl(p["facets"], p["height"], p["radius"]),
    "potion": lambda p: _make_potion_stl(p["body_radius"], p["neck_radius"], p["height"]),
    "shield": lambda p: _make_shield_stl(p["radius"], p["depth"]),
    "sword": lambda p: _make_sword_stl(p["blade_length"], p["blade_width"]),
}

def generate_models(config, output_dir):
    md = os.path.join(output_dir, "models_3d"); os.makedirs(md, exist_ok=True)
    gen = []
    for m in config["pipeline_3d"]["models"]:
        name = m["name"]; t = m["type"]; p = m["params"]
        builder = FALLBACK_BUILDERS.get(t)
        if not builder: continue
        try:
            mesh_obj = builder(p)
            stl_path = os.path.join(md, f"{name}.stl")
            mesh_obj.save(stl_path)
            # Also export as simple OBJ
            obj_path = os.path.join(md, f"{name}.obj")
            _stl_to_obj(mesh_obj, obj_path, name)
            gen.append({"type":"3d_model","name":name,"stl_path":stl_path,
                        "obj_path":obj_path,"vertices":len(mesh_obj.vectors)*3,
                        "faces":len(mesh_obj.vectors),"format":"STL+OBJ"})
        except Exception as e:
            gen.append({"type":"3d_model","name":name,"error":str(e)})
    return gen

def _stl_to_obj(stl_m, obj_path, name):
    verts = []; faces = []; vi = 1
    for tri in stl_m.vectors:
        for v in tri:
            verts.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
        faces.append(f"f {vi} {vi+1} {vi+2}")
        vi += 3
    with open(obj_path, "w", encoding="utf-8") as f:
        f.write(f"# OBJ: {name}\n# Auto-generated by Game Asset Pipeline\n")
        f.write(f"o {name}\n")
        f.write("\n".join(verts) + "\n")
        f.write("\n".join(faces) + "\n")

def run(config, output_dir):
    return generate_models(config, output_dir) + generate_blender_scripts(config, output_dir)
