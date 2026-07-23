import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';

import {
  AiInsightsResponse,
  AiInsightsService,
  InsightSummary,
  MonthlyTrendItem,
  MonthlyTrendResponse,
  SpendingInsight
} from '../../services/ai-insights.service';

type InsightFilter =
  | 'all'
  | 'critical'
  | 'warning'
  | 'info'
  | 'success'
  | 'opportunity';

@Component({
  selector: 'app-ai-insights',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ai-insights.html',
  styleUrl: './ai-insights.css'
})
export class AiInsightsComponent implements OnInit {
  userId = 1;

  insightsData: AiInsightsResponse | null = null;
  monthlyTrend: MonthlyTrendResponse | null = null;

  loading = true;
  refreshing = false;
  trendLoading = true;

  errorMessage = '';
  trendError = '';

  selectedFilter: InsightFilter = 'all';

  constructor(
    private readonly aiInsightsService: AiInsightsService
  ) {}

  ngOnInit(): void {
    this.loadInsights();
    this.loadMonthlyTrend();
  }

  loadInsights(showRefreshLoader = false): void {
    if (showRefreshLoader) {
      this.refreshing = true;
    } else {
      this.loading = true;
    }

    this.errorMessage = '';

    this.aiInsightsService
      .getUserInsights(this.userId)
      .subscribe({
        next: response => {
          this.insightsData = response;
          this.loading = false;
          this.refreshing = false;
        },
        error: error => {
          console.error(
            'Unable to load AI insights:',
            error
          );

          this.errorMessage =
            'Unable to load your financial insights.';

          this.loading = false;
          this.refreshing = false;
        }
      });
  }

  loadMonthlyTrend(): void {
    this.trendLoading = true;
    this.trendError = '';

    this.aiInsightsService
      .getMonthlyTrend(this.userId, 6)
      .subscribe({
        next: response => {
          this.monthlyTrend = response;
          this.trendLoading = false;
        },
        error: error => {
          console.error(
            'Unable to load monthly trend:',
            error
          );

          this.monthlyTrend = null;
          this.trendError =
            'Monthly spending trend could not be loaded.';

          this.trendLoading = false;
        }
      });
  }

  refreshInsights(): void {
    this.loadInsights(true);
    this.loadMonthlyTrend();
  }

  setFilter(filter: InsightFilter): void {
    this.selectedFilter = filter;
  }

  get summary(): InsightSummary | null {
    return this.insightsData?.summary ?? null;
  }

  get allInsights(): SpendingInsight[] {
    return this.insightsData?.insights ?? [];
  }

  get filteredInsights(): SpendingInsight[] {
    if (this.selectedFilter === 'all') {
      return this.allInsights;
    }

    return this.allInsights.filter(
      insight =>
        this.normalizeSeverity(insight.severity) ===
        this.selectedFilter
    );
  }

  get criticalInsights(): SpendingInsight[] {
    return this.allInsights.filter(
      insight =>
        this.normalizeSeverity(insight.severity) ===
        'critical'
    );
  }

  get warningInsights(): SpendingInsight[] {
    return this.allInsights.filter(
      insight =>
        this.normalizeSeverity(insight.severity) ===
        'warning'
    );
  }

  get forecastInsight():
    SpendingInsight | undefined {
    return this.allInsights.find(
      insight => insight.type === 'FORECAST'
    );
  }

  get rewardInsight():
    SpendingInsight | undefined {
    return this.allInsights.find(
      insight =>
        insight.type === 'REWARD_OPPORTUNITY'
    );
  }

  get spendingPatternInsight():
    SpendingInsight | undefined {
    return this.allInsights.find(
      insight =>
        insight.type === 'SPENDING_PATTERN' ||
        insight.type === 'SPENDING_TREND'
    );
  }

  get futureRecommendationInsight():
    SpendingInsight | undefined {
    return this.allInsights.find(
      insight =>
        insight.type === 'FUTURE_RECOMMENDATION'
    );
  }

  get budgetInsight():
    SpendingInsight | undefined {
    return this.allInsights.find(
      insight =>
        insight.type === 'BUDGET_WARNING' ||
        insight.type === 'BUDGET_STATUS'
    );
  }

  get financialHealthScore(): number {
    const backendScore =
      this.insightsData
        ?.financial_health
        ?.overall_score;

    if (
      typeof backendScore === 'number'
    ) {
      return backendScore;
    }

    let score = 90;

    score -=
      this.criticalInsights.length * 14;

    score -=
      this.warningInsights.length * 5;

    const summary = this.summary;

    if (
      summary &&
      summary.previous_month_spend > 0 &&
      summary.current_month_spend >
        summary.previous_month_spend
    ) {
      score -= 5;
    }

    return Math.max(
      25,
      Math.min(100, score)
    );
  }

