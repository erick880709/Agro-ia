import { Component, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [MatCardModule, MatGridListModule, MatIconModule, MatChipsModule],
  template: `
    <h1>Dashboard</h1>
    <mat-grid-list cols="3" rowHeight="160px" gutterSize="16px">
      <mat-grid-tile>
        <mat-card class="stat-card">
          <mat-card-content>
            <div class="stat-icon"><mat-icon>grass</mat-icon></div>
            <div class="stat-value">{{ stats.cultivos }}</div>
            <div class="stat-label">Cultivos en catálogo</div>
          </mat-card-content>
        </mat-card>
      </mat-grid-tile>
      <mat-grid-tile>
        <mat-card class="stat-card">
          <mat-card-content>
            <div class="stat-icon"><mat-icon>analytics</mat-icon></div>
            <div class="stat-value">{{ stats.recomendaciones }}</div>
            <div class="stat-label">Recomendaciones</div>
          </mat-card-content>
        </mat-card>
      </mat-grid-tile>
      <mat-grid-tile>
        <mat-card class="stat-card">
          <mat-card-content>
            <div class="stat-icon"><mat-icon>sensors</mat-icon></div>
            <div class="stat-value">{{ stats.lecturas }}</div>
            <div class="stat-label">Lecturas IoT</div>
          </mat-card-content>
        </mat-card>
      </mat-grid-tile>
    </mat-grid-list>

    <div style="margin-top: 24px;">
      <mat-card>
        <mat-card-header>
          <mat-card-title>🌱 Bienvenido a AgroInteligente Colombia</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <p>Plataforma de análisis de suelo y recomendación de cultivos basada en IA.</p>
          <mat-chip-set>
            <mat-chip>IA + ML</mat-chip>
            <mat-chip>IoT Sensores</mat-chip>
            <mat-chip>Reglas Agronómicas</mat-chip>
            <mat-chip>Chat RAG</mat-chip>
          </mat-chip-set>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [
    `
      h1 { margin-bottom: 24px; color: #2e7d32; }
      .stat-card { width: 100%; text-align: center; }
      .stat-icon mat-icon { font-size: 2.5rem; width: 2.5rem; height: 2.5rem; color: #2e7d32; }
      .stat-value { font-size: 2rem; font-weight: 700; color: #333; }
      .stat-label { color: #666; font-size: 0.9rem; }
    `,
  ],
})
export class DashboardComponent implements OnInit {
  stats = { cultivos: 30, recomendaciones: 0, lecturas: 0 };

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.http.get<{data: any[]; meta: {total: number}}>('http://localhost:8000/api/v1/catalogo/cultivos').subscribe({
      next: (res) => (this.stats.cultivos = res.meta?.total || res.data?.length || 0),
    });
  }
}
