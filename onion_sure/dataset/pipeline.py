"""
Reproducible Dataset Engineering Pipeline Orchestrator

Full End-to-End Pipeline:
1. Dataset Discovery & Multi-Threaded Quality Analysis (Blur, Brightness, Hashes)
2. Exact Duplicate Hashing & Perceptual Cluster Grouping
3. Cluster-Aware Stratified Train/Val/Test Splitting (No Leakage)
4. Comprehensive PS26031 Manifest Generation
5. Atomic File Persistence
"""

import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .analyzer import ImageQualityAnalyzer, DatasetScanner, ImageMetrics
from .duplicates import PerceptualDuplicateDetector
from .splitter import ClusterAwareSplitter
from .manifest import DatasetManifestGenerator

DEFAULT_SOURCE_DIR = Path("Red and White Onion Dataset") / "New Onion"
DEFAULT_OUTPUT_DIR = Path("data")


def run_dataset_pipeline(
    source_dir: Path = DEFAULT_SOURCE_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    workers: int = 8,
    random_seed: int = 42,
    hamming_threshold: int = 2,
    blur_threshold: float = 100.0,
    max_images: Optional[int] = None,
) -> Dict[str, Any]:
    print("=" * 70)
    print("ONION_SURE — Phase 1 Dataset Engineering Pipeline")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Source Directory: {source_dir}")
    print(f"Workers: {workers} | Seed: {random_seed} | Hamming Threshold: {hamming_threshold}")
    print("=" * 70)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory '{source_dir}' does not exist.")

    scanner = DatasetScanner(source_dir)
    file_tasks = scanner.discover_files()
    total_found = len(file_tasks)
    print(f"Discovered {total_found} image files in source dataset.")

    if max_images and max_images < total_found:
        file_tasks = file_tasks[:max_images]
        print(f"Subsetting to first {max_images} images for testing/sample execution.")

    total_tasks = len(file_tasks)
    analyzer = ImageQualityAnalyzer(blur_threshold=blur_threshold)

    print(f"Executing multi-threaded inspection on {total_tasks} images...")
    metrics_list = []
    completed = 0
    corrupt_count = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_task = {
            executor.submit(analyzer.analyze_image, path, part, cond, subcat): path
            for path, part, cond, subcat in file_tasks
        }

        for future in as_completed(future_to_task):
            m = future.result()
            metrics_list.append(m)
            completed += 1
            if m.is_corrupt:
                corrupt_count += 1

            if completed % 3000 == 0 or completed == total_tasks:
                pct = completed / total_tasks * 100
                print(f"Progress: {completed}/{total_tasks} ({pct:.1f}%) | Corrupt: {corrupt_count}")

    # 2. Duplicate Detection & Clustering
    print("\nDetecting exact and perceptual duplicates...")
    dup_detector = PerceptualDuplicateDetector(max_hamming_distance=hamming_threshold)
    exact_duplicates = dup_detector.find_exact_duplicates(metrics_list)
    cluster_map, cluster_info = dup_detector.cluster_perceptual_duplicates(metrics_list)
    print(f"Found {len(exact_duplicates)} exact duplicate groups.")
    print(f"Found {len(cluster_info)} multi-image perceptual duplicate clusters.")

    # 3. Cluster-Aware Stratified Splitting
    print("\nGenerating cluster-aware stratified train/val/test splits (70/15/15)...")
    splitter = ClusterAwareSplitter(random_seed=random_seed)
    split_result = splitter.split(metrics_list, cluster_map)
    summary = split_result["split_summary"]
    print(f"Train: {summary['train']['count']} ({summary['train']['percentage']}%)")
    print(f"Val:   {summary['val']['count']} ({summary['val']['percentage']}%)")
    print(f"Test:  {summary['test']['count']} ({summary['test']['percentage']}%)")

    # 4. Manifest Generation
    print("\nGenerating PS26031 dataset manifest...")
    manifest_gen = DatasetManifestGenerator(version="1.0.0")
    manifest = manifest_gen.generate(
        metrics_list=metrics_list,
        exact_duplicates=exact_duplicates,
        cluster_info=cluster_info,
        split_result=split_result,
        source_dir=source_dir.as_posix(),
    )

    # 5. Atomic Persistence
    manifests_dir = output_dir / "manifests"
    splits_dir = output_dir / "splits"
    reports_dir = output_dir / "reports"

    manifests_dir.mkdir(parents=True, exist_ok=True)
    splits_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = manifests_dir / "dataset_manifest_v1.0.0.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Persist split text files
    for split_name in ["train", "val", "test"]:
        txt_path = splits_dir / f"{split_name}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            for p in split_result["splits"][split_name]:
                f.write(f"{p}\n")

    # Persist concise quality summary
    summary_file = reports_dir / "dataset_quality_summary.json"
    concise_summary = {
        "dataset_name": manifest["dataset_name"],
        "manifest_version": manifest["manifest_version"],
        "timestamp": manifest["created_at"],
        "summary": manifest["summary"],
        "class_distribution": manifest["class_distribution"],
        "class_imbalance": manifest["class_imbalance"],
        "quality_metrics": manifest["quality_metrics"],
        "label_gap_audit": manifest["label_gap_audit"],
        "splits": manifest["splits"],
    }
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(concise_summary, f, indent=2)

    print("\n" + "=" * 70)
    print("PIPELINE EXECUTION COMPLETE:")
    print(f"- Dataset Manifest: {manifest_file}")
    print(f"- Quality Summary:  {summary_file}")
    print(f"- Split Files:      {splits_dir}/{{train,val,test}}.txt")
    print("=" * 70)

    return manifest


if __name__ == "__main__":
    run_dataset_pipeline()