  get financialHealthLabel(): string {
    const backendStatus =
      this.insightsData
        ?.financial_health
        ?.status;

    const statusLabels:
      Record<string, string> = {
        EXCELLENT: 'Excellent',
        GOOD: 'Good',
        NEEDS_ATTENTION: 'Needs attention',
        AT_RISK: 'High risk',
        INSUFFICIENT_DATA:
          'Insufficient data'
      };

    if (
      backendStatus &&
      statusLabels[backendStatus]
    ) {
      return statusLabels[backendStatus];
    }

    const score =
      this.financialHealthScore;

    if (score >= 85) {
      return 'Excellent';
    }

    if (score >= 65) {
      return 'Good';
    }

    if (score >= 45) {
      return 'Needs attention';
    }

    return 'High risk';
  }

  get healthProgressDegrees(): string {
    return `${
      this.financialHealthScore * 3.6
    }deg`;
  }

  get forecastProgress(): number {
    const summary = this.summary;

    if (
      !summary ||
      summary.projected_month_end_spend <= 0
    ) {
      return 0;
    }

    const percentage =
      (
        summary.current_month_spend /
        summary.projected_month_end_spend
      ) * 100;

    return Math.min(
      100,
      Math.max(0, percentage)
    );
  }

  get trendMonths(): MonthlyTrendItem[] {
    return this.monthlyTrend?.months ?? [];
  }

  get trendMaximumAmount(): number {
    const amounts =
      this.trendMonths.map(
        item => item.amount
      );

    return amounts.length
      ? Math.max(...amounts)
      : 0;
  }

  get trendDirection():
    'up' | 'down' | 'flat' {
    const percentage =
      this.monthlyTrend
        ?.trend_percentage ?? 0;

    if (percentage > 0) {
      return 'up';
    }

    if (percentage < 0) {
      return 'down';
    }

    return 'flat';
  }

  get trendDirectionLabel(): string {
    const percentage =
      this.monthlyTrend
        ?.trend_percentage ?? 0;

    if (percentage > 0) {
      return `${
        Math.abs(percentage).toFixed(1)
      }% increase`;
    }

    if (percentage < 0) {
      return `${
        Math.abs(percentage).toFixed(1)
      }% decrease`;
    }

    return 'No change';
  }

  getBarHeight(amount: number): number {
    if (
      this.trendMaximumAmount <= 0
    ) {
      return 0;
    }

    const percentage =
      amount /
      this.trendMaximumAmount *
      100;

    return Math.max(8, percentage);
  }

  getInsightIcon(type: string): string {
    const iconMap:
      Record<string, string> = {
        FORECAST: '↗',
        SPENDING_TREND: '▥',
        SPENDING_PATTERN: '◉',
        BUDGET_WARNING: '!',
        BUDGET_STATUS: '✓',
        REWARD_OPPORTUNITY: '◇',
        FUTURE_RECOMMENDATION: '▣',
        NO_DATA: 'i'
      };

    return iconMap[type] ?? 'i';
  }

  getSeverityLabel(
    severity: SpendingInsight['severity']
  ): string {
    const normalized =
      this.normalizeSeverity(severity);

    const labels:
      Record<string, string> = {
        critical: 'Critical',
        warning: 'Warning',
        info: 'Info',
        success: 'On track',
        opportunity: 'Opportunity'
      };

    return labels[normalized] ?? 'Info';
  }

  getSeverityClass(
    severity: SpendingInsight['severity']
  ): string {
    return this.normalizeSeverity(severity);
  }

  formatInsightType(type: string): string {
    return type
      .toLowerCase()
      .split('_')
      .map(
        word =>
          word.charAt(0).toUpperCase() +
          word.slice(1)
      )
      .join(' ');
  }

  trackInsight(
    index: number,
    insight: SpendingInsight
  ): string {
    return (
      insight.id ??
      `${insight.type}-${index}`
    );
  }

  trackTrendMonth(
    index: number,
    item: MonthlyTrendItem
  ): string {
    return `${
      item.year
    }-${item.month_number}`;
  }

  private normalizeSeverity(
    severity: string
  ): string {
    return String(
      severity ?? 'INFO'
    ).toLowerCase();
  }
  get topMerchantInsight(): SpendingInsight | undefined {
    return this.allInsights.find(
      insight => insight.type === 'TOP_MERCHANT'
    );
  }

  get largestTransactionInsight(): SpendingInsight | undefined {
    return this.allInsights.find(
      insight => insight.type === 'LARGEST_TRANSACTION'
    );
  }
  
}