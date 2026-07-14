from collections import defaultdict

def analyze_spending(transactions):
    category_totals = defaultdict(float)

    for txn in transactions:
        category_totals[txn.category] += txn.amount

    total_spend = sum(category_totals.values())

    top_category = None
    if category_totals:
        top_category = max(category_totals, key=category_totals.get)

    return {
        "total_spend": total_spend,
        "category_totals": dict(category_totals),
        "top_category": top_category
    }