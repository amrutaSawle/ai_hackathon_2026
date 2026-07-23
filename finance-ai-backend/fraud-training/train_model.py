import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

print("======================================")
print("Loading Dataset...")
print("======================================")

df = pd.read_csv("data/creditcard.csv")

print("Dataset Shape:", df.shape)

# -------------------------
# Remove IDs
# -------------------------

df = df.drop(columns=[
    "transaction_id",
    "customer_id"
])

# -------------------------
# Features & Target
# -------------------------

X = df.drop("is_fraud", axis=1)

y = df["is_fraud"]

# -------------------------
# Categorical Columns
# -------------------------

categorical_features = [
    "transaction_type",
    "transaction_time",
    "transaction_location",
    "device_type"
]

numeric_features = [
    "transaction_amount",
    "previous_transactions_count",
    "new_beneficiary",
    "iban_valid",
    "weekend",
    "night_transaction"
]

# -------------------------
# Preprocessing
# -------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features
        ),
        (
            "num",
            "passthrough",
            numeric_features
        )
    ]
)

# -------------------------
# AI Model
# -------------------------

model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=200,
            random_state=42
        ))
    ]
)

# -------------------------
# Train/Test Split
# -------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining AI Model...")

model.fit(X_train, y_train)

print("Training Completed.")

# -------------------------
# Prediction
# -------------------------

pred = model.predict(X_test)

print("\nAccuracy")

print(accuracy_score(y_test, pred))

print("\nClassification Report")

print(classification_report(y_test, pred))

print("\nConfusion Matrix")

print(confusion_matrix(y_test, pred))

# -------------------------
# Save Model
# -------------------------

joblib.dump(model, "models/fraud_model.pkl")

print("\nModel Saved Successfully")