import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-spending',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './spending.html',
  styleUrl: './spending.css'
})
export class Spending implements OnInit {
  advisorResult: any = null;
  transactions: any[] = [];
  loading = true;
  errorMessage = '';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadSpendingData();
  }

  loadSpendingData(): void {
    this.loading = true;
    this.errorMessage = '';

    this.http
      .get<any>('http://localhost:8000/api/advisor/user/1')
      .subscribe({
        next: (response) => {
          this.advisorResult = response;
          this.loadTransactions();
        },
        error: (error) => {
          console.error('Unable to load spending summary', error);
          this.errorMessage = 'Unable to load spending information.';
          this.loading = false;
        }
      });
  }

  private loadTransactions(): void {
    this.http
      .get<any[]>(
  'http://localhost:8000/api/transactions/user/1/with-analysis')
      .subscribe({
        next: (response) => {
          this.transactions = [...response].sort(
            (first, second) =>
              new Date(second.transaction_date).getTime() -
              new Date(first.transaction_date).getTime()
          );

          this.loading = false;
        },
        error: (error) => {
          console.error('Unable to load transactions', error);
          this.transactions = [];
          this.loading = false;
        }
      });
  }

  getCategoryPercentage(amount: number): number {
    const totalSpend =
      Number(this.advisorResult?.spend_summary?.total_spend) || 0;

    if (totalSpend === 0) {
      return 0;
    }

    return Math.round((Number(amount) / totalSpend) * 100);
  }
getCategoryIcon(category: string | number | symbol): string {
  const value = String(category).toLowerCase();
    if (value.includes('flight') || value.includes('travel')) {
      return 'flight';
    }

    if (value.includes('hotel')) {
      return 'hotel';
    }

    if (value.includes('shopping')) {
      return 'shopping_bag';
    }

    if (value.includes('grocery')) {
      return 'local_grocery_store';
    }

    if (value.includes('utility') || value.includes('bill')) {
      return 'receipt_long';
    }

    if (value.includes('dining') || value.includes('food')) {
      return 'restaurant';
    }

    if (value.includes('fuel')) {
      return 'local_gas_station';
    }

    return 'payments';
  }

getCategoryTheme(category: string | number | symbol): string {
  const value = String(category).toLowerCase();
    if (value.includes('flight') || value.includes('travel')) {
      return 'theme-travel';
    }

    if (value.includes('hotel')) {
      return 'theme-hotel';
    }

    if (value.includes('shopping')) {
      return 'theme-shopping';
    }

    if (value.includes('grocery')) {
      return 'theme-grocery';
    }

    if (value.includes('utility') || value.includes('bill')) {
      return 'theme-utility';
    }

    if (value.includes('dining') || value.includes('food')) {
      return 'theme-dining';
    }

    return 'theme-default';
  }

  formatDate(value: string): string {
    return new Intl.DateTimeFormat('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    }).format(new Date(value));
  }
}