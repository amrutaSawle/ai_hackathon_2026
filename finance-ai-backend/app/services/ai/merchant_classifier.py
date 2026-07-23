import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.models.merchant_category import MerchantCategory
from app.models.spending_category import SpendingCategory
from app.services.ai.merchant_normalizer import normalize_merchant_name


@dataclass
class ClassificationResult:
    merchant_name: str
    normalized_name: str
    category_id: int
    category_name: str
    category_code: str
    parent_category: str | None
    confidence: float
    source: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "merchant_name": self.merchant_name,
            "normalized_name": self.normalized_name,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "category_code": self.category_code,
            "parent_category": self.parent_category,
            "confidence": round(self.confidence, 4),
            "source": self.source,
            "reason": self.reason,
        }


def _build_result(
    merchant: MerchantCategory,
    confidence: float,
    source: str,
    reason: str,
) -> ClassificationResult:
    category = merchant.category
    parent_name = category.parent.name if category.parent else None

    return ClassificationResult(
        merchant_name=merchant.merchant_name,
        normalized_name=merchant.normalized_name,
        category_id=category.id,
        category_name=category.name,
        category_code=category.code,
        parent_category=parent_name,
        confidence=confidence,
        source=source,
        reason=reason,
    )


def _find_exact_match(
    db: Session,
    normalized_name: str,
) -> MerchantCategory | None:
    return (
        db.query(MerchantCategory)
        .filter(
            MerchantCategory.normalized_name == normalized_name
        )
        .first()
    )


def _find_contained_match(
    db: Session,
    normalized_name: str,
) -> MerchantCategory | None:
    merchants = db.query(MerchantCategory).all()

    matches = [
        merchant
        for merchant in merchants
        if merchant.normalized_name in normalized_name
        or normalized_name in merchant.normalized_name
    ]

    if not matches:
        return None

    # Prefer the longest matched merchant name.
    return max(matches, key=lambda merchant: len(merchant.normalized_name))


def _find_fuzzy_match(
    db: Session,
    normalized_name: str,
    minimum_score: int = 86,
) -> tuple[MerchantCategory | None, float]:
    merchants = db.query(MerchantCategory).all()

    if not merchants:
        return None, 0.0

    choices = {
        merchant.id: merchant.normalized_name
        for merchant in merchants
    }

    match = process.extractOne(
        normalized_name,
        choices,
        scorer=fuzz.token_set_ratio,
    )

    if not match:
        return None, 0.0

    _, score, merchant_id = match

    if score < minimum_score:
        return None, score / 100

    merchant = next(
        (
            merchant
            for merchant in merchants
            if merchant.id == merchant_id
        ),
        None,
    )

    return merchant, score / 100


def _get_allowed_categories(
    db: Session,
) -> list[SpendingCategory]:
    return (
        db.query(SpendingCategory)
        .filter(SpendingCategory.is_active.is_(True))
        .all()
    )


