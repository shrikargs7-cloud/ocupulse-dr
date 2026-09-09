"""
OcuPulse Retinal Lesion Detection

Deterministic, classical computer-vision detectors for the four lesion classes
that drive diabetic-retinopathy grading:

* **Microaneurysms** - small, round, dark red outpouchings of capillaries. The
  earliest clinically visible sign of DR.
* **Haemorrhages** - larger, irregular dark red blotches from ruptured vessels.
* **Exudates** - bright yellow-white lipid deposits leaking from compromised
  vessels; the hallmark of macular oedema risk.
* **Drusen** - small pale deposits, reported separately because they are an
  age-related finding rather than a DR finding.

Each detector is a morphological contrast filter (black-hat for dark lesions,
top-hat for bright ones) followed by shape, size and colour gating. Optic-disc
and vessel pixels are explicitly excluded, because those are by far the largest
sources of false positives: the disc rim reads as bright exudate and the
vasculature reads as dark haemorrhage.

Landmarks
---------
Lesion *location* matters as much as lesion count - a microaneurysm within one
disc diameter of the fovea threatens central vision, while the same lesion far
in the periphery does not. :func:`detect_optic_disc` and
:func:`estimate_fovea_center` therefore run first, and every reported lesion
carries its distance from the fovea in disc diameters (DD), the standard
clinical unit.

This module intentionally uses no deep-learning runtime. See
``docs/MATLAB_integration.md`` and the project README for the upgrade path to a
trained detector.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np

from ..config import settings

#: Lesion classes reported by the detector.
LESION_TYPES: Tuple[str, ...] = (
    "microaneurysm",
    "hemorrhage",
    "exudate",
    "drusen",
)

#: Clinical weight of each lesion class when computing the burden index.
#: Haemorrhages and exudates indicate more advanced disease than isolated MAs.
LESION_WEIGHTS: Dict[str, float] = {
    "microaneurysm": 1.0,
    "hemorrhage": 2.5,
    "exudate": 3.0,
    "drusen": 0.5,
}

#: Hard cap on reported lesions, keeping API payloads bounded on severe cases.
MAX_REPORTED_LESIONS = 400


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _to_uint8_gray(image: np.ndarray) -> np.ndarray:
    """Convert any input image to a single-channel uint8 array."""
    if image.ndim == 2:
        return image.astype(np.uint8)
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _channel(image: np.ndarray, index: int) -> np.ndarray:
    """
    Extract a colour channel, tolerating grayscale input.

    Args:
        image: BGR image or 2-D grayscale array.
        index: Channel index (0=blue, 1=green, 2=red in OpenCV's BGR order).

    Returns:
        2-D uint8 channel.
    """
    if image.ndim == 2:
        return image.astype(np.uint8)
    if image.shape[2] <= index:
        return _to_uint8_gray(image)
    return image[:, :, index].astype(np.uint8)


def _binary_from_mask(mask: Optional[np.ndarray], shape: Tuple[int, int]) -> np.ndarray:
    """Return a 0/255 uint8 mask, or an all-255 mask when ``mask`` is ``None``."""
    if mask is None:
        return np.full(shape[:2], 255, dtype=np.uint8)
    binary = (np.asarray(mask) > 0).astype(np.uint8) * 255
    if binary.shape[:2] != tuple(shape[:2]):
        binary = cv2.resize(binary, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
    return binary


def _scale_kernel(image_shape: Tuple[int, ...], fraction: float, minimum: int = 3) -> int:
    """Derive an odd kernel size as a fraction of the image's smaller side."""
    smallest = min(image_shape[0], image_shape[1])
    size = int(round(smallest * fraction))
    size = max(minimum, size)
    if size % 2 == 0:
        size += 1
    return size


def _restrict_to_region(response: np.ndarray, region_mask: np.ndarray) -> np.ndarray:
    """
    Zero a float response map outside ``region_mask``.

    ``cv2.bitwise_and`` with a mask argument leaves unmasked pixels
    uninitialised for freshly allocated float arrays, which silently injects
    garbage into the detector statistics. Multiplication is explicit and safe.

    Args:
        response: Float32 response map.
        region_mask: Binary uint8 mask, 255 inside the region of interest.

    Returns:
        Float32 response with everything outside the mask set to zero.
    """
    return (response * ((region_mask > 0).astype(np.float32))).astype(np.float32)


def _local_response(
    channel_image: np.ndarray,
    morphology: int,
    kernel_fraction: float = 0.035,
    background_fraction: float = 0.12,
    preblur: bool = True,
) -> np.ndarray:
    """
    Build a local-contrast response map emphasising small blobs.

    Morphological black-hat (dark spots) or top-hat (bright spots) is computed
    at a lesion-scale kernel, then a large-scale background estimate is
    subtracted so broad illumination gradients do not masquerade as lesions.

    The channel is Gaussian-smoothed first. Fundus sensors contribute
    pixel-level noise that the morphology would otherwise amplify into hundreds
    of candidate blobs; smoothing at a scale well below lesion diameter removes
    that noise while leaving true lesions intact.

    Args:
        channel_image: 2-D uint8 channel to filter.
        morphology: ``cv2.MORPH_BLACKHAT`` or ``cv2.MORPH_TOPHAT``.
        kernel_fraction: Blob-scale structuring element as a fraction of image size.
        background_fraction: Background-estimation blur as a fraction of image size.
        preblur: Whether to apply sensor-noise suppression first.

    Returns:
        Float32 response map, higher meaning stronger local contrast.
    """
    if preblur:
        sigma = max(0.6, min(channel_image.shape[:2]) * settings.lesions.preblur_sigma_fraction)
        channel_image = cv2.GaussianBlur(channel_image, (0, 0), sigmaX=sigma)

    blob_kernel_size = _scale_kernel(channel_image.shape, kernel_fraction)
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (blob_kernel_size, blob_kernel_size)
    )
    response = cv2.morphologyEx(channel_image, morphology, kernel).astype(np.float32)

    background_size = _scale_kernel(channel_image.shape, background_fraction)
    if background_size % 2 == 0:
        background_size += 1
    background = cv2.GaussianBlur(response, (background_size, background_size), 0)

    return response - background


def _adaptive_blob_threshold(response: np.ndarray, roi_mask: np.ndarray, sigma: float) -> np.ndarray:
    """
    Threshold a response map at ``mean + sigma * std`` measured inside the ROI.

    Deriving the cutoff from the image's own statistics makes the detector
    adapt across cameras and exposure settings instead of relying on an
    absolute intensity that only suits one device.

    Args:
        response: Float32 local-contrast response.
        roi_mask: Binary ROI mask (0/255).
        sigma: Number of standard deviations above the mean to cut at.

    Returns:
        Binary uint8 candidate mask.
    """
    inside = response[roi_mask > 0]
    if inside.size < 64:
        inside = response.ravel()
    if inside.size == 0:
        return np.zeros(response.shape[:2], dtype=np.uint8)

    mean = float(np.mean(inside))
    std = float(np.std(inside))
    cutoff = mean + max(1.0, sigma) * std

    _, binary = cv2.threshold(response.astype(np.float32), cutoff, 255, cv2.THRESH_BINARY)
    return binary.astype(np.uint8)


