import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Subscription, interval, startWith, switchMap } from 'rxjs';

@Component({
  selector: 'app-advisor',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './advisor.html',
  styleUrl: './advisor.css'
})
export class Advisor implements OnInit, OnDestroy {
  advisorResult: any = null;
  loading = true;
  errorMessage = '';
  lastUpdated = new Date();
  private refreshSubscription?: Subscription;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.refreshSubscription = interval(10000)
      .pipe(
        startWith(0),
        switchMap(() =>
          this.http.get<any>('http://localhost:8000/api/advisor/user/1')
        )
      )
      .subscribe({
        next: (response) => {
          this.advisorResult = response;
          this.loading = false;
          this.errorMessage = '';
          this.lastUpdated = new Date();
        },
        error: (error) => {
          console.error('Failed to load advisor data:', error);
          this.errorMessage = 'Unable to refresh your recommendation right now.';
          this.loading = false;
        }
      });
  }

  ngOnDestroy(): void {
    this.refreshSubscription?.unsubscribe();
  }

  getCardTheme(cardName: string): string {
    const themes: Record<string, string> = {
      'Deutsche Bank Platinum Card': 'theme-platinum',
      'Deutsche Bank Cashback Card': 'theme-cashback',
      'Deutsche Bank Travel Card': 'theme-travel'
    };
    return themes[cardName] ?? 'theme-default';
  }

  getCardLabel(cardName: string): string {
    const labels: Record<string, string> = {
      'Deutsche Bank Platinum Card': 'PLATINUM',
      'Deutsche Bank Cashback Card': 'CASHBACK',
      'Deutsche Bank Travel Card': 'TRAVEL'
    };
    return labels[cardName] ?? 'PREMIUM';
  }

  formatLabel(value: string | number | symbol): string {
    return String(value)
      .replaceAll('_', ' ')
      .replace(/\b\w/g, (character) => character.toUpperCase());
  }

  getCategoryIcon(category: string | number | symbol): string {
    const value = String(category).toLowerCase();
    if (value.includes('flight') || value.includes('travel')) return 'flight';
    if (value.includes('hotel')) return 'hotel';
    if (value.includes('shopping') || value.includes('amazon')) return 'shopping_bag';
    if (value.includes('grocery')) return 'local_grocery_store';
    if (value.includes('utility') || value.includes('bill')) return 'receipt_long';
    if (value.includes('food') || value.includes('dining')) return 'restaurant';
    if (value.includes('medical') || value.includes('health')) return 'medication';
    return 'payments';
  }

  getCategoryTheme(category: string | number | symbol): string {
    const value = String(category).toLowerCase();
    if (value.includes('flight') || value.includes('travel')) return 'category-travel';
    if (value.includes('hotel')) return 'category-hotel';
    if (value.includes('shopping') || value.includes('amazon')) return 'category-shopping';
    if (value.includes('grocery')) return 'category-grocery';
    if (value.includes('utility') || value.includes('bill')) return 'category-utility';
    if (value.includes('medical') || value.includes('health')) return 'category-medical';
    return 'category-default';
  }

  getCategoryPercentage(amount: number): number {
    const total = Number(this.advisorResult?.spend_summary?.total_spend || 0);
    return total ? Math.min(100, Math.round((Number(amount) / total) * 100)) : 0;
  }

  getTopCategories(): Array<{ key: string; value: number }> {
    return Object.entries(this.advisorResult?.spend_summary?.category_totals || {})
      .map(([key, value]) => ({ key, value: Number(value) }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 4);
  }

  getWhyRecommended(): string[] {
    const card = this.advisorResult?.best_card;
    const topCategory = this.advisorResult?.spend_summary?.top_category;
    if (!card) return [];
    return [
      `${topCategory || 'Your leading spending category'} strongly matches this card.`,
      card.lounge_access
        ? 'Airport lounge access supports your travel lifestyle.'
        : 'The reward structure aligns with your everyday spending.',
      `${card.forex_markup}% forex markup improves value on international transactions.`,
      `${card.confidence}% confidence indicates a strong fit for your spending pattern.`
    ];
  }

  getAnalysisCount(): number {
    return Object.keys(this.advisorResult?.spend_summary?.category_totals || {}).length;
  }

  scrollToComparison(): void {
    document.getElementById('card-comparison')?.scrollIntoView({ behavior: 'smooth' });
  }
}
