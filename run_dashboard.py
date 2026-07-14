import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from culler.dashboard.feedback_server import run_server  # noqa: E402
import argparse  # noqa: E402


def print_banner():
    try:
        with open(Path(__file__).parent / "VERSION", "r") as f:
            version = f.read().strip()
    except FileNotFoundError:
        version = "Unknown"
    print("========================================")
    print(" Local AI Culling Dashboard")
    print(f" Version {version}")
    print("========================================\n")


if __name__ == "__main__":
    print_banner()
    parser = argparse.ArgumentParser(
        description="Run the Image Culling Feedback Dashboard"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output",
        help="Path to the output directory",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    if not output_dir.exists():
        print(
            f"Error: {output_dir}/ directory not found. Please run the main pipeline first."
        )
        sys.exit(1)

    print("Starting Feedback Dashboard...")
    run_server(output_dir=output_dir, port=5000)
