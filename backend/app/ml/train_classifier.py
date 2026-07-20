"""
CertiGuard AI - Certificate Classifier Training
Model   : GBM + Random Forest ensemble (soft voting)
Features: 17 calibrated features from OCR, forensics, and rule engine
Data    : Realistic synthetic data (2000 genuine + 2000 fake)

Run:
    cd backend
    python -m app.ml.train_classifier
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Tuple

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_score, recall_score, f1_score, roc_auc_score,
)

from app.services.feature_engineering import FEATURE_COLUMNS

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))
MODEL_PATH = os.path.join(MODEL_DIR, "certificate_classifier.pkl")


# ------------------------------------------------------------------ #
#  Synthetic data generators                                           #
# ------------------------------------------------------------------ #

def _genuine(rng: np.random.Generator) -> dict:
    """
    Realistic genuine certificate.
    - Moderate OCR confidence (not always perfect on scanned docs)
    - Some missing fields (OCR misses ~30% of fields on real certs)
    - Low-moderate ELA / tampering (JPEG re-compression artefacts)
    - No DB match is normal (small seed DB is not a fake signal)
    """
    is_digital = rng.random() < 0.25  # 25% are high-quality digital certs
    return {
        "ocr_confidence":             float(np.clip(rng.normal(0.80 if is_digital else 0.72, 0.08), 0.45, 0.97)),
        "structural_completeness":    float(np.clip(rng.normal(0.70 if is_digital else 0.55, 0.18), 0.25, 1.0)),
        "ocr_word_count":             float(np.clip(rng.normal(0.45, 0.18), 0.10, 0.90)),
        "id_valid":                   int(rng.choice([0, 1], p=[0.30, 0.70])),
        "issue_date_valid":           int(rng.choice([0, 1], p=[0.20, 0.80])),
        "issuer_match_score":         float(np.clip(rng.normal(0.45, 0.28), 0.0, 1.0)),
        "layout_confidence":          float(np.clip(rng.normal(0.74, 0.12), 0.30, 1.0)),
        "tampering_score":            float(np.clip(rng.normal(0.12, 0.08), 0.0, 0.42)),
        "ela_score":                  float(np.clip(rng.normal(0.15, 0.08), 0.0, 0.40)),
        "copy_move_score":            float(np.clip(rng.normal(0.05, 0.05), 0.0, 0.25)),
        "logo_region_consistency":    float(np.clip(rng.normal(0.78, 0.10), 0.40, 1.0)),
        "compression_artifact_score": float(np.clip(rng.normal(0.28, 0.10), 0.05, 0.55)),
        "edge_mismatch_score":        float(np.clip(rng.normal(0.18, 0.08), 0.0, 0.42)),
        "color_consistency_score":    float(np.clip(rng.normal(0.12, 0.07), 0.0, 0.35)),
        "noise_score":                float(np.clip(rng.normal(0.15, 0.07), 0.0, 0.38)),
        "blur_score":                 float(np.clip(rng.normal(0.22, 0.12), 0.0, 0.60)),
        "verification_match":         int(rng.choice([0, 1], p=[0.78, 0.22])),
    }


def _fake(rng: np.random.Generator) -> dict:
    """
    Forged certificate - three forgery subtypes with different forensic profiles.
    """
    forgery_type = rng.choice(["photoshop", "printed_scan", "digital_edit"], p=[0.45, 0.30, 0.25])

    if forgery_type == "photoshop":
        ela        = float(np.clip(rng.normal(0.72, 0.12), 0.45, 1.0))
        copy_move  = float(np.clip(rng.normal(0.55, 0.18), 0.20, 1.0))
        tampering  = float(np.clip(rng.normal(0.75, 0.12), 0.50, 1.0))
    elif forgery_type == "printed_scan":
        ela        = float(np.clip(rng.normal(0.45, 0.12), 0.22, 0.80))
        copy_move  = float(np.clip(rng.normal(0.30, 0.15), 0.05, 0.70))
        tampering  = float(np.clip(rng.normal(0.52, 0.12), 0.30, 0.85))
    else:  # digital_edit
        ela        = float(np.clip(rng.normal(0.60, 0.15), 0.30, 0.95))
        copy_move  = float(np.clip(rng.normal(0.65, 0.15), 0.30, 1.0))
        tampering  = float(np.clip(rng.normal(0.68, 0.12), 0.40, 1.0))

    return {
        "ocr_confidence":             float(np.clip(rng.normal(0.52, 0.15), 0.10, 0.82)),
        "structural_completeness":    float(np.clip(rng.normal(0.30, 0.18), 0.0,  0.75)),
        "ocr_word_count":             float(np.clip(rng.normal(0.22, 0.15), 0.0,  0.65)),
        "id_valid":                   int(rng.choice([0, 1], p=[0.72, 0.28])),
        "issue_date_valid":           int(rng.choice([0, 1], p=[0.55, 0.45])),
        "issuer_match_score":         float(np.clip(rng.normal(0.18, 0.14), 0.0,  0.55)),
        "layout_confidence":          float(np.clip(rng.normal(0.28, 0.14), 0.0,  0.58)),
        "tampering_score":            tampering,
        "ela_score":                  ela,
        "copy_move_score":            copy_move,
        "logo_region_consistency":    float(np.clip(rng.normal(0.28, 0.14), 0.0,  0.62)),
        "compression_artifact_score": float(np.clip(rng.normal(0.72, 0.14), 0.40, 1.0)),
        "edge_mismatch_score":        float(np.clip(rng.normal(0.68, 0.14), 0.35, 1.0)),
        "color_consistency_score":    float(np.clip(rng.normal(0.62, 0.15), 0.25, 1.0)),
        "noise_score":                float(np.clip(rng.normal(0.58, 0.15), 0.20, 1.0)),
        "blur_score":                 float(np.clip(rng.normal(0.45, 0.18), 0.05, 0.90)),
        "verification_match":         int(rng.choice([0, 1], p=[0.92, 0.08])),
    }


def generate_dataset(n_per_class: int = 2000, seed: int = 42) -> Tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(seed)
    samples, labels = [], []
    for _ in range(n_per_class):
        samples.append(_genuine(rng))
        labels.append(0)
        samples.append(_fake(rng))
        labels.append(1)
    return pd.DataFrame(samples, columns=FEATURE_COLUMNS), np.array(labels)


# ------------------------------------------------------------------ #
#  Model definition                                                    #
# ------------------------------------------------------------------ #

def build_model() -> Pipeline:
    gbm = GradientBoostingClassifier(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=4,
        min_samples_leaf=8,
        subsample=0.8,
        max_features="sqrt",
        random_state=42,
    )
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=6,
        max_features="sqrt",
        class_weight={0: 1.2, 1: 1.0},  # favour genuine to reduce false positives
        random_state=42,
    )
    ensemble = VotingClassifier(
        estimators=[("gbm", gbm), ("rf", rf)],
        voting="soft",
        weights=[0.6, 0.4],
    )
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", ensemble),
    ])


# ------------------------------------------------------------------ #
#  Evaluation                                                          #
# ------------------------------------------------------------------ #

def evaluate(model: Pipeline, X_test: pd.DataFrame, y_test: np.ndarray) -> None:
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print("Precision (fake):  %.4f" % precision_score(y_test, y_pred))
    print("Recall    (fake):  %.4f" % recall_score(y_test, y_pred))
    print("F1-Score  (fake):  %.4f" % f1_score(y_test, y_pred))
    print("ROC-AUC:           %.4f" % roc_auc_score(y_test, y_prob))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Genuine", "Fake"]))

    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix (rows=actual, cols=predicted):")
    print("  Genuine -> Genuine : %d  (correct)" % cm[0][0])
    print("  Genuine -> Fake    : %d  << FALSE POSITIVES" % cm[0][1])
    print("  Fake    -> Genuine : %d  << FALSE NEGATIVES" % cm[1][0])
    print("  Fake    -> Fake    : %d  (correct)" % cm[1][1])
    print("=" * 60)

    try:
        rf_model = model.named_steps["clf"].estimators_[1]
        importances = rf_model.feature_importances_
        feat_imp = sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: x[1], reverse=True)
        print("\nTop Feature Importances (Random Forest):")
        for feat, imp in feat_imp[:10]:
            bar = "|" * int(imp * 100)
            print("  %-35s %.4f  %s" % (feat, imp, bar))
    except Exception:
        pass


# ------------------------------------------------------------------ #
#  Training entry point                                                #
# ------------------------------------------------------------------ #

def run_training():
    print("Generating realistic synthetic dataset (2000 genuine + 2000 fake)...")
    X, y = generate_dataset(n_per_class=2000)

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=42
    )
    print("Train: %d  Val: %d  Test: %d" % (len(X_train), len(X_val), len(X_test)))

    model = build_model()
    print("\nRunning 5-fold cross-validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1", n_jobs=-1)
    print("CV F1 scores: %s  mean=%.4f" % (cv_scores.round(4), cv_scores.mean()))

    print("\nTraining final model...")
    model.fit(X_train, y_train)

    evaluate(model, X_test, y_test)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print("\nModel saved: %s" % MODEL_PATH)


if __name__ == "__main__":
    run_training()
