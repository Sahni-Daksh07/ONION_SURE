"""
Unit Tests for Phase 1 Dataset Engineering Subsystem
"""

import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
from PIL import Image

from onion_sure.dataset.analyzer import ImageQualityAnalyzer, ImageMetrics
from onion_sure.dataset.duplicates import (
    hamming_distance,
    PerceptualDuplicateDetector,
    DisjointSet,
)
from onion_sure.dataset.splitter import ClusterAwareSplitter
from onion_sure.dataset.manifest import DatasetManifestGenerator


@pytest.fixture
def temp_image_dir(tmp_path):
    """Creates temporary images for testing the analysis pipeline."""
    img_dir = tmp_path / "test_images"
    img_dir.mkdir()

    # Image 1: Sharp patterned image with normal exposure (mean ~135)
    arr1 = np.full((100, 100, 3), 128, dtype=np.uint8)
    arr1[::10, :] = 255
    arr1[:, ::10] = 0
    img1_path = img_dir / "sharp.jpg"
    Image.fromarray(arr1).save(img1_path)

    # Image 2: Exact duplicate of Image 1
    img2_path = img_dir / "duplicate_sharp.jpg"
    Image.fromarray(arr1).save(img2_path)

    # Image 3: Uniform gray (low contrast, blurry)
    arr3 = np.full((100, 100, 3), 128, dtype=np.uint8)
    img3_path = img_dir / "flat.jpg"
    Image.fromarray(arr3).save(img3_path)

    return {
        "dir": img_dir,
        "sharp1": img1_path,
        "sharp2": img2_path,
        "flat": img3_path,
    }


def test_image_quality_analyzer_metrics(temp_image_dir):
    """Tests decodability, sha256, dhash, blur, and exposure calculation."""
    analyzer = ImageQualityAnalyzer(blur_threshold=50.0)
    m = analyzer.analyze_image(
        filepath=temp_image_dir["sharp1"],
        part="Bulb",
        condition="Healthy",
        subcategory="Red Onion",
    )

    assert not m.is_corrupt
    assert m.width == 100
    assert m.height == 100
    assert m.size_bytes > 0
    assert len(m.sha256) == 64
    assert len(m.dhash) == 16
    assert m.blur_variance > 0
    assert not m.is_blurry
    assert not m.is_underexposed
    assert not m.is_overexposed


def test_dhash_and_exact_duplicates(temp_image_dir):
    """Verifies that exact clones produce identical SHA256 and dHash."""
    analyzer = ImageQualityAnalyzer()
    m1 = analyzer.analyze_image(temp_image_dir["sharp1"], "Bulb", "Healthy", "Red Onion")
    m2 = analyzer.analyze_image(temp_image_dir["sharp2"], "Bulb", "Healthy", "Red Onion")

    assert m1.sha256 == m2.sha256
    assert m1.dhash == m2.dhash
    assert hamming_distance(m1.dhash, m2.dhash) == 0

    detector = PerceptualDuplicateDetector(max_hamming_distance=2)
    exact_dups = detector.find_exact_duplicates([m1, m2])
    assert len(exact_dups) == 1

    cluster_map, clusters_info = detector.cluster_perceptual_duplicates([m1, m2])
    assert cluster_map[m1.path] == cluster_map[m2.path]
    assert len(clusters_info) == 1


def test_cluster_aware_splitter_prevents_leakage():
    """Guarantees that items in the same cluster are placed in the same split."""
    # Synthesize 20 items across 2 strata, with one cluster containing 3 items
    metrics = []
    cluster_map = {}
    for i in range(20):
        path = f"/mock/image_{i}.jpg"
        m = ImageMetrics(
            path=path,
            filename=f"image_{i}.jpg",
            part="Bulb",
            condition="Healthy" if i < 10 else "Unhealthy",
            subcategory="Red Onion",
            size_bytes=1000,
            width=1024,
            height=768,
        )
        metrics.append(m)
        # Images 0, 1, 2 share a near-duplicate cluster
        if i in [0, 1, 2]:
            cluster_map[path] = "cluster_shared_001"
        else:
            cluster_map[path] = f"cluster_single_{i}"

    splitter = ClusterAwareSplitter(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, random_seed=42)
    split_res = splitter.split(metrics, cluster_map)

    train_set = set(split_res["splits"]["train"])
    val_set = set(split_res["splits"]["val"])
    test_set = set(split_res["splits"]["test"])

    # Disjointness
    assert len(train_set.intersection(val_set)) == 0
    assert len(train_set.intersection(test_set)) == 0
    assert len(val_set.intersection(test_set)) == 0
    assert len(train_set) + len(val_set) + len(test_set) == 20

    # Cluster isolation check: images 0, 1, 2 must all be in the same split
    c_images = {"/mock/image_0.jpg", "/mock/image_1.jpg", "/mock/image_2.jpg"}
    in_train = c_images.issubset(train_set)
    in_val = c_images.issubset(val_set)
    in_test = c_images.issubset(test_set)
    assert in_train or in_val or in_test, "Near-duplicate cluster was split across splits!"


def test_manifest_generator_label_audit():
    """Ensures the manifest generator accurately identifies missing PS26031 labels."""
    generator = DatasetManifestGenerator(version="1.0.0")
    dummy_metric = ImageMetrics(
        path="/mock/img.jpg",
        filename="img.jpg",
        part="Bulb",
        condition="Healthy",
        subcategory="Red Onion",
        width=1024,
        height=768,
        blur_variance=150.0,
        mean_brightness=120.0,
        contrast_std=45.0,
    )
    manifest = generator.generate(
        metrics_list=[dummy_metric],
        exact_duplicates={},
        cluster_info=[],
        split_result={"split_summary": {"train": {"count": 1, "percentage": 100.0}}, "strata_breakdown": {}},
        source_dir="mock/dir",
    )

    assert manifest["manifest_version"] == "1.0.0"
    gap = manifest["label_gap_audit"]["gap_summary"]
    assert gap["label_fabrication_prohibited"] is True
    assert "damaged" in gap["missing_fine_grained_labels"]
    assert "rotten" in gap["missing_fine_grained_labels"]
    assert "sprouted" in gap["missing_fine_grained_labels"]
