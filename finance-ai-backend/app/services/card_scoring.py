def get_weight(weights, factor, default=0):
    return weights.get(factor, default)


def score_card(card, rules, spend_summary, personas, weights):
    category_totals = spend_summary["category_totals"]

    estimated_reward = 0
    matched_categories = 0

    for rule in rules:
        spend = category_totals.get(rule.category, 0)

        if spend > 0:
            matched_categories += 1

        reward = spend * rule.reward_percent / 100

        if rule.monthly_cap:
            reward = min(reward, rule.monthly_cap)

        estimated_reward += reward

    reward_score = min(estimated_reward / 100, get_weight(weights, "reward"))
    category_score = min(matched_categories * 10, get_weight(weights, "category_match"))
    lounge_score = get_weight(weights, "lounge") if card.lounge_access else 0
    forex_score = max(0, get_weight(weights, "forex") - card.forex_markup)
    fee_penalty = min(card.annual_fee / 1000, get_weight(weights, "annual_fee"))

    lifestyle_score = 0
    if "Frequent Traveller" in personas and "travel" in card.best_for.lower():
        lifestyle_score = get_weight(weights, "lifestyle")
    elif "Online Shopper" in personas and "shopping" in card.best_for.lower():
        lifestyle_score = get_weight(weights, "lifestyle")

    total_score = (
        reward_score
        + category_score
        + lounge_score
        + forex_score
        + lifestyle_score
        - fee_penalty
    )

    net_value = estimated_reward - card.annual_fee
    confidence = min(95, 60 + total_score / 2)

    return {
        "card_name": card.card_name,
        "annual_fee": card.annual_fee,
        "reward_type": card.reward_type,
        "lounge_access": card.lounge_access,
        "forex_markup": card.forex_markup,
        "best_for": card.best_for,
        "estimated_reward": round(estimated_reward, 2),
        "net_value_after_fee": round(net_value, 2),
        "score": round(total_score, 2),
        "confidence": round(confidence, 2),
        "score_breakdown": {
            "reward_score": round(reward_score, 2),
            "category_match_score": round(category_score, 2),
            "lounge_score": round(lounge_score, 2),
            "forex_score": round(forex_score, 2),
            "lifestyle_score": round(lifestyle_score, 2),
            "annual_fee_penalty": round(fee_penalty, 2)
        }
    }