"""
Unit tests for PredictionEngine — predict(), explain(), get_model_metrics().

These tests run against the real pre-trained model and the real test_sample.csv,
so they are genuine integration-level checks on the ML pipeline, not mocks.
"""
import pytest


# ---------------------------------------------------------------------------
# Engine loading
# ---------------------------------------------------------------------------

class TestEngineLoading:
    def test_model_is_loaded(self, engine):
        """PredictionEngine must load a scikit-learn model from models/."""
        assert engine.model is not None, "Model should not be None after init"

    def test_scaler_is_loaded(self, engine):
        assert engine.scaler is not None, "StandardScaler should not be None after init"

    def test_feature_cols_loaded(self, engine):
        assert engine.feature_cols is not None
        assert len(engine.feature_cols) == 29, (
            f"Expected 29 feature columns, got {len(engine.feature_cols)}"
        )

    def test_dataframe_loaded(self, engine):
        assert not engine.df.empty, "test_sample.csv must be loaded into engine.df"
        assert len(engine.df) > 10_000, "Dataset should have >10k rows"

    def test_dataframe_has_required_columns(self, engine):
        required = {"case_id", "MAP_current", "HR_current", "SpO2_current"}
        missing = required - set(engine.df.columns)
        assert not missing, f"Missing columns in dataframe: {missing}"


# ---------------------------------------------------------------------------
# predict()
# ---------------------------------------------------------------------------

class TestPredict:
    def test_returns_three_tuple(self, engine, healthy_vitals):
        result = engine.predict(healthy_vitals)
        assert len(result) == 3, "predict() must return (risk_score, alert_level, alert_message)"

    def test_risk_score_is_float_in_range(self, engine, healthy_vitals):
        risk_score, _, _ = engine.predict(healthy_vitals)
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0, f"Risk score {risk_score} out of [0, 1]"

    def test_alert_level_valid_values(self, engine, healthy_vitals):
        _, alert_level, _ = engine.predict(healthy_vitals)
        assert alert_level in ("low", "medium", "high"), (
            f"Unexpected alert level: {alert_level}"
        )

    def test_alert_message_is_string(self, engine, healthy_vitals):
        _, _, alert_message = engine.predict(healthy_vitals)
        assert isinstance(alert_message, str) and len(alert_message) > 0

    def test_stable_patient_gives_low_risk(self, engine, healthy_vitals):
        """A patient with MAP=95 and no downward trend should score low risk."""
        risk_score, alert_level, _ = engine.predict(healthy_vitals)
        assert risk_score < 0.5, (
            f"Expected low risk for stable vitals, got {risk_score:.3f}"
        )
        assert alert_level == "low"

    def test_high_risk_vitals_score_higher_than_stable(self, engine, healthy_vitals, high_risk_vitals):
        """Vitals near IOH threshold should score strictly higher than stable vitals."""
        stable_score, _, _ = engine.predict(healthy_vitals)
        risky_score, _, _  = engine.predict(high_risk_vitals)
        assert risky_score > stable_score, (
            f"High-risk vitals ({risky_score:.3f}) should score higher than "
            f"stable vitals ({stable_score:.3f})"
        )

    def test_predict_is_deterministic(self, engine, healthy_vitals):
        """Same input must always produce the same output."""
        score_a, level_a, _ = engine.predict(healthy_vitals)
        score_b, level_b, _ = engine.predict(healthy_vitals)
        assert score_a == score_b
        assert level_a == level_b

    def test_missing_feature_key_returns_error_tuple(self, engine):
        """If a required feature is absent, predict() must not raise — return safe fallback."""
        incomplete = {"MAP_current": 90.0}  # missing 28 features
        risk_score, alert_level, msg = engine.predict(incomplete)
        # Should degrade gracefully, not crash
        assert isinstance(risk_score, float)
        assert alert_level in ("low", "medium", "high", "error") or "error" in msg.lower()


# ---------------------------------------------------------------------------
# explain()
# ---------------------------------------------------------------------------

