# Fraud model training bundle

This directory preserves the developer-provided fraud-training work without
adding heavy data-science packages to the production API image.

## Train a model locally

```sh
cd finance-ai-backend/fraud-training
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p models
python train_model.py
```

The original script writes `models/fraud_model.pkl`. Keep this model artifact
out of Git unless your repository policy explicitly allows model binaries.
The deployed API currently uses the verified rules-based scorer. A later change
can load this artifact as an optional enhancement without changing the browser
API.

`data/creditcard.csv` and `data/europe_bank_dataset.csv` are the original
developer-provided datasets. Use `generate_dataset.py` only when you want to
replace the generated credit-card training data.
