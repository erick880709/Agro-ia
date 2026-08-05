import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';

export interface SensorData {
  variable: string;
  valor: number;
  unidad: string;
  rango_ideal: string;
  estado: 'ok' | 'warning' | 'critical';
}

@Component({
  selector: 'app-iot',
  standalone: true,
  imports: [MatCardModule, MatTableModule, MatIconModule, MatChipsModule],
  template: `
    <h1>Monitoreo IoT — Sensores de Suelo</h1>

    <mat-card>
      <mat-card-header>
        <mat-card-title>📡 Última Lectura — Finca Demo (Quindío)</mat-card-title>
      </mat-card-header>
      <mat-card-content>
        <table mat-table [dataSource]="dataSource" class="sensor-table">
          <ng-container matColumnDef="variable">
            <th mat-header-cell *matHeaderCellDef>Variable</th>
            <td mat-cell *matCellDef="let row">{{ row.variable }}</td>
          </ng-container>
          <ng-container matColumnDef="valor">
            <th mat-header-cell *matHeaderCellDef>Valor</th>
            <td mat-cell *matCellDef="let row">{{ row.valor }} {{ row.unidad }}</td>
          </ng-container>
          <ng-container matColumnDef="rango">
            <th mat-header-cell *matHeaderCellDef>Rango Ideal</th>
            <td mat-cell *matCellDef="let row">{{ row.rango_ideal }}</td>
          </ng-container>
          <ng-container matColumnDef="estado">
            <th mat-header-cell *matHeaderCellDef>Estado</th>
            <td mat-cell *matCellDef="let row">
              <mat-chip [color]="row.estado">{{ row.estado }}</mat-chip>
            </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="columns"></tr>
          <tr mat-row *matRowDef="let row; columns: columns"></tr>
        </table>
      </mat-card-content>
    </mat-card>
  `,
  styles: [
    `
      h1 { margin-bottom: 24px; color: #2e7d32; }
      .sensor-table { width: 100%; }
    `,
  ],
})
export class IotComponent {
  columns = ['variable', 'valor', 'rango', 'estado'];
  dataSource: SensorData[] = [
    { variable: 'pH', valor: 6.2, unidad: '', rango_ideal: '5.5 - 6.5', estado: 'ok' },
    { variable: 'Nitrógeno', valor: 210, unidad: 'ppm', rango_ideal: '200 - 400', estado: 'ok' },
    { variable: 'Fósforo', valor: 48, unidad: 'ppm', rango_ideal: '30 - 75', estado: 'ok' },
    { variable: 'Potasio', valor: 175, unidad: 'ppm', rango_ideal: '100 - 300', estado: 'ok' },
    { variable: 'Materia Orgánica', valor: 12, unidad: '%', rango_ideal: '8 - 20', estado: 'ok' },
    { variable: 'Humedad', valor: 65, unidad: '%', rango_ideal: '60 - 80', estado: 'ok' },
    { variable: 'Temperatura', valor: 22, unidad: '°C', rango_ideal: '18 - 24', estado: 'ok' },
  ];
}
