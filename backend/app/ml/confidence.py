"""
OcuPulse Confidence Estimation and Calibration

Turns raw rule-based grading evidence into a probability distribution over DR
levels plus a single calibrated confidence figure the UI can display honestly.

Two distinct quantities are produced, and it is important not to conflate them:

* **Grade probability distribution** - a softmax over evidence-derived logits,
  giving P(level 0..4). The margin between the top two classes says how
  decisive the evidence was.
* **Reliability score** - how much the *inputs* can be trusted: were lesions
  actually detectable, was the vasculature measurable, was the photograph
  technically adequate? A confident-looking grade on a blurred image is
  worthless, so reliability gates the grade.

Temperature scaling
-------------------
The specification calls for temperature scaling to calibrate confidence. That
is implemented properly here: :func:`fit_temperature` learns a single scalar
``T`` that minimises negative log-likelihood on held-out labels, exactly as in
Guo et al. (2017). When no calibration set is available the configured prior
(``settings.confidence.temperature``) is used instead, which softens the sharp
distributions that uncalibrated evidence scores tend to produce.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import minimize_scalar

from ..config import settings

#: Numerical floor to keep logarithms finite.
_EPS = 1e-12


# ---------------------------------------------------------------------------
# Softmax / temperature scaling
# ---------------------------------------------------------------------------

def softmax(logits: Sequence[float], temperature: float = 1.0) -> np.ndarray:
    """
    Numerically stable softmax with an optional temperature.

    Args:
        logits: Unnormalised class scores.
        temperature: Divisor applied before exponentiation. Values above 1
            flatten the distribution (less confident); below 1 sharpen it.

    Returns:
        Probability vector summing to 1.0.
    """
    values = np.asarray(logits, dtype=np.float64).ravel()

    if values.size == 0:
        return values

    temp = float(temperature)
    if not np.isfinite(temp) or temp <= 0:
        temp = 1.0

    scaled = values / temp
    scaled = scaled - np.max(scaled)          # stabilise the exponent
    exponentials = np.exp(scaled)
    total = float(np.sum(exponentials))

    if total <= 0 or not np.isfinite(total):
        return np.full(values.shape, 1.0 / values.size, dtype=np.float64)

    return exponentials / total


def negative_log_likelihood(
    logits: np.ndarray,
    labels: np.ndarray,
    temperature: float = 1.0,
) -> float:
    """
    Mean negative log-likelihood of ``labels`` under temperature-scaled logits.

    This is the objective temperature scaling minimises.

    Args:
        logits: ``(N, C)`` matrix of raw class scores.
        labels: ``(N,)`` integer ground-truth class indices.
        temperature: Candidate temperature.

    Returns:
        Mean NLL; ``inf`` for degenerate inputs.
    """
    matrix = np.asarray(logits, dtype=np.float64)
    truth = np.asarray(labels, dtype=np.int64).ravel()

    if matrix.ndim != 2 or matrix.shape[0] == 0 or truth.shape[0] != matrix.shape[0]:
        return float("inf")

    classes = matrix.shape[1]
    if truth.min() < 0 or truth.max() >= classes:
        return float("inf")

    temp = float(temperature)
    if not np.isfinite(temp) or temp <= 0:
        return float("inf")

    scaled = matrix / temp
    scaled = scaled - np.max(scaled, axis=1, keepdims=True)
    log_normaliser = np.log(np.sum(np.exp(scaled), axis=1) + _EPS)
    log_likelihood = scaled[np.arange(scaled.shape[0]), truth] - log_normaliser

    return float(-np.mean(log_likelihood))


def fit_temperature(
    logits: np.ndarray,
    labels: np.ndarray,
    bounds: Tuple[float, float] = (0.05, 20.0),
) -> Dict[str, Any]:
    """
    Learn the optimal calibration temperature on a held-out set.

    Temperature scaling is a single-parameter post-hoc calibration: it rescales
    logits without changing the argmax, so accuracy is preserved while the
    reported probabilities become trustworthy.

    Args:
        logits: ``(N, C)`` raw class scores from the validation split.
        labels: ``(N,)`` integer ground-truth grades.
        bounds: Search interval for ``T``.

    Returns:
        Dictionary with ``temperature``, ``nll_before``, ``nll_after`` and
        ``improved``. Falls back to ``temperature = 1.0`` when the fit fails.
    """
    matrix = np.asarray(logits, dtype=np.float64)
    truth = np.asarray(labels, dtype=np.int64).ravel()

    nll_before = negative_log_likelihood(matrix, truth, 1.0)

    if not np.isfinite(nll_before) or matrix.shape[0] < 8:
        # Too little data to fit a calibration parameter meaningfully.
        return {
            "temperature": float(settings.confidence.temperature),
            "nll_before": nll_before,
            "nll_after": nll_before,
            "improved": False,
            "n_samples": int(matrix.shape[0]) if matrix.ndim == 2 else 0,
            "note": "Insufficient calibration data; using configured prior.",
        }

    try:
        result = minimize_scalar(
            lambda t: negative_log_likelihood(matrix, truth, t),
            bounds=bounds,
            method="bounded",
            options={"xatol": 1e-4},
        )
        temperature = float(result.x)
        nll_after = float(result.fun)
    except Exception:
        temperature = float(settings.confidence.temperature)
        nll_after = negative_log_likelihood(matrix, truth, temperature)

    if not np.isfinite(temperature) or temperature <= 0:
        temperature = float(settings.confidence.temperature)
        nll_after = negative_log_likelihood(matrix, truth, temperature)

    return {
        "temperature": round(temperature, 4),
        "nll_before": round(nll_before, 6),
        "nll_after": round(nll_after, 6),
        "improved": bool(nll_after < nll_before),
        "n_samples": int(matrix.shape[0]),
        "note": "Temperature fitted by minimising NLL on the calibration split.",
    }


def expected_calibration_error(
    probabilities: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 10,
) -> float:
    """
    Expected calibration error (ECE) of predicted confidences.

    Bins predictions by confidence, then measures the sample-weighted gap
    between mean confidence and realised accuracy in each bin. An ECE near 0
    means "80% confident" predictions really are right about 80% of the time.

    Args:
        probabilities: ``(N, C)`` predicted class probabilities.
        labels: ``(N,)`` integer ground-truth classes.
        n_bins: Number of confidence bins.

    Returns:
        ECE in ``[0, 1]``; NaN when there is nothing to evaluate.
    """
    matrix = np.asarray(probabilities, dtype=np.float64)
    truth = np.asarray(labels, dtype=np.int64).ravel()

    if matrix.ndim != 2 or matrix.shape[0] == 0 or truth.shape[0] != matrix.shape[0]:
        return float("nan")

    confidences = np.max(matrix, axis=1)
    predictions = np.argmax(matrix, axis=1)
    correct = (predictions == truth).astype(np.float64)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    total = float(confidences.size)
    ece = 0.0

    for index in range(n_bins):
        low, high = bins[index], bins[index + 1]
        # Last bin is closed on the right so confidence == 1.0 is included.
        in_bin = (confidences > low) & (confidences <= high) if index < n_bins - 1 \
            else (confidences > low) & (confidences <= high + _EPS)

        count = int(np.count_nonzero(in_bin))
        if count == 0:
            continue

        mean_confidence = float(np.mean(confidences[in_bin]))
        mean_accuracy = float(np.mean(correct[in_bin]))
        ece += (count / total) * abs(mean_accuracy - mean_confidence)

    return float(round(ece, 5))


def reliability_curve(
    probabilities: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 10,
) -> List[Dict[str, Any]]:
    """
    Build reliability-diagram data (confidence vs realised accuracy per bin).

    Args:
        probabilities: ``(N, C)`` predicted class probabilities.
        labels: ``(N,)`` integer ground-truth classes.
        n_bins: Number of confidence bins.

    Returns:
        List of per-bin dictionaries suitable for direct chart rendering.
    """
    matrix = np.asarray(probabilities, dtype=np.float64)
    truth = np.asarray(labels, dtype=np.int64).ravel()

    if matrix.ndim != 2 or matrix.shape[0] == 0 or truth.shape[0] != matrix.shape[0]:
        return []

    confidences = np.max(matrix, axis=1)
    correct = (np.argmax(matrix, axis=1) == truth).astype(np.float64)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    curve: List[Dict[str, Any]] = []

    for index in range(n_bins):
        low, high = bins[index], bins[index + 1]
        in_bin = (confidences > low) & (confidences <= high)
        count = int(np.count_nonzero(in_bin))

        curve.append({
            "bin_index": index,
            "bin_low": round(float(low), 3),
            "bin_high": round(float(high), 3),
            "bin_center": round(float((low + high) / 2.0), 3),
            "count": count,
            "mean_confidence": round(float(np.mean(confidences[in_bin])), 4) if count else None,
            "mean_accuracy": round(float(np.mean(correct[in_bin])), 4) if count else None,
        })

    return curve


# ---------------------------------------------------------------------------
# Evidence channels
# ---------------------------------------------------------------------------

def lesion_evidence_score(lesion_result: Dict[str, Any]) -> float:
    """
    Score how decisively lesion evidence supports a grade, in ``[0, 1]``.

    Detection *quality* matters as much as detection *quantity*: a handful of
    clearly contrasting, well-formed lesions is stronger evidence than a dense
    scatter of marginal blobs that may be noise.

    Args:
        lesion_result: Output of
            :func:`backend.app.ml.lesion_detector.detect_lesions`.

    Returns:
        Evidence score where higher means more decisive.
    """
    if not lesion_result:
        return 0.0

    lesions = lesion_result.get("lesions", []) or []
    counts = lesion_result.get("counts", {}) or {}
    total = int(counts.get("total", len(lesions)))

    if total == 0:
        # A clean retina is itself informative: absence of lesions after a
        # successful detection pass is real evidence for grade 0.
        detection_ok = float(lesion_result.get("detection_reliability", 0.0))
        return round(0.55 * detection_ok, 4)

    mean_confidence = float(np.mean([
        float(lesion.get("confidence", 0.0)) for lesion in lesions
    ])) if lesions else 0.0

    # Saturating count term: evidence grows with lesion count but plateaus,
    # since 40 lesions is not meaningfully "more moderate" than 20.
    count_term = 1.0 - np.exp(-total / 12.0)

    # Haemorrhages and exudates carry more diagnostic weight than isolated MAs.
    significant = int(counts.get("hemorrhage", 0)) + int(counts.get("exudate", 0))
    severity_term = 1.0 - np.exp(-significant / 6.0)

    score = (
        0.40 * mean_confidence
        + 0.30 * float(count_term)
        + 0.30 * float(severity_term)
    )
    return round(float(np.clip(score, 0.0, 1.0)), 4)


def vascular_evidence_score(geometry: Dict[str, Any]) -> float:
    """
    Score how decisively vascular measurements support a grade, in ``[0, 1]``.

    Vessel geometry is only informative when the segmentation actually captured
    a plausible vascular tree; a degenerate mask yields a near-zero score so
    the grading falls back on lesion evidence.

    Args:
        geometry: Output of
            :func:`backend.app.processing.geometry.analyze_vessel_geometry`.

    Returns:
        Evidence score where higher means the vascular read-out is trustworthy.
    """
    if not geometry:
        return 0.0

    vessel_density = float(geometry.get("vessel_density", 0.0) or 0.0)
    skeleton_length = float(geometry.get("vessel_length_pixels", 0.0) or 0.0)
    branch_points = int(geometry.get("branch_points", 0) or 0)
    endpoints = int(geometry.get("endpoints", 0) or 0)
    fractal_dimension = float(geometry.get("fractal_dimension", 0.0) or 0.0)

    # A real retinal tree fills 4-20% of the field with vessels and branches
    # dozens of times. Outside that envelope the segmentation is suspect.
    density_term = float(np.clip((vessel_density - 2.0) / 6.0, 0.0, 1.0))
    length_term = float(np.clip(skeleton_length / 3000.0, 0.0, 1.0))
    branch_term = float(np.clip(branch_points / 25.0, 0.0, 1.0))

    # Fractal dimension of healthy retinal vasculature is roughly 1.35-1.75;
    # values far outside indicate over- or under-segmentation.
    if 1.20 <= fractal_dimension <= 1.90:
        fractal_term = 1.0 - abs(fractal_dimension - 1.55) / 0.35
        fractal_term = float(np.clip(fractal_term, 0.0, 1.0))
    else:
        fractal_term = 0.0

    # Topological sanity: a connected tree has roughly one endpoint per branch.
    topology_term = 1.0
    if branch_points > 0 and endpoints > 0:
        ratio = endpoints / float(branch_points)
        topology_term = float(np.clip(1.0 - abs(ratio - 2.0) / 4.0, 0.0, 1.0))

    score = (
        0.25 * density_term
        + 0.25 * length_term
        + 0.20 * branch_term
        + 0.15 * fractal_term
        + 0.15 * topology_term
    )
    return round(float(np.clip(score, 0.0, 1.0)), 4)


def quality_evidence_score(quality: Dict[str, Any]) -> float:
    """
    Score how far the image quality permits reliable automated reading.

    Args:
        quality: Output of
            :func:`backend.app.processing.quality.assess_image_quality`.

    Returns:
        Evidence score in ``[0, 1]``; near zero for ungradeable images.
    """
    if not quality:
        return 0.0

    score = float(quality.get("score", 0.0) or 0.0)
    metrics = quality.get("metrics", {}) or {}

    uniformity = float(metrics.get("illumination_uniformity", 0.0) or 0.0)
    coverage = float(metrics.get("roi_coverage_percent", 0.0) or 0.0)

    coverage_term = float(np.clip(coverage / 60.0, 0.0, 1.0))
    score = float(np.clip(score, 0.0, 1.0))
    uniformity = float(np.clip(uniformity, 0.0, 1.0))

    combined = 0.55 * score + 0.25 * uniformity + 0.20 * coverage_term
    return round(float(np.clip(combined, 0.0, 1.0)), 4)


def aggregate_confidence(
    lesion_score: float,
    vascular_score: float,
    quality_score: float,
    weights: Optional[Tuple[float, float, float]] = None,
) -> float:
    """
    Combine the three evidence channels into one reliability figure.

    The channels are weighted by configuration, then *attenuated* by the
    weakest one: strong lesion evidence cannot rescue a photograph too blurred
    to trust, so the aggregate is pulled toward the limiting factor rather than
    being a plain weighted mean.

    Args:
        lesion_score: From :func:`lesion_evidence_score`.
        vascular_score: From :func:`vascular_evidence_score`.
        quality_score: From :func:`quality_evidence_score`.
        weights: Optional ``(lesion, vascular, quality)`` overrides.

    Returns:
        Aggregate reliability in ``[0, 1]``.
    """
    config = settings.confidence

    if weights is None:
        weights = (
            config.weight_lesion_evidence,
            config.weight_vascular_evidence,
            config.weight_image_quality,
        )

    total_weight = float(sum(weights))
    if total_weight <= 0:
        weights = (1.0, 1.0, 1.0)
        total_weight = 3.0

    scores = (
        float(np.clip(lesion_score, 0.0, 1.0)),
        float(np.clip(vascular_score, 0.0, 1.0)),
        float(np.clip(quality_score, 0.0, 1.0)),
    )

    weighted_mean = sum(w * s for w, s in zip(weights, scores)) / total_weight
    weakest = min(scores)

    # Blend the mean with the limiting channel; 0.35 keeps a single weak input
    # from zeroing out an otherwise strong reading, while still biting.
    aggregate = 0.65 * weighted_mean + 0.35 * (weighted_mean * weakest)

    return round(float(np.clip(aggregate, 0.0, 1.0)), 4)


def confidence_label(value: float) -> str:
    """
    Map a numeric confidence to the tier label shown in the UI.

    Args:
        value: Confidence in ``[0, 1]``.

    Returns:
        One of ``High``, ``Moderate``, ``Low``.
    """
    config = settings.confidence
    try:
        score = float(value)
    except (TypeError, ValueError):
        return "Low"

    if not np.isfinite(score):
        return "Low"
    if score >= config.high_confidence_threshold:
        return "High"
    if score >= config.low_confidence_threshold:
        return "Moderate"
    return "Low"


def probability_distribution(
    logits: Sequence[float],
    temperature: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Convert grading logits into a calibrated probability distribution.

    Args:
        logits: Raw per-level evidence scores.
        temperature: Calibration temperature; defaults to the configured prior.

    Returns:
        Dictionary with ``probabilities``, ``temperature``, ``margin`` (gap
        between the top two classes) and ``entropy``.
    """
    config = settings.confidence
    temp = float(config.temperature if temperature is None else temperature)

    raw = np.asarray(logits, dtype=np.float64).ravel()
    if raw.size == 0:
        return {
            "probabilities": [],
            "temperature": temp,
            "margin": 0.0,
            "entropy": 0.0,
        }

    probabilities = softmax(raw, temp)
    ordered = np.sort(probabilities)[::-1]

    margin = float(ordered[0] - ordered[1]) if ordered.size > 1 else 1.0
    entropy = float(-np.sum(probabilities * np.log(probabilities + _EPS)))
    max_entropy = float(np.log(raw.size)) if raw.size > 1 else 1.0
    normalised_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    return {
        "probabilities": [round(float(p), 5) for p in probabilities],
        "temperature": round(temp, 4),
        "margin": round(margin, 5),
        "entropy": round(entropy, 5),
        "normalised_entropy": round(float(normalised_entropy), 5),
    }


