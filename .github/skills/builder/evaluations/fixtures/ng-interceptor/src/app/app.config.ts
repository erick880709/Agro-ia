import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { authInterceptor } from './core/auth-interceptor';
import { API_BASE_URL } from './core/api-base-url';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    { provide: API_BASE_URL, useValue: 'https://api.bank.test' },
    provideHttpClient(withInterceptors([authInterceptor])),
  ],
};
