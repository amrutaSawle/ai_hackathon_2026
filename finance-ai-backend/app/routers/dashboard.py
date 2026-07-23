from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
def summary():
    """Prototype dashboard data; can be connected to persisted fraud events later."""
    return {
        "protectionScore": 96,
        "todayTransactions": 24,
        "blocked": 5,
        "safe": 19,
        "fraudDistribution": [
            {"name": "High Risk", "value": 25, "color": "#E53935"},
            {"name": "Medium Risk", "value": 45, "color": "#FB8C00"},
            {"name": "Low Risk", "value": 30, "color": "#43A047"},
        ],
        "weeklyTrend": [3, 5, 7, 9, 7, 5, 3],
        "countries": ["Germany", "France", "United Kingdom", "Italy", "Spain"],
        "recentAlerts": [
            {"title": "High Risk Payment", "status": "Blocked", "icon": "🛑", "color": "#E53935"},
            {"title": "Voice Scam", "status": "Warning", "icon": "🎙", "color": "#FB8C00"},
            {"title": "Safe Transfer", "status": "Completed", "icon": "✅", "color": "#43A047"},
        ],
    }
