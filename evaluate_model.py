import numpy as np
from sklearn.metrics import (
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    r2_score,
    mean_absolute_error,
    mean_squared_error
)
from backend.ml_risk_model import PolarMLRiskModel


print("ML MODEL EVALUATION & VALIDATION")


# Model load
ml = PolarMLRiskModel()

# Generate unseen test dataset (500 samples)
X_test, y_test_continuous = ml._generate_polar_dataset(n_samples=500)

# Continuous Predictions (Regression)
preds_continuous = ml.model.predict(X_test)

# 1. Regression Metrics
r2 = r2_score(y_test_continuous, preds_continuous)
mae = mean_absolute_error(y_test_continuous, preds_continuous)
rmse = np.sqrt(mean_squared_error(y_test_continuous, preds_continuous))

print("\n[1] REGRESSION METRICS (Continuous Risk Prediction 0.0 - 1.0):")
print(f"  • R² Score (Variance Explained) : {r2 * 100:.2f}%")
print(f"  • Mean Absolute Error (MAE)     : {mae:.4f}")
print(f"  • Root Mean Squared Error (RMSE): {rmse:.4f}")

# 2. Classification Metrics (Risk Severity Binning: Safe < 0.40, Medium 0.40-0.70, Severe > 0.70)
def to_severity_class(vals):
    classes = []
    for v in vals:
        if v < 0.40:
            classes.append("Safe Water")
        elif v < 0.70:
            classes.append("Moderate Ice")
        else:
            classes.append("Severe Pack Ice")
    return classes

y_test_classes = to_severity_class(y_test_continuous)
preds_classes = to_severity_class(preds_continuous)

f1 = f1_score(y_test_classes, preds_classes, average="weighted")
precision = precision_score(y_test_classes, preds_classes, average="weighted")
recall = recall_score(y_test_classes, preds_classes, average="weighted")

print("\n[2] CLASSIFICATION METRICS (Hazard Severity Bins):")
print(f"  • Weighted F1-Score  : {f1 * 100:.2f}%")
print(f"  • Weighted Precision : {precision * 100:.2f}%")
print(f"  • Weighted Recall    : {recall * 100:.2f}%")

print("\n[3] DETAILED CLASSIFICATION REPORT:")
print(classification_report(y_test_classes, preds_classes, target_names=["Moderate Ice", "Safe Water", "Severe Pack Ice"]))
print("="*60)