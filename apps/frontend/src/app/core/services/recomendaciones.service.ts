import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Recomendacion {
  id: string;
  finca_id: string;
  cultivo_id: string;
  clasificacion_upra: 'Alta' | 'Media' | 'Baja' | 'NoApta';
  confianza: number;
  justificacion: Record<string, any>;
  estado: string;
  created_at: string;
}

export interface SolicitudRecomendacion {
  finca_id: string;
  cultivo_id: string;
}

@Injectable({ providedIn: 'root' })
export class RecomendacionesService {
  private apiUrl = 'http://localhost:8000/api/v1/recomendaciones';

  constructor(private http: HttpClient) {}

  solicitar(data: SolicitudRecomendacion): Observable<Recomendacion> {
    return this.http.post<Recomendacion>(`${this.apiUrl}/analyze`, data);
  }

  historial(fincaId: string): Observable<Recomendacion[]> {
    return this.http.get<Recomendacion[]>(`${this.apiUrl}/historial/${fincaId}`);
  }

  detalle(id: string): Observable<Recomendacion> {
    return this.http.get<Recomendacion>(`${this.apiUrl}/${id}`);
  }
}
