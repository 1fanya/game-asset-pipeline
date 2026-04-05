# ============================================================
# Blender Python Script: gem_emerald
# Run: blender --background --python model_gem_emerald.py
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


# ── Create Gem: gem_emerald ──
def create_gem(facets=6, height=1.4, radius=0.5):
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
    me = bpy.data.meshes.new("gem_emerald_mesh")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("gem_emerald", me)
    scene.collection.objects.link(obj)
    # Material
    mat = bpy.data.materials.new("gem_emerald_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.118, 0.784, 0.314, 1)
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
bpy.ops.wm.obj_export(filepath=os.path.join(output_dir, "gem_emerald.obj"))
bpy.ops.wm.stl_export(filepath=os.path.join(output_dir, "gem_emerald.stl"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "gem_emerald.blend"))
