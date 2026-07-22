import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface InsightSummary {
  total_spend: number;
  transaction_count: number;
  current_month_spend: number;
  previous_month_spend: number;
  projected_month_end_spend: number;
}

export interface SpendingInsight {
  id: string;
  type: string;
  title: string;
  message: string;

  priority:
    | 'LOW'
    | 'MEDIUM'
    | 'HIGH';

  severity:
    | 'INFO'
    | 'WARNING'
    | 'CRITICAL'
    | 'SUCCESS'
    | 'OPPORTUNITY';

  icon?: string;
  impact_amount?: number;
  confidence?: number;

  action?: {
    label: string;
    prompt: string;
  };

  metadata?: Record<string, any>;
}

export interface AiInsightsResponse {
  user_id: number;
  summary: InsightSummary;
  summary_text: string;
  insights: SpendingInsight[];
  financial_health: any;
  generated_from: string[];
  persisted: boolean;
}
export interface MonthlyTrendItem {
  year: number;
  month_number: number;
  month: string;
  label: string;
  amount: number;
}

export interface MonthlyTrendResponse {
  months: MonthlyTrendItem[];
  total: number;
  average: number;
  highest_month: MonthlyTrendItem | null;
  trend_percentage: number;
}
@Injectable({
  providedIn: 'root'
})
export class AiInsightsService {
  private readonly apiUrl = 'http://127.0.0.1:8000/api/insights';

  constructor(private http: HttpClient) {}

  getUserInsights(userId: number): Observable<AiInsightsResponse> {
    return this.http.get<AiInsightsResponse>(
      `${this.apiUrl}/user/${userId}`
    );
  }
  getMonthlyTrend(
  userId: number,
  months = 6
): Observable<MonthlyTrendResponse> {
  return this.http.get<MonthlyTrendResponse>(
    `${this.apiUrl}/user/${userId}/monthly-trend`,
    {
      params: {
        months: months.toString()
      }
    }
  );
}

}