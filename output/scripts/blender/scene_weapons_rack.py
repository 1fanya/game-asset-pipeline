# Blender Python: Scene Composition — weapons_rack
# Run: blender --background --python scene_weapons_rack.py
import bpy, os, math

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
output_dir = r"output/scenes"
os.makedirs(output_dir, exist_ok=True)

# Import models
models_dir = r"output/models_3d"
positions = [(2.0, 0.0, 0), (-1.0, 1.73, 0), (-1.0, -1.73, 0)]
model_files = ['sword_basic', 'axe_war', 'shield_round']

for i, model_file in enumerate(model_files):
    obj_path = os.path.join(models_dir, model_file + ".obj")
    if os.path.exists(obj_path):
        bpy.ops.wm.obj_import(filepath=obj_path)
        obj = bpy.context.selected_objects[-1]
        if i < len(positions):
            obj.location = positions[i]

# Camera
cam_data = bpy.data.cameras.new("SceneCamera")
cam_data.lens = 50
cam = bpy.data.objects.new("SceneCamera", cam_data)
scene.collection.objects.link(cam)
cam.location = (4, 2, 2)
from mathutils import Vector
direction = Vector((0, 0, 1)) - cam.location
rot = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot.to_euler()
scene.camera = cam

# Lighting: warm

sun = bpy.data.lights.new("Sun", 'SUN')
sun.energy = 2.5; sun.color = (1.0, 0.85, 0.65)
sun_obj = bpy.data.objects.new("Sun", sun)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (0.6, 0, 0.3)
ambient = bpy.data.lights.new("Ambient", 'AREA')
ambient.energy = 30; ambient.color = (1.0, 0.9, 0.7); ambient.size = 8
amb_obj = bpy.data.objects.new("Ambient", ambient)
scene.collection.objects.link(amb_obj)
amb_obj.location = (0, 0, 6)


# Ground plane
bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,0))
plane = bpy.context.active_object
mat = bpy.data.materials.new("Ground")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.18, 1)
plane.data.materials.append(mat)

# Render settings
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(output_dir, "weapons_rack_render.png")
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "weapons_rack.blend"))
print("Scene rendered: weapons_rack")
