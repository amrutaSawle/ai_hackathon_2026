import { Component, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CopilotResponse, CopilotService } from '../../services/copilot.service';

type RichResponseType =
  | 'TOTAL_SPEND'
  | 'CATEGORY_SPEND'
  | 'TOP_CATEGORY'
  | 'SPENDING_BREAKDOWN'
  | 'MERCHANT_BREAKDOWN'
  | 'TRIPS'
  | 'CARD_RECOMMENDATION'
  | 'SUMMARY'
  | 'FALLBACK';

interface ChatMessage {
  sender: 'user' | 'assistant';
  text: string;
  intent?: string;
  data?: Record<string, unknown>;
  suggestions?: string[];
  generatedBy?: string;
  error?: boolean;
}

interface SpendingCategoryItem {
  category: string;
  amount: number;
  percentage: number;
}

interface MerchantItem {
  merchant: string;
  amount: number;
}

interface TripItem {
  title: string;
  eventType?: string;
  location?: string;
  startDate?: string;
  endDate?: string;
  totalAmount: number;
  transactionCount: number;
  summary?: string;
  merchants: MerchantItem[];
}

interface CardRecommendation {
  cardName: string;
  score: number;
  confidence: number;
  estimatedReward: number;
  annualFee: number;
  netValue: number;
  loungeAccess: boolean;
  forexMarkup: number;
  reason?: string;
}

@Component({
  selector: 'app-copilot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './copilot.html',
  styleUrl: './copilot.css'
})
export class CopilotComponent {
  @ViewChild('messageContainer')
  private messageContainer?: ElementRef<HTMLDivElement>;

  readonly userId = 1;
  userMessage = '';
  isLoading = false;

  messages: ChatMessage[] = [
    {
      sender: 'assistant',
      text: 'Hello! I am your Finance AI Copilot. Ask me anything about your spending, trips, cards, or financial habits.',
      suggestions: [
        'What is my top category?',
        'How much did I spend on hotels?',
        'Show my spending breakdown',
        'Show my trips',
        'Which card should I use?'
      ]
    }
  ];

  constructor(private readonly copilotService: CopilotService) {}

  sendMessage(message?: string): void {
    const finalMessage = (message ?? this.userMessage).trim();
    if (!finalMessage || this.isLoading) return;

    this.messages.push({ sender: 'user', text: finalMessage });
    this.userMessage = '';
    this.isLoading = true;
    this.scrollToBottom();

    this.copilotService.sendMessage({ user_id: this.userId, message: finalMessage })
      .subscribe({
        next: (response: CopilotResponse) => {
          this.messages.push({
            sender: 'assistant',
            text: response.answer,
            intent: response.intent,
            data: response.data,
            suggestions: response.suggestions ?? [],
            generatedBy: response.generated_by
          });
          this.isLoading = false;
          this.scrollToBottom();
        },
        error: (error: unknown) => {
          console.error('Copilot API error:', error);
          this.messages.push({
            sender: 'assistant',
            text: 'I could not connect to the Finance AI service. Please verify that the FastAPI backend is running.',
            error: true
          });
          this.isLoading = false;
          this.scrollToBottom();
        }
      });
  }

