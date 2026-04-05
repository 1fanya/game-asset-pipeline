# Blender Python: Normal Map Baker for gem_ruby
# Run: blender --background --python normal_gem_ruby.py
import bpy, os
bpy.ops.wm.read_factory_settings(use_empty=True)
output_dir = r"output/normal_maps"

bpy.ops.wm.obj_import(filepath=r"output/models_3d/gem_ruby.obj")
obj = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = obj

# Ensure UV map exists
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=66)
bpy.ops.object.mode_set(mode='OBJECT')

# Create bake target image
bake_img = bpy.data.images.new("gem_ruby_normal_bake", 960, 960)

# Material with image node
mat = bpy.data.materials.new("gem_ruby_bake_mat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
img_node = nodes.new('ShaderNodeTexImage')
img_node.image = bake_img
img_node.select = True
nodes.active = img_node
obj.data.materials.clear()
obj.data.materials.append(mat)

# Bake normals
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 16
bpy.ops.object.bake(type='NORMAL')

bake_img.filepath_raw = os.path.join(output_dir, "gem_ruby_normal.png")
bake_img.file_format = 'PNG'
bake_img.save()
print(f"Normal map baked for gem_ruby")
