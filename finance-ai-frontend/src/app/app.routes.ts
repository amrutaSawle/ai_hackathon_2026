import { Routes } from '@angular/router';

import { Home } from './pages/home/home';
import { Wallet } from './pages/wallet/wallet';
import { Advisor } from './pages/advisor/advisor';
import { Spending } from './pages/spending/spending';
import { Cards } from './pages/cards/cards';
import { Transactions } from './pages/transactions/transactions';
import { Rewards } from './pages/rewards/rewards';
import { Chat } from './pages/chat/chat';
import { Profile } from './pages/profile/profile';
import { CopilotComponent } from './pages/copilot/copilot';
import { AiInsightsComponent } from './pages/ai-insights/ai-insights';
import { FinancialDnaComponent } from './pages/financial-dna/financial-dna';
import { DashboardComponent } from './pages/dashboard/dashboard';
import { FraudComponent } from './pages/fraud/fraud';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full'
  },
  {
    path: 'home',
    component: Home
  },
  {
    path: 'dashboard',
    component: DashboardComponent
  },
  {
    path: 'fraud',
    component: FraudComponent
  },
  {
    path: 'wallet',
    component: Wallet
  },
  {
    path: 'advisor',
    component: Advisor
  },
  {
    path: 'spending',
    component: Spending
  },
  {
    path: 'cards',
    component: Cards
  },
  {
    path: 'transactions',
    component: Transactions
  },
  {
    path: 'rewards',
    component: Rewards
  },
  {
    path: 'chat',
    component: CopilotComponent
  },
  {
    path: 'profile',
    component: Profile
  },
  {
    path: 'copilot',
    component: CopilotComponent
  },
 {
    path: 'ai-insights',
    component: AiInsightsComponent
  },
  {
  path: 'financial-dna',
  component: FinancialDnaComponent
},

  {
    path: '**',
    redirectTo: 'home'
  }
];
