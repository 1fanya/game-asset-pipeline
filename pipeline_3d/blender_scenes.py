"""
Blender Scene Compositor — Generates scene scripts + matplotlib fallback previews
Assembles multi-object scenes with lighting and camera for rendering.
"""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw

# ─── BLENDER SCENE SCRIPTS ──────────────────────────────────────────

BLENDER_SCENE_SCRIPT = """# Blender Python: Scene Composition — {name}
# Run: blender --background --python {script_name}
import bpy, os, math

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
output_dir = r"{output_dir}"
os.makedirs(output_dir, exist_ok=True)

# Import models
models_dir = r"{models_dir}"
positions = {positions}
model_files = {model_files}

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
cam.location = ({cam_x}, {cam_y}, {cam_z})
from mathutils import Vector
direction = Vector(({tgt_x}, {tgt_y}, {tgt_z})) - cam.location
rot = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot.to_euler()
scene.camera = cam

# Lighting: {lighting}
{lighting_code}

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
scene.render.resolution_x = {res_x}
scene.render.resolution_y = {res_y}
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(output_dir, "{name}_render.png")
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_dir, "{name}.blend"))
print("Scene rendered: {name}")
"""

LIGHTING_TEMPLATES = {
    "dramatic": """
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
""",
    "studio": """
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
""",
    "warm": """
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
"""
}

def generate_scene_scripts(config, output_dir):
    sd = os.path.join(output_dir, "scripts", "blender"); os.makedirs(sd, exist_ok=True)
    gen = []
    res = config["pipeline_3d"]["render_resolution"]
    md = os.path.join(output_dir, "models_3d").replace("\\","/")

    for sc in config["pipeline_3d"]["scenes"]:
        name = sc["name"]; models = sc["models"]
        cam = sc["camera"]; light = sc.get("lighting","studio")

        # Arrange models in a circle
        positions = []
        for i, m in enumerate(models):
            angle = 2*math.pi*i/max(len(models),1)
            r = 2.0
            positions.append((round(r*math.cos(angle),2), round(r*math.sin(angle),2), 0))

        sn = f"scene_{name}.py"; sp = os.path.join(sd, sn)
        with open(sp, "w") as f:
            f.write(BLENDER_SCENE_SCRIPT.format(
                name=name, script_name=sn,
                output_dir=os.path.join(output_dir,"scenes").replace("\\","/"),
                models_dir=md, positions=positions, model_files=models,
                cam_x=cam["position"][0], cam_y=cam["position"][1], cam_z=cam["position"][2],
                tgt_x=cam["target"][0], tgt_y=cam["target"][1], tgt_z=cam["target"][2],
                lighting=light, lighting_code=LIGHTING_TEMPLATES.get(light,""),
                res_x=res[0], res_y=res[1]))
        gen.append({"type":"blender_scene_script","name":sn,"path":sp,
                    "tool":"Blender","scene":name,"models":models})
    return gen

# ─── MATPLOTLIB/PILLOW FALLBACK SCENE PREVIEWS ─────────────────────

def generate_scene_previews(config, output_dir):
    sd = os.path.join(output_dir, "scenes"); os.makedirs(sd, exist_ok=True)
    gen = []
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        from stl import mesh as stl_mesh

        for sc in config["pipeline_3d"]["scenes"]:
            name = sc["name"]; models = sc["models"]
            cam = sc["camera"]

            fig = plt.figure(figsize=(16,9), facecolor="#0f0f1a")
            ax = fig.add_subplot(111, projection="3d", facecolor="#0f0f1a")

            for i, mname in enumerate(models):
                stl_path = os.path.join(output_dir, "models_3d", f"{mname}.stl")
                if os.path.exists(stl_path):
                    m = stl_mesh.Mesh.from_file(stl_path)
                    angle = 2*math.pi*i/max(len(models),1)
                    ox, oy = 2*math.cos(angle), 2*math.sin(angle)
                    ax.plot_trisurf(m.x.flatten()+ox, m.y.flatten()+oy,
                                   m.z.flatten(), alpha=0.7,
                                   color=plt.cm.cool(i/max(len(models),1)))

            ax.set_xlabel("X", color="#666"); ax.set_ylabel("Y", color="#666")
            ax.set_zlabel("Z", color="#666")
            ax.tick_params(colors="#444")
            ax.set_title(name.replace("_"," ").title(), color="#e2e8f0",
                        fontsize=14, fontweight="bold", pad=15)

            # Set camera angle
            ax.view_init(elev=30, azim=45)

            # Style panes
            ax.xaxis.pane.fill = False; ax.yaxis.pane.fill = False; ax.zaxis.pane.fill = False
            ax.xaxis.pane.set_edgecolor("#333"); ax.yaxis.pane.set_edgecolor("#333")
            ax.zaxis.pane.set_edgecolor("#333")
            ax.grid(True, alpha=0.15)

            pp = os.path.join(sd, f"{name}_preview.png")
            plt.savefig(pp, dpi=150, bbox_inches="tight",
                       facecolor="#0f0f1a", edgecolor="none")
            plt.close(fig)
            gen.append({"type":"scene_preview","name":f"{name}_preview.png","path":pp,
                        "scene":name})
    except Exception as e:
        # Minimal Pillow fallback
        for sc in config["pipeline_3d"]["scenes"]:
            name = sc["name"]
            img = Image.new("RGB", (800,450), (15,15,26))
            draw = ImageDraw.Draw(img)
            draw.text((20,20), f"Scene: {name}", fill=(200,210,230))
            draw.text((20,40), f"Models: {', '.join(sc['models'])}", fill=(140,150,170))
            pp = os.path.join(sd, f"{name}_preview.png")
            img.save(pp)
            gen.append({"type":"scene_preview","name":f"{name}_preview.png","path":pp})
    return gen

def run(config, output_dir):
    return generate_scene_scripts(config, output_dir) + generate_scene_previews(config, output_dir)
