import { Component } from '@angular/core';
import { ErrorListContainer } from '../../containers/error-list/error-list.container';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [ErrorListContainer],
  templateUrl: './dashboard.page.html'
})
export class DashboardPage {}
