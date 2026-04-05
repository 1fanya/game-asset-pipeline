"""
Game Asset Pipeline — Main Entry Point
Usage:
  python main.py generate   Run full asset pipeline
  python main.py serve      Launch web dashboard
  python main.py all        Generate + serve
"""
import sys, os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command in ("generate", "gen"):
        from automation.pipeline_runner import run_pipeline, load_config
        manifest = run_pipeline()
        # Generate report
        config = load_config()
        from automation.report_generator import generate_report
        generate_report(config, manifest, config["output"]["root"])

    elif command == "serve":
        from dashboard.app import create_app
        app = create_app()
        print("\n  Dashboard: http://localhost:5000\n")
        app.run(host="0.0.0.0", port=5000, debug=True)

    elif command == "all":
        from automation.pipeline_runner import run_pipeline, load_config
        manifest = run_pipeline()
        config = load_config()
        from automation.report_generator import generate_report
        generate_report(config, manifest, config["output"]["root"])
        from dashboard.app import create_app
        app = create_app()
        print("\n  Dashboard: http://localhost:5000\n")
        app.run(host="0.0.0.0", port=5000, debug=True)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
