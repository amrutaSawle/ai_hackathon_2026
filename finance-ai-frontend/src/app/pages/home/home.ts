import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

interface QuickAction {
  label: string;
  icon: string;
  className: string;
  route?: string;
}
interface FinancialInsight {
  id: string;
  type: 'warning' | 'reward' | 'forecast';
  title: string;
  message: string;
  value: string;
  icon: string;
  actionLabel: string;
  route: string;
}

interface BankAccount {
  accountType: string;
  accountNumber: string;
  balance: number;
  availableBalance: number;
  icon: string;
}

interface Transaction {
  merchant: string;
  description: string;
  amount: number;
  type: 'credit' | 'debit';
  icon: string;
}

interface UpcomingPayment {
  name: string;
  dueDate: string;
  amount: number;
  icon: string;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.html',
  styleUrl: './home.css'
})
export class Home {
  customerName = 'Amruta';
  hideBalance = false;
  financialHealth = {
  score: 84,
  status: 'Good',
  summary: 'Your spending and reward usage are performing well.',
  monthlySpend: 102000,
  predictedSpend: 147000,
  expectedRewards: 4800
  };
  financialInsights: FinancialInsight[] = [
    {
      id: 'budget-warning',
      type: 'warning',
      title: 'Budget warning',
      message: 'At your current pace, you may exceed this month’s budget.',
      value: '₹8,900',
      icon: 'warning_amber',
      actionLabel: 'Find savings',
      route: '/chat'
    },
    {
      id: 'reward-opportunity',
      type: 'reward',
      title: 'Reward opportunity',
      message: 'A travel-focused card could earn additional rewards.',
      value: '+₹2,400',
      icon: 'stars',
      actionLabel: 'Compare cards',
      route: '/wallet'
    },
    {
      id: 'spending-forecast',
      type: 'forecast',
      title: 'Spending forecast',
      message: 'Your expected month-end spending based on current activity.',
      value: '₹1,47,000',
      icon: 'trending_up',
      actionLabel: 'View forecast',
      route: '/spending'
    }
  ];

  totalBalance = 485000;
  availableBalance = 460000;

  quickActions: QuickAction[] = [
    { label: 'Transfer', icon: 'swap_horiz', className: 'transfer-action' },
    { label: 'Pay Bills', icon: 'receipt_long', className: 'bill-action' },
    { label: 'Manage Payee', icon: 'person_add', className: 'payee-action' },
    { label: 'Deposits', icon: 'savings', className: 'deposit-action' },
    { label: 'Loans', icon: 'account_balance', className: 'loan-action' },
    { label: 'Cards', icon: 'credit_card', className: 'card-action', route: '/wallet' },
    { label: 'Statements', icon: 'description', className: 'statement-action' },
    { label: 'Support', icon: 'support_agent', className: 'support-action', route: '/chat' }
  ];

  accounts: BankAccount[] = [
    {
      accountType: 'Savings Account',
      accountNumber: '•••• 4587',
      balance: 310000,
      availableBalance: 305000,
      icon: 'account_balance_wallet'
    },
    {
      accountType: 'Salary Account',
      accountNumber: '•••• 9021',
      balance: 175000,
      availableBalance: 155000,
      icon: 'payments'
    }
  ];

  recentTransactions: Transaction[] = [
    {
      merchant: 'Salary Credit',
      description: 'Monthly salary',
      amount: 95000,
      type: 'credit',
      icon: 'south_west'
    },
    {
      merchant: 'Amazon',
      description: 'Online shopping',
      amount: 2400,
      type: 'debit',
      icon: 'shopping_bag'
    },
    {
      merchant: 'Electricity Bill',
      description: 'Utility payment',
      amount: 3200,
      type: 'debit',
      icon: 'bolt'
    },
    {
      merchant: 'Netflix',
      description: 'Monthly subscription',
      amount: 649,
      type: 'debit',
      icon: 'movie'
    }
  ];

  upcomingPayments: UpcomingPayment[] = [
    { name: 'Credit Card Bill', dueDate: 'Due 24 July', amount: 18500, icon: 'credit_card' },
    { name: 'Home Loan EMI', dueDate: 'Due 1 August', amount: 32000, icon: 'home' }
  ];

  toggleBalance(): void {
    this.hideBalance = !this.hideBalance;
  }

  handleQuickAction(action: QuickAction): void {
    if (!action.route) {
      console.log(`${action.label} selected`);
    }
  }

  trackByLabel(index: number, action: QuickAction): string {
    return action.label;
  }

  trackByAccount(index: number, account: BankAccount): string {
    return account.accountNumber;
  }

  trackByTransaction(index: number, transaction: Transaction): string {
    return `${transaction.merchant}-${index}`;
  }

  trackByPayment(index: number, payment: UpcomingPayment): string {
    return payment.name;
  }
  trackByInsight(index: number, insight: FinancialInsight): string {
  return insight.id;
}
  getHealthProgress(): string {
  return `${this.financialHealth.score}%`;
}

getHealthRing(): string {
  return `conic-gradient(
    #40c98b 0% ${this.financialHealth.score}%,
    rgba(255, 255, 255, 0.18) ${this.financialHealth.score}% 100%
  )`;
}
}
