import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subscription, interval, startWith, switchMap } from 'rxjs';

@Component({
  selector: 'app-advisor',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './advisor.html',
  styleUrl: './advisor.css'
})
export class Advisor implements OnInit,OnDestroy {
  advisorResult: any = null;
  loading = true;
  errorMessage = '';
  private refreshSubscription?: Subscription;

  constructor(private http: HttpClient) {}

   ngOnInit(): void {
    this.refreshSubscription = interval(10000)
      .pipe(
        startWith(0),
        switchMap(() =>
          this.http.get<any>(
            '/api/advisor/user/1'
          )
        )
      )
      .subscribe({
        next: (response) => {
          this.advisorResult = response;
          this.loading = false;
          this.errorMessage = '';
        },
        error: (error) => {
          console.error('Failed to load advisor data:', error);
          this.errorMessage =
            'Unable to refresh spending analysis.';
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
revealedMetrics = new Set<string>();

toggleMetric(metric: string): void {
  if (this.revealedMetrics.has(metric)) {
    this.revealedMetrics.delete(metric);
  } else {
    this.revealedMetrics.add(metric);
  }
}

isMetricRevealed(metric: string): boolean {
  return this.revealedMetrics.has(metric);
}
getCategoryIcon(category: string | number | symbol): string {
  const categoryName = String(category).toLowerCase();

  if (
    categoryName.includes('shopping') ||
    categoryName.includes('amazon')
  ) {
    return 'shopping_bag';
  }

  if (
    categoryName.includes('medical') ||
    categoryName.includes('medicine') ||
    categoryName.includes('health')
  ) {
    return 'medication';
  }

  if (
    categoryName.includes('flight') ||
    categoryName.includes('travel')
  ) {
    return 'flight';
  }

  if (categoryName.includes('hotel')) {
    return 'hotel';
  }

  if (categoryName.includes('grocery')) {
    return 'local_grocery_store';
  }

  if (
    categoryName.includes('utility') ||
    categoryName.includes('bill')
  ) {
    return 'receipt_long';
  }

  if (
    categoryName.includes('sport') ||
    categoryName.includes('fitness')
  ) {
    return 'sports_basketball';
  }

  if (
    categoryName.includes('food') ||
    categoryName.includes('dining')
  ) {
    return 'restaurant';
  }

  return 'payments';
}

getCategoryTheme(category: string | number | symbol): string {
  const categoryName = String(category).toLowerCase();

  if (
    categoryName.includes('shopping') ||
    categoryName.includes('amazon')
  ) {
    return 'category-shopping';
  }

  if (
    categoryName.includes('medical') ||
    categoryName.includes('medicine') ||
    categoryName.includes('health')
  ) {
    return 'category-medical';
  }

  if (
    categoryName.includes('flight') ||
    categoryName.includes('travel')
  ) {
    return 'category-travel';
  }

  if (categoryName.includes('hotel')) {
    return 'category-hotel';
  }

  if (categoryName.includes('grocery')) {
    return 'category-grocery';
  }

  if (
    categoryName.includes('utility') ||
    categoryName.includes('bill')
  ) {
    return 'category-utility';
  }

  return 'category-default';
}

getCategoryDescription(category: string | number | symbol): string {
  const categoryName = String(category).toLowerCase();

  if (categoryName.includes('shopping')) {
    return 'Online and retail purchases';
  }

  if (categoryName.includes('flight')) {
    return 'Flight bookings and airfare';
  }

  if (categoryName.includes('hotel')) {
    return 'Hotels and accommodation';
  }

  if (categoryName.includes('grocery')) {
    return 'Groceries and household items';
  }

  if (
    categoryName.includes('utility') ||
    categoryName.includes('bill')
  ) {
    return 'Bills and recurring payments';
  }

  if (categoryName.includes('medical')) {
    return 'Medical and healthcare';
  }

  return 'Transaction category';
}
}
