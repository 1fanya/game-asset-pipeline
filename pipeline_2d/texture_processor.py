"""
Texture Processor — GIMP Python-Fu Scripts + Pillow Fallback
Generates procedural textures, atlases, and GIMP batch scripts.
"""
import os, json, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# ─── GIMP PYTHON-FU SCRIPT TEMPLATE ──────────────────────────────────
GIMP_TEX_SCRIPT = '''#!/usr/bin/env python
# GIMP Python-Fu: Texture Pipeline for {name} @ {size}px
# Usage: gimp -i -b 'python-fu-eval -s "{path}"' -b '(gimp-quit 0)'
from gimpfu import *

def process_{safe}():
    img = pdb.gimp_file_load("{input}", "{input}")
    d = pdb.gimp_image_get_active_drawable(img)
    pdb.gimp_image_scale_full(img, {size}, {size}, INTERPOLATION_LANCZOS)
    pdb.plug_in_unsharp_mask(img, d, 3.0, 0.5, 0)
    pdb.gimp_drawable_hue_saturation(d, HUE_RANGE_ALL, 0, 0, 15, 0)
    n = pdb.gimp_layer_copy(d, True)
    pdb.gimp_image_insert_layer(img, n, None, -1)
    pdb.plug_in_emboss(img, n, 315, 45.0, 7, True)
    pdb.file_png_save(img, d, "{out}/{name}_processed.png", "{name}", 0,9,1,1,1,1,1)
    pdb.gimp_image_set_active_layer(img, n)
    pdb.file_png_save(img, n, "{out}/{name}_normal.png", "{name}_n", 0,9,1,1,1,1,1)
    pdb.gimp_image_delete(img)

process_{safe}()
'''

TEX_NAMES = ["stone_wall","wood_plank","metal_plate","fabric_cloth","brick_red","sand_desert"]

def generate_gimp_texture_scripts(config, output_dir):
    sd = os.path.join(output_dir, "scripts", "gimp"); os.makedirs(sd, exist_ok=True)
    gen = []
    for tn in TEX_NAMES:
        safe = tn.replace("-","_")
        for sz in config["pipeline_2d"]["texture_sizes"]:
            p = os.path.join(sd, f"texture_{tn}_{sz}.py")
            with open(p,"w") as f:
                f.write(GIMP_TEX_SCRIPT.format(
                    name=tn, safe=safe, size=sz, path=p.replace("\\","/"),
                    input=os.path.join(output_dir,"textures",f"{tn}_{sz}.png").replace("\\","/"),
                    out=os.path.join(output_dir,"textures").replace("\\","/")))
            gen.append({"type":"gimp_texture_script","name":f"texture_{tn}_{sz}.py",
                       "path":p,"tool":"GIMP Python-Fu"})
    return gen

# ─── PROCEDURAL TEXTURE GENERATORS ──────────────────────────────────
def _gen_stone(size, seed=1):
    img = Image.new("RGB",(size,size)); draw = ImageDraw.Draw(img); random.seed(seed)
    br,bg,bb = 140,135,125
    for y in range(0,size,2):
        for x in range(0,size,2):
            v=random.randint(-25,25)
            draw.rectangle([x,y,x+1,y+1],fill=(max(0,min(255,br+v)),max(0,min(255,bg+v-3)),max(0,min(255,bb+v-5))))
    for _ in range(8):
        sx,sy=random.randint(0,size),random.randint(0,size)
        for s in range(random.randint(10,30)):
            sx=(sx+random.randint(-2,2))%size; sy=(sy+random.randint(-2,2))%size
            draw.point((sx,sy),fill=(br-40,bg-40,bb-40))
    return img.filter(ImageFilter.SMOOTH)