def _channel_stats(
    channel: np.ndarray,
    roi_binary: np.ndarray,
) -> Tuple[float, float]:
    """
    Mean and standard deviation of one channel measured inside the retinal ROI.

    Used to set the absolute-intensity gate that separates a genuine lesion from
    a merely locally-contrasty patch of ordinary background.

    Args:
        channel: Single-channel float or uint8 array.
        roi_binary: Binary ROI mask (0/255) defining the measurement region.

    Returns:
        ``(mean, std)`` of the channel over ROI pixels. Returns ``(0.0, 0.0)``
        when the ROI is empty, which makes any gate built from it reject
        everything rather than accept everything.
    """
    data = channel.astype(np.float32)
    inside = data[roi_binary > 0]
    if inside.size == 0:
        return 0.0, 0.0
    return float(np.mean(inside)), float(np.std(inside))


def _describe_components(
    candidate_mask: np.ndarray,
    response: np.ndarray,
    response_threshold: float,
    intensity: Optional[np.ndarray] = None,
) -> List[Dict[str, Any]]:
    """
    Measure every connected candidate blob.

    Args:
        candidate_mask: Binary mask of thresholded candidates.
        response: Local-contrast response used to score each blob.
        response_threshold: Cutoff that produced ``candidate_mask``.
        intensity: Optional source channel, used to record each blob's absolute
            mean intensity so callers can reject blobs that are locally
            contrasty but not genuinely bright or dark.

    Returns:
        List of per-blob dictionaries with exact pixel area, centroid,
        perimeter, circularity, solidity, peak/mean contrast and mean intensity.
    """
    if int(np.count_nonzero(candidate_mask)) == 0:
        return []

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        candidate_mask, connectivity=8
    )

    blobs: List[Dict[str, Any]] = []
    for index in range(1, num_labels):
        left = int(stats[index, cv2.CC_STAT_LEFT])
        top = int(stats[index, cv2.CC_STAT_TOP])
        width = int(stats[index, cv2.CC_STAT_WIDTH])
        height = int(stats[index, cv2.CC_STAT_HEIGHT])
        area_px = int(stats[index, cv2.CC_STAT_AREA])

        if area_px <= 0:
            continue

        component = (labels[top:top + height, left:left + width] == index).astype(np.uint8) * 255
        contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        perimeter = float(sum(cv2.arcLength(c, True) for c in contours)) if contours else 0.0
        hull_area = 0.0
        if contours:
            largest = max(contours, key=cv2.contourArea)
            hull = cv2.convexHull(largest)
            hull_area = float(cv2.contourArea(hull))

        # Circularity 4*pi*A/P^2 is 1.0 for a perfect disc and falls off for
        # elongated or ragged shapes - the key MA-vs-haemorrhage discriminator.
        circularity = (4.0 * math.pi * area_px / (perimeter ** 2)) if perimeter > 0 else 0.0
        solidity = (area_px / hull_area) if hull_area > 0 else 0.0

        region_response = response[top:top + height, left:left + width][component > 0]
        peak_contrast = float(np.max(region_response)) if region_response.size else 0.0
        mean_contrast = float(np.mean(region_response)) if region_response.size else 0.0

        mean_intensity = None
        if intensity is not None:
            region_intensity = intensity[top:top + height, left:left + width][component > 0]
            if region_intensity.size:
                mean_intensity = round(float(np.mean(region_intensity)), 2)

        centroid_x, centroid_y = centroids[index]
        blob: Dict[str, Any] = {
            "x": float(centroid_x),
            "y": float(centroid_y),
            "bbox": (left, top, width, height),
            "area_px": area_px,
            "perimeter_px": round(perimeter, 2),
            "circularity": round(float(np.clip(circularity, 0.0, 1.0)), 4),
            "solidity": round(float(np.clip(solidity, 0.0, 1.0)), 4),
            "aspect_ratio": round(
                float(max(width, height) / max(1, min(width, height))), 3
            ),
            "peak_contrast": round(peak_contrast, 3),
            "mean_contrast": round(mean_contrast, 3),
            "contrast_margin": round(peak_contrast - response_threshold, 3),
        }
        if mean_intensity is not None:
            blob["mean_intensity"] = mean_intensity

        blobs.append(blob)

    return blobs


# ---------------------------------------------------------------------------
# Landmark localisation
# ---------------------------------------------------------------------------

