"""
Image Quality and Dataset Metrics Analyzer

Calculates:
- Decodability and corruption detection
- Image dimensions, channels, aspect ratio
- Exact SHA256 hash
- 64-bit Perceptual Difference Hash (dHash)
- Blur metrics via Laplacian variance (scipy.ndimage.laplace)
- Luminance / brightness, contrast, and exposure flags
"""

import os
import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any, List
import numpy as np
from PIL import Image
from scipy.ndimage import laplace


@dataclass
class ImageMetrics:
    path: str
    filename: str
    part: str                     # Bulb or Leaves
    condition: str                # Healthy or Unhealthy
    subcategory: str              # e.g., Mixed/1WO9RO, Red Onion, Multiple, Single
    is_corrupt: bool = False
    error_message: Optional[str] = None
    size_bytes: int = 0
    width: int = 0
    height: int = 0
    aspect_ratio: float = 0.0
    channels: str = "RGB"
    sha256: Optional[str] = None
    dhash: Optional[str] = None   # 16-hex-digit perceptual hash (64-bit)
    blur_variance: float = 0.0    # Laplacian variance (higher = sharper)
    is_blurry: bool = False       # Flag if variance < blur_threshold
    mean_brightness: float = 0.0  # 0.0 to 255.0
    contrast_std: float = 0.0     # Standard deviation of pixel intensities
    is_underexposed: bool = False # Flag if mean < 50
    is_overexposed: bool = False  # Flag if mean > 215

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ImageQualityAnalyzer:
    """Analyzes image decodability, hashes, blur, and exposure without modifying source data."""

    def __init__(
        self,
        blur_threshold: float = 100.0,
        underexposed_threshold: float = 50.0,
        overexposed_threshold: float = 215.0,
        standard_blur_size: int = 256,
    ):
        self.blur_threshold = blur_threshold
        self.underexposed_threshold = underexposed_threshold
        self.overexposed_threshold = overexposed_threshold
        self.standard_blur_size = standard_blur_size

    def compute_dhash(self, img_gray: Image.Image) -> str:
        """Computes 64-bit Difference Hash (dHash) from grayscale PIL Image."""
        # Resize to 9x8 (9 columns, 8 rows)
        resized = img_gray.resize((9, 8), Image.Resampling.BILINEAR)
        pixels = np.asarray(resized, dtype=np.int16)
        # Compute adjacent difference (8x8 boolean matrix)
        diff = pixels[:, 1:] > pixels[:, :-1]
        # Pack 64 booleans into 64-bit integer
        bit_val = 0
        for bit in diff.flatten():
            bit_val = (bit_val << 1) | int(bit)
        return f"{bit_val:016x}"

    def analyze_image(
        self,
        filepath: Path,
        part: str,
        condition: str,
        subcategory: str,
    ) -> ImageMetrics:
        metrics = ImageMetrics(
            path=filepath.as_posix(),
            filename=filepath.name,
            part=part,
            condition=condition,
            subcategory=subcategory,
        )

        try:
            stat = filepath.stat()
            metrics.size_bytes = stat.st_size

            # 1. SHA256 exact hash
            hasher = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
            metrics.sha256 = hasher.hexdigest()

            # 2. Decode verification
            with Image.open(filepath) as img:
                img.verify()

            # 3. Reload image to extract properties and pixels
            with Image.open(filepath) as img:
                metrics.width, metrics.height = img.size
                metrics.channels = img.mode
                if metrics.height > 0:
                    metrics.aspect_ratio = round(metrics.width / metrics.height, 3)

                # Convert to grayscale for dHash and optical metrics
                gray_img = img.convert("L")
                metrics.dhash = self.compute_dhash(gray_img)

                # Standardized blur analysis (scale-invariant Laplacian variance)
                blur_resized = gray_img.resize(
                    (self.standard_blur_size, self.standard_blur_size),
                    Image.Resampling.BILINEAR,
                )
                gray_arr = np.asarray(blur_resized, dtype=np.float32)
                lap = laplace(gray_arr)
                metrics.blur_variance = round(float(lap.var()), 2)
                metrics.is_blurry = metrics.blur_variance < self.blur_threshold

                # Luminance / Brightness & Contrast
                # Use raw grayscale array for exposure assessment
                full_gray_arr = np.asarray(gray_img, dtype=np.float32)
                metrics.mean_brightness = round(float(full_gray_arr.mean()), 2)
                metrics.contrast_std = round(float(full_gray_arr.std()), 2)
                metrics.is_underexposed = metrics.mean_brightness < self.underexposed_threshold
                metrics.is_overexposed = metrics.mean_brightness > self.overexposed_threshold

        except Exception as e:
            metrics.is_corrupt = True
            metrics.error_message = str(e)

        return metrics


class DatasetScanner:
    """Recursively scans and analyzes images in the dataset."""

    def __init__(self, source_dir: Path, analyzer: Optional[ImageQualityAnalyzer] = None):
        self.source_dir = source_dir
        self.analyzer = analyzer or ImageQualityAnalyzer()

    def discover_files(self) -> List[tuple]:
        """Discovers all supported image files and their hierarchy parts."""
        valid_extensions = {".jpg", ".jpeg", ".png"}
        tasks = []
        for root, _, files in os.walk(self.source_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in valid_extensions:
                    rel_parts = file_path.relative_to(self.source_dir).parts
                    part = rel_parts[0] if len(rel_parts) > 0 else "Unknown"
                    condition = rel_parts[1] if len(rel_parts) > 1 else "Unknown"
                    subcat = "/".join(rel_parts[2:-1]) if len(rel_parts) > 3 else (rel_parts[2] if len(rel_parts) > 2 else "Root")
                    tasks.append((file_path, part, condition, subcat))
        return tasks
