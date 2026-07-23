import os
import joblib
import shap

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "models",
    "fraud_model.pkl"
)

model = joblib.load(MODEL_PATH)

# Get the RandomForest from the pipeline
classifier = model.named_steps["classifier"]

explainer = shap.TreeExplainer(classifier)