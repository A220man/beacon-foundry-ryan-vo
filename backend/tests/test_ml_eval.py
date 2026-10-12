import pytest
from app.services.ml_eval_runner import (
    run_ml_benchmark, heuristic_predict, embedding_predict,
    get_text_embedding, compute_metrics, EVAL_DATASET
)

def test_embedding_projection_dimension():
    vec = get_text_embedding("CA TIME1\nTC CHECKTIM")
    assert len(vec) == 64
    # L2 norm check
    norm_sq = sum(x * x for x in vec)
    assert abs(norm_sq - 1.0) < 1e-4

def test_heuristic_predict_clean_vs_corrupt():
    clean = "CA TIME1\nTC CHECKTIM\nCCS WAITEXIT"
    corrupt = "TX TIME1\nTC\nCCS"
    clean_score = heuristic_predict(clean)
    corrupt_score = heuristic_predict(corrupt)
    assert corrupt_score > clean_score

def test_embedding_predict_clean_vs_corrupt():
    clean = "CA TIME1\nTC CHECKTIM\nCCS WAITEXIT"
    corrupt = "ZZ_UNKNOWN_OPCODE 9999\nBROKEN_OPERAND"
    clean_score = embedding_predict(clean)
    corrupt_score = embedding_predict(corrupt)
    assert corrupt_score > clean_score

def test_compute_metrics_accuracy():
    y_true = [0, 0, 1, 1]
    y_scores = [0.1, 0.2, 0.8, 0.9]
    metrics = compute_metrics(y_true, y_scores, threshold=0.5)
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1_score == 1.0
    assert metrics.roc_auc == 1.0

def test_full_ml_benchmark():
    res = run_ml_benchmark()
    assert res.total_samples == len(EVAL_DATASET)
    assert res.baseline_metrics.f1_score > 0.6
    assert res.embedding_metrics.f1_score > 0.7
    assert res.embedding_metrics.roc_auc > 0.8
    assert res.baseline_metrics.mean_latency_ms >= 0.0