def _large_scale_background(gray: np.ndarray, sigma: float) -> np.ndarray:
    """
    Estimate the smooth illumination field underlying a fundus photograph.

    Blurring at a large sigma directly is expensive, so the image is shrunk,
    blurred at the proportionally reduced sigma, and upsampled again. The result
    tracks slow vignetting and choroidal gradients while ignoring structures at
    the scale of the optic disc.

    Args:
        gray: Single-channel uint8 luminance image.
        sigma: Gaussian sigma, in pixels of the *full-resolution* image.

    Returns:
        Full-resolution float32 background estimate.
    """
    sigma = max(1.0, float(sigma))
    height, width = gray.shape[:2]
    factor = max(1, int(round(sigma / 6.0)))

    if factor == 1:
        blurred = cv2.GaussianBlur(gray.astype(np.float32), (0, 0), sigmaX=sigma)
        return blurred.astype(np.float32)

    small = cv2.resize(
        gray,
        (max(1, width // factor), max(1, height // factor)),
        interpolation=cv2.INTER_AREA,
    )
    small = cv2.GaussianBlur(small.astype(np.float32), (0, 0), sigmaX=sigma / factor)
    return cv2.resize(small, (width, height), interpolation=cv2.INTER_LINEAR).astype(np.float32)


def detect_optic_disc(
    image: np.ndarray,
    roi_mask: np.ndarray,
) -> Dict[str, Any]:
    """
    Locate the optic disc (optic nerve head).

    The disc is the brightest roughly-circular structure inside the retinal
    field, but it is *not* the brightest region in absolute terms: vignetting and
    the radial choroidal gradient leave the centre of the field nearly as bright.
    Detection therefore thresholds the local brightness **excess** - luminance
    minus a large-scale background estimate - which isolates the disc from that
    plateau. The component whose locally-averaged peak excess is highest wins,
    and its radius is then grown back out to where the excess decays, since the
    high-percentile core is deliberately smaller than the true disc.

    When no plausible candidate survives, a nasal-side geometric prior is used
    and the result is flagged low-confidence so callers can discount it.

    Args:
        image: BGR fundus photograph.
        roi_mask: Binary retinal field-of-view mask (0/255).

    Returns:
        Dictionary with ``center`` ``(x, y)``, ``radius_px``, ``diameter_px``,
        ``mask`` (binary), ``confidence`` and ``method``.
    """
    landmarks = settings.landmarks
    gray = _to_uint8_gray(image)
    height, width = gray.shape

    roi_binary = _binary_from_mask(roi_mask, gray.shape)
    roi_pixels = int(np.count_nonzero(roi_binary))
    if roi_pixels == 0:
        roi_binary = np.full((height, width), 255, dtype=np.uint8)
        roi_pixels = height * width

    # Expected disc diameter from the field-of-view extent: the disc subtends
    # a fairly consistent fraction of a standard fundus field.
    ys, xs = np.where(roi_binary > 0)
    if ys.size == 0:
        expected_diameter = max(8.0, float(min(height, width)) * landmarks.disc_diameter_fraction)
        center = (width / 2.0, height / 2.0)
    else:
        field_width = float(xs.max() - xs.min())
        expected_diameter = max(
            8.0, field_width * landmarks.disc_diameter_fraction
        )
        center = (float(np.mean(xs)), float(np.mean(ys)))

    expected_radius = expected_diameter / 2.0

    smoothed = cv2.GaussianBlur(
        gray.astype(np.float32), (0, 0), sigmaX=max(1.0, expected_radius / 3.0)
    )
    background = _large_scale_background(
        gray, expected_radius * landmarks.disc_background_radius_scale
    )
    excess = smoothed - background
    excess = _restrict_to_region(excess, roi_binary)

    inside = excess[roi_binary > 0]
    if inside.size < 64:
        return _fallback_disc(center, expected_radius, (height, width), roi_binary)

    cutoff = float(np.percentile(inside, landmarks.disc_excess_percentile))
    if cutoff <= 0:
        return _fallback_disc(center, expected_radius, (height, width), roi_binary)

    bright = np.where(excess >= cutoff, 255, 0).astype(np.uint8)
    bright = cv2.bitwise_and(bright, roi_binary)

    # Clean up before measuring: opening removes noise speckle, closing reunites
    # a disc whose core has been split by intervening vessel shadows.
    kernel_size = max(3, int(round(expected_radius * 0.6)))
    if kernel_size % 2 == 0:
        kernel_size += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    bright = cv2.morphologyEx(bright, cv2.MORPH_OPEN, kernel)
    bright = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        bright, connectivity=8
    )

    # The disc is the brightest compact structure in the field once the
    # large-scale illumination is flattened, so its *peak* excess is the cue.
    # Scoring by total excess mass instead hands the win to the broad central
    # vignette plateau, which accumulates more mass than the disc without ever
    # exceeding its peak.
    #
    # The peak is taken over a quarter-disc-radius window rather than at a
    # single pixel, so a hot pixel or small specular glint cannot masquerade as
    # a disc. Measured on the demo set this window is the largest one that still
    # separates the disc from the plateau; wider windows let the plateau's
    # extent outvote the disc's intensity.
    peak_radius = max(2, int(round(expected_radius * 0.25)))
    peak_kernel = np.zeros((2 * peak_radius + 1, 2 * peak_radius + 1), dtype=np.float32)
    cv2.circle(peak_kernel, (peak_radius, peak_radius), peak_radius, 1.0, -1)
    local_mean_excess = cv2.filter2D(excess, -1, peak_kernel) / max(1.0, float(peak_kernel.sum()))

    # Ranking is by robust peak alone. An earlier revision also weighted each
    # candidate by how close its radius sat to ``expected_radius``, but the
    # thresholded core is only about 0.6 of the full disc at this stage - the
    # radius is grown back out below - so that term penalised the genuine disc
    # and cancelled its intensity advantage. The scale gate still rejects
    # candidates that are nothing like disc-sized.
    best: Optional[Tuple[int, float]] = None
    for index in range(1, num_labels):
        area = int(stats[index, cv2.CC_STAT_AREA])
        if area <= 0:
            continue

        equivalent_radius = math.sqrt(area / math.pi)
        # Reject candidates wildly unlike a disc core in scale.
        if not (0.30 * expected_radius <= equivalent_radius <= 2.5 * expected_radius):
            continue

        component = labels == index
        robust_peak = float(np.max(local_mean_excess[component]))
        if best is None or robust_peak > best[1]:
            best = (index, robust_peak)

    if best is None:
        return _fallback_disc(center, expected_radius, (height, width), roi_binary)

    index, _robust_peak = best
    core_mask = np.where(labels == index, 255, 0).astype(np.uint8)
    disc_x, disc_y = centroids[index]

    peak_excess = float(np.max(excess[core_mask > 0]))

    # Recover the full disc radius from the high-percentile core by walking
    # outward along rays and stopping where the brightness excess decays to the
    # level of the disc's local surround.
    #
    # Growing a thresholded contour instead looks simpler but fails: the search
    # window has to be wide enough to contain the whole disc, and the central
    # vignette plateau usually falls inside it too. Where the two touch they
    # merge, the merged blob then fails the scale gate, and the radius is left
    # at the small core value. Rays cannot merge with anything, and taking their
    # median means the minority pointing at the plateau cannot drag the result.
    ray_count = 72
    max_ray_radius = int(round(expected_radius * 2.5))
    step_radii = np.arange(1, max_ray_radius + 1, dtype=np.float64)
    angles = np.linspace(0.0, 2.0 * math.pi, ray_count, endpoint=False)

    ray_x = disc_x + step_radii[None, :] * np.cos(angles)[:, None]
    ray_y = disc_y + step_radii[None, :] * np.sin(angles)[:, None]

    sample_rows = np.clip(ray_y, 0, height - 1).astype(int)
    sample_cols = np.clip(ray_x, 0, width - 1).astype(int)
    # Restricting samples to the ROI matters: outside it the excess reads as
    # zero, which a ray would otherwise mistake for a disc boundary that is
    # really just the edge of the photograph.
    usable = (
        (ray_x >= 0) & (ray_x < width) & (ray_y >= 0) & (ray_y < height)
        & (roi_binary[sample_rows, sample_cols] > 0)
    )
    sampled_excess = np.where(usable, excess[sample_rows, sample_cols], -np.inf)

    # The boundary is where the excess decays to the level of the disc's own
    # surround, not to a fixed fraction of the peak. The surrounding field
    # already carries substantial excess - typically more than a peak-fraction
    # cutoff - so tying the cutoff to the peak alone leaves it below the
    # surround and no ray ever finds an edge.
    annulus = (step_radii >= expected_radius * 1.5) & (step_radii <= expected_radius * 2.5)
    annulus_values = sampled_excess[:, annulus]
    annulus_values = annulus_values[np.isfinite(annulus_values)]
    surround = float(np.median(annulus_values)) if annulus_values.size else 0.0

    contrast = max(1.0, peak_excess - surround)
    boundary_level = surround + landmarks.disc_edge_excess_fraction * contrast

    boundary_radii: List[float] = []
    for ray in range(ray_count):
        reached_edge = np.where(usable[ray])[0]
        if reached_edge.size == 0:
            continue
        decayed = np.where(sampled_excess[ray] < boundary_level)[0]
        if decayed.size == 0:
            boundary_radii.append(float(step_radii[reached_edge[-1]]))
        else:
            boundary_radii.append(float(step_radii[decayed[0]]))

    core_radius = max(2.0, math.sqrt(float(stats[index, cv2.CC_STAT_AREA]) / math.pi))
    if boundary_radii:
        measured_radius = float(np.median(boundary_radii))
        # Never shrink below the core that was actually detected, and never
        # believe a radius that is implausible for an optic nerve head.
        disc_radius = float(np.clip(
            measured_radius, core_radius, max(core_radius, 2.0 * expected_radius)
        ))
    else:
        disc_radius = core_radius

    disc_mask = np.zeros((height, width), dtype=np.uint8)
    cv2.circle(
        disc_mask,
        (int(round(disc_x)), int(round(disc_y))),
        int(round(disc_radius)),
        255,
        thickness=-1,
    )
    disc_mask = cv2.bitwise_and(disc_mask, roi_binary)

    if int(np.count_nonzero(disc_mask)) == 0:
        disc_mask = core_mask

    # Confidence from how strongly the disc stands above the illumination field,
    # normalised by the expected contrast of a healthy disc, combined with how
    # close the grown radius came to the expected disc radius. Plausibility is
    # measured on the final radius rather than the thresholded core, which is
    # deliberately only the bright centre of the disc.
    plausibility = 1.0 - min(
        1.0, abs(disc_radius - expected_radius) / max(expected_radius, 1.0)
    )
    contrast_term = float(np.clip((peak_excess / 30.0), 0.0, 1.0))
    confidence = round(float(np.clip(0.5 * plausibility + 0.5 * contrast_term, 0.0, 1.0)), 4)

    return {
        "center": (round(float(disc_x), 2), round(float(disc_y), 2)),
        "radius_px": round(float(disc_radius), 2),
        "diameter_px": round(float(disc_radius * 2.0), 2),
        "mask": disc_mask,
        "confidence": confidence,
        "method": "local-brightness-excess-threshold+peak-excess-component",
    }


def _fallback_disc(
    center: Tuple[float, float],
    radius: float,
    shape: Tuple[int, ...],
    roi_binary: np.ndarray,
) -> Dict[str, Any]:
    """
    Synthesise a geometric-prior optic disc when detection fails.

    Args:
        center: Prior centre (ROI centroid).
        radius: Prior radius in pixels.
        shape: Image shape.
        roi_binary: ROI mask to intersect with.

    Returns:
        Disc dictionary with ``confidence`` 0 and ``method`` flagged as a prior.
    """
    height, width = shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.circle(mask, (int(round(center[0])), int(round(center[1]))),
               int(round(max(2.0, radius))), 255, thickness=-1)
    mask = cv2.bitwise_and(mask, roi_binary)

    return {
        "center": (round(float(center[0]), 2), round(float(center[1]), 2)),
        "radius_px": round(float(max(2.0, radius)), 2),
        "diameter_px": round(float(max(4.0, radius * 2.0)), 2),
        "mask": mask,
        "confidence": 0.0,
        "method": "geometric-prior-fallback",
    }


def estimate_fovea_center(
    image: np.ndarray,
    roi_mask: np.ndarray,
    disc: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Estimate the fovea (centre of the macula).

    The fovea is the darkest avascular region, located roughly 2.5 disc
    diameters *temporal* to the disc centre. Laterality is not reliably
    recoverable from a single uncropped photograph, so both temporal candidates
    (left and right of the disc) are scored and the darker one wins.

    Args:
        image: BGR fundus photograph.
        roi_mask: Binary ROI mask (0/255).
        disc: Output of :func:`detect_optic_disc`.

    Returns:
        Dictionary with ``center`` ``(x, y)``, ``radius_px``, ``mask``,
        ``confidence`` and ``method``.
    """
    landmarks = settings.landmarks
    gray = _to_uint8_gray(image)
    height, width = gray.shape

    roi_binary = _binary_from_mask(roi_mask, gray.shape)
    disc_radius = max(2.0, float(disc.get("radius_px", min(height, width) * 0.08)))
    disc_diameter = disc_radius * 2.0
    disc_x, disc_y = disc.get("center", (width / 2.0, height / 2.0))

    offset = landmarks.fovea_offset_disc_diameters * disc_diameter
    macula_radius = max(4.0, disc_diameter * landmarks.macula_radius_disc_diameters)

    smoothed = cv2.GaussianBlur(gray, (0, 0), sigmaX=max(1.0, macula_radius / 2.0))

    # The fovea is dark *relative to its own surround*. Scoring raw darkness
    # instead lets the heavily vignetted nasal periphery out-darken the macula
    # and wins the wrong side of the disc, so subtract a large-scale background
    # estimate first - the same correction the disc detector relies on.
    background = _large_scale_background(gray, max(8.0, macula_radius * 2.0))
    darkness = _restrict_to_region(background - smoothed, roi_binary)
    darkness = cv2.GaussianBlur(darkness, (0, 0), sigmaX=max(1.0, macula_radius / 3.0))

    # Laterality is not recoverable from a single uncropped photograph, so the
    # temporal direction is taken as the ray from the disc through the centre of
    # the retinal field: the disc sits nasal to the posterior pole, so the fovea
    # lies along that ray extended past it. Both senses are scored.
    roi_rows, roi_cols = np.where(roi_binary > 0)
    if roi_rows.size == 0:
        field_x, field_y = width / 2.0, height / 2.0
    else:
        field_x = float(np.mean(roi_cols))
        field_y = float(np.mean(roi_rows))

    direction_x = field_x - disc_x
    direction_y = field_y - disc_y
    direction_norm = math.hypot(direction_x, direction_y)
    if direction_norm < 1e-3:
        direction_x, direction_y = 1.0, 0.0
    else:
        direction_x /= direction_norm
        direction_y /= direction_norm

    window_radius = max(4, int(round(macula_radius)))
    candidates = [
        (disc_x + offset * direction_x, disc_y + offset * direction_y),
        (disc_x - offset * direction_x, disc_y - offset * direction_y),
    ]

    field_values = darkness[roi_binary > 0]
    field_spread = float(np.std(field_values)) if field_values.size else 0.0

    best: Optional[Tuple[float, float, float]] = None
    runner_up = float("-inf")
    for candidate_x, candidate_y in candidates:
        left = int(max(0, round(candidate_x) - window_radius))
        top = int(max(0, round(candidate_y) - window_radius))
        right = int(min(width, round(candidate_x) + window_radius + 1))
        bottom = int(min(height, round(candidate_y) + window_radius + 1))
        if right - left < 3 or bottom - top < 3:
            continue

        patch_mask = roi_binary[top:bottom, left:right] > 0
        if int(np.count_nonzero(patch_mask)) < 32:
            continue

        score = float(np.mean(darkness[top:bottom, left:right][patch_mask]))
        if best is None or score > best[2]:
            runner_up = best[2] if best is not None else float("-inf")
            best = (float(candidate_x), float(candidate_y), score)
        elif score > runner_up:
            runner_up = score

    if best is None:
        chosen = (
            float(disc_x + offset * direction_x),
            float(disc_y + offset * direction_y),
        )
        confidence = 0.0
        method = "geometric-prior-fallback"
    else:
        chosen_x, chosen_y, score = best

        # Snap to the darkest point nearby: the ray lands the estimate roughly
        # where the macula should be, but not exactly on the foveal centre.
        left = int(max(0, round(chosen_x) - window_radius))
        top = int(max(0, round(chosen_y) - window_radius))
        right = int(min(width, round(chosen_x) + window_radius + 1))
        bottom = int(min(height, round(chosen_y) + window_radius + 1))

        patch = np.where(
            roi_binary[top:bottom, left:right] > 0,
            darkness[top:bottom, left:right],
            -np.inf,
        )
        if np.any(np.isfinite(patch)):
            peak_row, peak_col = np.unravel_index(int(np.argmax(patch)), patch.shape)
            chosen_x = float(left + peak_col)
            chosen_y = float(top + peak_row)
            peak_darkness = float(patch[peak_row, peak_col])
        else:
            peak_darkness = score

        # Normalise by the spread of the darkness field rather than a fixed
        # constant, so confidence means the same thing on a bright and a dim
        # photograph. Two standard deviations counts as a decisive macula.
        confidence = round(float(np.clip(
            peak_darkness / max(1e-6, 2.0 * field_spread), 0.0, 1.0
        )), 4)
        chosen = (chosen_x, chosen_y)
        method = "local-darkness-excess-along-disc-fovea-ray"

    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.circle(mask, (int(round(chosen[0])), int(round(chosen[1]))),
               int(round(macula_radius)), 255, thickness=-1)
    mask = cv2.bitwise_and(mask, roi_binary)

    return {
        "center": (round(chosen[0], 2), round(chosen[1], 2)),
        "radius_px": round(float(macula_radius), 2),
        "diameter_px": round(float(macula_radius * 2.0), 2),
        "mask": mask,
        "confidence": confidence,
        "method": method,
    }


def _disc_exclusion_mask(
    disc: Dict[str, Any],
    shape: Tuple[int, ...],
    diameters: float,
) -> np.ndarray:
    """
    Build a mask of the region around the optic disc to ignore for lesions.

    Args:
        disc: Output of :func:`detect_optic_disc`.
        shape: Image shape.
        diameters: Exclusion radius in disc diameters.

    Returns:
        Binary uint8 mask, 255 inside the exclusion zone.
    """
    height, width = shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)

    disc_radius = max(2.0, float(disc.get("radius_px", 10.0)))
    center_x, center_y = disc.get("center", (width / 2.0, height / 2.0))
    exclusion_radius = int(round(disc_radius * 2.0 * diameters))

    cv2.circle(mask, (int(round(center_x)), int(round(center_y))),
               max(1, exclusion_radius), 255, thickness=-1)
    return mask


# ---------------------------------------------------------------------------
# Dark lesions: microaneurysms and haemorrhages
# ---------------------------------------------------------------------------

def detect_dark_lesions(
    image: np.ndarray,
    roi_mask: np.ndarray,
    vessel_mask: Optional[np.ndarray] = None,
    disc: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Detect dark red lesions - microaneurysms and haemorrhages.

    Blood absorbs strongly, so these lesions appear as locally dark blobs. The
    response is taken from both the red and green channels (haemoglobin
    contrast peaks in green, while the red channel suppresses pigment noise)
    and the stronger of the two wins per pixel.

    Vasculature is excluded by removing a dilated vessel mask: without that
    step every vessel crossing is reported as a haemorrhage. The two classes
    are then separated by size and circularity - microaneurysms are tiny and
    round, haemorrhages are larger and blotchy.

    Args:
        image: BGR fundus photograph.
        roi_mask: Binary ROI mask (0/255).
        vessel_mask: Binary vessel mask (0/255) to exclude, if available.
        disc: Optic disc result, used to build the exclusion zone.

    Returns:
        Dictionary with per-class ``blobs``, a combined ``mask``, the
        ``threshold`` used and the ``response`` map.
    """
    config = settings.lesions
    gray = _to_uint8_gray(image)
    shape = gray.shape

    roi_binary = _binary_from_mask(roi_mask, shape)
    roi_area = max(1, int(np.count_nonzero(roi_binary)))

    exclusion = (
        _disc_exclusion_mask(disc, shape, config.disc_exclusion_diameters)
        if disc else np.zeros(shape, dtype=np.uint8)
    )

    # Suppress vessel pixels. The exclusion band must be comparable in width to
    # the black-hat kernel itself: a narrow band leaves the bright background
    # trapped between two adjacent vessel branches free to fire as a candidate.
    vessel_exclusion = np.zeros(shape, dtype=np.uint8)
    if vessel_mask is not None:
        vessel_binary = _binary_from_mask(vessel_mask, shape)
        dilate_size = _scale_kernel(shape, config.vessel_exclusion_fraction, minimum=5)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_size, dilate_size))
        vessel_exclusion = cv2.dilate(vessel_binary, kernel, iterations=1)

    valid_region = cv2.bitwise_and(roi_binary, cv2.bitwise_not(exclusion))
    valid_region = cv2.bitwise_and(valid_region, cv2.bitwise_not(vessel_exclusion))

    # Green channel carries the best lesion-vs-background contrast and supplies
    # the absolute-intensity reference for the gate below.
    green = _channel(image, 1).astype(np.float32)
    green_mean, green_std = _channel_stats(green, roi_binary)
    # A true dark lesion is darker than the surrounding retina in absolute terms,
    # not merely darker than its immediate neighbourhood.
    darkness_ceiling = green_mean - config.dark_absolute_margin * green_std

    # Combine red- and green-channel black-hat responses, taking the maximum.
    red_response = _local_response(_channel(image, 2), cv2.MORPH_BLACKHAT)
    green_response = _local_response(_channel(image, 1), cv2.MORPH_BLACKHAT)
    response = np.maximum(red_response, green_response).astype(np.float32)

    response = _restrict_to_region(response, valid_region)

    inside = response[valid_region > 0]
    if inside.size < 64:
        return {
            "blobs": {"microaneurysm": [], "hemorrhage": []},
            "mask": np.zeros(shape, dtype=np.uint8),
            "threshold": 0.0,
            "response": response,
            "roi_area_px": roi_area,
        }

    mean = float(np.mean(inside))
    std = float(np.std(inside))
    # Both a statistical cutoff and an absolute contrast floor must be cleared,
    # so a uniformly noisy image cannot lower its own detection bar.
    threshold = max(
        mean + config.dark_lesion_sigma * std,
        mean + config.dark_min_contrast,
    )

    _, binary = cv2.threshold(response, threshold, 255, cv2.THRESH_BINARY)
    candidates = cv2.bitwise_and(binary.astype(np.uint8), valid_region)

    # Drop single-pixel speckle before component analysis.
    open_size = _scale_kernel(shape, 0.004, minimum=3)
    open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_size, open_size))
    candidates = cv2.morphologyEx(candidates, cv2.MORPH_OPEN, open_kernel)

    blobs = _describe_components(candidates, response, threshold, intensity=green)

    min_area = max(6.0, roi_area * config.min_lesion_area_fraction)
    max_ma_area = max(min_area * 4.0, roi_area * config.microaneurysm_max_area_fraction)

    microaneurysms: List[Dict[str, Any]] = []
    haemorrhages: List[Dict[str, Any]] = []

    for blob in blobs:
        area = float(blob["area_px"])
        if area < min_area or area > roi_area * config.max_lesion_area_fraction:
            continue

        # Absolute-intensity gate: a blob that is not actually darker than the
        # surrounding retina is background texture, not a haemorrhage.
        intensity = blob.get("mean_intensity")
        if intensity is not None and intensity > darkness_ceiling:
            continue

        blob["contrast_score"] = round(
            float(np.clip(blob["mean_contrast"] / max(threshold, 1.0), 0.0, 2.0)), 4
        )

        is_small = area <= max_ma_area
        is_round = blob["circularity"] >= config.microaneurysm_min_circularity
        is_solid = blob["solidity"] >= 0.55

        if is_small and (is_round or is_solid):
            blob["lesion_type"] = "microaneurysm"
            blob["confidence"] = round(float(np.clip(
                0.45 * blob["circularity"]
                + 0.30 * min(1.0, blob["contrast_score"])
                + 0.25 * blob["solidity"],
                0.0, 1.0,
            )), 4)
            microaneurysms.append(blob)
        else:
            blob["lesion_type"] = "hemorrhage"
            # Larger, irregular blotches with strong contrast are convincing.
            size_term = float(np.clip(area / (max_ma_area * 6.0), 0.0, 1.0))
            blob["confidence"] = round(float(np.clip(
                0.45 * min(1.0, blob["contrast_score"])
                + 0.35 * size_term
                + 0.20 * blob["solidity"],
                0.0, 1.0,
            )), 4)
            haemorrhages.append(blob)

    combined_mask = candidates.copy()

    return {
        "blobs": {"microaneurysm": microaneurysms, "hemorrhage": haemorrhages},
        "mask": combined_mask,
        "threshold": round(float(threshold), 3),
        "response": response,
        "roi_area_px": roi_area,
    }


