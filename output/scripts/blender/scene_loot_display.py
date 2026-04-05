# Blender Python: Scene Composition — loot_display
# Run: blender --background --python scene_loot_display.py
import bpy, os, math

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
output_dir = r"output/scenes"
os.makedirs(output_dir, exist_ok=True)

# Import models
models_dir = r"output/models_3d"
positions = [(2.0, 0.0, 0), (0.62, 1.9, 0), (-1.62, 1.18, 0), (-1.62, -1.18, 0), (0.62, -1.9, 0)]
model_files = ['gem_ruby', 'gem_sapphire', 'gem_emerald', 'potion_health', 'potion_mana']

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
cam.location = (3, 3, 3)
from mathutils import Vector
direction = Vector((0, 0, 0.5)) - cam.location
rot = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot.to_euler()
scene.camera = cam

# Lighting: studio

key = bpy.data.lights.new("Key", 'AREA')
key.energy = 100; key.size = 3
key_obj = bpy.data.objects.new("Key", key)
scene.collection.objects.link(key_obj)
key_obj.location = (3, -3, 4)
fill = bpy.data.lights.new("Fill", 'AREA')
fill.energy = 40; fill.size = 4
fill_obj = bpy.data.objects.new("Fill", fill)
scene.collection.objects.link(fill_obj)
fill_obj.location = (-4, -1, 3)
rim = bpy.data.lights.new("Rim", 'SPOT')
rim.energy = 80
rim_obj = bpy.data.objects.new("Rim", rim)
scene.collection.objects.link(rim_obj)
rim_obj.location = (0, 4, 3)


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
scene.render.filepath = os.path.join(output_dir, "loot_display_render.png")
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "loot_display.blend"))
print("Scene rendered: loot_display")
