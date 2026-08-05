import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    MatCardModule, MatInputModule, MatButtonModule,
    MatIconModule, MatTabsModule, FormsModule,
  ],
  template: `
    <div class="auth-container">
      <mat-card class="auth-card">
        <div class="auth-header">
          <span class="auth-logo">🌱</span>
          <h1>AgroIA</h1>
          <p>AgroInteligente Colombia</p>
        </div>

        <mat-tab-group>
          <mat-tab label="Iniciar Sesión">
            <form (ngSubmit)="login()" class="auth-form">
              <mat-form-field appearance="outline">
                <mat-label>Email</mat-label>
                <input matInput type="email" [(ngModel)]="loginData.email" name="email" required>
                <mat-icon matPrefix>email</mat-icon>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Contraseña</mat-label>
                <input matInput type="password" [(ngModel)]="loginData.password" name="password" required>
                <mat-icon matPrefix>lock</mat-icon>
              </mat-form-field>

              <button mat-raised-button color="primary" type="submit" [disabled]="loading">
                {{ loading ? 'Ingresando...' : 'Ingresar' }}
              </button>
              @if (error) { <p class="error">{{ error }}</p> }
            </form>
          </mat-tab>

          <mat-tab label="Registrarse">
            <form (ngSubmit)="register()" class="auth-form">
              <mat-form-field appearance="outline">
                <mat-label>Nombre completo</mat-label>
                <input matInput [(ngModel)]="registerData.nombre" name="nombre" required>
                <mat-icon matPrefix>person</mat-icon>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Email</mat-label>
                <input matInput type="email" [(ngModel)]="registerData.email" name="regEmail" required>
                <mat-icon matPrefix>email</mat-icon>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Contraseña</mat-label>
                <input matInput type="password" [(ngModel)]="registerData.password" name="regPassword" required>
                <mat-icon matPrefix>lock</mat-icon>
              </mat-form-field>

              <button mat-raised-button color="accent" type="submit" [disabled]="loading">
                {{ loading ? 'Registrando...' : 'Crear Cuenta' }}
              </button>
              @if (error) { <p class="error">{{ error }}</p> }
            </form>
          </mat-tab>
        </mat-tab-group>
      </mat-card>
    </div>
  `,
  styles: [
    `
      .auth-container {
        display: flex; justify-content: center; align-items: center;
        min-height: 100vh; background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
      }
      .auth-card { width: 100%; max-width: 440px; padding: 24px; }
      .auth-header { text-align: center; margin-bottom: 16px; }
      .auth-logo { font-size: 3rem; }
      .auth-header h1 { color: #2e7d32; margin: 8px 0; font-size: 1.8rem; }
      .auth-form { display: flex; flex-direction: column; gap: 12px; padding: 16px 0; }
      .error { color: #f44336; text-align: center; font-size: 0.9rem; }
    `,
  ],
})
export class LoginComponent {
  loginData = { email: '', password: '' };
  registerData = { email: '', password: '', nombre: '' };
  loading = false;
  error = '';

  constructor(private auth: AuthService, private router: Router) {}

  login(): void {
    this.loading = true;
    this.error = '';
    this.auth.login(this.loginData.email, this.loginData.password).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: (err: { error?: { detail?: string } }) => { this.error = err.error?.detail || 'Error al iniciar sesión'; this.loading = false; },
    });
  }

  register(): void {
    this.loading = true;
    this.error = '';
    this.auth.register(this.registerData).subscribe({
      next: () => {
        // Auto-login after register
        this.auth.login(this.registerData.email, this.registerData.password).subscribe({
          next: () => this.router.navigate(['/dashboard']),
          error: () => { this.loading = false; },
        });
      },
      error: (err: { error?: { detail?: string } }) => { this.error = err.error?.detail || 'Error al registrarse'; this.loading = false; },
    });
  }
}
