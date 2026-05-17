"""
FastAPI endpoint tests via TestClient.

Covers every route defined in main.py:
  GET  /health
  POST /predict
  POST /explain
  GET  /patient/{case_id}
  GET  /analytics
  GET  /model/metrics
  GET  /rag/suggestions
  GET  /history/{session_id}
  POST /rag/query  (offline — expects 503 when RAG pipeline is None)
"""
import pytest


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_status_200(self, test_client):
        res = test_client.get("/health")
        assert res.status_code == 200

    def test_body_schema(self, test_client):
        body = test_client.get("/health").json()
        assert "status" in body
        assert "model_loaded" in body
        assert "rag_ready" in body
        assert "total_cases" in body

    def test_model_is_loaded(self, test_client):
        body = test_client.get("/health").json()
        assert body["model_loaded"] is True

    def test_total_cases_positive(self, test_client):
        body = test_client.get("/health").json()
        assert body["total_cases"] > 0


# ---------------------------------------------------------------------------
# POST /predict
# ---------------------------------------------------------------------------

class TestPredictEndpoint:
    def test_status_200(self, test_client, healthy_vitals):
        res = test_client.post("/predict", json=healthy_vitals)
        assert res.status_code == 200

    def test_response_schema(self, test_client, healthy_vitals):
        body = test_client.post("/predict", json=healthy_vitals).json()
        assert "risk_score"   in body
        assert "risk_percent" in body
        assert "alert_level"  in body
        assert "alert_message" in body
        assert "timestamp"    in body

    def test_risk_score_range(self, test_client, healthy_vitals):
        body = test_client.post("/predict", json=healthy_vitals).json()
        assert 0.0 <= body["risk_score"] <= 1.0

    def test_risk_percent_is_score_times_100(self, test_client, healthy_vitals):
        body = test_client.post("/predict", json=healthy_vitals).json()
        assert abs(body["risk_percent"] - body["risk_score"] * 100) < 0.001

    def test_alert_level_valid(self, test_client, healthy_vitals):
        body = test_client.post("/predict", json=healthy_vitals).json()
        assert body["alert_level"] in ("low", "medium", "high")

    def test_missing_field_returns_422(self, test_client):
        """Pydantic validation should reject incomplete payloads."""
        res = test_client.post("/predict", json={"MAP_current": 90.0})
        assert res.status_code == 422

    def test_high_risk_returns_higher_score(self, test_client, healthy_vitals, high_risk_vitals):
        stable = test_client.post("/predict", json=healthy_vitals).json()["risk_score"]
        risky  = test_client.post("/predict", json=high_risk_vitals).json()["risk_score"]
        assert risky > stable


# ---------------------------------------------------------------------------
# POST /explain
# ---------------------------------------------------------------------------

class TestExplainEndpoint:
    def _payload(self, vitals):
        return {**vitals, "case_id": 1}

    def test_status_200(self, test_client, healthy_vitals):
        res = test_client.post("/explain", json=self._payload(healthy_vitals))
        assert res.status_code == 200

    def test_response_has_shap_values(self, test_client, healthy_vitals):
        body = test_client.post("/explain", json=self._payload(healthy_vitals)).json()
        assert "shap_values" in body
        assert "top_features" in body

    def test_top_features_is_list(self, test_client, healthy_vitals):
        body = test_client.post("/explain", json=self._payload(healthy_vitals)).json()
        assert isinstance(body["top_features"], list)
        assert len(body["top_features"]) >= 1

    def test_top_features_have_impact(self, test_client, healthy_vitals):
        body = test_client.post("/explain", json=self._payload(healthy_vitals)).json()
        for feat in body["top_features"]:
            assert "name" in feat
            assert "impact" in feat


# ---------------------------------------------------------------------------
# GET /patient/{case_id}
# ---------------------------------------------------------------------------

