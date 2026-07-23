import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FraudService } from '../../services/fraud.service';

@Component({
  selector: 'app-fraud',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './fraud.html',
  styleUrls: ['./fraud.css']
})
export class FraudComponent {

  bankName = "Deutsche Bank";

  today = new Date();

  transactionsToday = 1284;

  blockedFrauds = 73;

  modelAccuracy = 98.7;

  systemStatus = "ONLINE";

  loading = false;

  response: any;

  riskPercentage = 0;

  circleColor = '#2E7D32';

  riskMessage = 'SAFE';
  
  private animationTimer: any;
  
  payment = {

  beneficiary_name: "",

  beneficiary_account: "",

  new_beneficiary: false,

  transaction_amount: 12000,

  transaction_type: "transfer",

  transaction_time: "21:30",

  transaction_location: "Frankfurt",

  device_type: "mobile",

  previous_transactions_count: 5

};

  constructor(private fraudService: FraudService) {}

  animateRisk(score: number) {

  // Stop previous animation
  if (this.animationTimer) {
    clearInterval(this.animationTimer);
  }

  this.riskPercentage = 0;

  if (score >= 80) {

    this.circleColor = '#D32F2F';
    this.riskMessage = 'HIGH RISK';

  } else if (score >= 50) {

    this.circleColor = '#FB8C00';
    this.riskMessage = 'MEDIUM RISK';

  } else {

    this.circleColor = '#2E7D32';
    this.riskMessage = 'SAFE';

  }

  this.animationTimer = setInterval(() => {

    if (this.riskPercentage >= score) {

      this.riskPercentage = score;

      clearInterval(this.animationTimer);

      return;

    }

    this.riskPercentage++;

  }, 20);

}

  checkFraud() {

  this.loading = true;

  this.response = undefined;

  this.fraudService.checkPayment(this.payment)
    .subscribe({

      next: (res: any) => {

        console.log("Fraud Response:", res);

        this.response = res;

        if (res && typeof res.riskScore === "number") {
          this.animateRisk(Math.round(res.riskScore));
        } else {
          console.error("Invalid response:", res);
        }

        this.loading = false;

      },

      error: (err: unknown) => {

        // Stop any running animation
        if (this.animationTimer) {
          clearInterval(this.animationTimer);
        }

        this.loading = false;

        console.log(err);

        alert("Backend not running");

      }

    });

}

}