class TestExplain:
    def test_returns_list(self, engine, healthy_vitals):
        result = engine.explain(healthy_vitals)
        assert isinstance(result, list), "explain() must return a list"

    def test_returns_up_to_ten_features(self, engine, healthy_vitals):
        result = engine.explain(healthy_vitals)
        assert 1 <= len(result) <= 10, f"Expected 1–10 SHAP features, got {len(result)}"

    def test_each_entry_has_required_keys(self, engine, healthy_vitals):
        result = engine.explain(healthy_vitals)
        for entry in result:
            assert "name" in entry,   f"Missing 'name' key in {entry}"
            assert "value" in entry,  f"Missing 'value' key in {entry}"
            assert "impact" in entry, f"Missing 'impact' key in {entry}"

    def test_impact_values_are_floats(self, engine, healthy_vitals):
        result = engine.explain(healthy_vitals)
        for entry in result:
            assert isinstance(entry["impact"], float), (
                f"impact should be float, got {type(entry['impact'])}"
            )

    def test_sorted_by_absolute_impact_descending(self, engine, healthy_vitals):
        result = engine.explain(healthy_vitals)
        impacts = [abs(e["impact"]) for e in result]
        assert impacts == sorted(impacts, reverse=True), (
            "SHAP features must be sorted by |impact| descending"
        )

    def test_feature_names_in_known_set(self, engine, healthy_vitals):
        result = engine.explain(healthy_vitals)
        known = set(engine.feature_cols)
        for entry in result:
            assert entry["name"] in known, (
                f"Unknown feature name in SHAP output: {entry['name']}"
            )


# ---------------------------------------------------------------------------
# get_model_metrics()
# ---------------------------------------------------------------------------

class TestModelMetrics:
    @pytest.fixture(scope="class")
    def metrics(self, engine):
        return engine.get_model_metrics()

    def test_returns_dict_not_none(self, metrics):
        assert metrics is not None, "get_model_metrics() returned None — model or data not loaded"
        assert isinstance(metrics, dict)

    def test_required_top_level_keys(self, metrics):
        required = {"auc_roc", "roc_curve", "sensitivity", "confusion_matrix",
                    "feature_importance", "total_rows", "ioh_rate", "default_threshold"}
        missing = required - metrics.keys()
        assert not missing, f"Missing keys in metrics: {missing}"

    def test_auc_roc_is_plausible(self, metrics):
        auc = metrics["auc_roc"]
        assert isinstance(auc, float)
        assert 0.5 < auc <= 1.0, f"AUC-ROC {auc} is implausibly low — model or labels broken"

    def test_roc_curve_has_100_points(self, metrics):
        assert len(metrics["roc_curve"]) == 100

    def test_roc_curve_points_have_fpr_tpr(self, metrics):
        for pt in metrics["roc_curve"]:
            assert "fpr" in pt and "tpr" in pt
            assert 0.0 <= pt["fpr"] <= 100.0
            assert 0.0 <= pt["tpr"] <= 100.0

    def test_sensitivity_has_entries(self, metrics):
        assert len(metrics["sensitivity"]) >= 10, "Need at least 10 threshold steps"

    def test_sensitivity_row_keys(self, metrics):
        for row in metrics["sensitivity"]:
            for key in ("threshold", "precision", "recall", "f1"):
                assert key in row, f"Missing key '{key}' in sensitivity row: {row}"
            assert 0.0 <= row["precision"] <= 1.0
            assert 0.0 <= row["recall"]    <= 1.0
            assert 0.0 <= row["f1"]        <= 1.0

    def test_confusion_matrix_cells_non_negative(self, metrics):
        cm = metrics["confusion_matrix"]
        for key in ("tn", "fp", "fn", "tp"):
            assert cm[key] >= 0, f"Confusion matrix cell {key} is negative: {cm[key]}"

    def test_confusion_matrix_totals_match_dataset(self, metrics):
        cm = metrics["confusion_matrix"]
        total = cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"]
        assert total == metrics["total_rows"], (
            f"Confusion matrix total ({total}) ≠ total_rows ({metrics['total_rows']})"
        )

    def test_feature_importance_top15(self, metrics):
        assert 1 <= len(metrics["feature_importance"]) <= 15

    def test_feature_importance_sorted_descending(self, metrics):
        scores = [f["importance"] for f in metrics["feature_importance"]]
        assert scores == sorted(scores, reverse=True), (
            "Feature importance must be sorted descending"
        )

    def test_feature_importance_normalised(self, metrics):
        """Individual importances are normalised fractions, each in (0, 1)."""
        for f in metrics["feature_importance"]:
            assert 0.0 < f["importance"] <= 1.0, (
                f"Importance {f['importance']} out of (0, 1] for feature {f['name']}"
            )

    def test_ioh_rate_plausible(self, metrics):
        assert 0.05 < metrics["ioh_rate"] < 0.5, (
            f"IOH rate {metrics['ioh_rate']} seems wrong — "
            "expected roughly 10-15% for surgical patients"
        )
