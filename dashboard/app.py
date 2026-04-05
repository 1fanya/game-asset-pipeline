"""
Flask Dashboard — Premium dark-themed web app for showcasing pipeline assets.
"""
import os, json, yaml
from flask import Flask, render_template, send_from_directory, jsonify

def create_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)
    output_dir = os.path.join(project_dir, "output")

    app = Flask(__name__,
                template_folder=os.path.join(base_dir, "templates"),
                static_folder=os.path.join(base_dir, "static"))

    def _asset_url(path):
        """Convert absolute path to relative /output/ URL."""
        if not path:
            return ""
        normalized = path.replace("\\", "/")
        if "output/" in normalized:
            return normalized.split("output/", 1)[-1]
        return normalized

    def _count_by_tool(scripts_list, tool_substr):
        """Count scripts matching a tool name substring."""
        return sum(1 for s in scripts_list if tool_substr in s.get("tool", ""))

    app.jinja_env.filters["asset_url"] = _asset_url
    app.jinja_env.globals["count_by_tool"] = _count_by_tool

    def _load_manifest():
        mp = os.path.join(output_dir, "manifest.json")
        if os.path.exists(mp):
            with open(mp) as f: return json.load(f)
        return {"stages":[],"assets":[],"summary":{}}

    def _load_config():
        cp = os.path.join(project_dir, "config.yaml")
        if os.path.exists(cp):
            with open(cp) as f: return yaml.safe_load(f)
        return {}

    @app.route("/")
    def index():
        manifest = _load_manifest()
        config = _load_config()
        return render_template("index.html", manifest=manifest, config=config)

    @app.route("/gallery/2d")
    def gallery_2d():
        manifest = _load_manifest()
        assets_2d = [a for a in manifest.get("assets",[])
                     if a.get("type") in ("sprite_sheet","tileset","icon_sheet",
                                           "texture","texture_atlas","ui_preview",
                                           "animation_gif","svg_ui")]
        return render_template("gallery_2d.html", assets=assets_2d)

    @app.route("/gallery/3d")
    def gallery_3d():
        manifest = _load_manifest()
        assets_3d = [a for a in manifest.get("assets",[])
                     if a.get("type") in ("3d_model","uv_layout","normal_map","scene_preview")]
        return render_template("gallery_3d.html", assets=assets_3d)

    @app.route("/pipeline")
    def pipeline():
        manifest = _load_manifest()
        return render_template("pipeline.html", manifest=manifest)

    @app.route("/report")
    def report():
        rp = os.path.join(output_dir, "reports", "technical_report.md")
        content = ""
        if os.path.exists(rp):
            with open(rp, encoding="utf-8") as f: content = f.read()
        return render_template("report.html", report_content=content)

    @app.route("/scripts")
    def scripts():
        manifest = _load_manifest()
        tool_scripts = [a for a in manifest.get("assets",[])
                        if "script" in a.get("type","") or "batch" in a.get("type","")]
        return render_template("scripts.html", scripts=tool_scripts)

    @app.route("/api/assets")
    def api_assets():
        return jsonify(_load_manifest())

    @app.route("/output/<path:filename>")
    def serve_output(filename):
        return send_from_directory(output_dir, filename)

    return app
