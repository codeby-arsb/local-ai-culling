import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.feedback_server import run_server

import argparse

def print_banner():
    try:
        with open(Path(__file__).parent / "VERSION", "r") as f:
            version = f.read().strip()
    except FileNotFoundError:
        version = "Unknown"
    print(f"========================================")
    print(f" Local AI Culling Dashboard")
    print(f" Version {version}")
    print(f"========================================\n")

if __name__ == "__main__":
    print_banner()
    parser = argparse.ArgumentParser(description="Run the Image Culling Feedback Dashboard")
    parser.add_argument("--output", "-o", type=str, default="output", help="Path to the output directory")
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    if not output_dir.exists():
        print(f"Error: {output_dir}/ directory not found. Please run the main pipeline first.")
        sys.exit(1)
        
    print("Starting Feedback Dashboard...")
    run_server(output_dir=output_dir, port=8000)