def _classify_with_ai(
    db: Session,
    raw_description: str,
    normalized_name: str,
    mcc: str | None,
    payment_method: str | None,
    amount: float | None,
) -> dict[str, Any] | None:
    if not OPENAI_API_KEY:
        return None

    categories = _get_allowed_categories(db)

    category_catalogue = [
        {
            "code": category.code,
            "name": category.name,
            "parent": (
                category.parent.name
                if category.parent
                else None
            ),
        }
        for category in categories
    ]

    client = OpenAI(api_key=OPENAI_API_KEY)
    print("OpenAI Enabled:", bool(OPENAI_API_KEY))
    print("Model:", OPENAI_MODEL)
    input_data = {
        "raw_transaction_description": raw_description,
        "normalized_merchant": normalized_name,
        "mcc": mcc,
        "payment_method": payment_method,
        "amount": amount,
        "allowed_categories": category_catalogue,
    }

    instructions = """
You classify banking transactions.

Use only one category from allowed_categories.
Do not invent a category or category code.

Consider:
- merchant wording
- MCC when supplied
- payment method
- merchant industry
- transaction context

Return valid JSON with exactly these fields:

{
  "merchant_name": "clean display merchant name",
  "category_code": "one exact allowed category code",
  "confidence": 0.0,
  "reason": "short explanation"
}

Confidence must be between 0 and 1.

Use a lower confidence when the merchant description is ambiguous.
Do not include markdown.
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=instructions,
        input=json.dumps(input_data, default=str),
    )

    try:
        result = json.loads(response.output_text)
    except (json.JSONDecodeError, TypeError):
        return None

    category_code = str(result.get("category_code", "")).strip()

    allowed_codes = {
        category.code
        for category in categories
    }

    if category_code not in allowed_codes:
        return None

    confidence = float(result.get("confidence", 0.0))
    confidence = max(0.0, min(confidence, 1.0))

    return {
        "merchant_name": (
            str(result.get("merchant_name", "")).strip()
            or normalized_name.title()
        ),
        "category_code": category_code,
        "confidence": confidence,
        "reason": str(
            result.get(
                "reason",
                "AI classified the transaction.",
            )
        ).strip(),
    }


def classify_transaction(
    db: Session,
    raw_description: str,
    mcc: str | None = None,
    payment_method: str | None = None,
    amount: float | None = None,
    save_ai_result: bool = True,
) -> ClassificationResult:
    normalized_name = normalize_merchant_name(raw_description)

    if not normalized_name:
        other_category = (
            db.query(SpendingCategory)
            .filter(SpendingCategory.code == "other")
            .first()
        )

        if not other_category:
            raise ValueError("The 'other' spending category is missing.")

        return ClassificationResult(
            merchant_name="Unknown Merchant",
            normalized_name="unknown",
            category_id=other_category.id,
            category_name=other_category.name,
            category_code=other_category.code,
            parent_category=None,
            confidence=0.10,
            source="FALLBACK",
            reason="The transaction did not contain a usable merchant name.",
        )

    exact_match = _find_exact_match(db, normalized_name)

    if exact_match:
        return _build_result(
            merchant=exact_match,
            confidence=1.0,
            source="EXACT_MATCH",
            reason="The normalized merchant exactly matched the merchant master.",
        )

    contained_match = _find_contained_match(db, normalized_name)

    if contained_match:
        return _build_result(
            merchant=contained_match,
            confidence=0.96,
            source="CONTAINED_MATCH",
            reason=(
                f"The transaction description contained the known merchant "
                f"'{contained_match.merchant_name}'."
            ),
        )

    fuzzy_match, fuzzy_confidence = _find_fuzzy_match(
        db=db,
        normalized_name=normalized_name,
    )

    if fuzzy_match:
        return _build_result(
            merchant=fuzzy_match,
            confidence=fuzzy_confidence,
            source="FUZZY_MATCH",
            reason=(
                f"The merchant closely matched "
                f"'{fuzzy_match.merchant_name}'."
            ),
        )

    ai_result = _classify_with_ai(
        db=db,
        raw_description=raw_description,
        normalized_name=normalized_name,
        mcc=mcc,
        payment_method=payment_method,
        amount=amount,
    )

    if ai_result:
        category = (
            db.query(SpendingCategory)
            .filter(
                SpendingCategory.code
                == ai_result["category_code"]
            )
            .first()
        )

        if not category:
            raise ValueError("AI returned an unknown category.")

        if save_ai_result and ai_result["confidence"] >= 0.75:
            learned_merchant = MerchantCategory(
                merchant_name=ai_result["merchant_name"],
                normalized_name=normalized_name,
                category_id=category.id,
                mcc=mcc,
                source="AI",
                confidence=ai_result["confidence"],
            )

            db.add(learned_merchant)
            db.flush()

        return ClassificationResult(
            merchant_name=ai_result["merchant_name"],
            normalized_name=normalized_name,
            category_id=category.id,
            category_name=category.name,
            category_code=category.code,
            parent_category=(
                category.parent.name
                if category.parent
                else None
            ),
            confidence=ai_result["confidence"],
            source="AI",
            reason=ai_result["reason"],
        )

    other_category = (
        db.query(SpendingCategory)
        .filter(SpendingCategory.code == "other")
        .first()
    )

    if not other_category:
        raise ValueError("The 'other' spending category is missing.")

    return ClassificationResult(
        merchant_name=normalized_name.title(),
        normalized_name=normalized_name,
        category_id=other_category.id,
        category_name=other_category.name,
        category_code=other_category.code,
        parent_category=None,
        confidence=0.25,
        source="FALLBACK",
        reason=(
            "No reliable merchant match was found and AI classification "
            "was unavailable."
        ),
    )