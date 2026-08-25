import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  nombre: string;
  rol: 'Admin' | 'Cliente' | 'Tecnico' | 'Investigador';
  activo: boolean;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly AUTH_KEY = 'agroia_tokens';
  private readonly USER_KEY = 'agroia_user';
  private apiUrl = 'http://localhost:8001/api/v1/auth';

  constructor(private http: HttpClient) {}

  login(email: string, password: string): Observable<AuthTokens> {
    const body = new URLSearchParams();
    body.set('username', email);
    body.set('password', password);

    const headers = new HttpHeaders({ 'Content-Type': 'application/x-www-form-urlencoded' });
    return this.http.post<AuthTokens>(`${this.apiUrl}/login`, body.toString(), { headers }).pipe(
      tap((tokens: AuthTokens) => {
        localStorage.setItem(this.AUTH_KEY, JSON.stringify(tokens));
      })
    );
  }

  register(data: { email: string; password: string; nombre: string }): Observable<User> {
    return this.http.post<User>(`${this.apiUrl}/register`, data);
  }

  logout(): void {
    localStorage.removeItem(this.AUTH_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  getAccessToken(): string | null {
    const stored = localStorage.getItem(this.AUTH_KEY);
    if (!stored) return null;
    return JSON.parse(stored).access_token;
  }

  isLoggedIn(): boolean {
    return !!this.getAccessToken();
  }

  getCurrentUser(): User | null {
    const stored = localStorage.getItem(this.USER_KEY);
    return stored ? JSON.parse(stored) : null;
  }

  setCurrentUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }
}
