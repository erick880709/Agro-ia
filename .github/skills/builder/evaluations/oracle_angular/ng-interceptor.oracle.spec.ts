import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { API_BASE_URL } from './core/api-base-url';
import { authInterceptor } from './core/auth-interceptor';
import { AuthSession } from './core/auth-session';

function setup(token: string | null) {
  TestBed.configureTestingModule({
    providers: [
      { provide: API_BASE_URL, useValue: 'https://api.bank.test' },
      { provide: AuthSession, useValue: { token: signal(token) } },
      provideHttpClient(withInterceptors([authInterceptor])),
      provideHttpClientTesting(),
    ],
  });
  return { http: TestBed.inject(HttpClient), ctrl: TestBed.inject(HttpTestingController) };
}

function authOf(url: string, token: string | null): string | null {
  const { http, ctrl } = setup(token);
  http.get(url).subscribe();
  const req = ctrl.expectOne(url);
  const header = req.request.headers.get('Authorization');
  req.flush({});
  ctrl.verify();
  TestBed.resetTestingModule();
  return header;
}

describe('Oracle authInterceptor', () => {
  it('añade el token solo a la API propia', () => {
    expect(authOf('/api/accounts', 't1')).toBe('Bearer t1');
    expect(authOf('https://api.bank.test/v1/accounts', 't1')).toBe('Bearer t1');
    expect(authOf('https://cdn.example.com/a.json', 't1')).toBeNull();
    expect(authOf('https://api.bank.test.evil.com/steal', 't1')).toBeNull();
    expect(authOf('https://evil.com/?next=https://api.bank.test', 't1')).toBeNull();
    expect(authOf('//evil.com/api/x', 't1')).toBeNull();
  });
  it('no añade cabecera sin token', () => {
    expect(authOf('/api/accounts', null)).toBeNull();
  });
});
