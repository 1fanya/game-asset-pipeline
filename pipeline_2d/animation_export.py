"""
Animation Exporter — GIMP Script-Fu + Pillow Fallback
Generates frame-by-frame animation sequences with GIMP batch scripts
for professional animation processing.
"""
import os, json, math, random
from PIL import Image, ImageDraw

# ─── GIMP ANIMATION SCRIPT ──────────────────────────────────────────
GIMP_ANIM_SCRIPT = """; GIMP Script-Fu: Animation Frame Processor for {name}
; Usage: gimp -i -b '(script-fu-load "{path}")' -b '(gimp-quit 0)'
(define (process-animation-{safe} output-dir frame-count)
  (let loop ((i 0))
    (when (< i frame-count)
      (let* (
        (img (car (gimp-image-new {size} {size} RGB)))
        (layer (car (gimp-layer-new img {size} {size} RGBA-IMAGE
                (string-append "frame_" (number->string i)) 100 LAYER-MODE-NORMAL)))
      )
      (gimp-image-insert-layer img layer 0 -1)

      ; Apply rotation transform for this frame
      (gimp-item-transform-rotate-default layer
        (* (/ (* 2 3.14159) frame-count) i) TRUE 0 0)

      ; Apply color overlay
      (gimp-context-set-foreground '({r} {g} {b}))
      (gimp-edit-fill layer FILL-FOREGROUND)

      ; Export frame
      (file-png-save RUN-NONINTERACTIVE img layer
        (string-append output-dir "/frame_" (number->string i) ".png")
        (string-append "frame_" (number->string i))
        0 9 1 1 1 1 1)

      (gimp-image-delete img)
      (loop (+ i 1))))))

(process-animation-{safe} "{outdir}" {frames})
"""

def generate_gimp_anim_scripts(config, output_dir):
    sd = os.path.join(output_dir, "scripts", "gimp"); os.makedirs(sd, exist_ok=True)
    gen = []
    anims = [
        {"name":"rotation_effect","color":[0,200,220],"desc":"Spinning rotation effect"},
        {"name":"pulse_glow","color":[255,200,50],"desc":"Pulsing glow animation"},
        {"name":"particle_burst","color":[220,50,50],"desc":"Particle burst VFX"},
        {"name":"shield_shimmer","color":[100,180,255],"desc":"Shield shimmer overlay"},
    ]
    frames = config["pipeline_2d"]["animation_frames"]
    size = config["pipeline_2d"]["sprite_size"] * 2  # Larger for effects
    for anim in anims:
        n = anim["name"]; safe = n.replace("-","_")
        r,g,b = anim["color"]
        p = os.path.join(sd, f"anim_{n}.scm")
        with open(p,"w") as f:
            f.write(GIMP_ANIM_SCRIPT.format(
                name=n, safe=safe, size=size, frames=frames,
                r=r, g=g, b=b, path=p.replace("\\","/"),
                outdir=os.path.join(output_dir,"animations",n).replace("\\","/")))
        gen.append({"type":"gimp_anim_script","name":f"anim_{n}.scm","path":p,
                    "tool":"GIMP Script-Fu","description":anim["desc"]})
    return gen

# ─── PILLOW ANIMATION RENDERER ──────────────────────────────────────

