import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

export interface LocationData {
  lat: number;
  lon: number;
  altitud?: number;
  departamento?: string;
  municipio?: string;
  clima?: any;
}

@Component({
  selector: 'app-google-maps-picker',
  standalone: true,
  imports: [MatCardModule, MatInputModule, MatButtonModule, MatIconModule, FormsModule],
  template: `
    <mat-card class="map-card">
      <mat-card-header>
        <mat-card-title>📍 Ubicación de la Finca</mat-card-title>
        <mat-card-subtitle>Arrastra el pin o busca una dirección en Colombia</mat-card-subtitle>
      </mat-card-header>
      <mat-card-content>
        <div class="search-row">
          <mat-form-field appearance="outline" class="search-field">
            <mat-label>Buscar dirección o lugar</mat-label>
            <input matInput [(ngModel)]="searchAddress" placeholder="Ej: Armenia, Quindío, Colombia"
                   (keyup.enter)="geocode()">
            <mat-icon matPrefix>search</mat-icon>
          </mat-form-field>
          <button mat-raised-button color="primary" (click)="geocode()" [disabled]="!searchAddress.trim()">
            <mat-icon>my_location</mat-icon> Buscar
          </button>
        </div>

        <div class="map-container">
          <iframe
            [src]="mapUrl"
            width="100%"
            height="350"
            style="border:0; border-radius: 8px;"
            allowfullscreen=""
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
            title="Mapa de ubicación de la finca">
          </iframe>
        </div>

        @if (selectedCoords.lat && selectedCoords.lon) {
          <div class="coords-display">
            <div class="coord-item">
              <mat-icon>pin_drop</mat-icon>
              <span><strong>Lat:</strong> {{ selectedCoords.lat.toFixed(6) }}</span>
            </div>
            <div class="coord-item">
              <mat-icon>pin_drop</mat-icon>
              <span><strong>Lon:</strong> {{ selectedCoords.lon.toFixed(6) }}</span>
            </div>
            @if (selectedCoords.altitud) {
              <div class="coord-item">
                <mat-icon>terrain</mat-icon>
                <span><strong>Altitud:</strong> {{ selectedCoords.altitud }} msnm</span>
              </div>
            }
            @if (selectedCoords.departamento) {
              <div class="coord-item">
                <mat-icon>location_city</mat-icon>
                <span>{{ selectedCoords.municipio }}, {{ selectedCoords.departamento }}</span>
              </div>
            }
          </div>
        }

        @if (climaData) {
          <div class="climate-preview">
            <h4>🌤️ Datos climáticos de referencia (IDEAM)</h4>
            <div class="climate-grid">
              <div class="climate-item">
                <span class="climate-label">🌡️ Temp. promedio</span>
                <strong>{{ climaData.temperatura_promedio }}°C</strong>
              </div>
              <div class="climate-item">
                <span class="climate-label">💧 Precip. anual</span>
                <strong>{{ climaData.precipitacion_anual_mm }} mm</strong>
              </div>
              <div class="climate-item">
                <span class="climate-label">💦 Humedad</span>
                <strong>{{ climaData.humedad_relativa }}%</strong>
              </div>
              <div class="climate-item">
                <span class="climate-label">⛰️ Altitud est.</span>
                <strong>{{ climaData.altitud_estimada_msnm }} msnm</strong>
              </div>
            </div>
            <p class="climate-note">{{ climaData.nota }}</p>
          </div>
        }
      </mat-card-content>
    </mat-card>
  `,
  styles: [
    `
      .map-card { margin-bottom: 16px; }
      .search-row { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 12px; }
      .search-field { flex: 1; }
      .map-container { margin-bottom: 12px; }
      .coords-display {
        display: flex; flex-wrap: wrap; gap: 16px; padding: 12px;
        background: #e8f5e9; border-radius: 8px; margin-bottom: 12px;
      }
      .coord-item { display: flex; align-items: center; gap: 6px; font-size: 0.9rem; }
      .climate-preview {
        padding: 12px; background: #e3f2fd; border-radius: 8px;
      }
      .climate-preview h4 { margin: 0 0 8px 0; color: #1565c0; }
      .climate-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
      .climate-item { display: flex; flex-direction: column; }
      .climate-label { font-size: 0.8rem; color: #666; }
      .climate-note { font-size: 0.75rem; color: #999; margin-top: 8px; font-style: italic; }
    `,
  ],
})
export class GoogleMapsPickerComponent {
  @Input() lat: number = 4.5339;  // Armenia, Quindío por defecto
  @Input() lon: number = -75.6811;
  @Output() locationSelected = new EventEmitter<LocationData>();

  searchAddress = '';
  selectedCoords: LocationData = { lat: this.lat, lon: this.lon };
  climaData: any = null;

  constructor(private http: HttpClient, private sanitizer: DomSanitizer) {}

  get mapUrl(): SafeResourceUrl {
    const url = `https://www.google.com/maps/embed/v1/place?q=${this.selectedCoords.lat},${this.selectedCoords.lon}&zoom=14&maptype=satellite&language=es`;
    return this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  geocode(): void {
    if (!this.searchAddress.trim()) return;
    this.http.get<{status: string; lat: number; lon: number; formatted_address?: string}>(
      `http://localhost:8000/api/v1/location/geocode?address=${encodeURIComponent(this.searchAddress)}`
    ).subscribe({
      next: (res) => {
        this.selectedCoords.lat = res.lat;
        this.selectedCoords.lon = res.lon;
        this.selectedCoords.departamento = res.formatted_address;
        this.fetchClimate();
        this.fetchElevation();
        this.locationSelected.emit(this.selectedCoords);
      },
      error: () => {
        // Si la API falla, usar las coordenadas por defecto y buscar clima offline
        this.fetchClimate();
      },
    });
  }

  fetchClimate(): void {
    this.http.get<any>(
      `http://localhost:8000/api/v1/location/climate?lat=${this.selectedCoords.lat}&lon=${this.selectedCoords.lon}`
    ).subscribe({
      next: (res) => {
        this.climaData = res.referencia_climatologica;
        this.selectedCoords.altitud = res.referencia_climatologica?.altitud_estimada_msnm;
        this.selectedCoords.clima = res;
        this.locationSelected.emit(this.selectedCoords);
      },
    });
  }

  fetchElevation(): void {
    this.http.get<any>(
      `http://localhost:8000/api/v1/location/elevation?lat=${this.selectedCoords.lat}&lon=${this.selectedCoords.lon}`
    ).subscribe({
      next: (res) => {
        if (res.altitud_estimada_msnm) {
          this.selectedCoords.altitud = res.altitud_estimada_msnm;
        }
      },
    });
  }

  updateCoords(lat: number, lon: number): void {
    this.selectedCoords.lat = lat;
    this.selectedCoords.lon = lon;
    this.fetchClimate();
    this.locationSelected.emit(this.selectedCoords);
  }
}
