import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnInit,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { catchError, finalize, of } from 'rxjs';

import { FinancialDnaService } from '../../services/financial-dna.service';
import {
  FinancialDnaTrait,
  FinancialDnaViewModel
} from './financial-dna.models';

@Component({
  selector: 'app-financial-dna',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './financial-dna.html',
  styleUrls: ['./financial-dna.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class FinancialDnaComponent implements OnInit {
  private readonly service = inject(FinancialDnaService);
  private readonly cdr = inject(ChangeDetectorRef);

  loading = true;
  usingDemoData = false;
  selectedTraitIndex = 0;
  dna: FinancialDnaViewModel = this.createDemoData();

  readonly circumference = 326.73;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.usingDemoData = false;

    this.service
      .getFinancialDna(1)
      .pipe(
        catchError((error) => {
          console.error('Financial DNA API error:', error);
          this.usingDemoData = true;
          return of(null);
        }),
        finalize(() => {
          this.loading = false;
          this.cdr.markForCheck();
        })
      )
      .subscribe((response) => {
        if (response) {
          this.dna = this.normalizeResponse(response);
        } else {
          this.dna = this.createDemoData();
        }

        this.selectedTraitIndex = 0;
        this.cdr.markForCheck();
      });
  }

  selectTrait(index: number): void {
    this.selectedTraitIndex = index;
  }

  get selectedTrait(): FinancialDnaTrait {
    return this.dna.traits[this.selectedTraitIndex] ?? this.dna.traits[0];
  }

  get scoreOffset(): number {
    const score = this.clamp(this.dna.personalityScore);
    return this.circumference - (score / 100) * this.circumference;
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value || 0);
  }

  trackByName(index: number, item: { name?: string; label?: string }): string {
    return item.name || item.label || String(index);
  }

  trackByPeriod(index: number, item: { period?: string }): string {
    return item.period || String(index);
  }

  private normalizeResponse(raw: unknown): FinancialDnaViewModel {
    const source = (raw ?? {}) as Record<string, any>;
    const nested = (source['financial_dna'] ?? source) as Record<string, any>;

    const fallback = this.createDemoData();

    const traitsRaw = this.asArray(
      nested['traits'] ?? nested['personality_traits'] ?? fallback.traits
    );

    const categoriesRaw = this.asArray(
      nested['top_categories'] ?? nested['categories'] ?? fallback.categories
    );

    const evidenceRaw = this.asArray(
      nested['evidence'] ?? nested['signals'] ?? fallback.evidence
    );

    const journeyRaw = this.asArray(
      nested['journey'] ?? nested['financial_journey'] ?? fallback.journey
    );

    const comparisonRaw = this.asArray(
      nested['comparison'] ?? nested['benchmarks'] ?? fallback.comparison
    );

    const coachRaw = (nested['coach'] ?? nested['ai_coach'] ?? fallback.coach) as Record<string, any>;
    const predictionRaw = (nested['prediction'] ?? nested['next_prediction'] ?? fallback.prediction) as Record<string, any>;

    return {
      primaryPersonality: this.text(
        nested['primary_personality'] ?? nested['primaryPersonality'],
        fallback.primaryPersonality
      ),
      personalityScore: this.number(
        nested['personality_score'] ?? nested['personalityScore'] ?? nested['score'],
        fallback.personalityScore
      ),
      confidence: this.number(nested['confidence'], fallback.confidence),
      transactionsAnalysed: this.number(
        nested['transactions_analysed'] ?? nested['transactionsAnalyzed'] ?? nested['transactions_count'],
        fallback.transactionsAnalysed
      ),
      totalSpend: this.number(
        nested['total_spend'] ?? nested['totalSpend'],
        fallback.totalSpend
      ),
      updatedAt: this.text(
        nested['updated_at'] ?? nested['updatedAt'],
        fallback.updatedAt
      ),
      summary: this.text(nested['summary'], fallback.summary),

      traits: traitsRaw.map((item, index) => ({
        name: this.text(item?.name, fallback.traits[index]?.name ?? `Trait ${index + 1}`),
        score: this.number(item?.score, fallback.traits[index]?.score ?? 0),
        reason: this.text(item?.reason, fallback.traits[index]?.reason ?? ''),
        icon: this.text(item?.icon, fallback.traits[index]?.icon ?? '•')
      })),

      categories: categoriesRaw.map((item, index) => ({
        name: this.text(item?.name ?? item?.category, fallback.categories[index]?.name ?? `Category ${index + 1}`),
        amount: this.number(item?.amount, fallback.categories[index]?.amount ?? 0),
        percentage: this.number(item?.percentage ?? item?.percent, fallback.categories[index]?.percentage ?? 0),
        icon: this.text(item?.icon, fallback.categories[index]?.icon ?? '•')
      })),

      evidence: evidenceRaw.map((item, index) => ({
        label: this.text(item?.label, fallback.evidence[index]?.label ?? `Signal ${index + 1}`),
        value: this.text(item?.value, fallback.evidence[index]?.value ?? '—'),
        helper: this.text(item?.helper, fallback.evidence[index]?.helper ?? ''),
        icon: this.text(item?.icon, fallback.evidence[index]?.icon ?? '•')
      })),

      journey: journeyRaw.map((item, index) => ({
        period: this.text(item?.period, fallback.journey[index]?.period ?? ''),
        personality: this.text(item?.personality, fallback.journey[index]?.personality ?? '')
      })),

      comparison: comparisonRaw.map((item, index) => ({
        label: this.text(item?.label, fallback.comparison[index]?.label ?? `Metric ${index + 1}`),
        userScore: this.number(item?.userScore ?? item?.user_score, fallback.comparison[index]?.userScore ?? 0),
        averageScore: this.number(item?.averageScore ?? item?.average_score, fallback.comparison[index]?.averageScore ?? 0)
      })),

      coach: {
        message: this.text(coachRaw?.['message'], fallback.coach.message),
        recommendedCard: this.text(
          coachRaw?.['recommendedCard'] ?? coachRaw?.['recommended_card'],
          fallback.coach.recommendedCard
        ),
        yearlyBenefit: this.number(
          coachRaw?.['yearlyBenefit'] ?? coachRaw?.['yearly_benefit'],
          fallback.coach.yearlyBenefit
        ),
        rewardPoints: this.number(
          coachRaw?.['rewardPoints'] ?? coachRaw?.['reward_points'],
          fallback.coach.rewardPoints
        )
      },

      prediction: {
        title: this.text(predictionRaw?.['title'], fallback.prediction.title),
        amount: this.number(predictionRaw?.['amount'], fallback.prediction.amount),
        rewardPoints: this.number(
          predictionRaw?.['rewardPoints'] ?? predictionRaw?.['reward_points'],
          fallback.prediction.rewardPoints
        ),
        confidence: this.number(predictionRaw?.['confidence'], fallback.prediction.confidence)
      }
    };
  }

  private asArray(value: unknown): any[] {
    return Array.isArray(value) && value.length ? value : [];
  }

  private text(value: unknown, fallback: string): string {
    return typeof value === 'string' && value.trim() ? value : fallback;
  }

  private number(value: unknown, fallback: number): number {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  private clamp(value: number): number {
    return Math.max(0, Math.min(100, value));
  }

  private createDemoData(): FinancialDnaViewModel {
    return {
      primaryPersonality: 'Explorer',
      personalityScore: 91,
      confidence: 92,
      transactionsAnalysed: 126,
      totalSpend: 139500,
      updatedAt: 'Updated today',
      summary: 'You value travel, convenience and memorable experiences more than material purchases.',

      traits: [
        {
          name: 'Explorer',
          score: 91,
          reason: 'Flights, hotels and international payments make up the largest part of your recent spending.',
          icon: '✈'
        },
        {
          name: 'Reward Hunter',
          score: 82,
          reason: 'You spend regularly in categories where card rewards and travel benefits can create meaningful value.',
          icon: '★'
        },
        {
          name: 'Smart Saver',
          score: 74,
          reason: 'Your essential spending remains controlled and you avoid unnecessary recurring expenses.',
          icon: '₹'
        },
        {
          name: 'Digital Native',
          score: 63,
          reason: 'Most payments are made through online merchants, mobile banking and digital channels.',
          icon: '◌'
        }
      ],

      categories: [
        { name: 'Flights', amount: 72000, percentage: 52, icon: '✈' },
        { name: 'Hotels', amount: 20000, percentage: 14, icon: '▦' },
        { name: 'Online shopping', amount: 18000, percentage: 13, icon: '▤' },
        { name: 'Dining', amount: 12500, percentage: 9, icon: '◉' }
      ],

      evidence: [
        { label: 'Travel spend', value: '₹92,000', helper: '66% of total spend', icon: '✈' },
        { label: 'Hotel bookings', value: '8', helper: 'in the last 6 months', icon: '▦' },
        { label: 'International', value: '4 countries', helper: 'recent payments', icon: '◎' },
        { label: 'Trips', value: '12', helper: 'this year', icon: '↗' }
      ],

      journey: [
        { period: 'January', personality: 'Smart Saver' },
        { period: 'March', personality: 'Online Shopper' },
        { period: 'May', personality: 'Traveller' },
        { period: 'Today', personality: 'Explorer' }
      ],

      comparison: [
        { label: 'Travel', userScore: 91, averageScore: 34 },
        { label: 'Dining', userScore: 18, averageScore: 25 },
        { label: 'Shopping', userScore: 13, averageScore: 42 }
      ],

      coach: {
        message: 'Your travel spending increased by 12% this month. A travel-focused card can improve rewards without changing your spending habits.',
        recommendedCard: 'Deutsche Bank Travel Card',
        yearlyBenefit: 7300,
        rewardPoints: 4800
      },

      prediction: {
        title: 'Predicted travel spend next month',
        amount: 19800,
        rewardPoints: 620,
        confidence: 92
      }
    };
  }
  getShortTraitName(name: string): string {
  const shortNames: Record<string, string> = {
    'Explorer': 'Explorer',
    'Smart Saver': 'Saver',
    'Digital Native': 'Digital',
    'Family Planner': 'Family',
    'Luxury Lifestyle': 'Luxury',
    'Reward Optimizer': 'Rewards',
    'Reward Hunter': 'Rewards'
  };

  return shortNames[name] ?? name.split(' ')[0];
}
}
