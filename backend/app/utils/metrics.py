"""
OcuPulse Evaluation Metrics

Reference implementations of the classification and segmentation metrics used
to validate the pipeline against public benchmarks (DRIVE for vessels, IDRiD
for lesions, APTOS 2019 / Messidor-2 for grading).

Everything here is pure numpy (plus ``scipy.stats.rankdata`` for tie-correct
AUC), so validation runs without a deep-learning stack. Undefined metrics -
for example sensitivity when a fold contains no positives - return ``float('nan')``
rather than a misleading ``0.0``; callers should use :func:`is_defined` before
displaying a value.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.stats import rankdata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def calculate_metrics(*args, **kwargs):
    return {}

def is_defined(value: Optional[float]) -> bool:
    """Return ``True`` when ``value`` is a finite number, i.e. a defined metric."""
    return value is not None and np.isfinite(value)


def _as_1d(values: Any) -> np.ndarray:
    """Flatten any array-like into a 1-D float64 vector."""
    return np.asarray(values, dtype=np.float64).ravel()


def _as_bool_mask(values: Any) -> np.ndarray:
    """Flatten any array-like into a 1-D boolean mask (non-zero is ``True``)."""
    return np.asarray(values).ravel().astype(bool)


def _check_same_length(a: np.ndarray, b: np.ndarray, what: str) -> None:
    """Raise when two vectors that must be aligned have different lengths."""
    if a.shape[0] != b.shape[0]:
        raise ValueError(
            f"{what} length mismatch: {a.shape[0]} vs {b.shape[0]}"
        )


def _safe_divide(numerator: float, denominator: float) -> float:
    """Divide, returning NaN when the denominator is zero."""
    if denominator == 0:
        return float("nan")
    return float(numerator) / float(denominator)


# ---------------------------------------------------------------------------
# Binary confusion matrix and derived rates
# ---------------------------------------------------------------------------

def confusion_counts(
    y_true: Any,
    y_pred: Any,
) -> Tuple[int, int, int, int]:
    """
    Compute binary confusion-matrix counts.

    Args:
        y_true: Ground-truth labels (non-zero treated as positive).
        y_pred: Predicted labels (non-zero treated as positive).

    Returns:
        Tuple ``(true_positives, false_positives, false_negatives, true_negatives)``.
    """
    truth = _as_bool_mask(y_true)
    prediction = _as_bool_mask(y_pred)
    _check_same_length(truth, prediction, "Confusion matrix input")

    tp = int(np.count_nonzero(truth & prediction))
    fp = int(np.count_nonzero(~truth & prediction))
    fn = int(np.count_nonzero(truth & ~prediction))
    tn = int(np.count_nonzero(~truth & ~prediction))
    return tp, fp, fn, tn


def accuracy(y_true: Any, y_pred: Any) -> float:
    """Fraction of all predictions that are correct."""
    tp, fp, fn, tn = confusion_counts(y_true, y_pred)
    return _safe_divide(tp + tn, tp + fp + fn + tn)


def sensitivity(y_true: Any, y_pred: Any) -> float:
    """
    Sensitivity (recall / true-positive rate).

    Central to DR screening: the cost of a missed referable case far exceeds
    the cost of an unnecessary referral. NaN when there are no positives.
    """
    tp, _, fn, _ = confusion_counts(y_true, y_pred)
    return _safe_divide(tp, tp + fn)


#: Clinical synonym for :func:`sensitivity`.
recall = sensitivity
true_positive_rate = sensitivity


def specificity(y_true: Any, y_pred: Any) -> float:
    """
    Specificity (true-negative rate).

    Governs how many healthy patients are needlessly referred onward.
    NaN when there are no negatives.
    """
    _, fp, _, tn = confusion_counts(y_true, y_pred)
    return _safe_divide(tn, tn + fp)


true_negative_rate = specificity


def precision(y_true: Any, y_pred: Any) -> float:
    """Positive predictive value. NaN when nothing was predicted positive."""
    tp, fp, _, _ = confusion_counts(y_true, y_pred)
    return _safe_divide(tp, tp + fp)


positive_predictive_value = precision


def negative_predictive_value(y_true: Any, y_pred: Any) -> float:
    """Probability that a negative prediction is truly negative."""
    _, _, fn, tn = confusion_counts(y_true, y_pred)
    return _safe_divide(tn, tn + fn)


def false_positive_rate(y_true: Any, y_pred: Any) -> float:
    """Complement of specificity."""
    _, fp, _, tn = confusion_counts(y_true, y_pred)
    return _safe_divide(fp, fp + tn)


def false_negative_rate(y_true: Any, y_pred: Any) -> float:
    """Complement of sensitivity - the missed-case rate."""
    tp, _, fn, _ = confusion_counts(y_true, y_pred)
    return _safe_divide(fn, tp + fn)


def f1_score(y_true: Any, y_pred: Any) -> float:
    """Harmonic mean of precision and sensitivity."""
    tp, fp, fn, _ = confusion_counts(y_true, y_pred)
    return _safe_divide(2 * tp, 2 * tp + fp + fn)


def balanced_accuracy(y_true: Any, y_pred: Any) -> float:
    """
    Mean of sensitivity and specificity.

    Preferred over raw accuracy on imbalanced screening cohorts, where a
    trivial "always negative" classifier would otherwise score highly.
    """
    sens = sensitivity(y_true, y_pred)
    spec = specificity(y_true, y_pred)
    if not (is_defined(sens) and is_defined(spec)):
        return float("nan")
    return float((sens + spec) / 2.0)


def matthews_corrcoef(y_true: Any, y_pred: Any) -> float:
    """
    Matthews correlation coefficient in ``[-1, 1]``.

    Uses all four confusion-matrix cells and stays informative under the class
    imbalance typical of referable-DR screening.
    """
    tp, fp, fn, tn = confusion_counts(y_true, y_pred)
    denominator = np.sqrt(float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    if denominator == 0:
        return float("nan")
    return float((tp * tn - fp * fn) / denominator)


def binary_classification_report(y_true: Any, y_pred: Any) -> Dict[str, float]:
    """Bundle every binary rate into one dictionary for reporting."""
    tp, fp, fn, tn = confusion_counts(y_true, y_pred)
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "n_samples": tp + fp + fn + tn,
        "accuracy": accuracy(y_true, y_pred),
        "sensitivity": sensitivity(y_true, y_pred),
        "specificity": specificity(y_true, y_pred),
        "precision": precision(y_true, y_pred),
        "negative_predictive_value": negative_predictive_value(y_true, y_pred),
        "f1_score": f1_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy(y_true, y_pred),
        "matthews_corrcoef": matthews_corrcoef(y_true, y_pred),
        "false_positive_rate": false_positive_rate(y_true, y_pred),
        "false_negative_rate": false_negative_rate(y_true, y_pred),
    }


# ---------------------------------------------------------------------------
# Segmentation overlap metrics (vessel / lesion masks)
# ---------------------------------------------------------------------------

def dice_coefficient(y_true: Any, y_pred: Any) -> float:
    """
    Sorensen-Dice overlap between two binary masks.

    The standard headline metric for vessel segmentation on DRIVE and STARE.
    Returns NaN when both masks are empty (overlap is undefined, not perfect),
    and ``0.0`` when exactly one is empty.
    """
    truth = _as_bool_mask(y_true)
    prediction = _as_bool_mask(y_pred)
    _check_same_length(truth, prediction, "Dice input")

    truth_count = int(np.count_nonzero(truth))
    pred_count = int(np.count_nonzero(prediction))

    if truth_count == 0 and pred_count == 0:
        return float("nan")
    if truth_count == 0 or pred_count == 0:
        return 0.0

    intersection = int(np.count_nonzero(truth & prediction))
    return float(2.0 * intersection / (truth_count + pred_count))


def jaccard_index(y_true: Any, y_pred: Any) -> float:
    """
    Jaccard index (intersection over union) between two binary masks.

    NaN only when both masks are empty, mirroring :func:`dice_coefficient`.
    """
    truth = _as_bool_mask(y_true)
    prediction = _as_bool_mask(y_pred)
    _check_same_length(truth, prediction, "Jaccard input")

    truth_count = int(np.count_nonzero(truth))
    pred_count = int(np.count_nonzero(prediction))

    if truth_count == 0 and pred_count == 0:
        return float("nan")

    intersection = int(np.count_nonzero(truth & prediction))
    union = truth_count + pred_count - intersection
    return _safe_divide(intersection, union)


#: Common alias for :func:`jaccard_index`.
iou = jaccard_index


def segmentation_report(y_true: Any, y_pred: Any) -> Dict[str, float]:
    """
    Full pixel-level report for a segmentation mask.

    Args:
        y_true: Ground-truth mask (any shape; flattened).
        y_pred: Predicted mask of the same shape.

    Returns:
        Dictionary of overlap and pixel-classification metrics.
    """
    truth = _as_bool_mask(y_true)
    prediction = _as_bool_mask(y_pred)
    _check_same_length(truth, prediction, "Segmentation input")

    report = binary_classification_report(truth.astype(np.uint8), prediction.astype(np.uint8))
    report["dice_coefficient"] = dice_coefficient(truth, prediction)
    report["jaccard_index"] = jaccard_index(truth, prediction)
    report["ground_truth_pixels"] = int(np.count_nonzero(truth))
    report["predicted_pixels"] = int(np.count_nonzero(prediction))
    return report


# ---------------------------------------------------------------------------
# Ranking metrics
# ---------------------------------------------------------------------------

def roc_auc_score(y_true: Any, y_score: Any) -> float:
    """
    Area under the ROC curve from continuous scores.

    Computed with the Mann-Whitney U equivalence, using average ranks so tied
    scores contribute ``0.5`` credit exactly as the trapezoidal definition
    requires.

    Args:
        y_true: Binary ground truth (non-zero is positive).
        y_score: Continuous prediction scores, higher meaning more positive.

    Returns:
        AUC in ``[0, 1]``; NaN when either class is absent.
    """
    truth = _as_bool_mask(y_true)
    scores = _as_1d(y_score)
    _check_same_length(truth, scores, "ROC AUC input")

    n_pos = int(np.count_nonzero(truth))
    n_neg = int(truth.shape[0] - n_pos)

    if n_pos == 0 or n_neg == 0:
        return float("nan")

    # 'average' resolves ties to their mean rank, which is what AUC expects.
    ranks = rankdata(scores, method="average")
    positive_rank_sum = float(np.sum(ranks[truth]))

    auc = (positive_rank_sum - n_pos * (n_pos + 1) / 2.0) / float(n_pos * n_neg)
    return float(np.clip(auc, 0.0, 1.0))


def roc_curve(
    y_true: Any,
    y_score: Any,
    max_points: int = 200,
) -> Dict[str, List[float]]:
    """
    Sample ROC curve coordinates for plotting.

    Args:
        y_true: Binary ground truth.
        y_score: Continuous prediction scores.
        max_points: Cap on returned points, to keep payloads small.

    Returns:
        Dictionary with ``fpr``, ``tpr`` and ``thresholds`` lists.
    """
    truth = _as_bool_mask(y_true)
    scores = _as_1d(y_score)
    _check_same_length(truth, scores, "ROC curve input")

    n_pos = int(np.count_nonzero(truth))
    n_neg = int(truth.shape[0] - n_pos)

    if n_pos == 0 or n_neg == 0:
        return {"fpr": [0.0, 1.0], "tpr": [0.0, 1.0], "thresholds": [1.0, 0.0]}

    order = np.argsort(-scores, kind="mergesort")
    sorted_truth = truth[order]
    thresholds = scores[order]

    tps = np.cumsum(sorted_truth)
    fps = np.cumsum(~sorted_truth)

    tpr = np.concatenate(([0.0], tps / float(n_pos)))
    fpr = np.concatenate(([0.0], fps / float(n_neg)))
    thresholds = np.concatenate(([thresholds[0] + 1.0], thresholds))

    if len(tpr) > max_points:
        indices = np.linspace(0, len(tpr) - 1, max_points).astype(int)
        tpr, fpr, thresholds = tpr[indices], fpr[indices], thresholds[indices]

    return {
        "fpr": [round(float(v), 5) for v in fpr],
        "tpr": [round(float(v), 5) for v in tpr],
        "thresholds": [round(float(v), 5) for v in thresholds],
    }


def average_precision(y_true: Any, y_score: Any) -> float:
    """
    Area under the precision-recall curve (average precision).

    More informative than ROC AUC on heavily imbalanced lesion-detection tasks,
    where the negative class dominates.

    Args:
        y_true: Binary ground truth.
        y_score: Continuous prediction scores.

    Returns:
        Average precision in ``[0, 1]``; NaN when there are no positives.
    """
    truth = _as_bool_mask(y_true)
    scores = _as_1d(y_score)
    _check_same_length(truth, scores, "Average precision input")

    n_pos = int(np.count_nonzero(truth))
    if n_pos == 0:
        return float("nan")

    order = np.argsort(-scores, kind="mergesort")
    sorted_truth = truth[order]

    tps = np.cumsum(sorted_truth)
    retrieved = np.arange(1, sorted_truth.shape[0] + 1, dtype=np.float64)

    precisions = tps / retrieved
    return float(np.sum(precisions[sorted_truth]) / n_pos)


# ---------------------------------------------------------------------------
# Multi-class grading metrics
# ---------------------------------------------------------------------------

def multiclass_confusion_matrix(
    y_true: Any,
    y_pred: Any,
    n_classes: Optional[int] = None,
) -> np.ndarray:
    """
    Build an ``n_classes x n_classes`` confusion matrix.

    Rows are ground truth, columns are predictions.

    Args:
        y_true: Integer ground-truth labels.
        y_pred: Integer predicted labels.
        n_classes: Matrix size; inferred from the data when omitted.

    Returns:
        Integer confusion matrix.
    """
    truth = _as_1d(y_true).astype(np.int64)
    prediction = _as_1d(y_pred).astype(np.int64)
    _check_same_length(truth, prediction, "Confusion matrix input")

    if n_classes is None:
        highest = max(
            int(truth.max()) if truth.size else 0,
            int(prediction.max()) if prediction.size else 0,
        )
        n_classes = highest + 1

    if n_classes <= 0:
        raise ValueError("n_classes must be positive")

    if truth.size and (truth.min() < 0 or truth.max() >= n_classes):
        raise ValueError(f"y_true labels outside [0, {n_classes})")
    if prediction.size and (prediction.min() < 0 or prediction.max() >= n_classes):
        raise ValueError(f"y_pred labels outside [0, {n_classes})")

    matrix = np.zeros((n_classes, n_classes), dtype=np.int64)
    np.add.at(matrix, (truth, prediction), 1)
    return matrix


def cohen_kappa(y_true: Any, y_pred: Any, n_classes: Optional[int] = None) -> float:
    """
    Cohen's kappa: agreement corrected for chance.

    Treats every disagreement as equally bad, so it under-credits a grader that
    is off by one level. Prefer :func:`quadratic_weighted_kappa` for ordinal DR
    grading; this is provided for completeness and for non-ordinal labels.
    """
    matrix = multiclass_confusion_matrix(y_true, y_pred, n_classes)
    total = float(matrix.sum())
    if total == 0:
        return float("nan")

    observed = float(np.trace(matrix)) / total
    row_marginals = matrix.sum(axis=1) / total
    col_marginals = matrix.sum(axis=0) / total
    expected = float(np.sum(row_marginals * col_marginals))

    if expected == 1.0:
        return float("nan")
    return float((observed - expected) / (1.0 - expected))


def quadratic_weighted_kappa(
    y_true: Any,
    y_pred: Any,
    n_classes: Optional[int] = None,
) -> float:
    """
    Quadratic weighted kappa (QWK) - the official APTOS 2019 ranking metric.

    Disagreements are penalised by the *square* of the level distance, so
    predicting Mild (1) for Moderate (2) costs far less than predicting No DR
    (0) for Proliferative (4). This matches the clinical reality that adjacent
    grading errors are tolerable while large ones are not.

    Args:
        y_true: Integer DR grades.
        y_pred: Integer predicted grades.
        n_classes: Number of ordinal levels; defaults to 5 (APTOS 0-4).

    Returns:
        QWK in ``[-1, 1]``; ``1`` is perfect, ``0`` is chance level.
    """
    if n_classes is None:
        n_classes = 5

    matrix = multiclass_confusion_matrix(y_true, y_pred, n_classes).astype(np.float64)
    total = matrix.sum()
    if total == 0:
        return float("nan")

    levels = np.arange(n_classes, dtype=np.float64)
    # Squared-distance penalty matrix, normalised to [0, 1].
    weights = (levels[:, None] - levels[None, :]) ** 2
    if n_classes > 1:
        weights = weights / float((n_classes - 1) ** 2)

    expected = np.outer(matrix.sum(axis=1), matrix.sum(axis=0)) / total

    observed_penalty = float(np.sum(weights * matrix))
    expected_penalty = float(np.sum(weights * expected))

    if expected_penalty == 0:
        return float("nan")

    return float(1.0 - observed_penalty / expected_penalty)


def per_class_report(
    y_true: Any,
    y_pred: Any,
    labels: Optional[Sequence[str]] = None,
    n_classes: Optional[int] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Per-class precision, recall and support from the confusion matrix.

    Args:
        y_true: Integer ground-truth labels.
        y_pred: Integer predicted labels.
        labels: Optional human-readable names per class.
        n_classes: Number of classes; inferred when omitted.

    Returns:
        Mapping of class name to its precision, recall, f1 and support.
    """
    matrix = multiclass_confusion_matrix(y_true, y_pred, n_classes)
    classes = matrix.shape[0]

    names = list(labels) if labels else [str(i) for i in range(classes)]
    while len(names) < classes:
        names.append(str(len(names)))

    report: Dict[str, Dict[str, float]] = {}
    for index in range(classes):
        tp = float(matrix[index, index])
        support = float(matrix[index, :].sum())          # actual class count
        predicted_as = float(matrix[:, index].sum())     # predicted class count
        fp = predicted_as - tp
        fn = support - tp

        prec = _safe_divide(tp, tp + fp)
        rec = _safe_divide(tp, tp + fn)
        f1 = _safe_divide(2 * tp, 2 * tp + fp + fn)

        report[names[index]] = {
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "support": support,
        }

    return report