def _draw_rotation_frame(draw, size, frame, total, color):
    cx, cy = size//2, size//2
    angle = (frame / total) * 2 * math.pi
    r = size // 3
    pts = []
    for i in range(6):
        a = angle + i * math.pi / 3
        pts.append((cx + int(r * math.cos(a)), cy + int(r * math.sin(a))))
    draw.polygon(pts, fill=(*color, 200), outline=(*[min(255,c+60) for c in color], 255))
    # Center glow
    for gr in range(r//2, 0, -2):
        alpha = int(80 * (gr / (r//2)))
        draw.ellipse([cx-gr, cy-gr, cx+gr, cy+gr],
                     fill=(*[min(255,c+40) for c in color], alpha))

def _draw_pulse_frame(draw, size, frame, total, color):
    cx, cy = size//2, size//2
    t = frame / total
    max_r = size // 3
    pulse_r = int(max_r * (0.6 + 0.4 * math.sin(t * 2 * math.pi)))
    for r in range(pulse_r, 0, -3):
        alpha = int(150 * (r / pulse_r))
        draw.ellipse([cx-r, cy-r, cx+r, cy+r],
                     fill=(*color, alpha))

def _draw_particle_frame(draw, size, frame, total, color):
    cx, cy = size//2, size//2
    random.seed(42 + frame)
    t = frame / total
    for i in range(12):
        angle = (i / 12) * 2 * math.pi + t * math.pi
        dist = int((size // 4) * t + random.randint(-5, 5))
        px = cx + int(dist * math.cos(angle))
        py = cy + int(dist * math.sin(angle))
        pr = max(1, int(4 * (1 - t)))
        alpha = int(255 * (1 - t * 0.7))
        draw.ellipse([px-pr, py-pr, px+pr, py+pr],
                     fill=(*color, alpha))

def _draw_shield_frame(draw, size, frame, total, color):
    cx, cy = size//2, size//2
    r = size // 3
    t = frame / total
    # Shield arc
    start = int(t * 360)
    draw.arc([cx-r, cy-r, cx+r, cy+r], start, start+270,
             fill=(*color, 200), width=4)
    # Shimmer highlights
    for i in range(3):
        a = math.radians(start + i * 90)
        sx = cx + int((r-2) * math.cos(a))
        sy = cy + int((r-2) * math.sin(a))
        draw.ellipse([sx-3, sy-3, sx+3, sy+3],
                     fill=(255, 255, 255, 150))

ANIM_DRAWERS = {
    "rotation_effect": _draw_rotation_frame,
    "pulse_glow": _draw_pulse_frame,
    "particle_burst": _draw_particle_frame,
    "shield_shimmer": _draw_shield_frame,
}

def generate_animations(config, output_dir):
    ad = os.path.join(output_dir, "animations"); os.makedirs(ad, exist_ok=True)
    gen = []
    frames = config["pipeline_2d"]["animation_frames"]
    size = config["pipeline_2d"]["sprite_size"] * 2

    anims = [
        {"name":"rotation_effect","color":[0,200,220]},
        {"name":"pulse_glow","color":[255,200,50]},
        {"name":"particle_burst","color":[220,50,50]},
        {"name":"shield_shimmer","color":[100,180,255]},
    ]

    for anim_def in anims:
        name = anim_def["name"]
        color = tuple(anim_def["color"])
        drawer = ANIM_DRAWERS.get(name)
        if not drawer: continue

        adir = os.path.join(ad, name); os.makedirs(adir, exist_ok=True)
        pil_frames = []
        frame_meta = []

        for i in range(frames):
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            drawer(draw, size, i, frames, color)
            fp = os.path.join(adir, f"frame_{i:03d}.png")
            img.save(fp)
            pil_frames.append(img)
            frame_meta.append({"index": i, "path": fp, "duration_ms": 100})

        # Save GIF preview
        if pil_frames:
            gif_path = os.path.join(ad, f"{name}.gif")
            pil_frames[0].save(gif_path, save_all=True, append_images=pil_frames[1:],
                              duration=100, loop=0, disposal=2)
            gen.append({"type":"animation_gif","name":f"{name}.gif","path":gif_path,
                        "frame_count":frames,"dimensions":f"{size}x{size}"})

        # Save metadata
        mp = os.path.join(adir, "meta.json")
        with open(mp, "w") as f:
            json.dump({"name":name,"frame_count":frames,"size":size,
                       "fps":10,"frames":frame_meta}, f, indent=2)
        gen.append({"type":"animation_sequence","name":name,"path":adir,
                    "meta_path":mp,"frame_count":frames})

    return gen

def run(config, output_dir):
    return generate_animations(config, output_dir) + generate_gimp_anim_scripts(config, output_dir)
