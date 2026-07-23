import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

export interface DashboardSummary {
  protectionScore: number;
  todayTransactions: number;
  blocked: number;
  safe: number;
  fraudDistribution: { name: string; value: number; color: string }[];
  recentAlerts: { title: string; status: string; icon: string; color: string }[];
  weeklyTrend: number[];
  countries: string[];
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  constructor(private readonly http: HttpClient) {}

  getSummary() {
    return this.http.get<DashboardSummary>('/api/dashboard/summary');
  }
}
