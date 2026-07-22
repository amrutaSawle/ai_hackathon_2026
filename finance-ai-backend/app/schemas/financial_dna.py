from pydantic import BaseModel, Field


class FinancialDnaTrait(BaseModel):
    name: str
    score: int = Field(ge=0, le=100)
    reason: str
    icon: str


class FinancialDnaCategory(BaseModel):
    name: str
    amount: float
    percentage: float = Field(ge=0, le=100)
    icon: str


class FinancialDnaEvidence(BaseModel):
    label: str
    value: str
    helper: str
    icon: str


class FinancialDnaJourneyItem(BaseModel):
    period: str
    personality: str


class FinancialDnaComparison(BaseModel):
    label: str
    user_score: float
    average_score: float


class FinancialDnaCoach(BaseModel):
    message: str
    recommended_card: str
    recommended_card_id: int | None = None
    yearly_benefit: float
    reward_points: int


class FinancialDnaPrediction(BaseModel):
    title: str
    amount: float
    reward_points: int
    confidence: int = Field(ge=0, le=100)


class FinancialDnaResponse(BaseModel):
    primary_personality: str
    personality_score: int
    confidence: int

    transactions_analysed: int
    total_spend: float
    updated_at: str
    summary: str

    traits: list[FinancialDnaTrait]
    top_categories: list[FinancialDnaCategory]
    evidence: list[FinancialDnaEvidence]
    journey: list[FinancialDnaJourneyItem]
    comparison: list[FinancialDnaComparison]

    coach: FinancialDnaCoach
    prediction: FinancialDnaPrediction