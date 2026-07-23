import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class FinancialDnaService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/financial-dna';

  getFinancialDna(userId: number): Observable<unknown> {
    return this.http.get<unknown>(`${this.apiUrl}/user/${userId}`);
  }
}
