import re


def normalize_merchant_name(text: str) -> str:
    """
    Convert raw transaction description
    into clean merchant name.
    """

    if not text:
        return ""

    text = text.lower()

    text = re.sub(r'upi/', '', text)

    text = re.sub(r'imps/', '', text)

    text = re.sub(r'neft/', '', text)

    text = re.sub(r'rtgs/', '', text)

    text = re.sub(r'paytm', '', text)

    text = re.sub(r'googlepay', '', text)

    text = re.sub(r'phonepe', '', text)

    text = re.sub(r'[^a-z ]', ' ', text)

    text = re.sub(r'\s+', ' ', text)

    return text.strip()