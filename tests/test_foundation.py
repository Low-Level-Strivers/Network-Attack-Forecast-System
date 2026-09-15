"""
Phase 0 Foundation Test: Validates directory structure, configuration loading, and package importability.
"""

import sys
from pathlib import Path

# Ensure project root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml


def test_config_structure():
    config_path = Path("config/config.yaml")
    assert config_path.exists(), "config/config.yaml does not exist"

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    assert "project" in cfg
    assert "paths" in cfg
    assert "windowing" in cfg
    assert "sequence" in cfg
    assert "features" in cfg
    assert "model" in cfg

    assert cfg["windowing"]["window_size_sec"] == 60
    assert cfg["sequence"]["lookback_steps"] == 30
    assert cfg["sequence"]["forecast_horizon"] == 5
    assert len(cfg["features"]["state_features"]) >= 20


def test_directories_exist():
    expected_dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("data/state_vectors"),
        Path("models"),
        Path("notebooks"),
        Path("dashboard"),
        Path("src/ingestion"),
        Path("src/preprocessing"),
        Path("src/feature_engineering"),
        Path("src/state_builder"),
        Path("src/sequence_builder"),
        Path("src/models"),
        Path("src/forecasting"),
        Path("src/mitre"),
        Path("src/explainability"),
        Path("src/evaluation"),
    ]
    for d in expected_dirs:
        assert d.exists() and d.is_dir(), f"Expected directory missing: {d}"


def test_module_imports():
    import src
    import src.ingestion
    import src.preprocessing
    import src.feature_engineering
    import src.state_builder
    import src.sequence_builder
    import src.models
    import src.forecasting
    import src.mitre
    import src.explainability
    import src.evaluation

    assert src.__version__ == "0.1.0"
