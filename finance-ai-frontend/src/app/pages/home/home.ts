import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.html',
  styleUrl: './home.css'
})
export class Home implements OnInit {
  advisorResult: any = null;
  loading = true;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.http
      .get<any>('http://localhost:8000/api/advisor/user/1')
      .subscribe({
        next: (response) => {
          this.advisorResult = response;
          this.loading = false;
        },
        error: (error) => {
          console.error('Unable to load dashboard data', error);
          this.loading = false;
        }
      });
  }
}