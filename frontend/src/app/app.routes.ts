import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/dashboard/dashboard.page').then(m => m.DashboardPage)
  },
  {
    path: 'simulate',
    loadComponent: () =>
      import('./pages/simulations/simulations.page').then(m => m.SimulationsPage)
  }
];
