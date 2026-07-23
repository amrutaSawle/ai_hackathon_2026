import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface CopilotRequest {
  user_id: number;
  message: string;
}

export interface CopilotResponse {
  user_id: number;
  question: string;
  intent: string;
  answer: string;
  data?: Record<string, unknown>;
  suggestions?: string[];
  sources?: string[];
  generated_by?: string;
}

@Injectable({
  providedIn: 'root'
})
export class CopilotService {
  private readonly apiUrl = '/api/copilot/chat';

  constructor(private http: HttpClient) {}

  sendMessage(
    request: CopilotRequest
  ): Observable<CopilotResponse> {
    return this.http.post<CopilotResponse>(
      this.apiUrl,
      request
    );
  }
}
