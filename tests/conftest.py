"""
Shared pytest fixtures for VitalWatch 2.0 test suite.

Fixtures here are auto-available to every test module.
The backend/ directory is added to sys.path so all imports
resolve correctly without installing the package.
"""
import sys
import os
import pytest

# Make backend/ importable without `pip install -e .`
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


@pytest.fixture(scope="session")
def engine():
    """
    One PredictionEngine instance shared across the whole test session.
    Loading the 22 MB CSV and the pickled model once is enough.
    """
    from predict import PredictionEngine
    return PredictionEngine()


@pytest.fixture(scope="session")
def healthy_vitals():
    """A realistic set of vitals for a stable patient (MAP well above 65)."""
    return {
        "MAP_current": 95.0,
        "HR_current": 72.0,
        "SpO2_current": 99.0,
        "MAP_mean_1m": 94.0,
        "MAP_mean_3m": 93.0,
        "MAP_std_1m": 2.5,
        "MAP_min_1m": 90.0,
        "MAP_min_3m": 88.0,
        "MAP_trend_30s": -0.5,
        "MAP_trend_60s": -0.3,
        "HR_mean_1m": 71.0,
        "HR_mean_3m": 70.0,
        "HR_std_1m": 1.8,
        "HR_min_1m": 68.0,
        "HR_min_3m": 67.0,
        "HR_trend_30s": 0.1,
        "HR_trend_60s": 0.2,
        "SpO2_mean_1m": 98.8,
        "SpO2_mean_3m": 98.5,
        "SpO2_std_1m": 0.4,
        "SpO2_min_1m": 98.0,
        "SpO2_min_3m": 97.5,
        "SpO2_trend_30s": 0.0,
        "SpO2_trend_60s": 0.0,
        "map_distance_to_65": 30.0,
        "map_below_75": 0.0,
        "map_below_70": 0.0,
        "map_dropping_fast": 0.0,
        "hr_map_ratio": 0.758,
    }


@pytest.fixture(scope="session")
def high_risk_vitals():
    """Vitals characteristic of an imminent IOH event (MAP near 65, dropping fast)."""
    return {
        "MAP_current": 66.0,
        "HR_current": 95.0,
        "SpO2_current": 97.0,
        "MAP_mean_1m": 72.0,
        "MAP_mean_3m": 80.0,
        "MAP_std_1m": 6.0,
        "MAP_min_1m": 64.0,
        "MAP_min_3m": 63.0,
        "MAP_trend_30s": -3.5,
        "MAP_trend_60s": -4.2,
        "HR_mean_1m": 93.0,
        "HR_mean_3m": 88.0,
        "HR_std_1m": 4.0,
        "HR_min_1m": 90.0,
        "HR_min_3m": 85.0,
        "HR_trend_30s": 2.0,
        "HR_trend_60s": 3.5,
        "SpO2_mean_1m": 97.2,
        "SpO2_mean_3m": 97.5,
        "SpO2_std_1m": 0.8,
        "SpO2_min_1m": 96.5,
        "SpO2_min_3m": 96.0,
        "SpO2_trend_30s": -0.2,
        "SpO2_trend_60s": -0.4,
        "map_distance_to_65": 1.0,
        "map_below_75": 1.0,
        "map_below_70": 1.0,
        "map_dropping_fast": 1.0,
        "hr_map_ratio": 1.439,
    }


@pytest.fixture(scope="session")
def test_client(engine):
    """
    FastAPI TestClient with the prediction engine pre-loaded.
    NODE_ENV=test prevents the server from binding a real port.
    """
    import os
    os.environ.setdefault("NODE_ENV", "test")

    # Patch the global prediction_engine before importing main
    import main as main_module
    main_module.prediction_engine = engine

    from fastapi.testclient import TestClient
    return TestClient(main_module.app)
