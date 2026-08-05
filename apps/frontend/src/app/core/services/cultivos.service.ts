import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable } from 'rxjs';

export interface Cultivo {
  id: string;
  nombre: string;
  nombre_cientifico?: string;
  descripcion?: string;
  icono?: string;
  activo: boolean;
}

export interface FichaTecnica {
  id: string;
  cultivo_id: string;
  estado: string;
  tipo_fuente: string;
  fuente: string;
  umbrales: Record<string, any>;
  datos_economicos: Record<string, any>;
  etiqueta_internacional: boolean;
}

interface PaginatedResponse<T> {
  data: T[];
  meta: { page: number; page_size: number; total: number; total_pages: number };
}

@Injectable({ providedIn: 'root' })
export class CultivosService {
  private apiUrl = 'http://localhost:8000/api/v1/catalogo';

  constructor(private http: HttpClient) {}

  listar(): Observable<Cultivo[]> {
    return this.http.get<PaginatedResponse<Cultivo>>(`${this.apiUrl}/cultivos`).pipe(
      map(res => res.data)
    );
  }

  detalle(id: string): Observable<Cultivo> {
    return this.http.get<Cultivo>(`${this.apiUrl}/cultivos/${id}`);
  }

  fichaTecnica(cultivoId: string): Observable<FichaTecnica> {
    return this.http.get<FichaTecnica>(`${this.apiUrl}/cultivos/${cultivoId}/ficha`);
  }
}
