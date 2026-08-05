import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSliderModule } from '@angular/material/slider';
import { MatDividerModule } from '@angular/material/divider';
import { JsonPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RecomendacionesService, Recomendacion, SolicitudRecomendacion } from '../../core/services/recomendaciones.service';

@Component({
  selector: 'app-recomendaciones',
  standalone: true,
  imports: [
    MatCardModule, MatFormFieldModule, MatSelectModule,
    MatInputModule, MatButtonModule, MatIconModule,
    MatSliderModule, MatDividerModule, FormsModule, JsonPipe,
  ],
  template: `
    <h1>Solicitar Recomendación</h1>

    <mat-card style="max-width: 700px;">
      <mat-card-content>
        <div class="form-row">
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Finca</mat-label>
            <mat-select [(ngModel)]="solicitud.finca_id">
              <mat-option value="demo">Finca Demo (Quindío)</mat-option>
            </mat-select>
          </mat-form-field>

          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Cultivo</mat-label>
            <mat-select [(ngModel)]="solicitud.cultivo_id">
              <mat-option value="cafe">☕ Café</mat-option>
              <mat-option value="maiz">🌽 Maíz</mat-option>
              <mat-option value="arroz">🍚 Arroz</mat-option>
            </mat-select>
          </mat-form-field>
        </div>

        <mat-divider style="margin: 16px 0;"></mat-divider>
        <h3>Parámetros del suelo</h3>

        <div class="form-row">
          <mat-form-field appearance="outline">
            <mat-label>pH</mat-label>
            <input matInput type="number" [(ngModel)]="solicitud.ph" placeholder="6.5" step="0.1">
          </mat-form-field>

          <mat-form-field appearance="outline">
            <mat-label>Nitrógeno (ppm)</mat-label>
            <input matInput type="number" [(ngModel)]="solicitud.nitrogeno" placeholder="200">
          </mat-form-field>

          <mat-form-field appearance="outline">
            <mat-label>Fósforo (ppm)</mat-label>
            <input matInput type="number" [(ngModel)]="solicitud.fosforo" placeholder="50">
          </mat-form-field>

          <mat-form-field appearance="outline">
            <mat-label>Potasio (ppm)</mat-label>
            <input matInput type="number" [(ngModel)]="solicitud.potasio" placeholder="150">
          </mat-form-field>
        </div>
      </mat-card-content>
      <mat-card-actions>
        <button mat-raised-button color="primary" (click)="solicitar()" [disabled]="loading">
          <mat-icon>analytics</mat-icon> {{ loading ? 'Analizando...' : 'Solicitar Recomendación' }}
        </button>
      </mat-card-actions>
    </mat-card>

    @if (resultado) {
      <mat-card style="max-width: 700px; margin-top: 24px;" [class]="'result-card ' + resultado.clasificacion_upra.toLowerCase()">
        <mat-card-header>
          <mat-card-title>Resultado del Análisis</mat-card-title>
          <mat-card-subtitle>Clasificación UPRA: <strong>{{ resultado.clasificacion_upra }}</strong></mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <p><strong>Confianza:</strong> {{ (resultado.confianza * 100).toFixed(1) }}%</p>
          <p><strong>Justificación:</strong></p>
          <pre>{{ resultado.justificacion | json }}</pre>
        </mat-card-content>
      </mat-card>
    }
  `,
  styles: [
    `
      h1 { margin-bottom: 24px; color: #2e7d32; }
      .form-row { display: flex; gap: 16px; flex-wrap: wrap; }
      .full-width { flex: 1; min-width: 200px; }
      .result-card.alta { border-left: 4px solid #4caf50; }
      .result-card.media { border-left: 4px solid #ff9800; }
      .result-card.baja { border-left: 4px solid #f44336; }
      .result-card.noapta { border-left: 4px solid #9e9e9e; }
      pre { background: #f5f5f5; padding: 12px; border-radius: 4px; font-size: 0.85rem; }
    `,
  ],
})
export class RecomendacionesComponent {
  solicitud: SolicitudRecomendacion = {
    finca_id: 'demo',
    cultivo_id: 'cafe',
    ph: 6.0,
    nitrogeno: 220,
    fosforo: 45,
    potasio: 180,
  };
  resultado: Recomendacion | null = null;
  loading = false;

  constructor(private service: RecomendacionesService) {}

  solicitar(): void {
    this.loading = true;
    this.resultado = null;
    this.service.solicitar(this.solicitud).subscribe({
      next: (r: Recomendacion) => { this.resultado = r; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }
}
