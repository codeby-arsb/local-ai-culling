import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from pathlib import Path
from typing import List
from culler.engine.models import ImageRecord

logger = logging.getLogger(__name__)


def generate_profiling_report(records: List[ImageRecord], output_dir: Path):
    """
    Generates dataset statistics, histograms, correlation matrices,
    and a manual review CSV from a list of completed ImageRecords.
    """
    logger.info("Generating Profiling Report...")

    profiling_dir = output_dir / "profiling"
    profiling_dir.mkdir(parents=True, exist_ok=True)

    # 1. Convert records to DataFrame
    data = []
    for r in records:
        data.append(
            {
                "filename": r.filename,
                "blur_score": r.blur_score,
                "global_sharpness": r.global_sharpness,
                "subject_sharpness": r.subject_sharpness,
                "face_sharpness": r.face_sharpness,
                "eye_sharpness": r.eye_sharpness,
                "underexposure_score": r.underexposure_score,
                "overexposure_score": r.overexposure_score,
                "luminance_noise": r.luminance_noise,
                "color_noise": r.color_noise,
                "subject_visibility_score": r.subject_visibility_score,
                "face_confidence": r.face_confidence,
                "eye_confidence": r.eye_confidence,
                "subject_confidence": r.subject_confidence,
                "composition_score": r.composition_score,
                "tilt_angle": r.tilt_angle,
                "iso": r.exif.iso if r.exif else None,
                "editability_score": r.editability_score,
                "editability_confidence": r.editability_confidence,
                "shadow_recovery_score": r.shadow_recovery_score,
                "highlight_recovery_score": r.highlight_recovery_score,
                "recovery_noise": r.recovery_noise,
                "recovery_failure_reason": r.recovery_failure_reason,
                "duplicate_group_id": r.duplicate_group_id,
                "similarity_score": r.similarity_score,
                "perceptual_hash": r.perceptual_hash,
                "burst_rank_position": r.burst_rank_position,
                "burst_rank_score": r.burst_rank_score,
                "ranking_reasons": " | ".join(r.ranking_reasons)
                if r.ranking_reasons
                else "",
                "is_best_frame": r.is_best_frame,
                "classification": r.classification,
                "classification_score": r.classification_score,
                "confidence_score": r.confidence_score,
                "processing_time_ms": r.processing_time_ms,
                "classification_reasons": " | ".join(r.classification_reasons)
                if r.classification_reasons
                else "",
                "eye_state_score": r.eye_state_score,
                "expression_score": r.expression_score,
                "expression_type": r.expression_type,
                "expression_confidence": r.expression_confidence,
                "face_visibility_score": r.face_visibility_score,
                "face_quality_score": r.face_quality_score,
                "number_of_faces": r.number_of_faces,
                "primary_face_index": r.primary_face_index,
                "largest_face_ratio": r.largest_face_ratio,
            }
        )

    df = pd.DataFrame(data)

    # 2. Manual Review CSV
    csv_path = profiling_dir / "manual_review.csv"
    csv_columns = [
        "filename",
        "blur_score",
        "subject_sharpness",
        "face_sharpness",
        "eye_sharpness",
        "luminance_noise",
        "subject_visibility_score",
        "duplicate_group_id",
        "similarity_score",
        "perceptual_hash",
    ]
    df[csv_columns].to_csv(csv_path, index=False)
    logger.info(f"Saved manual review CSV to {csv_path}")

    # User-Requested Burst Outputs
    duplicate_groups_path = output_dir / "duplicate_groups.csv"
    df[
        ["filename", "duplicate_group_id", "perceptual_hash", "similarity_score"]
    ].to_csv(duplicate_groups_path, index=False)
    logger.info(f"Saved duplicate groups to {duplicate_groups_path}")

    burst_ranking_path = output_dir / "burst_ranking.csv"
    df[
        [
            "duplicate_group_id",
            "filename",
            "burst_rank_position",
            "burst_rank_score",
            "ranking_reasons",
            "is_best_frame",
        ]
    ].to_csv(burst_ranking_path, index=False)
    logger.info(f"Saved burst ranking to {burst_ranking_path}")

    # Shared logic for Classification / Validation Outputs
    classification_cols = [
        "filename",
        "classification",
        "classification_score",
        "confidence_score",
        "editability_score",
        "editability_confidence",
        "shadow_recovery_score",
        "highlight_recovery_score",
        "recovery_noise",
        "recovery_failure_reason",
        "processing_time_ms",
        "classification_reasons",
        "duplicate_group_id",
        "burst_rank_position",
        "is_best_frame",
        "eye_state_score",
        "expression_score",
        "expression_type",
        "expression_confidence",
        "face_visibility_score",
        "face_quality_score",
        "number_of_faces",
        "primary_face_index",
        "largest_face_ratio",
    ]

    def save_classification_csv(filename: str):
        path = output_dir / filename
        df[classification_cols].to_csv(path, index=False)
        logger.info(f"Saved classification output to {path}")

    save_classification_csv("classification.csv")

    # Temporarily keeping manual_validation.csv to avoid breaking external dependencies
    # It contains identical data to classification.csv.
    save_classification_csv("manual_validation.csv")

    # 3. Statistical Summary
    stats_path = profiling_dir / "statistical_summary.csv"
    # Describe generates count, mean, std, min, 25%, 50% (median), 75%, max
    stats_df = df.describe()
    stats_df.to_csv(stats_path)
    logger.info(f"Saved statistical summary to {stats_path}")

    # 4. Histograms Generation
    metrics_to_plot = [
        "global_sharpness",
        "subject_sharpness",
        "face_sharpness",
        "luminance_noise",
        "subject_visibility_score",
        "underexposure_score",
    ]

    for metric in metrics_to_plot:
        if metric in df.columns and not df[metric].isna().all():
            plt.figure(figsize=(10, 6))
            sns.histplot(df[metric].dropna(), kde=True, bins=30)
            plt.title(f"Distribution of {metric}")
            plt.xlabel(metric)
            plt.ylabel("Frequency")
            plot_path = profiling_dir / f"hist_{metric}.png"
            plt.savefig(plot_path)
            plt.close()

    # 5. Correlation Analysis
    plt.figure(figsize=(12, 10))
    # Select only numeric columns for correlation
    numeric_df = df.select_dtypes(include=["float64", "int64"])
    corr = numeric_df.corr()

    sns.heatmap(corr, annot=False, cmap="coolwarm", vmin=-1, vmax=1)
    plt.title("Metric Correlation Heatmap")
    plt.tight_layout()
    corr_path = profiling_dir / "correlation_heatmap.png"
    plt.savefig(corr_path)
    plt.close()

    # Save correlation raw data
    corr.to_csv(profiling_dir / "correlation_matrix.csv")
    logger.info(f"Saved histograms and correlation matrix to {profiling_dir}")
