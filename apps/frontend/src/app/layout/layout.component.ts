import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { AuthService } from '../core/services/auth.service';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [
    RouterModule,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatSidenavModule,
    MatListModule,
    MatMenuModule,
  ],
  template: `
    <mat-sidenav-container class="sidenav-container">
      <mat-sidenav #drawer mode="side" opened class="sidenav">
        <div class="logo">
          <span class="logo-icon">🌱</span>
          <span class="logo-text">AgroIA</span>
        </div>
        <mat-nav-list>
          <a mat-list-item routerLink="/dashboard" routerLinkActive="active">
            <mat-icon>dashboard</mat-icon> Dashboard
          </a>
          <a mat-list-item routerLink="/cultivos" routerLinkActive="active">
            <mat-icon>grass</mat-icon> Catálogo Cultivos
          </a>
          <a mat-list-item routerLink="/recomendaciones" routerLinkActive="active">
            <mat-icon>analytics</mat-icon> Recomendaciones
          </a>
          <a mat-list-item routerLink="/iot" routerLinkActive="active">
            <mat-icon>sensors</mat-icon> Sensores IoT
          </a>
          <a mat-list-item routerLink="/chat" routerLinkActive="active">
            <mat-icon>smart_toy</mat-icon> Chat IA
          </a>
        </mat-nav-list>
      </mat-sidenav>

      <mat-sidenav-content>
        <mat-toolbar color="primary">
          <span class="toolbar-title">AgroInteligente Colombia</span>
          <span class="toolbar-spacer"></span>
          <button mat-icon-button [matMenuTriggerFor]="menu">
            <mat-icon>account_circle</mat-icon>
          </button>
          <mat-menu #menu="matMenu">
            <button mat-menu-item (click)="logout()">
              <mat-icon>logout</mat-icon> Cerrar Sesión
            </button>
          </mat-menu>
        </mat-toolbar>

        <main class="content">
          <router-outlet />
        </main>
      </mat-sidenav-content>
    </mat-sidenav-container>
  `,
  styles: [
    `
      .sidenav-container { height: 100vh; }
      .sidenav { width: 240px; background: #f5f5f5; }
      .logo {
        padding: 16px; display: flex; align-items: center; gap: 8px;
        font-size: 1.4rem; font-weight: 600; color: #2e7d32;
      }
      .logo-icon { font-size: 1.8rem; }
      .active { background: rgba(46, 125, 50, 0.1) !important; color: #2e7d32 !important; }
      mat-nav-list a { display: flex; align-items: center; gap: 12px; }
      .toolbar-spacer { flex: 1; }
      .toolbar-title { font-size: 1.1rem; }
      .content { padding: 24px; max-width: 1200px; margin: 0 auto; }
    `,
  ],
})
export class LayoutComponent {
  constructor(private auth: AuthService) {}

  logout(): void {
    this.auth.logout();
  }
}
