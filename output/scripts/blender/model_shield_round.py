# ============================================================
# Blender Python Script: shield_round
# Run: blender --background --python model_shield_round.py
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


# ── Create Shield: shield_round ──
def create_shield(radius=0.8, depth=0.15, rim=0.08):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(0,0,0))
    obj = bpy.context.active_object
    obj.name = "shield_round"
    obj.scale[1] = depth / radius
    # Rim torus
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=rim,
        location=(0,0,0), rotation=(math.pi/2,0,0))
    rim_obj = bpy.context.active_object
    rim_obj.name = "shield_round_rim"
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    obj = bpy.context.active_object

    mat = bpy.data.materials.new("shield_round_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.627, 0.549, 0.196, 1)
    bsdf.inputs["Metallic"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.3
    obj.data.materials.append(mat)
    return obj

shield = create_shield()
bpy.ops.wm.obj_export(filepath=os.path.join(output_dir, "shield_round.obj"))
bpy.ops.wm.stl_export(filepath=os.path.join(output_dir, "shield_round.stl"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "shield_round.blend"))