# ---------------------------------------------------------------------------
# Bright lesions: exudates and drusen
# ---------------------------------------------------------------------------

def detect_bright_lesions(
    image: np.ndarray,
    roi_mask: np.ndarray,
    vessel_mask: Optional[np.ndarray] = None,
    disc: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Detect bright lesions - hard exudates and drusen.

    Lipid exudates are bright yellow-white, so detection combines a top-hat
    brightness response with a chromatic test: exudates keep red and green high
    while blue stays comparatively low. That colour gate removes specular
    reflections and the bright disc rim, which are achromatic and would
    otherwise dominate.

    Args:
        image: BGR fundus photograph.
        roi_mask: Binary ROI mask (0/255).
        vessel_mask: Binary vessel mask (0/255) to exclude, if available.
        disc: Optic disc result, used to build the exclusion zone.

    Returns:
        Dictionary with per-class ``blobs``, a combined ``mask``, the
        ``threshold`` used and the ``response`` map.
    """
    config = settings.lesions
    gray = _to_uint8_gray(image)
    shape = gray.shape

    roi_binary = _binary_from_mask(roi_mask, shape)
    roi_area = max(1, int(np.count_nonzero(roi_binary)))

    exclusion = (
        _disc_exclusion_mask(disc, shape, config.disc_exclusion_diameters)
        if disc else np.zeros(shape, dtype=np.uint8)
    )

    vessel_exclusion = np.zeros(shape, dtype=np.uint8)
    if vessel_mask is not None:
        vessel_binary = _binary_from_mask(vessel_mask, shape)
        # Match the exclusion band to the top-hat kernel scale; a narrow band
        # leaves bright inter-vessel background firing as exudate candidates.
        dilate_size = _scale_kernel(shape, config.vessel_exclusion_fraction, minimum=5)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_size, dilate_size))
        vessel_exclusion = cv2.dilate(vessel_binary, kernel, iterations=1)

    valid_region = cv2.bitwise_and(roi_binary, cv2.bitwise_not(exclusion))
    valid_region = cv2.bitwise_and(valid_region, cv2.bitwise_not(vessel_exclusion))

    green_channel = _channel(image, 1)
    green = green_channel.astype(np.float32)
    green_mean, green_std = _channel_stats(green, roi_binary)
    brightness_floor = green_mean + config.bright_absolute_margin * green_std

    # Brightness response on the green channel (best lesion-vs-background SNR).
    response = _local_response(green_channel, cv2.MORPH_TOPHAT).astype(np.float32)

    # Chromatic gate: yellow-white lesions satisfy (R + G)/2 - B > 0 strongly.
    if image.ndim == 3 and image.shape[2] >= 3:
        red_f = image[:, :, 2].astype(np.float32)
        blue_f = image[:, :, 0].astype(np.float32)
        chromatic = (red_f + green) / 2.0 - blue_f
        chromatic = cv2.GaussianBlur(chromatic, (0, 0), sigmaX=2.0)
        chromatic_norm = (chromatic - float(np.mean(chromatic))) / max(
            1.0, float(np.std(chromatic))
        )
        # Scale the colour evidence into a multiplicative gain of roughly
        # [0.5, 1.5] so it modulates rather than dominates brightness.
        gain = np.clip(1.0 + 0.5 * chromatic_norm, 0.5, 1.5).astype(np.float32)
        response = response * gain

    response = _restrict_to_region(response, valid_region)

    inside = response[valid_region > 0]
    if inside.size < 64:
        return {
            "blobs": {"exudate": [], "drusen": []},
            "mask": np.zeros(shape, dtype=np.uint8),
            "threshold": 0.0,
            "response": response,
            "roi_area_px": roi_area,
        }

    mean = float(np.mean(inside))
    std = float(np.std(inside))
    threshold = max(
        mean + config.bright_lesion_sigma * std,
        mean + config.bright_min_contrast,
    )

    _, binary = cv2.threshold(response, threshold, 255, cv2.THRESH_BINARY)
    candidates = cv2.bitwise_and(binary.astype(np.uint8), valid_region)

    open_size = _scale_kernel(shape, 0.004, minimum=3)
    open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_size, open_size))
    candidates = cv2.morphologyEx(candidates, cv2.MORPH_OPEN, open_kernel)

    blobs = _describe_components(candidates, response, threshold, intensity=green)

    min_area = max(6.0, roi_area * config.min_lesion_area_fraction)
    drusen_max_area = max(min_area * 6.0, roi_area * config.microaneurysm_max_area_fraction * 2.0)

    exudates: List[Dict[str, Any]] = []
    drusen: List[Dict[str, Any]] = []

    for blob in blobs:
        area = float(blob["area_px"])
        if area < min_area or area > roi_area * config.max_lesion_area_fraction:
            continue

        # Absolute-intensity gate: lipid exudates are genuinely brighter than the
        # surrounding retina. Background trapped between vessel branches is not.
        intensity = blob.get("mean_intensity")
        if intensity is not None and intensity < brightness_floor:
            continue

        blob["contrast_score"] = round(
            float(np.clip(blob["mean_contrast"] / max(threshold, 1.0), 0.0, 2.0)), 4
        )

        is_small = area <= drusen_max_area
        is_round = blob["circularity"] >= 0.45

        if is_small and is_round:
            blob["lesion_type"] = "drusen"
            blob["confidence"] = round(float(np.clip(
                0.40 * blob["circularity"]
                + 0.35 * min(1.0, blob["contrast_score"])
                + 0.25 * blob["solidity"],
                0.0, 1.0,
            )), 4)
            drusen.append(blob)
        else:
            blob["lesion_type"] = "exudate"
            size_term = float(np.clip(area / (drusen_max_area * 5.0), 0.0, 1.0))
            blob["confidence"] = round(float(np.clip(
                0.45 * min(1.0, blob["contrast_score"])
                + 0.30 * size_term
                + 0.25 * blob["solidity"],
                0.0, 1.0,
            )), 4)
            exudates.append(blob)

    return {
        "blobs": {"exudate": exudates, "drusen": drusen},
        "mask": candidates.copy(),
        "threshold": round(float(threshold), 3),
        "response": response,
        "roi_area_px": roi_area,
    }


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def _quadrant_of(
    x: float,
    y: float,
    roi_center: Tuple[float, float],
) -> str:
    """
    Assign a point to one of four retinal quadrants relative to the ROI centre.

    Args:
        x: Horizontal coordinate.
        y: Vertical coordinate.
        roi_center: ``(x, y)`` centre of the retinal field.

    Returns:
        One of ``superior-nasal``, ``superior-temporal``,
        ``inferior-nasal``, ``inferior-temporal``.
    """
    center_x, center_y = roi_center
    vertical = "superior" if y < center_y else "inferior"
    horizontal = "nasal" if x < center_x else "temporal"
    return f"{vertical}-{horizontal}"


def detect_lesions(
    image: np.ndarray,
    roi_mask: np.ndarray,
    vessel_mask: Optional[np.ndarray] = None,
    quality: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the full lesion-detection stage and quantify the findings.

    Args:
        image: BGR fundus photograph, already resized by preprocessing.
        roi_mask: Binary retinal field-of-view mask (0/255).
        vessel_mask: Binary vessel mask (0/255), used to suppress vessels.
        quality: Optional quality assessment; scales ``detection_reliability``.

    Returns:
        Dictionary containing:
            - ``lesions``: per-lesion records with type, position, area,
              circularity, contrast, confidence and macular distance.
            - ``counts``: lesion count per class plus ``total``.
            - ``total_lesion_area_px`` / ``lesion_area_fraction``: burden area.
            - ``macular_lesion_count`` / ``macular_lesion_types``: fovea-adjacent findings.
            - ``quadrants``: lesion counts per retinal quadrant (feeds the
              ETDRS 4-2-1 severe-NPDR rule).
            - ``burden_index``: class-weighted lesion burden in ``[0, 1]``.
            - ``detection_reliability``: how much the detection pass is trusted.
            - ``landmarks``: optic disc and fovea localisation results.
            - ``masks``: binary masks per lesion class.
            - ``thresholds``: detector cutoffs, for reproducibility.
    """
    config = settings.lesions
    gray = _to_uint8_gray(image)
    shape = gray.shape

    roi_binary = _binary_from_mask(roi_mask, shape)
    roi_area = max(1, int(np.count_nonzero(roi_binary)))

    # --- Landmarks first: lesion location is meaningless without them ---
    disc = detect_optic_disc(image, roi_binary)
    fovea = estimate_fovea_center(image, roi_binary, disc)

    disc_diameter = max(4.0, float(disc.get("diameter_px", 20.0)))
    fovea_x, fovea_y = fovea.get("center", (shape[1] / 2.0, shape[0] / 2.0))

    roi_center = _roi_center(roi_binary, shape)

    dark = detect_dark_lesions(image, roi_binary, vessel_mask, disc)
    bright = detect_bright_lesions(image, roi_binary, vessel_mask, disc)

    all_blobs: List[Dict[str, Any]] = []
    for lesion_type in LESION_TYPES:
        source = dark["blobs"].get(lesion_type) or bright["blobs"].get(lesion_type) or []
        all_blobs.extend(source)

    # Strongest evidence first, so the reporting cap keeps the best lesions.
    all_blobs.sort(key=lambda b: float(b.get("confidence", 0.0)), reverse=True)
    all_blobs = all_blobs[:MAX_REPORTED_LESIONS]

    lesions: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {name: 0 for name in LESION_TYPES}
    quadrants: Dict[str, int] = {}
    macular_types: Dict[str, int] = {name: 0 for name in LESION_TYPES}
    total_area = 0
    weighted_area = 0.0
    macular_count = 0

    per_class_masks: Dict[str, np.ndarray] = {
        name: np.zeros(shape, dtype=np.uint8) for name in LESION_TYPES
    }

    for index, blob in enumerate(all_blobs):
        lesion_type = str(blob.get("lesion_type", "microaneurysm"))
        counts[lesion_type] = counts.get(lesion_type, 0) + 1

        distance_px = math.hypot(blob["x"] - fovea_x, blob["y"] - fovea_y)
        distance_dd = distance_px / disc_diameter
        is_macular = distance_dd <= settings.landmarks.macula_radius_disc_diameters

        quadrant = _quadrant_of(blob["x"], blob["y"], roi_center)
        quadrants[quadrant] = quadrants.get(quadrant, 0) + 1

        area_px = int(blob["area_px"])
        total_area += area_px
        weighted_area += area_px * LESION_WEIGHTS.get(lesion_type, 1.0)

        if is_macular:
            macular_count += 1
            macular_types[lesion_type] = macular_types.get(lesion_type, 0) + 1

        # Record the blob in its class mask for heatmap and overlay rendering.
        left, top, width, height = blob["bbox"]
        per_class_masks[lesion_type][top:top + height, left:left + width] = np.maximum(
            per_class_masks[lesion_type][top:top + height, left:left + width],
            (dark["mask"] if lesion_type in ("microaneurysm", "hemorrhage")
             else bright["mask"])[top:top + height, left:left + width],
        )

        lesions.append({
            "id": index,
            "type": lesion_type,
            "x": round(float(blob["x"]), 2),
            "y": round(float(blob["y"]), 2),
            "area_px": area_px,
            "circularity": blob["circularity"],
            "solidity": blob["solidity"],
            "aspect_ratio": blob["aspect_ratio"],
            "mean_contrast": blob["mean_contrast"],
            "peak_contrast": blob["peak_contrast"],
            "confidence": blob["confidence"],
            "distance_to_fovea_px": round(distance_px, 2),
            "distance_to_fovea_dd": round(distance_dd, 3),
            "is_macular": bool(is_macular),
            "quadrant": quadrant,
        })

    counts["total"] = len(lesions)

    lesion_area_fraction = total_area / float(roi_area)
    weighted_lesion_area_fraction = weighted_area / float(roi_area)

    # burden_index is deliberately the *raw* weighted area fraction, not a
    # normalised score, so it can be compared directly against the grading
    # thresholds in GradingSettings (mild/moderate/severe/proliferative).
    burden_index = round(weighted_lesion_area_fraction, 6)

    # Saturating display score in [0, 1] for UI gauges; 0.015 weighted fraction
    # maps to roughly 63% of the gauge.
    burden_score = float(1.0 - math.exp(-weighted_lesion_area_fraction / 0.015))
    burden_score = round(float(np.clip(burden_score, 0.0, 1.0)), 5)

    detection_reliability = _detection_reliability(quality, disc, fovea, roi_area)

    return {
        "lesions": lesions,
        "counts": counts,
        "total_lesion_area_px": int(total_area),
        "lesion_area_fraction": round(lesion_area_fraction, 6),
        "weighted_lesion_area_px": round(weighted_area, 2),
        "weighted_lesion_area_fraction": round(weighted_lesion_area_fraction, 6),
        "burden_index": burden_index,
        "burden_score": burden_score,
        "macular_lesion_count": macular_count,
        "macular_lesion_types": macular_types,
        "quadrants": quadrants,
        "detection_reliability": detection_reliability,
        "landmarks": {
            "optic_disc": {
                "center": disc["center"],
                "radius_px": disc["radius_px"],
                "diameter_px": disc["diameter_px"],
                "confidence": disc["confidence"],
                "method": disc["method"],
            },
            "fovea": {
                "center": fovea["center"],
                "radius_px": fovea["radius_px"],
                "confidence": fovea["confidence"],
                "method": fovea["method"],
            },
            "disc_diameter_px": round(disc_diameter, 2),
            "roi_center": (round(roi_center[0], 2), round(roi_center[1], 2)),
        },
        "masks": per_class_masks,
        "combined_mask": cv2.bitwise_or(dark["mask"], bright["mask"]),
        "thresholds": {
            "dark": dark["threshold"],
            "bright": bright["threshold"],
            "min_area_px": round(max(2.0, roi_area * config.min_lesion_area_fraction), 2),
            "max_area_px": round(roi_area * config.max_lesion_area_fraction, 2),
        },
        "roi_area_px": roi_area,
        "image_size": {"width": int(shape[1]), "height": int(shape[0])},
        "method": (
            "Morphological black-hat/top-hat contrast detection with chromatic "
            "gating, vessel and optic-disc exclusion, then size/circularity "
            "classification. Deterministic classical CV - no trained detector."
        ),
    }


def _roi_center(roi_binary: np.ndarray, shape: Tuple[int, ...]) -> Tuple[float, float]:
    """
    Compute the centroid of the retinal field of view.

    Args:
        roi_binary: Binary ROI mask (0/255).
        shape: Image shape, used as a fallback.

    Returns:
        ``(x, y)`` centroid, or the image centre for an empty mask.
    """
    ys, xs = np.where(roi_binary > 0)
    if xs.size == 0:
        return (shape[1] / 2.0, shape[0] / 2.0)
    return (float(np.mean(xs)), float(np.mean(ys)))


def _detection_reliability(
    quality: Optional[Dict[str, Any]],
    disc: Dict[str, Any],
    fovea: Dict[str, Any],
    roi_area: int,
) -> float:
    """
    Estimate how much the lesion-detection pass should be trusted.

    Detection can only be as good as its inputs: a blurred photograph hides
    microaneurysms entirely, and failed landmark localisation means macular
    distances are meaningless. This score lets the grading stage discount
    lesion evidence rather than treating silence as a clean retina.

    Args:
        quality: Quality assessment dictionary, if available.
        disc: Optic disc localisation result.
        fovea: Fovea localisation result.
        roi_area: ROI pixel area.

    Returns:
        Reliability in ``[0, 1]``.
    """
    if quality:
        quality_score = float(np.clip(float(quality.get("score", 0.0) or 0.0), 0.0, 1.0))
    else:
        quality_score = 0.6

    landmark_score = 0.5 * float(disc.get("confidence", 0.0)) + 0.5 * float(
        fovea.get("confidence", 0.0)
    )

    # A degenerate ROI cannot support detection at all.
    resolution_term = float(np.clip(roi_area / 200000.0, 0.0, 1.0))
    resolution_term = 0.5 + 0.5 * resolution_term

    reliability = (0.55 * quality_score + 0.30 * landmark_score + 0.15 * resolution_term)
    return round(float(np.clip(reliability, 0.0, 1.0)), 4)


# ---------------------------------------------------------------------------
# Visualisation
# ---------------------------------------------------------------------------

def create_lesion_overlay(
    image: np.ndarray,
    lesion_result: Dict[str, Any],
    label: bool = True,
) -> np.ndarray:
    """
    Render detected lesions onto the fundus photograph.

    Each class is drawn in its configured colour, with the circle radius scaled
    to the lesion's own extent so small microaneurysms stay visible without
    large haemorrhages being understated. Macular lesions additionally get a
    white ring, since proximity to the fovea is what makes them clinically
    significant.

    Args:
        image: BGR fundus photograph.
        lesion_result: Output of :func:`detect_lesions`.
        label: Whether to annotate the count per class.

    Returns:
        BGR image with lesion markers drawn.
    """
    config = settings.lesions
    overlay = image.copy()

    if overlay.ndim == 2:
        overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)

    lesions = lesion_result.get("lesions", []) or []
    landmarks = lesion_result.get("landmarks", {}) or {}

    scale = max(1.0, min(overlay.shape[:2]) / 700.0)

    for lesion in lesions:
        lesion_type = str(lesion.get("type", "microaneurysm"))
        colour = config.marker_colors.get(lesion_type, (0, 0, 255))

        radius = max(3, int(round(math.sqrt(max(1, lesion.get("area_px", 4)) / math.pi) * 1.6)))
        radius = int(round(radius * scale))
        center = (int(round(lesion["x"])), int(round(lesion["y"])))

        cv2.circle(overlay, center, radius, colour, thickness=max(1, int(round(1.5 * scale))))

        if lesion.get("is_macular"):
            cv2.circle(overlay, center, radius + max(2, int(round(2 * scale))),
                       (255, 255, 255), thickness=max(1, int(round(1.2 * scale))))

    # Landmark crosshairs: disc in pale blue, fovea in pale green.
    disc = landmarks.get("optic_disc", {})
    if disc.get("center"):
        cv2.circle(overlay, (int(disc["center"][0]), int(disc["center"][1])),
                   int(disc.get("radius_px", 10)), (255, 200, 150),
                   thickness=max(1, int(round(1.5 * scale))))

    fovea = landmarks.get("fovea", {})
    if fovea.get("center"):
        cv2.drawMarker(overlay, (int(fovea["center"][0]), int(fovea["center"][1])),
                       (150, 255, 200), markerType=cv2.MARKER_CROSS,
                       markerSize=int(round(18 * scale)),
                       thickness=max(1, int(round(1.5 * scale))))

    if label:
        counts = lesion_result.get("counts", {}) or {}
        text = "MA:{ma}  H:{h}  EX:{ex}  DR:{dr}".format(
            ma=counts.get("microaneurysm", 0),
            h=counts.get("hemorrhage", 0),
            ex=counts.get("exudate", 0),
            dr=counts.get("drusen", 0),
        )
        font_scale = 0.55 * scale
        thickness = max(1, int(round(1.5 * scale)))
        (text_width, text_height), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
        cv2.rectangle(
            overlay,
            (8, 8),
            (8 + text_width + 12, 8 + text_height + baseline + 12),
            (10, 14, 24),
            thickness=-1,
        )
        cv2.putText(
            overlay, text, (14, 8 + text_height + 6),
            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (230, 240, 255), thickness, cv2.LINE_AA,
        )

    return overlay


