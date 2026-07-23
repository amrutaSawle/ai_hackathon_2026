import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

export interface PaymentRequest {
  beneficiary_name: string;
  beneficiary_account: string;
  new_beneficiary: boolean;
  transaction_amount: number;
  transaction_type: string;
  transaction_time: string;
  transaction_location: string;
  device_type: string;
  previous_transactions_count: number;
}

export interface FraudResponse {
  prediction: number;
  riskScore: number;
  aiScore: number;
  riskLevel: string;
  recommendation: string;
  reasons: string[];
}

@Injectable({ providedIn: 'root' })
export class FraudService {
  constructor(private readonly http: HttpClient) {}

  checkPayment(payment: PaymentRequest) {
    return this.http.post<FraudResponse>('/api/fraud/check-payment', payment);
  }
}
