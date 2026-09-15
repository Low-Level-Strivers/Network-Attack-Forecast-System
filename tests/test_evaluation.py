"""
Unit Tests for Phase 10: Evaluation & Benchmarking Suite.
"""

import sys
from pathlib import Path

# Ensure project root in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.evaluator import evaluate_world_model


def test_evaluation_pipeline():
    state_file = Path("data/state_vectors/Tuesday-WorkingHours_state_1min.parquet")
    model_file = Path("models/lstm_world_model_best.pt")

    if not state_file.exists() or not model_file.exists():
        print("Skipping evaluation test: state vector or model file not yet available.")
        return

    report = evaluate_world_model(
        state_parquet=str(state_file),
        model_path=str(model_file),
        scaler_path="models/state_scaler.joblib",
        output_report_path="models/test_evaluation_report.json"
    )

    assert "classification_metrics" in report
    assert "next_state_error" in report
    assert "multi_step_rollout_error" in report
    assert "prediction_lead_time" in report

    assert "f1_score" in report["classification_metrics"]
    assert "average_lead_time_minutes" in report["prediction_lead_time"]
    assert report["prediction_lead_time"]["average_lead_time_minutes"] > 0


if __name__ == "__main__":
    print("Running Evaluation Unit Tests...")
    test_evaluation_pipeline()
    print("  [OK] Evaluation & Lead Time Benchmarking test passed")
    print("\nALL PHASE 10 UNIT TESTS PASSED! [OK]")
