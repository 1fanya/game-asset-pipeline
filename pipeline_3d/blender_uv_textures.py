"""
Blender UV/Texture Scripts + Normal Map Generator
Generates Blender Python scripts for UV unwrapping + PBR texture workflow
and numpy/Pillow fallback for normal/bump map generation.
"""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ─── BLENDER UV/MATERIAL SCRIPTS ────────────────────────────────────

BLENDER_UV_SCRIPT = """# Blender Python: UV Unwrap + Texture Bake for {name}
# Run: blender --background --python {script_name}
import bpy, os, math
bpy.ops.wm.read_factory_settings(use_empty=True)
output_dir = r"{output_dir}"
os.makedirs(output_dir, exist_ok=True)

# Import model
bpy.ops.wm.obj_import(filepath=r"{obj_path}")
obj = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = obj

# Smart UV Project
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')

# Create UV layout image
bpy.ops.object.mode_set(mode='EDIT')
uv_img = bpy.data.images.new("{name}_uv_layout", {tex_size}, {tex_size})
for area in bpy.context.screen.areas:
    if area.type == 'IMAGE_EDITOR':
        area.spaces.active.image = uv_img
        break
bpy.ops.uv.export_layout(filepath=os.path.join(output_dir, "{name}_uv_layout.png"),
                          size=({tex_size}, {tex_size}))
bpy.ops.object.mode_set(mode='OBJECT')

# PBR Material Setup
mat = bpy.data.materials.new("{name}_pbr")
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

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "{name}_textured.blend"))
print(f"UV unwrap + material setup done for {name}")
"""

BLENDER_NORMAL_SCRIPT = """# Blender Python: Normal Map Baker for {name}
# Run: blender --background --python {script_name}
import bpy, os
bpy.ops.wm.read_factory_settings(use_empty=True)
output_dir = r"{output_dir}"

bpy.ops.wm.obj_import(filepath=r"{obj_path}")
obj = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = obj

# Ensure UV map exists
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=66)
bpy.ops.object.mode_set(mode='OBJECT')

# Create bake target image
bake_img = bpy.data.images.new("{name}_normal_bake", {tex_size}, {tex_size})

# Material with image node
mat = bpy.data.materials.new("{name}_bake_mat")
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

bake_img.filepath_raw = os.path.join(output_dir, "{name}_normal.png")
bake_img.file_format = 'PNG'
bake_img.save()
print(f"Normal map baked for {name}")
"""

def generate_blender_uv_scripts(config, output_dir):
    sd = os.path.join(output_dir, "scripts", "blender"); os.makedirs(sd, exist_ok=True)
    gen = []
    tex_size = config["pipeline_3d"]["render_resolution"][0] // 2  # 960
    for m in config["pipeline_3d"]["models"]:
        name = m["name"]
        obj_path = os.path.join(output_dir, "models_3d", f"{name}.obj").replace("\\","/")
        uv_dir = os.path.join(output_dir, "uv_maps").replace("\\","/")
        nm_dir = os.path.join(output_dir, "normal_maps").replace("\\","/")

        # UV script
        uv_sn = f"uv_{name}.py"; uv_sp = os.path.join(sd, uv_sn)
        with open(uv_sp, "w") as f:
            f.write(BLENDER_UV_SCRIPT.format(name=name, script_name=uv_sn,
                    output_dir=uv_dir, obj_path=obj_path, tex_size=tex_size))
        gen.append({"type":"blender_uv_script","name":uv_sn,"path":uv_sp,"tool":"Blender"})

        # Normal map script
        nm_sn = f"normal_{name}.py"; nm_sp = os.path.join(sd, nm_sn)
        with open(nm_sp, "w") as f:
            f.write(BLENDER_NORMAL_SCRIPT.format(name=name, script_name=nm_sn,
                    output_dir=nm_dir, obj_path=obj_path, tex_size=tex_size))
        gen.append({"type":"blender_normal_script","name":nm_sn,"path":nm_sp,"tool":"Blender"})

    return gen

# ─── PILLOW/NUMPY FALLBACK ──────────────────────────────────────────