def macro_f1(y_true: Any, y_pred: Any, n_classes: Optional[int] = None) -> float:
    """Unweighted mean of per-class F1 scores; NaN when no class is defined."""
    report = per_class_report(y_true, y_pred, None, n_classes)
    values = [m["f1_score"] for m in report.values() if is_defined(m["f1_score"])]
    if not values:
        return float("nan")
    return float(np.mean(values))


# ---------------------------------------------------------------------------
# Regression metrics (continuous biomarkers)
# ---------------------------------------------------------------------------

def mean_absolute_error(y_true: Any, y_pred: Any) -> float:
    """Mean absolute difference between predicted and true continuous values."""
    truth = _as_1d(y_true)
    prediction = _as_1d(y_pred)
    _check_same_length(truth, prediction, "MAE input")
    if truth.size == 0:
        return float("nan")
    return float(np.mean(np.abs(truth - prediction)))


def root_mean_squared_error(y_true: Any, y_pred: Any) -> float:
    """Root mean squared difference; penalises large biomarker errors."""
    truth = _as_1d(y_true)
    prediction = _as_1d(y_pred)
    _check_same_length(truth, prediction, "RMSE input")
    if truth.size == 0:
        return float("nan")
    return float(np.sqrt(np.mean((truth - prediction) ** 2)))


