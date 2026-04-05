"""
Report Generator — Produces Markdown technical report from pipeline manifest.
"""
import os, json, time

def generate_report(config, manifest, output_dir):
    """Generate comprehensive Markdown technical report."""
    rd = os.path.join(output_dir, "reports"); os.makedirs(rd, exist_ok=True)
    rp = os.path.join(rd, "technical_report.md")

    s = manifest.get("summary", {})
    stages = manifest.get("stages", [])
    assets = manifest.get("assets", [])

    # Categorize assets
    categories = {}
    scripts = []
    for a in assets:
        t = a.get("type", "unknown")
        if "script" in t or "batch" in t:
            scripts.append(a)
        else:
            categories.setdefault(t, []).append(a)

    lines = []
    lines.append(f"# {config['reports']['title']}")
    lines.append(f"\n**Generated:** {manifest.get('generated_at', 'N/A')}")
    lines.append(f"**Pipeline Version:** {config['project']['version']}")
    lines.append(f"**Author:** {config['project']['author']}\n")

    lines.append("---\n")
    lines.append("## Executive Summary\n")
    lines.append(f"This report documents the automated game asset pipeline that produced "
                 f"**{s.get('total_assets',0)} assets** and **{s.get('total_scripts',0)} tool scripts** "
                 f"across **{len(stages)} pipeline stages** in **{s.get('total_time_s',0):.1f} seconds**.\n")
    lines.append("### Tools & Technologies\n")
    lines.append("| Tool | Purpose | Script Type |")
    lines.append("|------|---------|-------------|")
    lines.append("| **Blender** | 3D modeling, UV unwrapping, materials, scene rendering | Python (`bpy`) |")
    lines.append("| **GIMP** | 2D sprite processing, texture filters, animation frames | Script-Fu / Python-Fu |")
    lines.append("| **Inkscape** | Vector UI/HUD elements, multi-DPI PNG export | CLI + SVG |")
    lines.append("| **Pillow/NumPy** | Fallback renders, procedural textures, normal maps | Python |")
    lines.append("| **Flask** | Web dashboard with Three.js 3D viewer | Python |")

    lines.append("\n---\n")
    lines.append("## Pipeline Performance\n")
    lines.append("| Stage | Status | Assets | Time |")
    lines.append("|-------|--------|--------|------|")
    for st in stages:
        status = "✅" if st["status"]=="success" else "❌"
        lines.append(f"| {st['name']} | {status} {st['status']} | {st.get('assets',0)} | {st.get('time_s',0):.3f}s |")
    lines.append(f"\n**Total pipeline time:** {s.get('total_time_s',0):.2f}s\n")

    lines.append("---\n")
    lines.append("## Asset Inventory\n")
    for cat, items in sorted(categories.items()):
        lines.append(f"### {cat.replace('_',' ').title()} ({len(items)} items)\n")
        lines.append("| Name | Dimensions | Details |")
        lines.append("|------|-----------|---------|")
        for a in items:
            dims = a.get("dimensions", "—")
            details = a.get("frame_count", a.get("texture_count", a.get("vertices", "—")))
            lines.append(f"| {a.get('name','?')} | {dims} | {details} |")
        lines.append("")

    if scripts:
        lines.append("---\n")
        lines.append(f"## Generated Tool Scripts ({len(scripts)})\n")
        lines.append("These scripts are ready to run with their respective tools:\n")
        lines.append("| Script | Tool | Description |")
        lines.append("|--------|------|-------------|")
        for sc in scripts:
            tool = sc.get("tool", "—")
            desc = sc.get("description", sc.get("model", sc.get("name","")))
            lines.append(f"| `{sc.get('name','?')}` | {tool} | {desc} |")
        lines.append("")
        lines.append("### Running Blender Scripts\n```bash")
        lines.append("blender --background --python output/scripts/blender/model_gem_ruby.py")
        lines.append("```\n")
        lines.append("### Running GIMP Scripts\n```bash")
        lines.append('gimp -i -b \'(script-fu-load "output/scripts/gimp/knight_sprites.scm")\' -b \'(gimp-quit 0)\'')
        lines.append("```\n")
        lines.append("### Running Inkscape Export\n```batch")
        lines.append("output\\scripts\\inkscape_export.bat")
        lines.append("```\n")

    lines.append("---\n")
    lines.append("## Methodology\n")
    lines.append("### 2D Pipeline\n")
    lines.append("1. **Sprite Generation**: Programmatic character frames with animation variants, "
                 "packed into sprite sheets with JSON metadata for game engine integration.\n")
    lines.append("2. **Procedural Textures**: Six texture types (stone, wood, metal, fabric, brick, sand) "
                 "generated algorithmically at multiple resolutions, packed into optimized atlases with UV coordinates.\n")
    lines.append("3. **UI/HUD Design**: Vector SVG elements designed for Inkscape with proper layer structure, "
                 "gradients, and typography. Batch-exportable at 72/144/288 DPI.\n")
    lines.append("4. **Animation Export**: Frame-by-frame VFX sequences (rotation, pulse, particle, shield) "
                 "with GIF previews and per-frame timing metadata.\n")
    lines.append("### 3D Pipeline\n")
    lines.append("1. **Parametric Modeling**: Blender Python scripts generate game objects (gems, potions, "
                 "weapons) with configurable parameters. Fallback STL/OBJ via numpy-stl.\n")
    lines.append("2. **UV Mapping**: Smart UV Project with island margin control. "
                 "UV layout visualization for texture artist handoff.\n")
    lines.append("3. **Material System**: PBR materials (Principled BSDF) with diffuse, normal, "
                 "roughness, and metallic channels. Sobel-based normal map generation from heightmaps.\n")
    lines.append("4. **Scene Composition**: Multi-object scenes with configurable camera and three "
                 "lighting presets (dramatic, studio, warm). Eevee/Cycles rendering.\n")

    with open(rp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  Report generated: {rp}")
    return [{"type":"report","name":"technical_report.md","path":rp}]

def run(config, manifest, output_dir):
    return generate_report(config, manifest, output_dir)
