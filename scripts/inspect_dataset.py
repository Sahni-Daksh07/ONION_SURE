"""
Dataset Inspection and Quality Analysis Script for ONION_SURE

Performs non-destructive quality analysis on the source dataset:
- Image decodability and corruption detection
- Image dimensions, channels, and aspect ratio analysis
- File size distribution and anomalies
- Exact duplicate detection (SHA256 hashing)
- Class balance and deep nested hierarchy distribution
Outputs structured report to data/reports/dataset_inspection_report.json
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from datetime import datetime, timezone
from PIL import Image

SOURCE_DIR = Path("Red and White Onion Dataset") / "New Onion"
OUTPUT_REPORT_DIR = Path("data") / "reports"
OUTPUT_REPORT_PATH = OUTPUT_REPORT_DIR / "dataset_inspection_report.json"


def inspect_single_image(filepath: Path, part: str, condition: str, subcategory: str):
    """Inspects a single image for corruption, dimensions, hash, and file size."""
    res = {
        "path": filepath.as_posix(),
        "part": part,
        "condition": condition,
        "subcategory": subcategory,
        "filename": filepath.name,
        "is_corrupt": False,
        "error": None,
        "size_bytes": 0,
        "width": 0,
        "height": 0,
        "aspect_ratio": 0.0,
        "mode": None,
        "sha256": None,
    }

    try:
        stat = filepath.stat()
        res["size_bytes"] = stat.st_size

        # Compute SHA256 for exact duplicate detection
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        res["sha256"] = hasher.hexdigest()

        # Check image decode
        with Image.open(filepath) as img:
            img.verify()  # Verifies file integrity header

        # Reopen to read dimensions and mode (verify closes file)
        with Image.open(filepath) as img:
            res["width"], res["height"] = img.size
            res["mode"] = img.mode
            if res["height"] > 0:
                res["aspect_ratio"] = round(res["width"] / res["height"], 3)
            # Ensure pixels can actually be decoded
            img.load()

    except Exception as e:
        res["is_corrupt"] = True
        res["error"] = str(e)

    return res


def main():
    print("=" * 60)
    print("ONION_SURE — Dataset Inspection & Quality Analysis")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Source Directory: {SOURCE_DIR}")
    print("=" * 60)

    if not SOURCE_DIR.exists():
        print(f"Error: Source directory '{SOURCE_DIR}' does not exist.")
        sys.exit(1)

    all_tasks = []
    print("Scanning directory structure recursively...")
    valid_extensions = {".jpg", ".jpeg", ".png"}

    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in valid_extensions:
                rel_parts = file_path.relative_to(SOURCE_DIR).parts
                part = rel_parts[0] if len(rel_parts) > 0 else "Unknown"
                condition = rel_parts[1] if len(rel_parts) > 1 else "Unknown"
                subcategory = "/".join(rel_parts[2:-1]) if len(rel_parts) > 3 else (rel_parts[2] if len(rel_parts) > 2 else "Root")
                all_tasks.append((file_path, part, condition, subcategory))

    total_files = len(all_tasks)
    print(f"Found {total_files} images across all subfolders.")
    print("Beginning multi-threaded inspection (workers=8)...")

    results = []
    completed = 0
    corrupt_count = 0
    hash_to_paths = defaultdict(list)
    dimensions_count = defaultdict(int)
    class_counts = defaultdict(int)
    detailed_counts = defaultdict(int)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(inspect_single_image, path, part, condition, subcat): path
            for path, part, condition, subcat in all_tasks
        }

        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1

            class_key = f"{res['part']}/{res['condition']}"
            class_counts[class_key] += 1
            detailed_key = f"{res['part']}/{res['condition']}/{res['subcategory']}"
            detailed_counts[detailed_key] += 1

            if res["is_corrupt"]:
                corrupt_count += 1
            else:
                dim_key = f"{res['width']}x{res['height']}"
                dimensions_count[dim_key] += 1
                if res["sha256"]:
                    hash_to_paths[res["sha256"]].append(res["path"])

            if completed % 3000 == 0 or completed == total_files:
                print(f"Progress: {completed}/{total_files} ({completed/total_files*100:.1f}%) — Corrupted: {corrupt_count}")

    # Analyze duplicates
    duplicates = {
        h: paths for h, paths in hash_to_paths.items() if len(paths) > 1
    }
    duplicate_image_count = sum(len(paths) - 1 for paths in duplicates.values())

    # File size stats (for non-corrupt)
    valid_sizes = [r["size_bytes"] for r in results if not r["is_corrupt"]]
    min_size = min(valid_sizes) if valid_sizes else 0
    max_size = max(valid_sizes) if valid_sizes else 0
    avg_size = (sum(valid_sizes) / len(valid_sizes)) if valid_sizes else 0

    # Summary report
    report = {
        "metadata": {
            "title": "ONION_SURE Dataset Inspection Report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_directory": SOURCE_DIR.as_posix(),
            "total_images_scanned": total_files,
            "total_valid_images": total_files - corrupt_count,
            "total_corrupt_images": corrupt_count,
            "total_exact_duplicate_groups": len(duplicates),
            "total_redundant_duplicate_images": duplicate_image_count,
        },
        "class_distribution": dict(class_counts),
        "detailed_hierarchy_distribution": dict(detailed_counts),
        "dimensions_distribution": dict(sorted(dimensions_count.items(), key=lambda x: x[1], reverse=True)[:20]),
        "file_size_stats_bytes": {
            "min": min_size,
            "max": max_size,
            "mean": round(avg_size, 2),
            "total_size_mb": round(sum(valid_sizes) / (1024 * 1024), 2),
        },
        "corrupt_files": [r for r in results if r["is_corrupt"]],
        "duplicate_groups_sample": [
            {"hash": h, "count": len(paths), "files": paths}
            for h, paths in list(duplicates.items())[:25]
        ],
    }

    OUTPUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("INSPECTION SUMMARY:")
    print(f"Total scanned: {total_files}")
    print(f"Valid images: {total_files - corrupt_count}")
    print(f"Corrupted images: {corrupt_count}")
    print(f"Exact duplicate groups: {len(duplicates)} (redundant images: {duplicate_image_count})")
    print(f"Top dimensions: {dict(list(report['dimensions_distribution'].items())[:5])}")
    print(f"Class breakdown: {dict(class_counts)}")
    print(f"Report written to: {OUTPUT_REPORT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