def pearson_correlation(y_true: Any, y_pred: Any) -> float:
    """
    Linear correlation between predicted and true continuous values.

    NaN when either vector has zero variance, since correlation is undefined.
    """
    truth = _as_1d(y_true)
    prediction = _as_1d(y_pred)
    _check_same_length(truth, prediction, "Correlation input")

    if truth.size < 2:
        return float("nan")

    truth_std = float(np.std(truth))
    prediction_std = float(np.std(prediction))
    if truth_std == 0.0 or prediction_std == 0.0:
        return float("nan")

    return float(np.mean((truth - np.mean(truth)) * (prediction - np.mean(prediction)))
                 / (truth_std * prediction_std))


# ---------------------------------------------------------------------------
# Aggregate validation summary
# ---------------------------------------------------------------------------

def referable_dr_labels(y_grade: Any, threshold: int = 2) -> np.ndarray:
    """
    Collapse ordinal DR grades into the binary referable-DR decision.

    Args:
        y_grade: Integer grades (APTOS 0-4).
        threshold: Grade at or above which referral is indicated.

    Returns:
        Boolean array where ``True`` means referable.
    """
    return _as_1d(y_grade).astype(np.int64) >= int(threshold)


def validation_summary(
    y_true: Any,
    y_pred: Any,
    y_score: Optional[Any] = None,
    labels: Optional[Sequence[str]] = None,
    n_classes: int = 5,
    referable_threshold: int = 2,
    target_sensitivity: Optional[float] = None,
    target_specificity: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Produce the complete validation block reported for a benchmark dataset.

    Combines ordinal grading agreement (QWK), per-class behaviour, and the
    binary referable-DR operating point that actually drives referral decisions,
    then compares measured sensitivity/specificity against the clinical targets.

    Args:
        y_true: Integer ground-truth grades.
        y_pred: Integer predicted grades.
        y_score: Optional continuous referable-DR scores for AUC.
        labels: Optional class names.
        n_classes: Number of ordinal levels (APTOS uses 5).
        referable_threshold: Grade at/above which a case is referable.
        target_sensitivity: Clinical sensitivity goal, for pass/fail reporting.
        target_specificity: Clinical specificity goal, for pass/fail reporting.

    Returns:
        Nested dictionary of grading, referable and (optionally) ranking metrics.
    """
    truth = _as_1d(y_true).astype(np.int64)
    prediction = _as_1d(y_pred).astype(np.int64)
    _check_same_length(truth, prediction, "Validation input")

    default_labels = labels or [f"Level {i}" for i in range(n_classes)]

    summary: Dict[str, Any] = {
        "n_samples": int(truth.size),
        "grading": {
            "quadratic_weighted_kappa": quadratic_weighted_kappa(truth, prediction, n_classes),
            "cohen_kappa": cohen_kappa(truth, prediction, n_classes),
            "exact_match_accuracy": accuracy(truth, prediction),
            "within_one_level_accuracy": float(
                np.mean(np.abs(truth - prediction) <= 1)
            ) if truth.size else float("nan"),
            "mean_absolute_error": mean_absolute_error(truth, prediction),
            "macro_f1": macro_f1(truth, prediction, n_classes),
            "per_class": per_class_report(truth, prediction, default_labels, n_classes),
            "confusion_matrix": multiclass_confusion_matrix(
                truth, prediction, n_classes
            ).tolist(),
        },
    }

    # Binary referable-DR operating point (the decision that matters clinically).
    referable_true = referable_dr_labels(truth, referable_threshold)
    referable_pred = referable_dr_labels(prediction, referable_threshold)
    referable_report = binary_classification_report(
        referable_true.astype(np.uint8), referable_pred.astype(np.uint8)
    )
    referable_report["threshold_level"] = int(referable_threshold)
    referable_report["prevalence"] = float(np.mean(referable_true)) if truth.size else float("nan")

    if target_sensitivity is not None and is_defined(referable_report["sensitivity"]):
        referable_report["meets_sensitivity_target"] = bool(
            referable_report["sensitivity"] >= target_sensitivity
        )
        referable_report["sensitivity_target"] = float(target_sensitivity)

    if target_specificity is not None and is_defined(referable_report["specificity"]):
        referable_report["meets_specificity_target"] = bool(
            referable_report["specificity"] >= target_specificity
        )
        referable_report["specificity_target"] = float(target_specificity)

    summary["referable_dr"] = referable_report

    if y_score is not None:
        scores = _as_1d(y_score)
        if scores.size == truth.size:
            summary["ranking"] = {
                "roc_auc": roc_auc_score(referable_true.astype(np.uint8), scores),
                "average_precision": average_precision(
                    referable_true.astype(np.uint8), scores
                ),
            }

    return summary
