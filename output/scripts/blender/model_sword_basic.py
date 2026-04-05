# ============================================================
# Blender Python Script: sword_basic
# Run: blender --background --python model_sword_basic.py
# Exports: OBJ, STL, and .blend files
# ============================================================
import bpy
import bmesh
import math
import os

# Clear default scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
output_dir = r"output/models_3d"
os.makedirs(output_dir, exist_ok=True)


# ── Create Sword: sword_basic ──
def create_sword(bl=2.0, bw=0.15, gw=0.5, hl=0.4):
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
    me = bpy.data.meshes.new("sword_basic_mesh")
    bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new("sword_basic", me)
    scene.collection.objects.link(obj)
    # Solidify
    mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
    mod.thickness = 0.03
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Solidify")
    mat = bpy.data.materials.new("sword_basic_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.745, 0.765, 0.784, 1)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.2
    obj.data.materials.append(mat)
    return obj

sword = create_sword()
bpy.ops.wm.obj_export(filepath=os.path.join(output_dir, "sword_basic.obj"))
bpy.ops.wm.stl_export(filepath=os.path.join(output_dir, "sword_basic.stl"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "sword_basic.blend"))
