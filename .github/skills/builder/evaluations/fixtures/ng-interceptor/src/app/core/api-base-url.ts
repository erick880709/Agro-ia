import { InjectionToken } from '@angular/core';

/** Origen de la API propia, p. ej. https://api.bank.test */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL');
