import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class AuthSession {
  readonly token = signal<string | null>(null);
}
