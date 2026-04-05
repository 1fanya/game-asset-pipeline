# ============================================================
# Blender Python Script: potion_health
# Run: blender --background --python model_potion_health.py
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


# ── Create Potion: potion_health ──
def create_potion(body_r=0.4, neck_r=0.15, height=1.0):
    # Body (sphere-ish)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=body_r, location=(0, 0, body_r))
    body = bpy.context.active_object
    body.name = "potion_health_body"
    body.scale[2] = height * 0.6 / (2 * body_r)

    # Neck (cylinder)
    neck_h = height * 0.35
    bpy.ops.mesh.primitive_cylinder_add(radius=neck_r, depth=neck_h,
        location=(0, 0, height * 0.6 + neck_h/2))
    neck = bpy.context.active_object
    neck.name = "potion_health_neck"

    # Cork
    bpy.ops.mesh.primitive_cylinder_add(radius=neck_r*1.3, depth=0.05,
        location=(0, 0, height * 0.6 + neck_h + 0.025))
    cork = bpy.context.active_object
    cork.name = "potion_health_cork"

    # Join all
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = "potion_health"

    # Material
    mat = bpy.data.materials.new("potion_health_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.863, 0.118, 0.118, 1)
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Transmission Weight"].default_value = 0.8
    obj.data.materials.append(mat)
    return obj

potion = create_potion()
bpy.ops.wm.obj_export(filepath=os.path.join(output_dir, "potion_health.obj"))
bpy.ops.wm.stl_export(filepath=os.path.join(output_dir, "potion_health.stl"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "potion_health.blend"))
