import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import {
  Component,
  ElementRef,
  OnDestroy,
  OnInit,
  ViewChild
} from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-wallet',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './wallet.html',
  styleUrl: './wallet.css'
})
export class Wallet implements OnInit, OnDestroy {
  @ViewChild('walletCarousel')
  walletCarousel?: ElementRef<HTMLDivElement>;

  advisorResult: any = null;
  selectedCard: any = null;
  loading = true;
  errorMessage = '';

  private scrollTimer?: ReturnType<typeof setTimeout>;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadWallet();
  }

  ngOnDestroy(): void {
    if (this.scrollTimer) {
      clearTimeout(this.scrollTimer);
    }
  }

  loadWallet(): void {
    this.loading = true;
    this.errorMessage = '';

    this.http
      .get<any>('/api/advisor/user/1')
      .subscribe({
        next: (response) => {
          this.advisorResult = response;

          const cards = response.all_recommendations ?? [];

          this.selectedCard =
            response.best_card ??
            cards[0] ??
            null;

          this.loading = false;
        },
        error: (error) => {
          console.error('Unable to load wallet data', error);
          this.errorMessage = 'Unable to load wallet information.';
          this.loading = false;
        }
      });
  }

  selectCard(card: any): void {
    this.selectedCard = card;
  }

  onCarouselScroll(): void {
    if (this.scrollTimer) {
      clearTimeout(this.scrollTimer);
    }

    this.scrollTimer = setTimeout(() => {
      requestAnimationFrame(() => {
        this.updateSelectedCardFromScroll();
      });
    }, 120);
  }

  private updateSelectedCardFromScroll(): void {
    const carousel = this.walletCarousel?.nativeElement;
    const cards = this.advisorResult?.all_recommendations ?? [];

    if (!carousel || cards.length === 0) {
      return;
    }

    const carouselRect = carousel.getBoundingClientRect();
    const carouselCenter =
      carouselRect.left + carouselRect.width / 2;

    const cardElements = Array.from(
      carousel.querySelectorAll<HTMLElement>('.wallet-card-item')
    );

    let nearestIndex = 0;
    let nearestDistance = Number.POSITIVE_INFINITY;

    cardElements.forEach((element, index) => {
      const cardRect = element.getBoundingClientRect();
      const cardCenter = cardRect.left + cardRect.width / 2;
      const distance = Math.abs(cardCenter - carouselCenter);

      if (distance < nearestDistance) {
        nearestDistance = distance;
        nearestIndex = index;
      }
    });

    if (cards[nearestIndex]) {
      this.selectedCard = cards[nearestIndex];
    }
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

  getCardNumber(cardName: string): string {
    const cardNumbers: Record<string, string> = {
      'Deutsche Bank Travel Card': '4587',
      'Deutsche Bank Cashback Card': '3256',
      'Deutsche Bank Platinum Card': '7890'
    };

    return cardNumbers[cardName] ?? '4587';
  }
}
