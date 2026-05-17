import os
import pickle
import numpy as np
import pandas as pd
import shap
import logging
from sklearn.metrics import roc_curve, auc, confusion_matrix, precision_recall_fscore_support

class PredictionEngine:
    # Candidate column names for the IOH label, in priority order
    _IOH_CANDIDATES = ('IOH', 'ioh', 'ioh_label_1m', 'ioh_label')

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.model_path = os.path.join(base_dir, 'models', 'ioh_model.pkl')
        self.scaler_path = os.path.join(base_dir, 'models', 'ioh_scaler.pkl')
        self.features_path = os.path.join(base_dir, 'models', 'feature_cols.pkl')
        self.data_path = os.path.join(base_dir, 'data', 'test_sample.csv')
        
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self.df = pd.DataFrame()
        
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
            else:
                logging.warning(f"Model file not found at {self.model_path}")
                
            if os.path.exists(self.scaler_path):
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            else:
                logging.warning(f"Scaler file not found at {self.scaler_path}")
                
            if os.path.exists(self.features_path):
                with open(self.features_path, 'rb') as f:
                    self.feature_cols = pickle.load(f)
            else:
                logging.warning(f"Feature cols file not found at {self.features_path}")
                
            if os.path.exists(self.data_path):
                self.df = pd.read_csv(self.data_path)
            else:
                logging.warning(f"Data file not found at {self.data_path}")
                
            logging.info("PredictionEngine initialized successfully.")
        except FileNotFoundError as e:
            logging.error(f"FileNotFoundError during initialization: {e}")
        except Exception as e:
            logging.error(f"Error during initialization: {e}")

    def predict(self, vital_signs_dict):
        if not self.model or not self.scaler or not self.feature_cols:
            return 0.0, "low", "Models not correctly loaded."
            
        try:
            input_data = [vital_signs_dict[col] for col in self.feature_cols]
            X = np.array(input_data).reshape(1, -1)
            X_scaled = self.scaler.transform(X)
            
            if hasattr(self.model, "predict_proba"):
                risk_score = float(self.model.predict_proba(X_scaled)[0, 1])
            else:
                risk_score = float(self.model.predict(X_scaled)[0])
                
            if risk_score > 0.6:
                alert_level = "high"
                alert_message = "High risk of IOH detected. Immediate attention recommended."
            elif risk_score >= 0.4:
                alert_level = "medium"
                alert_message = "Medium risk of IOH. Monitor closely."
            else:
                alert_level = "low"
                alert_message = "Patient is stable."
                
            return risk_score, alert_level, alert_message
        except Exception as e:
            logging.error(f"Prediction error: {e}")
            return 0.0, "low", f"Prediction error: {str(e)}"

    def explain(self, vital_signs_dict):
        if not self.model or not self.scaler or not self.feature_cols:
            return []
            
        try:
            input_data = [vital_signs_dict[col] for col in self.feature_cols]
            X = np.array(input_data).reshape(1, -1)
            X_scaled = self.scaler.transform(X)
            
            explainer = shap.LinearExplainer(self.model, shap.maskers.Independent(X_scaled))
            shap_values = explainer.shap_values(X_scaled)
            
            if isinstance(shap_values, list): 
                vals = shap_values[1][0]
            else:
                vals = shap_values[0]
                
            features_impact = []
            for i, col in enumerate(self.feature_cols):
                features_impact.append({
                    "name": col,
                    "value": float(vital_signs_dict[col]),
                    "impact": float(vals[i])
                })
                
            features_impact.sort(key=lambda x: abs(x["impact"]), reverse=True)
            return features_impact[:10]
        except Exception as e:
            logging.error(f"Explanation error: {e}")
            return []

    def get_patient_data(self, case_id):
        if self.df.empty:
            return []
        
        try:
            case_data = self.df[self.df['case_id'] == case_id]
            return case_data.to_dict(orient='records')
        except Exception as e:
            logging.error(f"Error fetching patient data: {e}")
            return []

    def get_analytics(self):
        if self.df.empty:
            return {
                "total_cases": 0, "total_rows": 0, "overall_ioh_rate": 0.0,
                "per_case": [], "map_distribution": {"bins": [], "counts": []},
                "risk_distribution": {"bins": [], "counts": []}
            }
            
        try:
            total_rows = len(self.df)
            case_col = 'case_id' if 'case_id' in self.df.columns else self.df.columns[0]
            total_cases = int(self.df[case_col].nunique())
            
            ioh_col = next((c for c in self._IOH_CANDIDATES if c in self.df.columns), None)
            overall_ioh_rate = float(self.df[ioh_col].mean()) if ioh_col else 0.0
            
            if self.model and self.scaler and self.feature_cols and all(col in self.df.columns for col in self.feature_cols):
                X_all = self.df[self.feature_cols]
                X_all_scaled = self.scaler.transform(X_all)
                if hasattr(self.model, "predict_proba"):
                    self.df['risk_score'] = self.model.predict_proba(X_all_scaled)[:, 1]
                else:
                    self.df['risk_score'] = self.model.predict(X_all_scaled)
            else:
                self.df['risk_score'] = 0.0
                
            per_case = []
            if case_col in self.df.columns:
                for cid, group in self.df.groupby(case_col):
                    per_case.append({
                        "case_id": int(cid),
                        "row_count": len(group),
                        "ioh_rate": float(group[ioh_col].mean()) if ioh_col else 0.0,
                        "avg_risk": float(group['risk_score'].mean()),
                        "max_risk": float(group['risk_score'].max()),
                        "duration_minutes": len(group)
                    })
                    
            map_col = 'MAP_current' if 'MAP_current' in self.df.columns else None
            if map_col:
                map_counts, map_bins = np.histogram(self.df[map_col].dropna(), bins=20)
                map_distribution = {"bins": map_bins.tolist(), "counts": map_counts.tolist()}
            else:
                map_distribution = {"bins": [], "counts": []}
                
            risk_counts, risk_bins = np.histogram(self.df['risk_score'].dropna(), bins=20)
            risk_distribution = {"bins": risk_bins.tolist(), "counts": risk_counts.tolist()}
            
            return {
                "total_cases": total_cases,
                "total_rows": total_rows,
                "overall_ioh_rate": overall_ioh_rate,
                "per_case": per_case,
                "map_distribution": map_distribution,
                "risk_distribution": risk_distribution
            }
        except Exception as e:
            logging.error(f"Error computing analytics: {e}")
            return {
                "total_cases": 0, "total_rows": 0, "overall_ioh_rate": 0.0,
                "per_case": [], "map_distribution": {"bins": [], "counts": []},
                "risk_distribution": {"bins": [], "counts": []}
            }

    def get_model_metrics(self):
        """Compute real model evaluation metrics from the test dataset."""
        if self.df.empty or not self.model or not self.scaler or not self.feature_cols:
            return None

        try:
            ioh_col = next((c for c in self._IOH_CANDIDATES if c in self.df.columns), None)
            if not ioh_col or not all(col in self.df.columns for col in self.feature_cols):
                logging.warning("get_model_metrics: missing IOH label or feature columns in dataset")
                return None

            X = self.df[self.feature_cols].values
            y_true = self.df[ioh_col].astype(int).values

            X_scaled = self.scaler.transform(X)
            y_prob = self.model.predict_proba(X_scaled)[:, 1]

            # --- ROC Curve (subsample to 100 points for JSON size) ---
            fpr_arr, tpr_arr, roc_thresholds = roc_curve(y_true, y_prob)
            auc_roc = float(auc(fpr_arr, tpr_arr))

            # Downsample to ~100 evenly-spaced points
            idx = np.round(np.linspace(0, len(fpr_arr) - 1, 100)).astype(int)
            roc_data = [
                {"fpr": round(float(fpr_arr[i]) * 100, 2), "tpr": round(float(tpr_arr[i]) * 100, 2)}
                for i in idx
            ]

            # --- Threshold Sensitivity (precision / recall / f1 at each threshold step) ---
            thresholds = np.arange(0.05, 0.96, 0.05)
            sensitivity_data = []
            for t in thresholds:
                y_pred_t = (y_prob >= t).astype(int)
                p, r, f1, _ = precision_recall_fscore_support(
                    y_true, y_pred_t, average='binary', zero_division=0
                )
                sensitivity_data.append({
                    "threshold": round(float(t), 2),
                    "precision": round(float(p), 4),
                    "recall": round(float(r), 4),
                    "f1": round(float(f1), 4),
                })

            # --- Confusion matrix at default threshold = 0.5 ---
            def conf_at(t):
                y_pred = (y_prob >= t).astype(int)
                cm = confusion_matrix(y_true, y_pred)
                tn, fp, fn, tp = cm.ravel()
                p, r, f1, _ = precision_recall_fscore_support(
                    y_true, y_pred, average='binary', zero_division=0
                )
                return {
                    "tn": int(tn), "fp": int(fp),
                    "fn": int(fn), "tp": int(tp),
                    "precision": round(float(p), 4),
                    "recall": round(float(r), 4),
                    "f1": round(float(f1), 4),
                }

            default_conf = conf_at(0.5)

            # --- Feature Importance from model coefficients ---
            coefs = np.abs(self.model.coef_[0])
            coef_sum = coefs.sum()
            feature_importance = sorted(
                [
                    {"name": col, "importance": round(float(coefs[i] / coef_sum), 4)}
                    for i, col in enumerate(self.feature_cols)
                ],
                key=lambda x: x["importance"],
                reverse=True,
            )[:15]

            return {
                "auc_roc": round(auc_roc, 4),
                "roc_curve": roc_data,
                "default_threshold": 0.5,
                "confusion_matrix": default_conf,
                "sensitivity": sensitivity_data,
                "feature_importance": feature_importance,
                "total_rows": len(y_true),
                "ioh_rate": round(float(y_true.mean()), 4),
            }

        except Exception as e:
            logging.error(f"Error computing model metrics: {e}")
            return None