def summarize_lesions(lesion_result: Dict[str, Any]) -> List[str]:
    """
    Render lesion findings as plain-language observations for the report.

    Wording stays descriptive and non-diagnostic, consistent with the rest of
    the screening summary.

    Args:
        lesion_result: Output of :func:`detect_lesions`.

    Returns:
        List of observation strings.
    """
    counts = lesion_result.get("counts", {}) or {}
    total = int(counts.get("total", 0))

    if total == 0:
        reliability = float(lesion_result.get("detection_reliability", 0.0))
        if reliability < 0.45:
            return [
                "No discrete lesions were detected, however detection reliability "
                f"is low ({reliability:.2f}); small microaneurysms may be obscured "
                "by image quality."
            ]
        return [
            "No microaneurysms, haemorrhages or exudates were detected above the "
            "detector threshold."
        ]

    observations: List[str] = []
    breakdown = ", ".join(
        f"{counts.get(name, 0)} {name}"
        for name in LESION_TYPES
        if counts.get(name, 0) > 0
    )
    observations.append(f"Detected {total} lesion candidate(s): {breakdown}.")

    area_fraction = float(lesion_result.get("lesion_area_fraction", 0.0))
    observations.append(
        f"Total lesion area is {lesion_result.get('total_lesion_area_px', 0):,} px "
        f"({area_fraction * 100.0:.3f}% of the retinal field)."
    )

    macular = int(lesion_result.get("macular_lesion_count", 0))
    if macular > 0:
        macular_types = lesion_result.get("macular_lesion_types", {}) or {}
        detail = ", ".join(
            f"{count} {name}" for name, count in macular_types.items() if count
        )
        observations.append(
            f"{macular} lesion(s) lie within one disc diameter of the estimated "
            f"fovea ({detail}), which is the region governing central vision."
        )

    quadrants = lesion_result.get("quadrants", {}) or {}
    if quadrants:
        spread = len([q for q, count in quadrants.items() if count > 0])
        observations.append(
            f"Lesions are distributed across {spread} of 4 retinal quadrants."
        )

    return observations