def _sobel_normal_map(heightmap_img):
    """Generate normal map from heightmap using Sobel operator."""
    arr = np.array(heightmap_img.convert("L"), dtype=np.float64) / 255.0
    h, w = arr.shape
    # Sobel kernels
    dx = np.zeros_like(arr); dy = np.zeros_like(arr)
    dx[:, 1:-1] = arr[:, 2:] - arr[:, :-2]
    dy[1:-1, :] = arr[2:, :] - arr[:-2, :]
    # Normal = (-dx, -dy, 1) normalized
    normal = np.zeros((h, w, 3), dtype=np.float64)
    normal[:,:,0] = -dx * 2.0
    normal[:,:,1] = -dy * 2.0
    normal[:,:,2] = 1.0
    # Normalize
    length = np.sqrt(np.sum(normal**2, axis=2, keepdims=True))
    length[length == 0] = 1
    normal = normal / length
    # Map [-1,1] to [0,255]
    normal_img = ((normal + 1) / 2 * 255).astype(np.uint8)
    return Image.fromarray(normal_img)

def generate_maps(config, output_dir):
    """Generate UV layout previews and normal maps using Pillow."""
    uv_dir = os.path.join(output_dir, "uv_maps"); os.makedirs(uv_dir, exist_ok=True)
    nm_dir = os.path.join(output_dir, "normal_maps"); os.makedirs(nm_dir, exist_ok=True)
    gen = []
    size = 512

    for m in config["pipeline_3d"]["models"]:
        name = m["name"]; c = m["color"]
        # UV layout preview
        uv_img = Image.new("RGB", (size, size), (20, 20, 35))
        draw = ImageDraw.Draw(uv_img)
        # Draw UV grid
        for i in range(0, size, size//8):
            draw.line([i,0,i,size], fill=(40,40,60), width=1)
            draw.line([0,i,size,i], fill=(40,40,60), width=1)
        # Draw UV islands (simulated)
        np.random.seed(hash(name) % 10000)
        n_islands = np.random.randint(4, 8)
        for _ in range(n_islands):
            ix = np.random.randint(20, size-80)
            iy = np.random.randint(20, size-80)
            iw = np.random.randint(40, 120)
            ih = np.random.randint(40, 120)
            pts = [(ix,iy),(ix+iw,iy),(ix+iw-10,iy+ih),(ix+10,iy+ih)]
            draw.polygon(pts, outline=(0,200,220), fill=None)
            draw.line(pts + [pts[0]], fill=(0,200,220), width=1)
            # internal edges
            draw.line([ix+iw//3,iy,ix+iw//4,iy+ih], fill=(0,160,180), width=1)
        uv_path = os.path.join(uv_dir, f"{name}_uv_layout.png")
        uv_img.save(uv_path)
        gen.append({"type":"uv_layout","name":f"{name}_uv_layout.png","path":uv_path})

        # Heightmap for normal map
        hm = Image.new("L", (size, size))
        draw_h = ImageDraw.Draw(hm)
        np.random.seed(hash(name) % 10000 + 1)
        for y in range(0, size, 4):
            for x in range(0, size, 4):
                v = int(128 + 60*math.sin(x/30.0)*math.cos(y/25.0) + np.random.randint(-20,20))
                draw_h.rectangle([x,y,x+3,y+3], fill=max(0,min(255,v)))
        hm = hm.filter(ImageFilter.GaussianBlur(3))
        hm_path = os.path.join(nm_dir, f"{name}_heightmap.png")
        hm.save(hm_path)

        # Normal map via Sobel
        nm = _sobel_normal_map(hm)
        nm_path = os.path.join(nm_dir, f"{name}_normal.png")
        nm.save(nm_path)
        gen.append({"type":"normal_map","name":f"{name}_normal.png","path":nm_path,
                    "heightmap":hm_path,"dimensions":f"{size}x{size}"})

    return gen

def run(config, output_dir):
    return generate_maps(config, output_dir) + generate_blender_uv_scripts(config, output_dir)
