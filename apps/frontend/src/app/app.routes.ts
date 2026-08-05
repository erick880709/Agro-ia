import { Routes } from '@angular/router';
import { LayoutComponent } from './layout/layout.component';

export const routes: Routes = [
  {
    path: '',
    component: LayoutComponent,
    children: [
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      {
        path: 'cultivos',
        loadComponent: () =>
          import('./features/cultivos/cultivos.component').then((m) => m.CultivosComponent),
      },
      {
        path: 'recomendaciones',
        loadComponent: () =>
          import('./features/recomendaciones/recomendaciones.component').then(
            (m) => m.RecomendacionesComponent
          ),
      },
      {
        path: 'iot',
        loadComponent: () =>
          import('./features/iot/iot.component').then((m) => m.IotComponent),
      },
      {
        path: 'chat',
        loadComponent: () =>
          import('./features/chat/chat.component').then((m) => m.ChatComponent),
      },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
    ],
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login.component').then((m) => m.LoginComponent),
  },
  { path: '**', redirectTo: '' },
];
