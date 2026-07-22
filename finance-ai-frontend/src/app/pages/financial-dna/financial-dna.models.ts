export interface FinancialDnaTrait {
  name: string;
  score: number;
  reason: string;
  icon: string;
}

export interface FinancialDnaCategory {
  name: string;
  amount: number;
  percentage: number;
  icon: string;
}

export interface FinancialDnaEvidence {
  label: string;
  value: string;
  helper: string;
  icon: string;
}

export interface FinancialDnaJourneyItem {
  period: string;
  personality: string;
}

export interface FinancialDnaComparison {
  label: string;
  userScore: number;
  averageScore: number;
}

export interface FinancialDnaCoach {
  message: string;
  recommendedCard: string;
  yearlyBenefit: number;
  rewardPoints: number;
}

export interface FinancialDnaPrediction {
  title: string;
  amount: number;
  rewardPoints: number;
  confidence: number;
}

export interface FinancialDnaViewModel {
  primaryPersonality: string;
  personalityScore: number;
  confidence: number;
  transactionsAnalysed: number;
  totalSpend: number;
  updatedAt: string;
  summary: string;
  traits: FinancialDnaTrait[];
  categories: FinancialDnaCategory[];
  evidence: FinancialDnaEvidence[];
  journey: FinancialDnaJourneyItem[];
  comparison: FinancialDnaComparison[];
  coach: FinancialDnaCoach;
  prediction: FinancialDnaPrediction;
}
