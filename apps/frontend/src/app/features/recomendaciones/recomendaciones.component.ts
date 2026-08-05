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
import { GoogleMapsPickerComponent, LocationData } from '../../shared/google-maps-picker.component';

@Component({
  selector: 'app-recomendaciones',
  standalone: true,
  imports: [
    MatCardModule, MatFormFieldModule, MatSelectModule,
    MatInputModule, MatButtonModule, MatIconModule,
    MatSliderModule, MatDividerModule, FormsModule, JsonPipe,
    GoogleMapsPickerComponent,
  ],
  template: `
    <h1>Solicitar Recomendación</h1>

    <!-- Mapa de ubicación -->
    <app-google-maps-picker
      (locationSelected)="onLocationSelected($event)">
    </app-google-maps-picker>

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

        @if (locationData?.clima) {
          <div class="climate-banner">
            <mat-icon>wb_sunny</mat-icon>
            <span>
              🌡️ {{ locationData?.clima?.referencia_climatologica?.temperatura_promedio }}°C
              &nbsp;|&nbsp; 💧 {{ locationData?.clima?.referencia_climatologica?.precipitacion_anual_mm }} mm/año
              &nbsp;|&nbsp; ⛰️ {{ locationData?.altitud || '—' }} msnm
              &nbsp;|&nbsp; 📍 {{ locationData?.clima?.referencia_climatologica?.region || '—' }}
            </span>
          </div>
        }

        <mat-divider style="margin: 16px 0;"></mat-divider>

        <p class="hint">
          💡 Los datos del suelo se obtienen automáticamente de los sensores IoT registrados en tu finca.
          Asegúrate de tener sensores configurados en la sección <strong>Sensores IoT</strong>.
        </p>
      </mat-card-content>
      <mat-card-actions>
        <button mat-raised-button color="primary" (click)="solicitar()" [disabled]="loading || !solicitud.finca_id || !solicitud.cultivo_id">
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
      .hint { font-size: 0.85rem; color: #666; background: #fff8e1; padding: 12px; border-radius: 8px; }
    `,
  ],
})
export class RecomendacionesComponent {
  solicitud: SolicitudRecomendacion = {
    finca_id: 'demo',
    cultivo_id: 'cafe',
  };
  resultado: Recomendacion | null = null;
  loading = false;
  locationData: LocationData | null = null;

  constructor(private service: RecomendacionesService) {}

  onLocationSelected(data: LocationData): void {
    this.locationData = data;
  }

  solicitar(): void {
    this.loading = true;
    this.resultado = null;
    this.service.solicitar(this.solicitud).subscribe({
      next: (r: Recomendacion) => { this.resultado = r; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }
}