  handleEnter(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  sendSuggestion(suggestion: string): void {
    this.sendMessage(suggestion);
  }

  getResponseType(message: ChatMessage): RichResponseType {
    const intent = (message.intent ?? '').toUpperCase();
    const data = message.data ?? {};

    if (['TOTAL_SPEND', 'TOTAL_SPENDING'].includes(intent)) return 'TOTAL_SPEND';
    if (['CATEGORY_SPEND', 'CATEGORY_SPENDING'].includes(intent)) return 'CATEGORY_SPEND';
    if (['TOP_CATEGORY', 'TOP_SPENDING_CATEGORY'].includes(intent)) return 'TOP_CATEGORY';

    if (
      intent === 'SPENDING_BREAKDOWN' ||
      ['categories', 'category_breakdown', 'spending_breakdown', 'breakdown']
        .some(key => Array.isArray(data[key]))
    ) return 'SPENDING_BREAKDOWN';

    if (
      intent === 'MERCHANT_BREAKDOWN' ||
      Array.isArray(data['merchant_breakdown']) ||
      Array.isArray(data['merchants'])
    ) return 'MERCHANT_BREAKDOWN';

    if (
      ['TRIPS', 'SHOW_TRIPS', 'MEMORIES', 'FINANCIAL_MEMORIES'].includes(intent) ||
      ['trips', 'memories', 'financial_events', 'events']
        .some(key => Array.isArray(data[key]))
    ) return 'TRIPS';

    if (
      ['CARD_RECOMMENDATION', 'RECOMMEND_CARD', 'BEST_CARD', 'CARD_ADVISOR'].includes(intent) ||
      Boolean(data['best_card']) || Boolean(data['card']) || Boolean(data['recommendation'])
    ) return 'CARD_RECOMMENDATION';

    if (intent === 'HELP' || intent === 'UNKNOWN' || !message.data) return 'FALLBACK';
    return 'SUMMARY';
  }

  hasData(data?: Record<string, unknown>): boolean {
    return Boolean(data && Object.keys(data).length > 0);
  }

  getDataEntries(data?: Record<string, unknown>): Array<[string, unknown]> {
    return data ? Object.entries(data) : [];
  }

  formatLabel(value: string): string {
    return value.replace(/_/g, ' ').replace(/\b\w/g, letter => letter.toUpperCase());
  }

  formatValue(value: unknown): string {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') return value.toLocaleString('en-IN');
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (Array.isArray(value)) return `${value.length} items`;
    if (typeof value === 'object') return 'View details';
    return String(value);
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency', currency: 'INR', maximumFractionDigits: 0
    }).format(value);
  }

  formatPercentage(value: number): string {
    return `${value.toFixed(1)}%`;
  }

  clampPercentage(value: number): number {
    return Math.min(Math.max(value, 0), 100);
  }

  getNumber(value: unknown, fallback = 0): number {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  getString(value: unknown, fallback = ''): string {
    return value === null || value === undefined ? fallback : String(value);
  }

  getTotalSpendData(data?: Record<string, unknown>) {
    const record = data ?? {};
    return {
      totalSpend: this.getNumber(record['total_spend'] ?? record['amount'] ?? record['total']),
      topCategory: this.getString(record['top_category'] ?? record['category'], 'Unknown'),
      categories: this.getCategoryTotals(record['category_totals'])
    };
  }

  getCategorySpendData(data?: Record<string, unknown>) {
    const record = data ?? {};
    return {
      category: this.getString(record['category'] ?? record['category_name'], 'Category'),
      total: this.getNumber(record['total'] ?? record['amount'] ?? record['total_amount']),
      transactionCount: this.getNumber(record['transaction_count'] ?? record['transactions_count']),
      merchantBreakdown: this.getMerchantBreakdown(record['merchant_breakdown'] ?? record['merchants'] ?? [])
    };
  }

  getTopCategoryData(data?: Record<string, unknown>): SpendingCategoryItem {
    const record = data ?? {};
    return {
      category: this.getString(record['category'] ?? record['category_name'], 'Unknown'),
      amount: this.getNumber(record['amount'] ?? record['total_amount'] ?? record['total']),
      percentage: this.getNumber(record['percentage'] ?? record['percent'])
    };
  }

  getSpendingBreakdown(data?: Record<string, unknown>): SpendingCategoryItem[] {
    if (!data) return [];
    const raw = data['categories'] ?? data['category_breakdown'] ?? data['spending_breakdown'] ?? data['breakdown'];
    if (!Array.isArray(raw)) return [];

    const items = raw.map(item => {
      const record = item as Record<string, unknown>;
      return {
        category: this.getString(record['category'] ?? record['category_name'] ?? record['name'], 'Other'),
        amount: this.getNumber(record['amount'] ?? record['total_amount'] ?? record['spend']),
        percentage: this.getNumber(record['percentage'] ?? record['percent'] ?? record['share'])
      };
    });

    const total = items.reduce((sum, item) => sum + item.amount, 0);
    return items.map(item => ({
      ...item,
      percentage: item.percentage > 0 ? item.percentage : (total > 0 ? item.amount / total * 100 : 0)
    })).sort((a, b) => b.amount - a.amount);
  }

  getCategoryTotals(value: unknown): SpendingCategoryItem[] {
    if (typeof value !== 'object' || value === null || Array.isArray(value)) return [];
    const items = Object.entries(value as Record<string, unknown>).map(([category, amount]) => ({
      category, amount: this.getNumber(amount), percentage: 0
    }));
    const total = items.reduce((sum, item) => sum + item.amount, 0);
    return items.map(item => ({
      ...item,
      percentage: total > 0 ? item.amount / total * 100 : 0
    })).sort((a, b) => b.amount - a.amount);
  }

  isMerchantBreakdown(value: unknown): boolean {
    if (!Array.isArray(value) || value.length === 0) return false;
    return value.every(item => {
      if (typeof item !== 'object' || item === null) return false;
      const record = item as Record<string, unknown>;
      return (
        ('merchant' in record || 'merchant_name' in record || 'name' in record) &&
        ('amount' in record || 'total_amount' in record || 'spend' in record)
      );
    });
  }

  getMerchantBreakdown(value: unknown): MerchantItem[] {
    if (!Array.isArray(value)) return [];
    return value.map(item => {
      const record = item as Record<string, unknown>;
      return {
        merchant: this.getString(record['merchant'] ?? record['merchant_name'] ?? record['name'], 'Unknown merchant'),
        amount: this.getNumber(record['amount'] ?? record['total_amount'] ?? record['spend'])
      };
    });
  }

  getMerchantResponse(data?: Record<string, unknown>): MerchantItem[] {
    if (!data) return [];
    return this.getMerchantBreakdown(data['merchant_breakdown'] ?? data['merchants'] ?? []);
  }

  getTrips(data?: Record<string, unknown>): TripItem[] {
    if (!data) return [];
    const raw = data['trips'] ?? data['memories'] ?? data['financial_events'] ?? data['events'];
    if (!Array.isArray(raw)) return [];

    return raw.map(item => {
      const record = item as Record<string, unknown>;
      return {
        title: this.getString(record['title'] ?? record['event_title'] ?? record['name'], 'Financial event'),
        eventType: this.getString(record['event_type'] ?? record['type']),
        location: this.getString(record['location']),
        startDate: this.getString(record['start_date'] ?? record['from_date']),
        endDate: this.getString(record['end_date'] ?? record['to_date']),
        totalAmount: this.getNumber(record['total_amount'] ?? record['amount']),
        transactionCount: this.getNumber(record['transaction_count'] ?? record['transactions_count']),
        summary: this.getString(record['summary'] ?? record['description']),
        merchants: this.getMerchantBreakdown(record['merchants'] ?? record['merchant_breakdown'] ?? [])
      };
    });
  }

  getCardRecommendation(data?: Record<string, unknown>): CardRecommendation | null {
    if (!data) return null;
    const raw = data['card'] ?? data['best_card'] ?? data['recommendation'] ?? data;
    if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) return null;
    const record = raw as Record<string, unknown>;
    const cardName = this.getString(record['card_name'] ?? record['name'] ?? record['title']);
    if (!cardName) return null;

    return {
      cardName,
      score: this.getNumber(record['score']),
      confidence: this.getNumber(record['confidence']),
      estimatedReward: this.getNumber(record['estimated_reward'] ?? record['reward_value']),
      annualFee: this.getNumber(record['annual_fee']),
      netValue: this.getNumber(record['net_value']),
      loungeAccess: Boolean(record['lounge_access']),
      forexMarkup: this.getNumber(record['forex_markup']),
      reason: this.getString(record['reason'] ?? record['explanation'])
    };
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      const container = this.messageContainer?.nativeElement;
      if (container) container.scrollTop = container.scrollHeight;
    }, 50);
  }
}