class TestPatientEndpoint:
    def test_valid_case_returns_list(self, test_client, engine):
        """Use the first real case_id from the loaded dataset."""
        first_case = int(engine.df["case_id"].iloc[0])
        res = test_client.get(f"/patient/{first_case}")
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body, list) and len(body) > 0

    def test_unknown_case_returns_404(self, test_client):
        res = test_client.get("/patient/999999")
        assert res.status_code == 404

    def test_patient_rows_have_map_column(self, test_client, engine):
        first_case = int(engine.df["case_id"].iloc[0])
        body = test_client.get(f"/patient/{first_case}").json()
        assert "MAP_current" in body[0]


# ---------------------------------------------------------------------------
# GET /analytics
# ---------------------------------------------------------------------------

class TestAnalyticsEndpoint:
    def test_status_200(self, test_client):
        res = test_client.get("/analytics")
        assert res.status_code == 200

    def test_required_keys(self, test_client):
        body = test_client.get("/analytics").json()
        for key in ("total_cases", "total_rows", "overall_ioh_rate", "per_case",
                    "map_distribution", "risk_distribution"):
            assert key in body, f"Missing key: {key}"

    def test_total_cases_matches_dataset(self, test_client, engine):
        body = test_client.get("/analytics").json()
        expected = int(engine.df["case_id"].nunique())
        assert body["total_cases"] == expected

    def test_per_case_has_correct_length(self, test_client, engine):
        body = test_client.get("/analytics").json()
        expected = int(engine.df["case_id"].nunique())
        assert len(body["per_case"]) == expected

    def test_ioh_rate_in_range(self, test_client):
        body = test_client.get("/analytics").json()
        assert 0.0 < body["overall_ioh_rate"] < 1.0


# ---------------------------------------------------------------------------
# GET /model/metrics
# ---------------------------------------------------------------------------

class TestModelMetricsEndpoint:
    def test_status_200(self, test_client):
        res = test_client.get("/model/metrics")
        assert res.status_code == 200

    def test_auc_roc_present(self, test_client):
        body = test_client.get("/model/metrics").json()
        assert "auc_roc" in body
        assert body["auc_roc"] > 0.5

    def test_roc_curve_100_points(self, test_client):
        body = test_client.get("/model/metrics").json()
        assert len(body["roc_curve"]) == 100

    def test_sensitivity_has_threshold_rows(self, test_client):
        body = test_client.get("/model/metrics").json()
        assert len(body["sensitivity"]) >= 10

    def test_feature_importance_not_empty(self, test_client):
        body = test_client.get("/model/metrics").json()
        assert len(body["feature_importance"]) >= 1


# ---------------------------------------------------------------------------
# GET /rag/suggestions
# ---------------------------------------------------------------------------

class TestRagSuggestions:
    def test_status_200(self, test_client):
        res = test_client.get("/rag/suggestions")
        assert res.status_code == 200

    def test_returns_list_of_strings(self, test_client):
        body = test_client.get("/rag/suggestions").json()
        assert isinstance(body, list)
        assert all(isinstance(s, str) for s in body)

    def test_returns_at_least_four_suggestions(self, test_client):
        body = test_client.get("/rag/suggestions").json()
        assert len(body) >= 4


# ---------------------------------------------------------------------------
# POST /rag/query — offline (no OpenAI key)
# ---------------------------------------------------------------------------

class TestRagQueryOffline:
    def test_returns_503_when_rag_not_initialised(self, test_client):
        """
        In test mode there is no OpenAI key, so rag_pipeline is None.
        The endpoint must return 503, not 500 or crash.
        """
        res = test_client.post("/rag/query", json={"question": "What is IOH?"})
        assert res.status_code == 503
        assert "detail" in res.json()


# ---------------------------------------------------------------------------
# GET /history/{session_id}
# ---------------------------------------------------------------------------

class TestHistoryEndpoint:
    def test_returns_list(self, test_client):
        """Without a DB, endpoint must return an empty list gracefully."""
        res = test_client.get("/history/test-session-abc")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
