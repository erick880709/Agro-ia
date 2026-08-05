import { Component, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { RouterModule } from '@angular/router';
import { Cultivo } from '../../core/services/cultivos.service';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-cultivos',
  standalone: true,
  imports: [
    MatCardModule, MatButtonModule, MatIconModule,
    MatChipsModule, MatProgressSpinnerModule, RouterModule,
  ],
  template: `
    <h1>Catálogo de Cultivos</h1>
    @if (loading) {
      <mat-spinner diameter="40" style="margin: 40px auto;"></mat-spinner>
    } @else {
      <div class="grid">
        @for (cultivo of cultivos; track cultivo.id) {
          <mat-card class="cultivo-card">
            <mat-card-header>
              <mat-card-title>
                <span class="cultivo-icon">{{ cultivo.icono || '🌱' }}</span>
                {{ cultivo.nombre }}
              </mat-card-title>
              <mat-card-subtitle>{{ cultivo.nombre_cientifico || '' }}</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              <p>{{ cultivo.descripcion || 'Sin descripción disponible.' }}</p>
            </mat-card-content>
            <mat-card-actions>
              <button mat-button color="primary" [routerLink]="['/cultivos', cultivo.id]">
                <mat-icon>info</mat-icon> Ver ficha técnica
              </button>
              <button mat-button color="accent" [routerLink]="['/recomendaciones']" [queryParams]="{cultivoId: cultivo.id}">
                <mat-icon>analytics</mat-icon> Analizar
              </button>
            </mat-card-actions>
          </mat-card>
        }
      </div>
    }
  `,
  styles: [
    `
      h1 { margin-bottom: 24px; color: #2e7d32; }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 16px;
      }
      .cultivo-card { transition: box-shadow 0.2s; }
      .cultivo-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
      .cultivo-icon { font-size: 1.5rem; margin-right: 8px; }
    `,
  ],
})
export class CultivosComponent implements OnInit {
  cultivos: Cultivo[] = [];
  loading = true;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.http.get<{data: Cultivo[]}>('http://localhost:8000/api/v1/catalogo/cultivos').subscribe({
      next: (res) => { this.cultivos = res.data; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }
}
