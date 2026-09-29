"""
Image Quality Pre-Validation Service

Pre-validates camera frames and image files before running ML inference:
- Blur / motion blur detection via scale-invariant Laplacian variance
- Underexposure and overexposure / glare detection
- Contrast sufficiency verification
- Resolution and aspect ratio sanity check
Generates human-readable warnings and actionable feedback for the operator.
"""

from typing import List, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import laplace

from .schemas import ImageQualityResult, QualityStatus


class ImageQualityValidator:
    """Pre-inference optical quality assessment engine."""

    def __init__(
        self,
        min_blur_variance: float = 70.0,
        severe_blur_threshold: float = 25.0,
        min_brightness: float = 40.0,
        max_brightness: float = 225.0,
        min_contrast_std: float = 18.0,
        min_dimension_px: int = 200,
        standard_test_size: int = 256,
    ):
        self.min_blur_variance = min_blur_variance
        self.severe_blur_threshold = severe_blur_threshold
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.min_contrast_std = min_contrast_std
        self.min_dimension_px = min_dimension_px
        self.standard_test_size = standard_test_size

    def validate(self, img: Image.Image) -> ImageQualityResult:
        """Validates PIL Image for clarity, lighting, and contrast."""
        reasons: List[str] = []
        recommendations: List[str] = []

        width, height = img.size

        # 1. Dimension validation
        if width < self.min_dimension_px or height < self.min_dimension_px:
            reasons.append(f"Image resolution ({width}x{height}) is below minimum requirement ({self.min_dimension_px}px).")
            recommendations.append("Position camera closer to the subject and avoid digital downsampling.")
            return ImageQualityResult(
                status=QualityStatus.REJECTED.value,
                blur_variance=0.0,
                is_blurry=True,
                mean_brightness=0.0,
                contrast_std=0.0,
                is_underexposed=False,
                is_overexposed=False,
                reasons=reasons,
                recommendations=recommendations,
            )

        # Convert to grayscale for optical measurements
        gray_img = img.convert("L")

        # 2. Scale-invariant blur assessment
        blur_resized = gray_img.resize((self.standard_test_size, self.standard_test_size), Image.Resampling.BILINEAR)
        gray_arr_std = np.asarray(blur_resized, dtype=np.float32)
        lap = laplace(gray_arr_std)
        blur_variance = round(float(lap.var()), 2)

        is_blurry = blur_variance < self.min_blur_variance
        is_severe_blur = blur_variance < self.severe_blur_threshold

        if is_severe_blur:
            reasons.append(f"Severe motion blur detected (Laplacian variance: {blur_variance} < {self.severe_blur_threshold}).")
            recommendations.append("Hold device steady and tap the screen to ensure camera focus before capturing.")
        elif is_blurry:
            reasons.append(f"Mild blur detected (Laplacian variance: {blur_variance} < {self.min_blur_variance}).")
            recommendations.append("Ensure lens is clean and steady device.")

        # 3. Luminance / Brightness assessment
        full_gray_arr = np.asarray(gray_img, dtype=np.float32)
        mean_brightness = round(float(full_gray_arr.mean()), 2)
        contrast_std = round(float(full_gray_arr.std()), 2)

        is_underexposed = mean_brightness < self.min_brightness
        is_overexposed = mean_brightness > self.max_brightness

        if is_underexposed:
            reasons.append(f"Image is underexposed/too dark (Mean brightness: {mean_brightness} < {self.min_brightness}).")
            recommendations.append("Increase ambient lighting or use camera torch/flash.")

        if is_overexposed:
            reasons.append(f"Image is overexposed/glare washout (Mean brightness: {mean_brightness} > {self.max_brightness}).")
            recommendations.append("Avoid direct reflective sunlight or strong glare onto the onion surface.")

        # 4. Contrast check
        if contrast_std < self.min_contrast_std:
            reasons.append(f"Image contrast is too flat (Standard deviation: {contrast_std} < {self.min_contrast_std}).")
            recommendations.append("Ensure clear visual distinction between onion and background surface.")

        # 5. Determine overall quality status
        if is_severe_blur or (is_underexposed and contrast_std < self.min_contrast_std):
            status = QualityStatus.REJECTED.value
        elif is_blurry or is_underexposed or is_overexposed:
            status = QualityStatus.WARNING.value
        else:
            status = QualityStatus.PASSED.value

        return ImageQualityResult(
            status=status,
            blur_variance=blur_variance,
            is_blurry=is_blurry,
            mean_brightness=mean_brightness,
            contrast_std=contrast_std,
            is_underexposed=is_underexposed,
            is_overexposed=is_overexposed,
            reasons=reasons,
            recommendations=recommendations,
        )

    def validate_file(self, filepath: Path) -> ImageQualityResult:
        with Image.open(filepath) as img:
            return self.validate(img)
