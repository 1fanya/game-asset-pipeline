"""
Pipeline Runner — Master orchestrator for all pipeline stages.
Runs 2D and 3D pipelines with timing, error handling, and manifest generation.
"""
import os, sys, json, time, yaml

def load_config(config_path="config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def run_pipeline(config_path="config.yaml"):
    """Execute the full asset pipeline."""
    config = load_config(config_path)
    output_dir = config["output"]["root"]
    os.makedirs(output_dir, exist_ok=True)

    manifest = {
        "project": config["project"],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "stages": [],
        "assets": [],
        "summary": {}
    }

    stages = [
        ("2D Sprites", "pipeline_2d.sprite_generator"),
        ("2D Textures", "pipeline_2d.texture_processor"),
        ("2D UI Design", "pipeline_2d.ui_designer"),
        ("2D Animations", "pipeline_2d.animation_export"),
        ("3D Models", "pipeline_3d.blender_modeler"),
        ("3D UV/Normals", "pipeline_3d.blender_uv_textures"),
        ("3D Scenes", "pipeline_3d.blender_scenes"),
    ]

    total_start = time.time()
    total_assets = 0
    total_scripts = 0

    for stage_name, module_path in stages:
        print(f"\n{'='*60}")
        print(f"  STAGE: {stage_name}")
        print(f"{'='*60}")

        stage_start = time.time()
        stage_result = {"name": stage_name, "status": "pending", "assets": 0, "time_s": 0}

        try:
            module = __import__(module_path, fromlist=["run"])
            results = module.run(config, output_dir)
            stage_result["status"] = "success"
            stage_result["assets"] = len(results)
            manifest["assets"].extend(results)

            for r in results:
                if "script" in r.get("type", ""):
                    total_scripts += 1
                else:
                    total_assets += 1

            print(f"  -> Generated {len(results)} items")

        except Exception as e:
            stage_result["status"] = "error"
            stage_result["error"] = str(e)
            print(f"  -> ERROR: {e}")
            import traceback
            traceback.print_exc()

        stage_result["time_s"] = round(time.time() - stage_start, 3)
        manifest["stages"].append(stage_result)
        print(f"  -> Time: {stage_result['time_s']}s")

    total_time = round(time.time() - total_start, 3)
    manifest["summary"] = {
        "total_assets": total_assets,
        "total_scripts": total_scripts,
        "total_items": total_assets + total_scripts,
        "total_time_s": total_time,
        "stages_passed": sum(1 for s in manifest["stages"] if s["status"] == "success"),
        "stages_failed": sum(1 for s in manifest["stages"] if s["status"] == "error"),
    }

    # Write manifest
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    # Print summary
    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"  Assets generated: {total_assets}")
    print(f"  Tool scripts generated: {total_scripts}")
    print(f"  Total time: {total_time}s")
    print(f"  Manifest: {manifest_path}")
    s = manifest["summary"]
    print(f"  Stages: {s['stages_passed']} passed, {s['stages_failed']} failed")
    print(f"{'='*60}\n")

    return manifest

def generate_report(config_path="config.yaml"):
    """Generate the technical report after pipeline run."""
    from automation.report_generator import generate_report as gen_report
    config = load_config(config_path)
    output_dir = config["output"]["root"]
    manifest_path = os.path.join(output_dir, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
        gen_report(config, manifest, output_dir)
    else:
        print("ERROR: Run pipeline first (no manifest.json found)")

if __name__ == "__main__":
    run_pipeline()