def build_confidence_report(
    logits: Sequence[float],
    lesion_result: Dict[str, Any],
    geometry: Dict[str, Any],
    quality: Dict[str, Any],
    temperature: Optional[float] = None,
    gradeable: bool = True,
) -> Dict[str, Any]:
    """
    Assemble the complete confidence block returned by the API.

    Args:
        logits: Raw per-level grading evidence scores.
        lesion_result: Lesion detection output.
        geometry: Vessel geometry output.
        quality: Image quality output.
        temperature: Optional calibration temperature override.
        gradeable: Whether the image passed the technical gradeability gate.

    Returns:
        Dictionary containing the calibrated distribution, per-channel evidence
        scores, the aggregate reliability, and a human-readable explanation.
    """
    config = settings.confidence

    lesion_score = lesion_evidence_score(lesion_result)
    vascular_score = vascular_evidence_score(geometry)
    quality_score = quality_evidence_score(quality)

    distribution = probability_distribution(logits, temperature)
    probabilities = distribution["probabilities"]

    margin_confidence = float(np.clip(distribution["margin"], 0.0, 1.0))
    reliability = aggregate_confidence(lesion_score, vascular_score, quality_score)

    # Reported confidence is the decisiveness of the evidence, discounted by
    # how trustworthy the inputs were. An ungradeable image cannot be confident.
    confidence = margin_confidence * (0.35 + 0.65 * reliability)
    if not gradeable:
        confidence *= 0.25
    confidence = round(float(np.clip(confidence, 0.0, 1.0)), 4)

    label = confidence_label(confidence)

    explanation = (
        f"Confidence {confidence:.0%} ({label}). "
        f"Evidence separation between the top two grades is "
        f"{distribution['margin']:.0%}; lesion evidence {lesion_score:.2f}, "
        f"vascular evidence {vascular_score:.2f}, image quality {quality_score:.2f}."
    )
    if label == "Low":
        explanation += (
            " Evidence is weak or the image quality limits automated reading - "
            "clinical review is strongly advised."
        )

    return {
        "confidence": confidence,
        "confidence_label": label,
        "probabilities": probabilities,
        "temperature": distribution["temperature"],
        "margin": distribution["margin"],
        "entropy": distribution["entropy"],
        "normalised_entropy": distribution["normalised_entropy"],
        "evidence_scores": {
            "lesion": lesion_score,
            "vascular": vascular_score,
            "quality": quality_score,
            "weights": {
                "lesion": config.weight_lesion_evidence,
                "vascular": config.weight_vascular_evidence,
                "quality": config.weight_image_quality,
            },
        },
        "reliability": reliability,
        "gradeable": bool(gradeable),
        "explanation": explanation,
        "method": (
            "Temperature-scaled softmax over deterministic evidence logits, "
            "attenuated by per-channel reliability. Classical CV; no neural "
            "network inference is performed."
        ),
    }
