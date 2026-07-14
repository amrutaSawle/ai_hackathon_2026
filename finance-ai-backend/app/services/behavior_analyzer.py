def identify_persona(spend_summary):
    category_totals = spend_summary["category_totals"]
    total_spend = spend_summary["total_spend"]

    if total_spend == 0:
        return ["No spending data"]

    personas = []

    def pct(category):
        return (category_totals.get(category, 0) / total_spend) * 100

    travel_pct = pct("Flights") + pct("Hotels") + pct("Travel")
    shopping_pct = pct("Online Shopping") + pct("Shopping")
    grocery_pct = pct("Grocery")
    utility_pct = pct("Utility Bills")
    dining_pct = pct("Dining")

    if travel_pct >= 30:
        personas.append("Frequent Traveller")

    if shopping_pct >= 25:
        personas.append("Online Shopper")

    if dining_pct >= 15:
        personas.append("Dining Focused Customer")

    if grocery_pct + utility_pct >= 25:
        personas.append("Family / Household Spender")

    if not personas:
        personas.append("Balanced Spender")

    return personas