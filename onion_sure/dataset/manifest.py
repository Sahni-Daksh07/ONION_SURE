"""
Dataset Manifest Generator for ONION_SURE

Generates standardized JSON manifest including:
- Metadata, version, timestamp, seed
- Complete class distribution and hierarchy
- Class imbalance metrics (majority/minority counts, imbalance ratio)
- Blur, brightness, contrast, and dimension metrics
- Available labels vs PS26031 missing labels documentation
- Perceptual and exact duplicate statistics
- Split allocations and checksums
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from collections import defaultdict
import numpy as np

from .analyzer import ImageMetrics


class DatasetManifestGenerator:
    """Produces the comprehensive, standardized PS26031-compliant dataset manifest."""

    def __init__(self, version: str = "1.0.0", dataset_name: str = "ONION_SURE_Source_V1"):
        self.version = version
        self.dataset_name = dataset_name

    def generate(
        self,
        metrics_list: List[ImageMetrics],
        exact_duplicates: Dict[str, List[str]],
        cluster_info: List[Dict[str, Any]],
        split_result: Dict[str, Any],
        source_dir: str,
    ) -> Dict[str, Any]:
        total_scanned = len(metrics_list)
        corrupted = [m for m in metrics_list if m.is_corrupt]
        valid = [m for m in metrics_list if not m.is_corrupt]
        total_valid = len(valid)

        # 1. Class Counts & Hierarchy
        class_counts = defaultdict(int)
        part_counts = defaultdict(int)
        condition_counts = defaultdict(int)
        detailed_hierarchy = defaultdict(int)

        for m in valid:
            class_counts[f"{m.part}/{m.condition}"] += 1
            part_counts[m.part] += 1
            condition_counts[m.condition] += 1
            detailed_hierarchy[f"{m.part}/{m.condition}/{m.subcategory}"] += 1

        # 2. Imbalance Analysis
        bulb_healthy = class_counts.get("Bulb/Healthy", 0)
        bulb_unhealthy = class_counts.get("Bulb/Unhealthy", 0)
        leaves_healthy = class_counts.get("Leaves/Healthy", 0)
        leaves_unhealthy = class_counts.get("Leaves/Unhealthy", 0)

        bulb_ratio = round(bulb_healthy / bulb_unhealthy, 2) if bulb_unhealthy else 0.0
        leaves_ratio = round(leaves_healthy / leaves_unhealthy, 2) if leaves_unhealthy else 0.0

        imbalance_report = {
            "bulb": {
                "healthy_count": bulb_healthy,
                "unhealthy_count": bulb_unhealthy,
                "imbalance_ratio": f"{bulb_ratio}:1 (Healthy:Unhealthy)",
                "healthy_percentage": round(bulb_healthy / (bulb_healthy + bulb_unhealthy) * 100, 2) if (bulb_healthy + bulb_unhealthy) else 0,
                "unhealthy_percentage": round(bulb_unhealthy / (bulb_healthy + bulb_unhealthy) * 100, 2) if (bulb_healthy + bulb_unhealthy) else 0,
                "mitigation_required": "Class-weighted loss function or stratified re-sampling for Bulb training.",
            },
            "leaves": {
                "healthy_count": leaves_healthy,
                "unhealthy_count": leaves_unhealthy,
                "imbalance_ratio": f"{leaves_ratio}:1 (Healthy:Unhealthy)",
                "healthy_percentage": round(leaves_healthy / (leaves_healthy + leaves_unhealthy) * 100, 2) if (leaves_healthy + leaves_unhealthy) else 0,
                "unhealthy_percentage": round(leaves_unhealthy / (leaves_healthy + leaves_unhealthy) * 100, 2) if (leaves_healthy + leaves_unhealthy) else 0,
                "status": "Balanced distribution (nearly 1:1 ratio).",
            },
        }

        # 3. Optical & Quality Statistics (Blur, Brightness, Dimensions)
        blur_values = [m.blur_variance for m in valid]
        brightness_values = [m.mean_brightness for m in valid]
        contrast_values = [m.contrast_std for m in valid]
        blurry_count = sum(1 for m in valid if m.is_blurry)
        underexposed_count = sum(1 for m in valid if m.is_underexposed)
        overexposed_count = sum(1 for m in valid if m.is_overexposed)

        dimensions_count = defaultdict(int)
        for m in valid:
            dimensions_count[f"{m.width}x{m.height}"] += 1

        quality_stats = {
            "dimensions_distribution": dict(sorted(dimensions_count.items(), key=lambda x: x[1], reverse=True)),
            "blur_laplacian_variance": {
                "mean": round(float(np.mean(blur_values)), 2) if blur_values else 0,
                "std": round(float(np.std(blur_values)), 2) if blur_values else 0,
                "min": round(float(np.min(blur_values)), 2) if blur_values else 0,
                "max": round(float(np.max(blur_values)), 2) if blur_values else 0,
                "blurry_images_flagged": blurry_count,
                "blurry_percentage": round(blurry_count / total_valid * 100, 2) if total_valid else 0,
            },
            "brightness_luminance_0_to_255": {
                "mean": round(float(np.mean(brightness_values)), 2) if brightness_values else 0,
                "std": round(float(np.std(brightness_values)), 2) if brightness_values else 0,
                "underexposed_flagged": underexposed_count,
                "underexposed_percentage": round(underexposed_count / total_valid * 100, 2) if total_valid else 0,
                "overexposed_flagged": overexposed_count,
                "overexposed_percentage": round(overexposed_count / total_valid * 100, 2) if total_valid else 0,
            },
            "contrast_standard_deviation": {
                "mean": round(float(np.mean(contrast_values)), 2) if contrast_values else 0,
                "std": round(float(np.std(contrast_values)), 2) if contrast_values else 0,
            },
        }

        # 4. Label Gap Analysis (PS26031 Compliance)
        label_gap_analysis = {
            "source_dataset_available_labels": [
                {"part": "Bulb", "condition": "Healthy", "subcategories": ["Mixed (1WO9RO-9WO1RO)", "Red Onion", "White Onion"]},
                {"part": "Bulb", "condition": "Unhealthy", "subcategories": ["Red Onion", "White Onion"]},
                {"part": "Leaves", "condition": "Healthy", "subcategories": ["Multiple", "Single"]},
                {"part": "Leaves", "condition": "Unhealthy", "subcategories": ["Multiple", "Single"]},
            ],
            "ps26031_mandatory_labels": [
                "healthy",
                "damaged",
                "rotten",
                "sprouted",
                "undersized (physical measurement)",
            ],
            "gap_summary": {
                "label_fabrication_prohibited": True,
                "unhealthy_class_nature": "Coarse superset containing unknown proportions of rot, physical damage, and sprouting.",
                "missing_fine_grained_labels": ["damaged", "rotten", "sprouted"],
                "missing_instance_annotations": "Bounding boxes for multi-onion images (Mixed and Multiple classes).",
                "missing_calibration_references": "Physical scale reference (ArUco / coin / ruler) for millimeter sizing.",
                "recommendation": "Maintain Healthy as ground-truth healthy; establish evidence-based sub-annotation workflow to partition Unhealthy."
            }
        }

        # 5. Assemble Manifest
        manifest = {
            "manifest_version": self.version,
            "dataset_name": self.dataset_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_directory": source_dir,
            "summary": {
                "total_images_scanned": total_scanned,
                "valid_images": total_valid,
                "corrupted_images": len(corrupted),
                "exact_duplicate_groups": len(exact_duplicates),
                "perceptual_duplicate_clusters": len(cluster_info),
            },
            "class_distribution": {
                "by_part_and_condition": dict(class_counts),
                "by_part": dict(part_counts),
                "by_condition": dict(condition_counts),
                "detailed_hierarchy": dict(detailed_hierarchy),
            },
            "class_imbalance": imbalance_report,
            "quality_metrics": quality_stats,
            "label_gap_audit": label_gap_analysis,
            "splits": split_result["split_summary"],
            "strata_splits": split_result["strata_breakdown"],
            "corrupt_file_details": [m.to_dict() for m in corrupted],
            "perceptual_duplicate_clusters_sample": cluster_info[:25],
        }

        return manifest
