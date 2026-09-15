"""
Unit Tests for Phase 7 (MITRE ATT&CK Mapping) and Phase 8 (Explainability XAI).
"""

import sys
from pathlib import Path

# Ensure project root in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import torch

from src.mitre.mapper import MitreMapper, MITRE_TACTIC_DATABASE
from src.explainability.attributor import RiskAttributor
from src.models.world_model import LSTMWorldModel
from src.state_builder.aggregator import STATE_FEATURE_COLS


def test_mitre_mapping():
    for stage_id in [0, 1, 2, 3, 4]:
        intel = MitreMapper.map_stage_to_mitre(stage_id=stage_id, risk_score=0.85)
        assert "tactic_name" in intel
        assert "technique_id" in intel
        assert "description" in intel
        assert "mitigations" in intel
        assert len(intel["mitigations"]) > 0

    # Test dynamic refinement on brute force
    ref_intel = MitreMapper.map_stage_to_mitre(
        stage_id=2,
        risk_score=0.90,
        physical_metrics={"flow_count": 2500}
    )
    assert "High-Velocity" in ref_intel["technique_name"]


def test_integrated_gradients_xai():
    F = len(STATE_FEATURE_COLS)
    model = LSTMWorldModel(input_dim=F, hidden_dim=32, latent_dim=16, num_layers=1)
    attributor = RiskAttributor(model=model, feature_cols=STATE_FEATURE_COLS)

    dummy_seq = np.random.randn(30, F).astype(np.float32)
    xai_res = attributor.attribute_risk(dummy_seq, num_steps=10, top_k=5)

    assert "top_contributing_features" in xai_res
    assert "analyst_narrative" in xai_res
    assert len(xai_res["top_contributing_features"]) == 5

    # Check top feature keys
    top1 = xai_res["top_contributing_features"][0]
    assert "feature_name" in top1
    assert "importance_pct" in top1
    assert "direction" in top1
    assert top1["importance_pct"] >= 0.0


if __name__ == "__main__":
    print("Running MITRE & XAI Unit Tests...")
    test_mitre_mapping()
    print("  [OK] MITRE ATT&CK Mapping test passed")
    test_integrated_gradients_xai()
    print("  [OK] Integrated Gradients XAI Attribution test passed")
    print("\nALL PHASE 7 & 8 UNIT TESTS PASSED! [OK]")