def _gen_wood(size, seed=2):
    img = Image.new("RGB",(size,size)); draw = ImageDraw.Draw(img); random.seed(seed)
    br,bg,bb = 140,90,50
    for y in range(size):
        grain = math.sin(y/4.0+random.random()*0.3)*15
        for x in range(size):
            v = int(math.sin((x+grain)/8.0)*20 + random.randint(-8,8))
            draw.point((x,y),fill=(max(0,min(255,br+v)),max(0,min(255,bg+v//2)),max(0,min(255,bb+v//3))))
    return img.filter(ImageFilter.SMOOTH)

def _gen_metal(size, seed=3):
    img = Image.new("RGB",(size,size)); draw = ImageDraw.Draw(img); random.seed(seed)
    br,bg,bb = 160,165,175
    for y in range(size):
        st=random.randint(-5,5)
        for x in range(size):
            v=st+random.randint(-10,10)
            draw.point((x,y),fill=(max(0,min(255,br+v)),max(0,min(255,bg+v)),max(0,min(255,bb+v))))
    img=img.filter(ImageFilter.SMOOTH_MORE)
    return ImageEnhance.Contrast(img).enhance(1.3)

def _gen_fabric(size, seed=4):
    img = Image.new("RGB",(size,size)); draw = ImageDraw.Draw(img); random.seed(seed)
    br,bg,bb = 80,60,120
    for y in range(size):
        for x in range(size):
            w = ((x+y)%4<2) != ((x-y)%4<2)
            v = (15 if w else -15)+random.randint(-8,8)
            draw.point((x,y),fill=(max(0,min(255,br+v)),max(0,min(255,bg+v)),max(0,min(255,bb+v))))
    return img.filter(ImageFilter.SMOOTH)

def _gen_brick(size, seed=5):
    img = Image.new("RGB",(size,size)); draw = ImageDraw.Draw(img); random.seed(seed)
    draw.rectangle([0,0,size,size],fill=(180,170,155))
    bh,bw = size//8, size//4
    for row in range(0,size,bh):
        off = (bw//2) if (row//bh)%2==1 else 0
        for col in range(-bw,size+bw,bw):
            x=col+off; v=random.randint(-20,20)
            draw.rectangle([x+1,row+1,x+bw-2,row+bh-2],
                          fill=(max(0,min(255,160+v)),max(0,min(255,60+v//2)),max(0,min(255,50+v//3))))
    return img.filter(ImageFilter.SMOOTH)

def _gen_sand(size, seed=6):
    img = Image.new("RGB",(size,size)); draw = ImageDraw.Draw(img); random.seed(seed)
    br,bg,bb = 210,190,140
    for y in range(size):
        for x in range(size):
            v=int(math.sin(x/6.0+y/10.0)*10+random.randint(-12,12))
            draw.point((x,y),fill=(max(0,min(255,br+v)),max(0,min(255,bg+v)),max(0,min(255,bb+v//2))))
    return img.filter(ImageFilter.SMOOTH)

GENERATORS = {"stone_wall":_gen_stone,"wood_plank":_gen_wood,"metal_plate":_gen_metal,
              "fabric_cloth":_gen_fabric,"brick_red":_gen_brick,"sand_desert":_gen_sand}

# ─── ATLAS PACKER ────────────────────────────────────────────────────
def _pack(textures, max_sz):
    placements=[]; sy=sh=cx=0
    for name,img in textures:
        w,h=img.size
        if cx+w>max_sz: sy+=sh; sh=cx=0
        if sy+h>max_sz: break
        placements.append((name,img,cx,sy)); cx+=w; sh=max(sh,h)
    return placements, max_sz, sy+sh

def generate_textures(config, output_dir):
    td = os.path.join(output_dir,"textures"); os.makedirs(td, exist_ok=True)
    gen=[]; all_256=[]
    for tn,gf in GENERATORS.items():
        for sz in config["pipeline_2d"]["texture_sizes"]:
            img=gf(sz, seed=hash(tn)%1000)
            p=os.path.join(td,f"{tn}_{sz}.png"); img.save(p)
            gen.append({"type":"texture","name":f"{tn}_{sz}.png","path":p,"dimensions":f"{sz}x{sz}"})
            if sz==256: all_256.append((tn,img))
    if all_256:
        pl,aw,ah = _pack(all_256, config["pipeline_2d"]["atlas_max_size"])
        atlas = Image.new("RGB",(aw,ah),(0,0,0))
        meta=[]
        for n,im,x,y in pl:
            atlas.paste(im,(x,y))
            meta.append({"name":n,"x":x,"y":y,"width":im.size[0],"height":im.size[1],
                         "u0":x/aw,"v0":y/ah,"u1":(x+im.size[0])/aw,"v1":(y+im.size[1])/ah})
        ap=os.path.join(td,"texture_atlas.png"); atlas.save(ap)
        mp=os.path.join(td,"atlas_meta.json")
        with open(mp,"w") as f: json.dump({"atlas_size":[aw,ah],"textures":meta},f,indent=2)
        gen.append({"type":"texture_atlas","name":"texture_atlas.png","path":ap,
                    "dimensions":f"{aw}x{ah}","texture_count":len(meta),"meta_path":mp})
    return gen

def run(config, output_dir):
    return generate_textures(config, output_dir) + generate_gimp_texture_scripts(config, output_dir)
