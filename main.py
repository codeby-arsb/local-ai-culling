import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import argparse  # noqa: E402
import logging  # noqa: E402
from culler.engine.pipeline import Pipeline  # noqa: E402
from culler.engine.config import AppConfig  # noqa: E402
from culler.engine.io.ingestion import ingest_folder  # noqa: E402
from culler.engine.io.preview import preview_generation_module  # noqa: E402
from culler.ai.blur import blur_analysis_module  # noqa: E402
from culler.ai.exposure import exposure_analysis_module  # noqa: E402
from culler.ai.noise import noise_analysis_module  # noqa: E402
from culler.ai.subject import subject_analysis_module  # noqa: E402
from culler.ai.face_eye import face_eye_analysis_module  # noqa: E402
from culler.ai.composition import composition_analysis_module  # noqa: E402
from culler.ai.editability import editability_analysis_module  # noqa: E402


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def print_banner():
    try:
        with open(Path(__file__).parent / "VERSION", "r") as f:
            version = f.read().strip()
    except FileNotFoundError:
        version = "Unknown"
    print("========================================")
    print(" Local AI Culling")
    print(f" Version {version}")
    print("========================================\n")


def main():
    print_banner()
    setup_logging()
    logger = logging.getLogger("CullingApp")

    AppConfig.load("config.yml")

    parser = argparse.ArgumentParser(
        description="Local AI Photographer Assistant (Version 1)"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        required=True,
        help="Input directory containing photos",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=True,
        help="Output directory for analysis results and previews",
    )
    parser.add_argument(
        "--profile", action="store_true", help="Run the dataset profiler after analysis"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists() or not input_path.is_dir():
        logger.error(
            f"Input directory does not exist or is not a directory: {input_path}"
        )
        sys.exit(1)

    output_path.mkdir(parents=True, exist_ok=True)

    # Create the cache directory for the extracted preview JPEGs
    cache_dir = output_path / ".internal" / "previews"
    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting photo analysis")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")

    # Initialize pipeline
    pipeline = Pipeline()

    # Add Phase 2 modules
    pipeline.add_module(preview_generation_module(cache_dir))

    # Add Phase 3 modules
    pipeline.add_module(blur_analysis_module())
    pipeline.add_module(exposure_analysis_module())
    pipeline.add_module(noise_analysis_module())

    # Phase 6C module
    pipeline.add_module(editability_analysis_module())

    # Phase 4 modules
    pipeline.add_module(subject_analysis_module())
    pipeline.add_module(face_eye_analysis_module())
    pipeline.add_module(composition_analysis_module())

    # Run Ingestion
    records = ingest_folder(input_path)
    logger.info(f"Initiated processing for {len(records)} records.")

    # Run pipeline
    processed_records = pipeline.process_batch(records)

    # Phase 5A: Duplicate Grouping
    from culler.ai.duplicates import group_duplicates, rank_burst_groups

    processed_records = group_duplicates(processed_records)

    # Phase 5A.6: Best Frame Selection
    processed_records = rank_burst_groups(processed_records)

    # Phase 5B: Rule-Based Classification
    from culler.ai.classification import classify_records

    processed_records = classify_records(processed_records)

    # Preview Cache Management
    from culler.engine.cache import CacheManager

    CacheManager(cache_dir, max_size_mb=500.0).enforce_limits()

    from culler.engine.analysis.metadata import export_metadata

    logger.info("Generating Scene Intelligence metadata...")
    export_metadata(processed_records, output_path)

    # Phase 4.5: Profiler & Output Generation
    if args.profile:
        from culler.engine.analysis.profiler import generate_profiling_report

        generate_profiling_report(processed_records, output_path)

        # Phase 5C: Visual Export Validation
        from culler.engine.io.visual_export import generate_visual_exports

        generate_visual_exports(processed_records, output_path)

    # Phase 7: Final Export Engine
    from culler.engine.io.export import run_final_export

    run_final_export(processed_records, output_path)

    logger.info("Analysis complete.")


if __name__ == "__main__":
    main()
