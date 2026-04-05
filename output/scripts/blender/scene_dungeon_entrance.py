# Blender Python: Scene Composition — dungeon_entrance
# Run: blender --background --python scene_dungeon_entrance.py
import bpy, os, math

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
output_dir = r"output/scenes"
os.makedirs(output_dir, exist_ok=True)

# Import models
models_dir = r"output/models_3d"
positions = [(2.0, 0.0, 0), (0.0, 2.0, 0), (-2.0, 0.0, 0), (-0.0, -2.0, 0)]
model_files = ['tower_defense', 'gem_ruby', 'sword_basic', 'shield_round']

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
cam.location = (8, 8, 6)
from mathutils import Vector
direction = Vector((0, 0, 1)) - cam.location
rot = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot.to_euler()
scene.camera = cam

# Lighting: dramatic

sun = bpy.data.lights.new("Sun", 'SUN')
sun.energy = 3.0
sun.color = (1.0, 0.9, 0.8)
sun_obj = bpy.data.objects.new("Sun", sun)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (0.8, 0, -0.5)
fill = bpy.data.lights.new("Fill", 'AREA')
fill.energy = 50
fill.color = (0.6, 0.7, 1.0)
fill_obj = bpy.data.objects.new("Fill", fill)
scene.collection.objects.link(fill_obj)
fill_obj.location = (-4, -2, 3)


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
scene.render.filepath = os.path.join(output_dir, "dungeon_entrance_render.png")
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "dungeon_entrance.blend"))
print("Scene rendered: dungeon_entrance")
