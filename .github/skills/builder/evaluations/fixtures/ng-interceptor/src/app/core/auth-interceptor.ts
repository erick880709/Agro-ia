import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthSession } from './auth-session';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthSession).token();
  return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};
