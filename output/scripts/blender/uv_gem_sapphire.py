# Blender Python: UV Unwrap + Texture Bake for gem_sapphire
# Run: blender --background --python uv_gem_sapphire.py
import bpy, os, math
bpy.ops.wm.read_factory_settings(use_empty=True)
output_dir = r"output/uv_maps"
os.makedirs(output_dir, exist_ok=True)

# Import model
bpy.ops.wm.obj_import(filepath=r"output/models_3d/gem_sapphire.obj")
obj = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = obj

# Smart UV Project
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')

# Create UV layout image
bpy.ops.object.mode_set(mode='EDIT')
uv_img = bpy.data.images.new("gem_sapphire_uv_layout", 960, 960)
for area in bpy.context.screen.areas:
    if area.type == 'IMAGE_EDITOR':
        area.spaces.active.image = uv_img
        break
bpy.ops.uv.export_layout(filepath=os.path.join(output_dir, "gem_sapphire_uv_layout.png"),
                          size=(960, 960))
bpy.ops.object.mode_set(mode='OBJECT')

# PBR Material Setup
mat = bpy.data.materials.new("gem_sapphire_pbr")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
bsdf = nodes["Principled BSDF"]

# Diffuse texture node
tex_node = nodes.new('ShaderNodeTexImage')
tex_node.location = (-400, 300)

# Normal map node
normal_node = nodes.new('ShaderNodeNormalMap')
normal_node.location = (-200, -200)
normal_tex = nodes.new('ShaderNodeTexImage')
normal_tex.location = (-400, -200)
links.new(normal_tex.outputs['Color'], normal_node.inputs['Color'])
links.new(normal_node.outputs['Normal'], bsdf.inputs['Normal'])

obj.data.materials.clear()
obj.data.materials.append(mat)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "gem_sapphire_textured.blend"))
print(f"UV unwrap + material setup done for gem_sapphire")
